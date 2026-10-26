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
- **Kinect depth:** reuses the original `launch_kinect.py` that probes `freenect` and loads the existing native depth analysis. Current viewer shows the *nearest valid depth point*, not an entire Kinect video image.
- **Check Kinect:** non-invasive USB/library/interpreter preflight; no capture.
- **Pose with webcam / video:** launches MediaPipe Pose Landmarker when both the optional Python dependency and a local `.task` model are available. Browse to the model once in the current Lab session.

For quick terminal access without Home:

```sh
python3 Applications/CameraLab/studio.py --camera 0
python3 Applications/CameraLab/studio.py --camera 0 --mode edges
python3 Applications/CameraLab/studio.py --video /path/to/video.mp4
python3 Playroom/Kinect/Experiments/launch_kinect.py --check
```

The basic studio needs `cv2` and `numpy` in the interpreter used to launch
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
original Kinect capture is exclusive. Avoid running multiple Kinect programs
concurrently. Manifold Connect routing and shared sensor ownership are not
yet implemented; Camera Lab currently runs one experiment at a time.

The code is a first usable experimental entry point, not yet hardware-verified
on this Pi. Read the diagnostics in the Camera Lab window if a camera cannot
be opened; copy them as needed.
