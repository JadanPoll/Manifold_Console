"""Development-mode process launcher. NOT a sandbox or permission enforcer."""
import os
from pathlib import Path
import subprocess

def launch(app):
    directory = Path(app["_directory"]).resolve()
    argv = app["entry"]["command"]
    # Avoid an implicit shell; do not claim that this prevents malicious executables.
    program = argv[0]
    if program == "python3":
        program = "python3"
    return subprocess.Popen([program, *argv[1:]], cwd=directory, env=os.environ.copy())

