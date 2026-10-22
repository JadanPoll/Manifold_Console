# From recorded observations to input latency

Run `make replay-check`. The same landmark stream produces the same
semantic events every time, without MediaPipe, webcams, GUI or input injection.

We can now compare different classifiers against identical recordings.
The fixture tests transitions, debouncing, hysteresis and tracking loss;
it does **not** benchmark model inference or prove realtime performance.

Next measurement harness: timestamp capture start, frame available,
MediaPipe submission, inference completion, semantic event and game delivery.
Report action-age p50/p95/p99, missed transitions, false transitions, and
CPU utilization for a fixed recording. Compare default live-stream tracking
against a task-specific latest-frame policy. Do not optimize solely for FPS.

MediaPipe references:
- https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python
- https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/c/vision/hand_landmarker/hand_landmarker.h
