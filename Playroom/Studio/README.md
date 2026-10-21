# Playroom Studio (first runnable prototype)

A standard-library Tkinter no-code interface for generating sine/triangle/square signals, adjusting gain and EMA smoothing, and inspecting pointer normalization. It does not depend on Kinect or a graphics engine, and it does not execute LLM-generated code.

From the repository root:

```bash
python3 Playroom/Studio/main.py
python3 AppOS/Shell/main.py
python3 -m unittest discover -s Playroom/Studio -p 'test_*.py'
```

On Debian/Raspberry Pi install `python3-tk` through the system package manager if tkinter is missing. GUI requires an active desktop session/display.

`example.recipe.json` and `recipe.py` establish the constrained JSON experiment format for future LLM-driven UI; the Load Recipe button imports and validates JSON then updates controls. The shell and launcher are **Dev only**: no sandbox, capability enforcement, app switch interception, or security guarantees.
