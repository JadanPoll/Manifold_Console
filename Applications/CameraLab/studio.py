"""Interactive webcam/video studio. No MediaPipe, hardware SDK or GUI shell dependency.

Modes: preview (1), Canny edges (2), frame motion (3).
q/ESC exits; s saves the currently displayed frame to ~/Pictures/Manifold.
"""
import argparse
from datetime import datetime
from pathlib import Path
import sys
import time


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--camera", type=int, default=None)
    inputs.add_argument("--video", type=Path)
    parser.add_argument("--mode", choices=("preview", "edges", "motion"), default="preview")
    parser.add_argument("--max-width", type=int, default=960)
    args = parser.parse_args(argv)
    if args.max_width < 64:
        parser.error("--max-width must be at least 64")
    if args.camera is not None and args.camera < 0:
        parser.error("--camera must be nonnegative")
    if args.video and not args.video.is_file():
        parser.error("video does not exist: " + str(args.video))

    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        print("Camera Studio requires OpenCV (cv2) and NumPy in this Python environment.", file=sys.stderr)
        print("Import error:", exc, file=sys.stderr)
        print("Use a Python interpreter with an existing OpenCV installation; no packages were installed.", file=sys.stderr)
        return 2

    source = str(args.video) if args.video else (0 if args.camera is None else args.camera)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Could not open {source!r}. Check that the camera is connected, not busy, and accessible.", file=sys.stderr)
        print("For Kinect 1473 DEPTH, use the separate Kinect mode; it is not a standard RGB webcam.", file=sys.stderr)
        cap.release()
        return 2

    mode = args.mode
    window = "Manifold / Camera Studio"
    previous = None
    processed = 0
    window_started = time.monotonic()
    print(f"Opened {source!r}; keys: 1 preview | 2 edges | 3 motion | s snapshot | q/ESC quit", flush=True)
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("End of video or unable to read a frame.", flush=True)
                break
            height, width = frame.shape[:2]
            if width > args.max_width:
                frame = cv2.resize(frame, (args.max_width, max(1, round(height * args.max_width / width))))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if mode == "edges":
                result = cv2.Canny(gray, 70, 140)
                output = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            elif mode == "motion":
                delta = cv2.absdiff(gray, previous) if previous is not None and previous.shape == gray.shape else np.zeros_like(gray)
                _, mask = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)
                output = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            else:
                output = frame.copy()
            previous = gray.copy()
            processed += 1
            elapsed = time.monotonic() - window_started
            fps = processed / elapsed if elapsed > 0 else 0
            cv2.putText(output, f"{mode.upper()} | {fps:.1f} processed FPS | 1/2/3 mode | S snapshot | Q quit",
                        (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 210), 1, cv2.LINE_AA)
            cv2.imshow(window, output)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in (ord("1"), ord("2"), ord("3")):
                mode = {"1": "preview", "2": "edges", "3": "motion"}[chr(key)]
                previous = None
                print("Mode: " + mode, flush=True)
            elif key == ord("s"):
                output_dir = Path.home() / "Pictures" / "Manifold"
                output_dir.mkdir(parents=True, exist_ok=True)
                dest = output_dir / ("camera_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png")
                if cv2.imwrite(str(dest), output):
                    print("Saved snapshot: " + str(dest), flush=True)
                else:
                    print("Could not save snapshot: " + str(dest), file=sys.stderr, flush=True)
            if processed % 120 == 0:
                print(f"Camera Studio: {mode}; {fps:.1f} processed FPS", flush=True)
    except KeyboardInterrupt:
        print("Interrupted.", flush=True)
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
