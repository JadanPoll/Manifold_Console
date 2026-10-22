"""Launch a single X11 app inside a private, software-backed XWayland server.

This is intentionally rootful: independently launched rootless XWayland requires
compositor XWM cooperation. On XWayland 22.1 the container may be fullscreen.
The launcher NEVER changes the system XWayland, compositor, or kernel.

Run from repository root:
  python3 -m AppOS.Runtime.software_xwayland -- python3 Playroom/Playground/gravity.py
  python3 -m AppOS.Runtime.software_xwayland --geometry 1024x768 -- python3 ...
The geometry option requires XWayland 23.1+.
"""
import argparse
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]


def available_display(start=110, stop=190):
    """Reserve a free display number using standard X server locks/sockets.

    This is a best-effort availability check, not an atomic reservation.
    Xwayland itself rejects a conflicting display.
    """
    for number in range(start, stop):
        if (Path("/tmp/.X11-unix") / ("X" + str(number))).exists():
            continue
        if (Path("/tmp") / (".X" + str(number) + "-lock")).exists():
            continue
        return number
    raise RuntimeError("No free private X11 display in range :110..:189")


def auth_record(number, cookie):
    """MIT-MAGIC-COOKIE-1 record with FamilyWild, Xauthority wire format."""
    def field(raw):
        return len(raw).to_bytes(2, "big") + raw
    return (bytes((255, 255)) + field(b"") + field(str(number).encode("ascii"))
            + field(b"MIT-MAGIC-COOKIE-1") + field(cookie))


def wait_ready(server, number, auth, timeout=8):
    """Test actual authenticated X11 connection, not just socket existence."""
    target = str(number)
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("Private XWayland exited before readiness")
        path = "/tmp/.X11-unix/X" + target
        if os.path.exists(path):
            env = os.environ.copy()
            env.update({"DISPLAY": ":" + target, "XAUTHORITY": str(auth)})
            check = subprocess.run(
                [sys.executable, "-c",
                 "import tkinter as t; x=t.Tk(); x.withdraw(); x.update(); x.destroy()"],
                env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                timeout=3, text=True)
            if check.returncode == 0:
                return
            last_error = check.stderr.strip()[-300:]
        time.sleep(0.15)
    raise RuntimeError("Private XWayland did not accept an authenticated Tk connection"
                       + (": " + last_error if last_error else ""))


def stop(proc):
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", metavar="WxH",
                        help="rootful window dimensions (requires XWayland 23.1+)")
    parser.add_argument("--seconds", type=float, default=0,
                        help="optional maximum duration, 0 means until app exits")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("supply an application after --")
    if args.seconds < 0 or args.seconds > 3600:
        parser.error("--seconds must be 0..3600")
    if args.geometry:
        import re
        if not re.fullmatch(r"[1-9][0-9]{1,4}x[1-9][0-9]{1,4}", args.geometry):
            parser.error("--geometry must be WxH, positive integer dimensions")
    if not os.environ.get("WAYLAND_DISPLAY"):
        parser.error("WAYLAND_DISPLAY missing; run from your Wayland desktop session")
    if not shutil.which("Xwayland"):
        parser.error("Xwayland binary not found")

    number = available_display()
    with tempfile.TemporaryDirectory(prefix="manifold-software-xwayland-") as folder:
        directory = Path(folder)
        auth = directory / "Xauthority"
        auth.write_bytes(auth_record(number, secrets.token_bytes(16)))
        auth.chmod(0o600)
        server_log = (directory / "xwayland.log").open("w")
        server = app = None
        env = os.environ.copy()
        env["XAUTHORITY"] = str(auth)
        env["XWAYLAND_NO_GLAMOR"] = "1"
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        cmd = ["Xwayland", ":" + str(number), "-shm", "-auth", str(auth),
               "-nolisten", "tcp"]
        if args.geometry:
            cmd.extend(["-geometry", args.geometry])
        try:
            server = subprocess.Popen(cmd, env=env, stdout=server_log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
            wait_ready(server, number, auth)
            child_env = os.environ.copy()
            child_env["DISPLAY"] = ":" + str(number)
            child_env["XAUTHORITY"] = str(auth)
            child_env["LIBGL_ALWAYS_SOFTWARE"] = "1"
            print("Manifold software XWayland on DISPLAY=:" + str(number), flush=True)
            print("This nested desktop may occupy the entire screen on XWayland 22.1.",
                  flush=True)
            app = subprocess.Popen(command, cwd=ROOT, env=child_env,
                                   start_new_session=True)
            if args.seconds:
                try:
                    return app.wait(timeout=args.seconds)
                except subprocess.TimeoutExpired:
                    print("Time limit reached; stopping app.", flush=True)
                    return 124
            return app.wait()
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            print("Software backend unavailable: " + str(exc), file=sys.stderr)
            server_log.flush()
            try:
                print((directory / "xwayland.log").read_text(errors="replace")[-1500:],
                      file=sys.stderr)
            except OSError:
                pass
            return 2
        except KeyboardInterrupt:
            return 130
        finally:
            stop(app)
            stop(server)
            server_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
