# Microsoft Kinect (Kinect for Windows 1473)

Device-specific setup, recovery history and capture smoke tests. Experiments live in [Playroom/Kinect](../../Playroom/Kinect).

## Existing working Pi

The previously working launcher is `~/.local/bin/kinect-run`. It currently uses `~/Desktop/KinectGames` and the PDFlets Python environment. **Do not replace or reinstall it merely to reorganize repository files.** A second capture may fail with `LIBUSB_ERROR_BUSY` while another program owns the camera.

## Restore on a different machine (not yet revalidated)

The native driver is [OpenKinect/libfreenect](https://github.com/OpenKinect/libfreenect), an **external dependency**, not a Manifold library. The original source tree is not checked into this repository. Preserve the historically working source revision, or explicitly provide another checkout via `KINECT_SOURCE`. An arbitrary upstream revision may not match the reversible USB-reset workaround.

From this directory:

```bash
KINECT_SOURCE="$HOME/Desktop/KinectGames/libfreenect" \
KINECT_FIRMWARE="$HOME/.libfreenect/audios.bin" \
bash setup/restore_kinect.sh
```

The script builds under `~/kinect-arm64` and creates `~/.venvs/beastgames-kinect` by default. It requires a Debian ARM64 toolchain, USB permissions and a user-supplied firmware file. Its invasive build/install actions are **not** an ordinary smoke test.

After restore, manually test using the printed command; the test script is at `tests/test_kinect.py`.

## Contents

- `setup/restore_kinect.sh`: existing restore procedure, paths adapted for this layout
- `setup/legacy/`: historical setup variants; not interchangeable supported installers
- `tests/test_kinect.py`: live depth-camera smoke test
- `docs/PROBLEMS.md`: empirical recovery notes and known limitations
- `docs/requirements-working.txt`: environment record

Do not assume RGB, audio, motor, or a clean-machine restore is verified. The recorded successful baseline is depth capture on the original Pi.
