"""Optional live Kinect v1 depth-image playground.

Requires the already-working freenect Python interpreter, NumPy and OpenCV.
Does not touch the existing native nearest-point viewer or reinstall drivers.
Keys: 1 depth, 2 edges, 3 motion, s snapshot, q/ESC quit.
"""
import argparse
from datetime import datetime
from pathlib import Path
import sys
import time


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("depth", "edges", "motion"), default="depth")
    parser.add_argument("--width", type=int, default=320, help="display width (default: low-cost 320 px)")
    args = parser.parse_args(argv)
    if not 160 <= args.width <= 640:
        parser.error("width must be between 160 and 640")
    try:
        import freenect
        import cv2
        import numpy as np
    except ImportError as exc:
        print("Kinect depth image requires freenect, cv2, numpy in the SAME interpreter.", file=sys.stderr)
        print("Import error:", exc, file=sys.stderr)
        print("Use the Kinect depth point viewer if OpenCV is unavailable.", file=sys.stderr)
        return 2

    # Camera is acquired only on the first sync_get_depth call.
    mode = args.mode
    previous = None
    frames = 0
    t0 = time.monotonic()
    window = "Manifold / Kinect Depth Lab"
    print("Kinect depth: 1 image, 2 edges, 3 motion, S snapshot, Q/ESC quit", flush=True)
    try:
        while True:
            frame, stamp = freenect.sync_get_depth(format=freenect.DEPTH_MM)
            if frame is None:
                print("Kinect returned no depth frame. Check USB ownership and firmware.", file=sys.stderr)
                break
            height, width = frame.shape
            if width > args.width:
                frame = cv2.resize(frame, (args.width, max(1, round(height * args.width / width))),
                                   interpolation=cv2.INTER_NEAREST)
            # Metric depth: 0/invalid black; ~0.5m near bright to 4.0m far dark.
            valid = (frame >= 500) & (frame <= 4000)
            scaled = (4000.0 - frame.astype(np.float32)) * (255.0 / 3500.0)
            gray = np.where(valid, np.clip(scaled, 0, 255), 0).astype(np.uint8)
            if mode == "edges":
                output = cv2.cvtColor(cv2.Canny(gray, 60, 120), cv2.COLOR_GRAY2BGR)
            elif mode == "motion":
                delta = cv2.absdiff(gray, previous) if previous is not None and previous.shape == gray.shape else np.zeros_like(gray)
                _, mask = cv2.threshold(delta, 20, 255, cv2.THRESH_BINARY)
                output = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            else:
                output = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            previous = gray.copy()
            frames += 1
            elapsed = max(1e-6, time.monotonic() - t0)
            cv2.putText(output, f"KINECT {mode.upper()} | {frames/elapsed:.1f} FPS | 1/2/3 S Q",
                        (5, 18), cv2.FONT_HERSHEY_SIMPLEX, .35, (0, 255, 210), 1, cv2.LINE_AA)
            cv2.imshow(window, output)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key in (ord("1"), ord("2"), ord("3")):
                mode = {"1":"depth", "2":"edges", "3":"motion"}[chr(key)]
                previous = None
                print("Kinect mode: " + mode, flush=True)
            elif key == ord("s"):
                destination = Path.home() / "Pictures" / "Manifold"
                destination.mkdir(parents=True, exist_ok=True)
                output_path = destination / ("kinect_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png")
                if cv2.imwrite(str(output_path), output):
                    print("Saved " + str(output_path), flush=True)
                else:
                    print("Could not save " + str(output_path), file=sys.stderr, flush=True)
    except KeyboardInterrupt:
        print("Capture interrupted.", flush=True)
    except Exception as exc:
        print(f"Kinect capture error: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
        return 2
    finally:
        try:
            freenect.sync_stop()
        except Exception as exc:
            print(f"Kinect stop warning: {exc}", file=sys.stderr, flush=True)
        cv2.destroyAllWindows()
        print("Kinect depth capture closed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
