"""Minimal Linux supervisor for known AppOS child processes, NOT a sandbox."""
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass

def host_memory():
    try:
        values = {}
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                k, _, v = line.partition(":")
                values[k] = int(v.strip().split()[0]) * 1024
        return values.get("MemAvailable"), values.get("MemTotal")
    except (OSError, ValueError, IndexError):
        return None, None

def process_rss(pid):
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return None

@dataclass
class ManagedApp:
    name: str
    proc: subprocess.Popen
    started: float

    def snapshot(self):
        active = self.proc.poll() is None
        return {"name": self.name, "pid": self.proc.pid, "running": active,
                "exit_code": self.proc.returncode,
                "rss": process_rss(self.proc.pid) if active else None}

    def stop(self, force=False):
        """Signal the owned POSIX session, not only its initial PID.

        No sandbox guarantee: descendants can create their own sessions.
        """
        if self.proc.poll() is not None:
            return
        sig = signal.SIGKILL if force else signal.SIGTERM
        if os.name == "posix":
            try:
                os.killpg(self.proc.pid, sig)
            except ProcessLookupError:
                pass
        elif force:
            self.proc.kill()
        else:
            self.proc.terminate()

    def wait(self, timeout=None):
        return self.proc.wait(timeout=timeout)

class Supervisor:
    def __init__(self):
        self.apps = []

    def launch(self, app, armed=False):
        argv = app["entry"]["command"]
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError("Invalid command")
        cmd = [sys.executable if argv[0] == "python3" else argv[0], *argv[1:]]
        if armed:
            if app['id'] != 'manifold.playroom':
                raise ValueError('Heartbeat watchdog is currently supported only by Playroom Studio')
            cmd = [sys.executable, '-m', 'AppOS.Latent.watchdog', '--timeout', '12', '--', *cmd]
        def lower_priority():
            os.nice(10)
        env=os.environ.copy()
        if armed:
            env['PYTHONPATH']=str(__import__('pathlib').Path(__file__).resolve().parents[2])+os.pathsep+env.get('PYTHONPATH','')
        process = subprocess.Popen(cmd, cwd=app["_directory"], env=env, start_new_session=True,
                                   preexec_fn=lower_priority if os.name == "posix" else None)
        item = ManagedApp(app["name"], process, time.monotonic())
        self.apps.append(item)
        return item

    def snapshots(self):
        return [app.snapshot() for app in self.apps]

    def reap_completed(self):
        """Bound retained exited-process history without touching live apps."""
        finished = [app for app in self.apps if app.proc.poll() is not None]
        self.apps = [app for app in self.apps if app.proc.poll() is None]
        return finished
