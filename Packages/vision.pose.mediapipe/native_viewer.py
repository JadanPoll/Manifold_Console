"""Camera/video viewer using Manifold's native pose ABI.

Python owns only capture/display. Pose inference is libmanifold_pose.so.
"""
import argparse
import ctypes
from pathlib import Path
import sys
import time
import os

LIB = Path.home() / ".local/lib/manifold/libmanifold_pose.so"
DEFAULT_MODEL = Path.home() / ".local/share/manifold/models/pose_landmarker_lite.task"
CONNECTIONS = (
    (11,12),(11,13),(13,15),(12,14),(14,16),
    (11,23),(12,24),(23,24),(23,25),(25,27),(24,26),(26,28),
    (27,29),(29,31),(28,30),(30,32),(15,17),(15,19),(15,21),
    (16,18),(16,20),(16,22),(17,19),(18,20),(19,21),(20,22),
)

class Landmark(ctypes.Structure):
    _fields_=[("x",ctypes.c_float),("y",ctypes.c_float),("z",ctypes.c_float),
              ("visibility",ctypes.c_float),("presence",ctypes.c_float)]

class PoseFrame(ctypes.Structure):
    _fields_=[("timestamp_ms",ctypes.c_uint64),("count",ctypes.c_uint32),
              ("landmarks",Landmark*33)]

def load_backend():
    if not LIB.is_file():
        raise SystemExit("Native body tracking is not set up yet.")

    # The private OpenCV libraries are installed beside libmanifold_pose.so.
    # ELF resolves a library's *dependencies* using the process loader path,
    # not the directory of an absolute dlopen() path. Re-exec once so the
    # loader sees this directory from process start.
    runtime_dir = LIB.parent
    marker = "MANIFOLD_POSE_RUNTIME_READY"
    if os.environ.get(marker) != "1":
        env = os.environ.copy()
        current = env.get("LD_LIBRARY_PATH", "")
        parts = [str(runtime_dir)]
        if current:
            parts.append(current)
        env["LD_LIBRARY_PATH"] = ":".join(parts)
        env[marker] = "1"
        os.execve(sys.executable, [sys.executable, *sys.argv], env)

    try:
        lib=ctypes.CDLL(str(LIB), mode=ctypes.RTLD_GLOBAL)
    except OSError as exc:
        raise SystemExit("Native body tracking runtime could not load: " + str(exc))
    lib.mf_pose_create.argtypes=[ctypes.c_char_p]
    lib.mf_pose_create.restype=ctypes.c_void_p
    lib.mf_pose_process_rgb.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.POINTER(PoseFrame)]
    lib.mf_pose_process_rgb.restype=ctypes.c_int
    lib.mf_pose_last_error.argtypes=[ctypes.c_void_p]
    lib.mf_pose_last_error.restype=ctypes.c_char_p
    lib.mf_pose_destroy.argtypes=[ctypes.c_void_p]
    return lib

def draw(frame,result,cv2):
    h,w=frame.shape[:2]
    def visible(i):
        return i<result.count and result.landmarks[i].visibility>=.35
    for a,b in CONNECTIONS:
        if visible(a) and visible(b):
            pa,pb=result.landmarks[a],result.landmarks[b]
            cv2.line(frame,(round(pa.x*w),round(pa.y*h)),
                     (round(pb.x*w),round(pb.y*h)),(50,230,110),2)
    for i in range(result.count):
        p=result.landmarks[i]
        if p.visibility>=.35:
            cv2.circle(frame,(round(p.x*w),round(p.y*h)),3,(30,180,255),-1)

def main(argv=None):
    p=argparse.ArgumentParser()
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument("--camera",type=int)
    source.add_argument("--video",type=Path)
    p.add_argument("--model",type=Path,default=DEFAULT_MODEL)
    p.add_argument("--max-width",type=int,default=960)
    args=p.parse_args(argv)
    if not args.model.is_file():
        raise SystemExit("Pose model is missing: "+str(args.model))
    try:
        import cv2
    except ImportError:
        raise SystemExit("Camera image tools are not set up yet.")
    lib=load_backend()
    ctx=lib.mf_pose_create(str(args.model).encode())
    if not ctx:
        raise SystemExit("Could not create native pose backend.")
    source_id=args.camera if args.camera is not None else str(args.video)
    cap=cv2.VideoCapture(source_id)
    if not cap.isOpened():
        lib.mf_pose_destroy(ctx)
        raise SystemExit("Could not open the selected camera or video.")
    started=time.monotonic_ns()
    last=-1
    try:
        while True:
            ok,frame=cap.read()
            if not ok: break
            h,w=frame.shape[:2]
            if w>args.max_width:
                frame=cv2.resize(frame,(args.max_width,round(h*args.max_width/w)))
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            if not rgb.flags["C_CONTIGUOUS"]:
                rgb=rgb.copy()
            stamp=(time.monotonic_ns()-started)//1_000_000
            stamp=max(last+1,stamp);last=stamp
            result=PoseFrame()
            ptr=rgb.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
            rc=lib.mf_pose_process_rgb(ctx,ptr,rgb.shape[1],rgb.shape[0],
                                       rgb.strides[0],stamp,ctypes.byref(result))
            if rc:
                err=lib.mf_pose_last_error(ctx)
                raise RuntimeError(err.decode(errors="replace") if err else "Pose inference failed.")
            draw(frame,result,cv2)
            cv2.putText(frame,f"NATIVE POSE | {result.count} landmarks | Q quit",
                        (12,25),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,210),1,cv2.LINE_AA)
            cv2.imshow("Manifold / Native Pose",frame)
            if cv2.waitKey(1)&0xff in (ord("q"),27): break
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print("Body tracking stopped: "+str(exc),file=sys.stderr,flush=True)
        return 2
    finally:
        cap.release()
        cv2.destroyAllWindows()
        lib.mf_pose_destroy(ctx)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
