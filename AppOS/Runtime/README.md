# AppOS Runtime

Implemented **Dev-mode** building blocks:

- `catalog.py`: discovers local `appos.json` manifests and validates basic required fields
- `launcher.py`: launches local native programs without a shell
- `test_catalog.py`: deterministic manifest discovery smoke test

Unimplemented: sandbox/confinement, permissions enforcement, per-app storage, audio policy, app focus, Home/Back interception, reliable termination/suspension and manifest signing/trust. Launching code through the current runtime provides **no security isolation**.

From the repository root: `python3 -m unittest AppOS.Runtime.test_catalog`.
