"""Optional MediaPipe Tasks pose viewer for a video file or camera.

Pure observer: no gesture control, no keyboard injection, no device installer.
"""
import argparse
import sys
import time
from pathlib import Path

# Pose Landmarker uses MediaPipe's 33 body landmarks.
CONNECTIONS = (
    (11,12),(11,13),(13,15),(12,14),(14,16),
    (11,23),(12,24),(23,24),(23,25),(25,27),(24,26),(26,28),
    (27,29),(29,31),(28,30),(30,32),
    (15,17),(15,19),(15,21),(16,18),(16,20),(16,22),
    (17,19),(18,20),(19,21),(20,22),
    (0,1),(1,2),(2,3),(3,7),(0,4),(4,5),(5,6),(6,8),
)

def timestamp_ms(source, capture, start_ns, last_ms):
    # File timestamps are not always reliable. Prefer monotonic clock for
    # camera feeds; ensure task timestamps strictly increase.
    if source == "camera":
        candidate = (time.monotonic_ns() - start_ns) // 1_000_000
    else:
        candidate = round(capture.get(0))  # cv2.CAP_PROP_POS_MSEC == 0
        if candidate <= 0:
            candidate = (time.monotonic_ns() - start_ns) // 1_000_000
    return max(last_ms + 1, int(candidate))

def draw_pose(frame, poses, cv2):
    h, w = frame.shape[:2]
    for landmarks in poses:
        for a, b in CONNECTIONS:
            pa, pb = landmarks[a], landmarks[b]
            if min(pa.visibility or 0, pb.visibility or 0) < .4:
                continue
            cv2.line(frame,(round(pa.x*w),round(pa.y*h)),
                     (round(pb.x*w),round(pb.y*h)),(50,230,110),2)
        for p in landmarks:
            if (p.visibility or 0) >= .4:
                cv2.circle(frame,(round(p.x*w),round(p.y*h)),3,(30,180,255),-1)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model",type=Path,required=True,
                        help="local MediaPipe Pose Landmarker .task model")
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video",type=Path)
    source.add_argument("--camera",type=int)
    parser.add_argument("--max-width",type=int,default=960)
    args=parser.parse_args(argv)
    if not args.model.is_file():
        parser.error("model not found: " + str(args.model))
    if args.max_width < 64:
        parser.error("--max-width must be >= 64")
    try:
        import cv2
        import mediapipe as mp
    except ImportError as exc:
        raise SystemExit(f"Optional video dependencies missing: {exc}. Install in a separate virtual environment.")
    options=mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_poses=1)
    source_id=args.camera if args.camera is not None else str(args.video)
    cap=cv2.VideoCapture(source_id)
    if not cap.isOpened():
        raise SystemExit("Unable to open video source: " + str(source_id))
    started=time.monotonic_ns()
    last_ms=-1
    frames=0
    last_fps=time.monotonic()
    try:
        with mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
            while True:
                ok,frame=cap.read()
                if not ok: break
                h,w=frame.shape[:2]
                if w>args.max_width:
                    frame=cv2.resize(frame,(args.max_width,round(h*args.max_width/w)))
                rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                image=mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
                stamp=timestamp_ms("camera" if args.camera is not None else "file",
                                   cap,started,last_ms)
                last_ms=stamp
                result=detector.detect_for_video(image,stamp)
                draw_pose(frame,result.pose_landmarks,cv2)
                frames+=1
                now=time.monotonic()
                if now-last_fps>=1:
                    print(f"pose: {frames/(now-last_fps):.1f} processed FPS",flush=True)
                    frames=0
                    last_fps=now
                cv2.imshow("Manifold / Pose Tracking (ESC to exit)",frame)
                if cv2.waitKey(1)&0xff==27: break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return 0

if __name__=="__main__":
    sys.exit(main())
