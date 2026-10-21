# Kinect 1473 / Debian 12 ARM64 no-sudo recovery

## Proven working baseline on the original Raspberry Pi

- Kinect for Windows / 1473, USB IDs `045e:02bf` camera, `045e:02be` audio, `045e:02c2` motor.
- Raspberry Pi Debian 12 ARM64; Python 3.11.2.
- libusb runtime shipped with system; extracted ARM64 development headers and provided a user-local linker symlink.
- Built libfreenect and libfreenect_sync with CMake under `~/kinect-arm64` (ext4), installed libraries into `~/.local/lib`.
- Disabled only `libusb_reset_device(audioHandle);` in `fnusb_keep_alive_led()` of `src/usb_libusb10.c`; preserved the original source in a backup. This is a local workaround, **not** a proven universal upstream fix.
- `audios.bin` must be at `~/.libfreenect/audios.bin` (original also at `~/.local/share/libfreenect/audios.bin`).
- Python wrapper built against NumPy 1.26.4 and OpenCV 4.11.0.86. OpenCV 5 upgraded NumPy to 2.x, causing ABI failure.
- Depth imagery visibly works. RGB and microphone capture have **not** been tested.
- OpenCV printed a Wayland Qt-plugin warning even while a depth image was visible; `QT_QPA_PLATFORM=xcb` is an optional unverified workaround.

## New Pi restore

1. Ensure Debian 12 ARM64, compilers, CMake, apt, and Python 3.11 `venv` are present. System USB permissions and hardware power must permit USB access. The script cannot fix those without admin rights.
2. Copy your `KinectGames/libfreenect` source to the new Pi, along with a legally obtained `audios.bin` file.
3. Run: `KINECT_FIRMWARE=/absolute/path/audios.bin bash restore_kinect.sh /absolute/path/KinectGames`
4. Run the displayed hardware smoke test; observe a depth image. Exit with ESC.

The script writes a **dedicated** virtual environment at `~/.venvs/beastgames-kinect`, avoiding reliance on the older PDFlets virtual environment. It is not tested on the new machine; failures should be handled as diagnostics rather than treated as a successful restore.

## Constraints and recovery

- No `sudo` required if the base build tools and USB permissions are already installed.
- Source is built in the home directory because the removable drive is FAT32/vfat.
- The script does not install kernel modules, modify udev rules, or validate microphone/LED/motor functionality.
- If USB hangs/disconnects reappear, inspect `journalctl -k -n 50 --no-pager`, `lsusb`, external power, and USB topology.
- To revert the native USB-reset workaround on the original Pi, restore `~/kinect-arm64/libfreenect/src/usb_libusb10.c.backup` (if present) and rebuild/reinstall the native libraries.
- Do not blindly upgrade NumPy: the `freenect` Cython extension is ABI-dependent.

## Exact root-cause sequence

Missing libusb development linker name + missing ARM64 freenect libraries → linker errors → wrapper installed → OpenCV absent → OpenCV 5/NumPy 2 ABI mismatch → downgrade/pin → USB reset causes camera initialization errors and audio re-enumeration → bypass reset → firmware missing → copy `audios.bin` into `~/.libfreenect` → successful depth image.

## References

- https://github.com/OpenKinect/libfreenect
- https://github.com/OpenKinect/libfreenect/issues/557
- https://github.com/OpenKinect/libfreenect/issues/580
