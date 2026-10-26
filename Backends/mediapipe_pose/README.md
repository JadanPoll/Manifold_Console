# Manifold MediaPipe Pose backend

This directory establishes the boundary we want long-term:

```text
Manifold applications
        |
        v
manifold_pose.h        <- stable C ABI owned by Manifold
        |
        v
MediaPipe Pose         <- C++ implementation detail / eventual fork
        |
        v
BlazePose models
```

The intent is **not** to make Manifold depend on Python MediaPipe. Python remains
useful for experiments, but applications should eventually load one native
backend and receive normalized pose observations.

## Why this boundary

- MediaPipe remains internally C++.
- Manifold gets a tiny C ABI usable from C, C++, Python/ctypes, Rust, etc.
- We can later fork/gut MediaPipe without changing applications.
- Segmentation is disabled by default.
- v1 asks for one body and only exports the 33 normalized landmarks.
- Camera capture is deliberately outside the backend. It receives RGB frames.

The current source targets MediaPipe's Pose Landmarker **VIDEO** mode first.
That mode already reuses tracking state across frames. A later low-latency
backend can change to LIVE_STREAM/latest-frame behavior without changing this
public landmark schema.

## Source ownership

The long-term source location should be a separate repository such as
`JadanPoll/mediapipe-manifold`. The GitHub connector available in this
session cannot create a new repository, so the fork-facing overlay is staged
here first rather than pretending the remote exists.

`PINNED_MEDIAPIPE.txt` records the upstream revision against which this
bridge was authored. Once the fork exists, this directory can become the
consumer/install recipe while the bridge source moves into that fork.

## Build direction

The intended build is CPU-first on the Pi. Do not make GPU support a
prerequisite. MediaPipe itself already provides CPU pose paths and detector /
tracker reuse. The first useful artifact is:

```text
libmanifold_pose.so
```

exporting the functions in `include/manifold_pose.h`.

No attempt has been made to hide build failures behind retries. The next
hardware step is simply to compile this against the pinned MediaPipe checkout
and fix whatever the current Bazel graph exposes on Debian ARM64.

## Optimization research later

Once the baseline works, profile these boundaries separately:

1. RGB acquisition/copy
2. detector invocation frequency
3. landmark inference
4. tracker/ROI propagation
5. smoothing
6. result conversion/copy
7. Manifold motion semantics

For Smash, accuracy of every anatomical point is not the objective. Relative
geometry, velocity, transitions, and temporal consistency are.
