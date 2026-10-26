"""Find and launch the existing Kinect Python stack without installing anything.

Use --check for a non-invasive preflight (no camera is opened).
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = HERE / "kinect_live.py"
DEPTH_STUDIO = HERE / "kinect_depth_tk.py"
NATIVE = ROOT / "AppOS/Native/build/libmcdepth.so"
USB_IDS = {"02bf": "Kinect camera", "02be": "Kinect audio", "02c2": "Kinect motor"}


def candidate_interpreters():
    configured = os.environ.get("MANIFOLD_KINECT_PYTHON")
    paths = [configured] if configured else []
    paths.extend((
        str(Path.home() / ".venvs/beastgames-kinect/bin/python"),
        str(Path.home() / "Desktop/PDFlets/.venv/bin/python"),
        str(Path.home() / "Desktop/pdflets_lean_v1_1/.venv/bin/python"),
        sys.executable,
    ))
    seen = set()
    for value in paths:
        if value and value not in seen:
            seen.add(value)
            yield value


def kinect_env():
    env = os.environ.copy()
    local_lib = str(Path.home() / ".local/lib")
    env["LD_LIBRARY_PATH"] = local_lib + (os.pathsep + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    return env


def supports_kinect(python):
    if not Path(python).is_file():
        return False
    try:
        result = subprocess.run(
            [python, "-c", "import freenect, numpy; print('ok')"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, env=kinect_env())
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def usb_devices():
    found = []
    base = Path("/sys/bus/usb/devices")
    try:
        devices = list(base.iterdir())
    except OSError:
        return found
    for device in devices:
        try:
            vendor = (device / "idVendor").read_text().strip().lower()
            product = (device / "idProduct").read_text().strip().lower()
        except OSError:
            continue
        if vendor == "045e" and product in USB_IDS:
            found.append((product, USB_IDS[product]))
    return found


def check(require_native=True):
    devices = usb_devices()
    print("Kinect 1473 USB:", ", ".join(name for _, name in devices) if devices else
          "not detected in /sys/bus/usb/devices")
    print("Native depth library:", str(NATIVE), "present" if NATIVE.is_file() else "missing")
    interpreter = next((p for p in candidate_interpreters() if supports_kinect(p)), None)
    print("Python freenect + NumPy:", interpreter if interpreter else "not found")
    if interpreter and (not require_native or NATIVE.is_file()) and any(product == "02bf" for product, _ in devices):
        print("Kinect detected and software found. Open a depth viewer to check live capture.")
        return interpreter, 0
    print("Preflight incomplete. No packages, drivers, or USB devices were changed.")
    if require_native and not NATIVE.is_file():
        print("Build existing local C library: make -C AppOS/Native")
    if not interpreter:
        print("Set MANIFOLD_KINECT_PYTHON to your existing working Kinect Python interpreter.")
    return interpreter, 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="inspect dependencies, do not open Kinect")
    parser.add_argument("--mode", choices=("point", "depth", "edges", "motion"),
                        default="point", help="point is the established nearest-point viewer")
    args = parser.parse_args(argv)
    interpreter, code = check(require_native=args.mode == "point")
    if args.check or code:
        return code
    if args.mode == "point":
        os.execve(interpreter, [interpreter, str(SCRIPT)], kinect_env())
    os.execve(interpreter, [interpreter, str(DEPTH_STUDIO), "--mode", args.mode], kinect_env())


if __name__ == "__main__":
    raise SystemExit(main())
