"""Opt-in, unprivileged diagnostic bundle for a command or the current host.

Examples (repository root):
    python3 -m AppOS.Latent.diagnose snapshot
    python3 -m AppOS.Latent.diagnose run --seconds 12 -- python3 Playroom/Playground/gravity.py

No graphics dependency, privilege escalation, persistent service, or system changes.
Results include potentially sensitive process commands and environment metadata:
inspect the archive before sharing.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def _read(path, limit=20000):
    try:
        return Path(path).read_text(errors="replace")[:limit]
    except (OSError, ValueError) as exc:
        return {"unavailable": type(exc).__name__}


def _command(args, timeout=3):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return {"returncode": p.returncode, "stdout": p.stdout[-20000:], "stderr": p.stderr[-4000:]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"unavailable": type(exc).__name__}


def _process(pid):
    base = Path("/proc") / str(pid)
    result = {"pid": pid, "status": _read(base / "status", 6000),
              "wchan": _read(base / "wchan", 256),
              "schedstat": _read(base / "schedstat", 256)}
    try:
        result["cmdline"] = (base / "cmdline").read_bytes()[:4096].replace(b"\0", b" ").decode(errors="replace")
    except OSError:
        result["cmdline"] = None
    try:
        threads = sorted((base / "task").iterdir(), key=lambda p: int(p.name))
        result["threads"] = [{"tid": int(t.name), "wchan": _read(t / "wchan", 128),
                              "schedstat": _read(t / "schedstat", 128)}
                             for t in threads[:32]]
        result["thread_count"] = len(threads)
    except OSError:
        result["threads"] = []
    return result


def _host():
    data = {"timestamp_wall_ns": time.time_ns(), "timestamp_mono_ns": time.monotonic_ns(),
            "platform": platform.platform(), "python": sys.version,
            "session": {key: os.environ.get(key) for key in
                        ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_CURRENT_DESKTOP")},
            "kernel": _command(["uname", "-a"]),
            "display": _command(["wlr-randr"]) if shutil.which("wlr-randr") else {"unavailable": "wlr-randr not installed"},
            "meminfo": _read("/proc/meminfo", 5000),
            "tools": {tool: shutil.which(tool) for tool in ("strace", "gdb", "xtrace", "gcc", "perf")},
            "processes": []}
    for name in ("Xwayland", "wayfire", "labwc"):
        pids = _command(["pgrep", "-x", name])
        if pids.get("returncode") == 0:
            for pid in pids["stdout"].split():
                if pid.isdecimal():
                    data["processes"].append(_process(int(pid)))
    return data


def _terminate(group_pid, proc):
    if proc.poll() is not None:
        return
    try:
        os.killpg(group_pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(group_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass


def collect(command, seconds, interval, output):
    if command and command[0] == "--":
        command = command[1:]
    if seconds < 1 or seconds > 120 or interval < 0.1 or interval > 10:
        raise ValueError("seconds must be 1..120; interval 0.1..10")
    if not command and output is None:
        pass
    with tempfile.TemporaryDirectory(prefix="manifold-diagnostic-") as folder:
        directory = Path(folder)
        (directory / "host.json").write_text(json.dumps(_host(), indent=2))
        meta = {"command": command, "seconds": seconds, "interval": interval,
                "started_wall_ns": time.time_ns()}
        if command:
            with (directory / "stdout.txt").open("w") as stdout, (directory / "stderr.txt").open("w") as stderr, (directory / "samples.jsonl").open("w") as samples:
                try:
                    proc = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                            start_new_session=True)
                except OSError as exc:
                    meta["launch_error"] = str(exc)
                else:
                    meta["pid"] = proc.pid
                    end = time.monotonic() + seconds
                    try:
                        while time.monotonic() < end and proc.poll() is None:
                            item = {"timestamp_mono_ns": time.monotonic_ns(),
                                    "child": _process(proc.pid)}
                            samples.write(json.dumps(item) + "\n")
                            samples.flush()
                            time.sleep(min(interval, max(0, end - time.monotonic())))
                    except KeyboardInterrupt:
                        meta["interrupted"] = True
                    finally:
                        _terminate(proc.pid, proc)
                    meta["exit_code"] = proc.poll()
                    meta["terminated_by_collector"] = bool(meta["exit_code"] is not None and proc.returncode in (-signal.SIGTERM, -signal.SIGKILL))
        meta["finished_wall_ns"] = time.time_ns()
        (directory / "result.json").write_text(json.dumps(meta, indent=2))
        if output is None:
            output = Path.cwd() / ("manifold_diagnostic_" + time.strftime("%Y%m%d-%H%M%S") + ".zip")
        else:
            output = Path(output).expanduser().resolve()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for entry in directory.iterdir():
                archive.write(entry, arcname=entry.name)
    return output


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_subparsers(dest="mode", required=True)
    snapshot = modes.add_parser("snapshot", help="Capture read-only host state")
    snapshot.add_argument("--output")
    run = modes.add_parser("run", help="Bounded command with per-process observations")
    run.add_argument("--seconds", type=float, default=10)
    run.add_argument("--interval", type=float, default=0.5)
    run.add_argument("--output")
    run.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args(argv)
    if args.mode == "run" and not args.command:
        p.error("run requires a command after --")
    out = collect(args.command if args.mode == "run" else [], args.seconds if args.mode == "run" else 1,
                  args.interval if args.mode == "run" else 0.5, args.output)
    print("Diagnostic archive:", out)


if __name__ == "__main__":
    main()
