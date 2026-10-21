"""Opt-in separate-process watchdog for cooperative GUI experiments (Linux only).

Usage: python -m AppOS.Latent.watchdog --timeout 12 -- python3 path/to/app.py
The child must update APPOS_HEARTBEAT_FILE at least once per timeout interval.
No heartbeat support means do not arm automatic termination.
"""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--timeout",type=float,default=12)
    parser.add_argument("command",nargs=argparse.REMAINDER)
    args=parser.parse_args()
    command=args.command[1:] if args.command[:1]==["--"] else args.command
    if not command or not 3<=args.timeout<=300:
        parser.error("require command and timeout in [3,300]")
    if os.name!="posix":
        parser.error("watchdog currently requires POSIX/Linux")
    owner=os.getppid()
    with tempfile.TemporaryDirectory(prefix="appos-latent-") as folder:
        heartbeat=Path(folder)/"heartbeat"
        heartbeat.touch()
        env=os.environ.copy()
        env["APPOS_HEARTBEAT_FILE"]=str(heartbeat)
        env["APPOS_WATCHDOG_TIMEOUT"]=str(args.timeout)
        proc=subprocess.Popen(command,env=env,start_new_session=True)
        reason=None
        try:
            while proc.poll() is None:
                # A dead or reparented owning shell should not orphan a managed app.
                if os.getppid()!=owner:
                    reason="supervisor exited"
                    break
                try:
                    last=heartbeat.stat().st_mtime
                except OSError:
                    last=0
                if time.time()-last>args.timeout:
                    reason="heartbeat expired"
                    break
                time.sleep(.5)
        except KeyboardInterrupt:
            reason="interrupted"
        if reason:
            print("Latent watchdog: "+reason+"; terminating managed process group",flush=True)
            try:
                os.killpg(proc.pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            return 124
        return proc.returncode

if __name__=="__main__":
    raise SystemExit(main())
