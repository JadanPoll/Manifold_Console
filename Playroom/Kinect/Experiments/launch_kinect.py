"""Select an existing Kinect-capable Python interpreter; never install packages."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "kinect_live.py"


def candidate_interpreters():
    configured = os.environ.get("MANIFOLD_KINECT_PYTHON")
    paths = [configured] if configured else []
    paths += [
        str(Path.home() / ".venvs/beastgames-kinect/bin/python"),
        str(Path.home() / "Desktop/pdflets_lean_v1_1/.venv/bin/python"),
        sys.executable,
    ]
    seen = set()
    for value in paths:
        if value and value not in seen:
            seen.add(value)
            yield value


def supports_kinect(python):
    if not Path(python).is_file():
        return False
    probe = "import freenect, numpy; print('ok')"
    try:
        result = subprocess.run([python, "-c", probe], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=5)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main():
    for candidate in candidate_interpreters():
        if supports_kinect(candidate):
            os.execv(candidate, [candidate, str(SCRIPT)])
    print("No working freenect+numpy Python environment found.\n"
          "Set MANIFOLD_KINECT_PYTHON to your existing Kinect interpreter, e.g.\n"
          "  MANIFOLD_KINECT_PYTHON=/path/to/venv/bin/python "
          "python3 Playroom/Kinect/Experiments/launch_kinect.py\n"
          "The previously working camera launcher is ~/.local/bin/kinect-run.\n"
          "Do not reinstall drivers merely to launch this application.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
