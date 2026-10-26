"""Find an existing camera-capable Python without changing system packages.

This only probes known local Python interpreters. It neither opens a camera
nor installs anything. Used by Camera Lab in a background worker.
"""
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys

HOME = Path.home()
CAMERA_VENV = HOME / ".venvs/manifold-camera"
PREFERENCE = HOME / ".config/manifold/camera.json"


def remembered_python():
    try:
        data = json.loads(PREFERENCE.read_text(encoding="utf-8"))
        return data.get("python") if isinstance(data.get("python"), str) else None
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def remember_python(python):
    PREFERENCE.parent.mkdir(parents=True, exist_ok=True)
    PREFERENCE.write_text(json.dumps({"python": str(python)}) + "\\n", encoding="utf-8")


def candidates():
    choices = [
        os.environ.get("MANIFOLD_CAMERA_PYTHON"),
        remembered_python(),
        str(CAMERA_VENV / "bin/python"),
        str(HOME / ".venvs/manifold-pose/bin/python"),
        str(HOME / "Desktop/PDFlets/.venv/bin/python"),
        str(HOME / "Desktop/pdflets_lean_v1_1/.venv/bin/python"),
        str(HOME / ".venvs/beastgames-kinect/bin/python"),
        sys.executable,
        "/usr/local/bin/python3",
        "/usr/bin/python3",
        shutil.which("python3"),
    ]
    seen = set()
    for choice in choices:
        if not choice:
            continue
        path = Path(choice).expanduser()
        if str(path) in seen or not path.is_file():
            continue
        seen.add(str(path))
        yield str(path)


def working_python(check=("cv2", "numpy"), available=None, timeout=4):
    """Return (interpreter or None, number actually probed).

    Tests imports in a child interpreter; never imports CV2 into Camera Lab.
    """
    checked = 0
    for python in candidates() if available is None else available:
        if not Path(python).is_file():
            continue
        checked += 1
        try:
            probe = subprocess.run(
                [str(python), "-c", "; ".join("import " + module for module in check)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=timeout, check=False,
            )
            if probe.returncode == 0:
                return str(python), checked
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None, checked


def install_camera_tools():
    """Explicit, optional user-space setup. No source builds or sudo.

    Returns (success, human-facing summary, technical diagnostics).
    """
    python = str(CAMERA_VENV / "bin/python")
    try:
        if not Path(python).is_file():
            create = subprocess.run(
                [sys.executable, "-m", "venv", str(CAMERA_VENV)],
                capture_output=True, text=True, timeout=45, check=False)
            if create.returncode:
                return False, (
                    "I couldn't create Camera Lab's private setup. You can still use Kinect "
                    "Depth Point, or choose another experiment."
                ), (create.stdout + "\n" + create.stderr).strip()
        package = subprocess.run(
            [python, "-m", "pip", "--disable-pip-version-check", "--no-input",
             "install", "--only-binary=:all:", "numpy", "opencv-python"],
            capture_output=True, text=True, timeout=180, check=False)
        if package.returncode:
            return False, (
                "Camera setup couldn't download or install a compatible image package "
                "right now. Your system installation was not changed, and "
                "other experiments still work."
            ), (package.stdout + "\n" + package.stderr).strip()
        interpreter, _ = working_python(available=[python])
        if not interpreter:
            return False, (
                "Camera tools installed, but couldn't start correctly. "
                "Other experiments are still available."
            ), (package.stdout + "\n" + package.stderr).strip()
        return True, "Camera tools are ready. Opening your selected experiment.", (
            package.stdout + "\n" + package.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, (
            "Camera setup couldn't finish. You can still use the Kinect tools "
            "or try again later."
        ), repr(exc)
