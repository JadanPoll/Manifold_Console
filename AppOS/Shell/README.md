# Shell

Wii-inspired console navigation and coherent default UI behavior: channels, app switch/home, focus and input conventions, transitions, sound cues. Start with one working screen and keyboard/mouse input; avoid prescribing app-internal rendering tools. Native UI freedom in Dev; common frame/navigation integration in Production.

## Runnable development shell

From repository root:

```sh
python3 -m AppOS.Shell.home
```

Home discovers local `appos.json` manifests without importing applications.
Choose Gravity Playground or Capability Browser, launch in an ordinary external
desktop window, return to the still-open Home, and stop or force-stop a selected
child from Running. F5 rescans manifests. Closing Home offers a choice to stop
known direct children or leave them running.

This is **dev-mode process management**, not containment, window-manager focus,
process-tree cleanup, GPU isolation, permissions enforcement, nor suspension.
"Switching" is performed through normal desktop windows, not compositor control.
No heartbeat or watchdog is armed by default. Avoid introducing a replacement
window manager until an observed use case makes it necessary.

Acceptance on the Pi: Home opens without stalls; both manifests appear; gravity
opens as a regular window; Home remains interactive; Stop terminates gravity;
relaunch works; closing Home respects the chosen child-process behavior.
