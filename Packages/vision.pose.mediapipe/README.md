# Pose Tracking — Manifold capability

Manifold now has **two** Pose paths:

1. **Native path (preferred):** MediaPipe remains C++ internally, while
   Manifold applications consume the stable C ABI in
   `Backends/mediapipe_pose/include/manifold_pose.h`.
2. **Python path (fallback/research):** the earlier MediaPipe Tasks viewer is
   retained because it is convenient while bringing up hardware.

The intended end state is not "Manifold depends on Python MediaPipe." It is:

```text
camera/video
    -> libmanifold_pose.so
    -> 33 normalized landmarks
    -> motion.landmarks / applications
```

Camera Lab exposes **Set up body tracking**. That explicitly runs:

```sh
python3 Backends/mediapipe_pose/setup_backend.py --download-model
```

The setup is user-space only. It obtains the pinned MediaPipe source, overlays
the Manifold bridge, obtains Bazelisk in `~/.local/bin` if necessary, builds a
CPU-only shared library, and installs it under:

```text
~/.local/lib/manifold/libmanifold_pose.so
~/.local/include/manifold/manifold_pose.h
~/.local/share/manifold/models/pose_landmarker_lite.task
```

No `sudo` or system Python mutation is part of this flow.

Once the native library exists, Camera Lab uses
`native_viewer.py`. Python then owns only camera/video capture and display;
pose inference crosses the Manifold C ABI.

## Why start with MediaPipe

Pose Landmarker is already designed around on-device tracking: a detector finds
the body/ROI and the landmark tracker can reuse temporal state instead of
redetecting from scratch on every frame. The Lite bundle outputs 33 normalized
and world-space landmarks and does not require segmentation.

This makes it a strong **reference baseline**, not an untouchable dependency.
The backend boundary exists specifically so later research can alter detector
frequency, ROI propagation, landmark model choice, smoothing, scheduling, or
replace MediaPipe entirely.

For Smash, the optimization target is not "perfect anatomical dots." It is
timely relative geometry, velocity, transitions and stable action-relevant
motion.

## Earlier Python fallback

If a working MediaPipe Python environment already exists, the original viewer
can still be run:

```sh
python Packages/vision.pose.mediapipe/pose_viewer.py \
  --model /path/to/pose_landmarker_lite.task --camera 0
```

That fallback is useful for experimentation but is no longer the architectural
boundary.

The native build has been staged from current upstream sources but has **not
yet been compiled on the user's Raspberry Pi**. Build errors should be treated
as concrete bring-up information, not as a reason to redesign the boundary.
