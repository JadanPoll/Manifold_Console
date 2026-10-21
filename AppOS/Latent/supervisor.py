"""Minimal Linux supervisor for known AppOS child processes, NOT a sandbox."""
import os
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
        if self.proc.poll() is not None:
            return
        if force:
            self.proc.kill()
        else:
            self.proc.terminate()

class Supervisor:
    def __init__(self):
        self.apps = []

    def launch(self, app):
        argv = app["entry"]["command"]
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError("Invalid command")
        cmd = [sys.executable if argv[0] == "python3" else argv[0], *argv[1:]]
        def lower_priority():
            os.nice(10)
        process = subprocess.Popen(cmd, cwd=app["_directory"], start_new_session=True,
                                   preexec_fn=lower_priority if os.name == "posix" else None)
        item = ManagedApp(app["name"], process, time.monotonic())
        self.apps.append(item)
        return item

    def snapshots(self):
        return [app.snapshot() for app in self.apps]
