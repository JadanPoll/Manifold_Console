# Pose Tracking — Video capability

An optional MediaPipe Tasks Pose Landmarker viewer. See yourself or a recorded
dance video as a 33-landmark skeleton. No game/mouse input injection.
The Console and other native packages do not depend on MediaPipe.

Create a **separate** virtual environment (don't modify the working Kinect
Python environment):

```sh
python3 -m venv ~/.venvs/manifold-pose
~/.venvs/manifold-pose/bin/python -m pip install mediapipe opencv-python
```

Get a Pose Landmarker `.task` model from the official Google AI Edge
documentation: https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker
Pass its actual local path (no automatic download or assumed files):

```sh
~/.venvs/manifold-pose/bin/python Packages/vision.pose.mediapipe/pose_viewer.py \
  --model /path/to/pose_landmarker_lite.task --camera 0
```

For a recorded dance video:

```sh
~/.venvs/manifold-pose/bin/python Packages/vision.pose.mediapipe/pose_viewer.py \
  --model /path/to/pose_landmarker_lite.task --video /path/to/dance.mp4
```

ESC closes the viewer. The model and video remain local. Only the camera path
accesses a device. This first capability displays inference results directly;
publishing normalized landmarks into Manifold Connect is a separate unimplemented
interface. No local Raspberry Pi test has yet been performed.

MediaPipe VIDEO mode uses timestamps and tracks pose across frames; it is
not a multi-application camera broker or a low-latency guarantee.
