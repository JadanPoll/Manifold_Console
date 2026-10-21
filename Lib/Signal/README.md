# Signal

A minimal reusable scalar clamp and exponential moving average (EMA) without camera, audio, UI or external dependencies. This is intentionally tiny. Signal processing is extracted only when it has a concrete reusable contract; other tracking/gesture logic remains experimental.

Run from root: `python3 -m unittest Lib.Signal.test_filters`.
