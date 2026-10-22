# AppOS Runtime

Implemented **Dev-mode** building blocks:

- `catalog.py`: discovers local `appos.json` manifests and validates basic required fields
- `launcher.py`: launches local native programs without a shell
- `test_catalog.py`: deterministic manifest discovery smoke test

Unimplemented: sandbox/confinement, permissions enforcement, per-app storage, audio policy, app focus, Home/Back interception, reliable termination/suspension and manifest signing/trust. Launching code through the current runtime provides **no security isolation**.

From the repository root: `python3 -m unittest AppOS.Runtime.test_catalog`.

## Experimental software-backed XWayland (Raspberry Pi / Wayfire)

For machines where XWayland GLAMOR becomes pathologically slow, use a **private
rootful XWayland instance** with the supported `-shm` backend:

```sh
python3 -m AppOS.Runtime.software_xwayland -- python3 Playroom/Playground/gravity.py
# automatic cleanup after 15 seconds:
python3 -m AppOS.Runtime.software_xwayland --seconds 15 -- python3 Playroom/Playground/gravity.py
```

This is an optional developer backend, not an AppOS-wide default. It creates a
private X11 display and Xauthority cookie, waits for an authenticated Tk client
connection, runs the app, and terminates its private server and app on exit. It
does not require sudo or change Wayfire's normal XWayland configuration.
Because this is a **separate X server**, it does not provide seamless rootless
integration with the desktop. In XWayland 22.1, a rootful server may occupy the
entire display; `-geometry WxH` was added only in 23.1. Do not pass `--geometry`
on the target Pi's 22.1.9 build.

The shell's existing `DISPLAY` remains unchanged, so other X11 applications
continue to use their usual server. The X11 rootful window may not have a
window manager, so decoration, focus and input differ from a normal desktop
application. Test and restore with Ctrl+C in the launching terminal if needed;
the launcher itself does not perform persistent system modifications.

The `-shm` path was much faster on the observed native X11 drawing benchmark,
but this launcher and the resulting Tk window still require validation on the
actual Pi. A software-backed Xwayland avoids the GLAMOR path inside that server,
but does not guarantee that every Wayland compositor operation avoids the GPU.
