"""Kinect acquisition via the existing working Python bindings; analysis in C.

Headless, read-only demonstration; does not open new GUI windows.
Run after building AppOS/Native using the already-working Kinect Python setup.
"""
import ctypes
from pathlib import Path
import time

import freenect
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / "AppOS" / "Native" / "build" / "libmcdepth.so"

class Point(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_uint32),
        ("y", ctypes.c_uint32),
        ("depth", ctypes.c_uint16),
        ("valid", ctypes.c_uint8),
    ]

def main():
    if not LIB.exists():
        raise SystemExit("Build native library first: make -C AppOS/Native")
    native = ctypes.CDLL(str(LIB))
    native.mc_nearest_depth.argtypes = (
        ctypes.POINTER(ctypes.c_uint16),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(Point),
    )
    native.mc_nearest_depth.restype = ctypes.c_int
    last_print = 0.0
    try:
        while True:
            frame, _ = freenect.sync_get_depth()
            if frame is None:
                continue
            if frame.dtype != np.uint16 or not frame.flags.c_contiguous:
                frame = np.ascontiguousarray(frame, dtype=np.uint16)
            height, width = frame.shape
            point = Point()
            result = native.mc_nearest_depth(
                frame.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)),
                width, height, ctypes.byref(point)
            )
            if result:
                raise RuntimeError("native frame dimensions rejected")
            now = time.monotonic()
            if now - last_print >= 0.5:
                if point.valid:
                    print(f"nearest depth: ({point.x}, {point.y}) raw={point.depth}", flush=True)
                else:
                    print("no valid depth sample", flush=True)
                last_print = now
    except KeyboardInterrupt:
        pass
    finally:
        freenect.sync_stop()

if __name__ == "__main__":
    main()
