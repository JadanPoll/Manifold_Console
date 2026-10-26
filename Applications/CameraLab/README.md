# Camera Lab

The fastest path from a camera to an experiment. Start through Manifold Home:

```sh
cd ~/Desktop/Manifold_Console
git pull --ff-only
python3 -m AppOS.Shell.home
```

Select **Camera Lab** and **Launch selected**.

Or launch just this tool:

```sh
python3 Applications/CameraLab/lab.py
```

## Modes

- **Start webcam studio:** OpenCV video. Keys `1` normal, `2` edges, `3` motion (frame difference), `s` save a screenshot, `q` or ESC to exit.
- **Open a video file:** same modes without any physical camera.
- **Kinect depth point:** reuses the original `launch_kinect.py` and native depth analysis; shows the nearest valid depth location.
- **Kinect depth image / edges:** an **optional** live Kinect depth video viewer with image, edges and motion modes (`1`, `2`, `3`). Requires `cv2` alongside the working freenect Python installation; the native point viewer remains available separately.
- **Check Kinect:** non-invasive USB/library/interpreter preflight; no capture.
- **Pose with webcam / video:** launches MediaPipe Pose Landmarker when both the optional Python dependency and a local `.task` model are available. Browse to the model once in the current Lab session.

For quick terminal access without Home:

```sh
python3 Applications/CameraLab/studio.py --camera 0
python3 Applications/CameraLab/studio.py --camera 0 --mode edges
python3 Applications/CameraLab/studio.py --video /path/to/video.mp4
python3 Playroom/Kinect/Experiments/launch_kinect.py --check
python3 Playroom/Kinect/Experiments/launch_kinect.py --mode depth
```

The basic studio and the optional Kinect depth-image studio need `cv2` and `numpy` in the interpreter used to launch
Manifold; it **does not** require MediaPipe. It never installs packages or
opens devices at startup. Screenshot capture only happens when pressing S,
saved under `~/Pictures/Manifold/`.

Pose dependencies and setup are documented in
[`Packages/vision.pose.mediapipe/README.md`](../../Packages/vision.pose.mediapipe/README.md).
Get a `.task` model from
https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker
and select the file in Camera Lab. If `~/.venvs/manifold-pose/bin/python`
exists, the Lab will use it for Pose; otherwise it uses its own interpreter.
A present environment is **not proof of import compatibility**; read the
copyable diagnostics if the child process fails.

**Important:** Kinect 1473 depth is not equivalent to `/dev/video0`. Use the
Kinect action for Kinect depth, and webcam actions for UVC cameras. The
original Kinect capture is exclusive. Depth-image display is intentionally 320px wide by default to limit Pi desktop rendering load. Avoid running multiple Kinect programs
concurrently. Manifold Connect routing and shared sensor ownership are not
yet implemented; Camera Lab currently runs one experiment at a time.

The code is a first usable experimental entry point, not yet hardware-verified
on this Pi. Read the diagnostics in the Camera Lab window if a camera cannot
be opened; copy them as needed.
