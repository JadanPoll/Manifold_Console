# Original hand-tracking and Smash projects

Both projects are available as **optional external research checkouts**;
they are not Console dependencies, stable capabilities, or safe-to-run apps.

```sh
cd ~/Desktop/Manifold_Console
python3 Playroom/Research_Campus/sync_research.py
python3 Playroom/Research_Campus/sync_research.py --fetch
```

Clones go under `Playroom/Research_Campus/external/` (ignored by Git).
A normal `git pull --ff-only` updates the Manifold manifest and scripts,
but **not these independent repositories**; run `--fetch` to clone/update
them. You do **not** need `--recurse-submodules`.

## Repair plan before live execution

**HandTrack.py:** separate camera->landmarks->pinch/pointer events from
Windows pywin32/pyautogui cursor injection and audio. Fix the anti-jitter
filter which currently returns the same value in both branches and the
finger-pinky detector which delegates to finger-thumb distance.
Make event injection opt-in, device resolution dynamic, and cleanup
exception-safe. Exercise processing on recorded landmark sequences.

**3DMotionSuperSmashBros2:** distinguish complete runnable sources from
experiments. `FullCodePutTogether.py` contains an HMM function returning an
undefined name. Split camera/pose extraction from feature windows, pose
classification, debounced action semantics, and platform-specific input.
Start with offline/replay tests before enabling a live camera or game input.

Do not automatically pip-install project requirements or execute these
programs from Manifold Home. On Raspberry Pi Wayland/XWayland, Windows
mouse APIs are not a portable input backend. Do not presume MediaPipe
wheels for the local Python/ARM platform are installed.

Once a research project passes its native Pi tests, create its own
`manifold-package.json` or `appos.json` and launch it explicitly.
