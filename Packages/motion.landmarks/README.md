# Motion Landmarks — experimental native capability

**Pure C11** pose geometry, EMA smoothing and pinch event detection. Does not
import MediaPipe, open cameras, render windows, or inject keyboard/mouse input.

```sh
cd Packages/motion.landmarks
make test
make
```

`motion.h` is the provisional API. Landmarks use normalized camera coordinates,
with `valid` per landmark and a source timestamp. Distances in camera-normalized
X/Y/Z space are **not physical metres**; perspective and detector-specific Z
conventions must be calibrated before thresholds transfer between cameras.
The caller defines the landmark index mapping (e.g. MediaPipe hands 4/8 for
thumb/index tips). Avoid fixed display resolutions and device-specific imports.

Pinch has hysteresis, consecutive-frame debounce and immediate release on
tracking loss. It emits **semantic events only**; downstream Connect adapters
must explicitly opt in to keyboard/mouse control. No heap allocation or threads
in the core. Recorded-input tests require no video hardware.

The package is a starting processing kernel, not yet an interprocess service
or a complete hand-pose detector. Future camera/MediaPipe adapters should feed
its landmark structs, and games should subscribe to its events.
