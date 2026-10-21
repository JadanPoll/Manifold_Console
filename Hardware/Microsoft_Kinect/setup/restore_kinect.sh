#!/usr/bin/env bash
# Kinect for Windows 1473, Debian 12 ARM64, user-local installation.
# Usage: bash setup/restore_kinect.sh
# Optional: KINECT_SOURCE=/path/to/libfreenect KINECT_FIRMWARE=/path/to/audios.bin bash setup/restore_kinect.sh
set -Eeuo pipefail
trap 'echo "ERROR on line $LINENO. Check the output above." >&2' ERR
PROJECT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${KINECT_SOURCE:-$HOME/Desktop/KinectGames/libfreenect}"
[[ -d "$SOURCE" ]] && SOURCE="$(cd "$SOURCE" && pwd)"
WORK="${KINECT_WORK:-$HOME/kinect-arm64}"
PREFIX="${KINECT_PREFIX:-$HOME/.local}"
VENV="${KINECT_VENV:-$HOME/.venvs/beastgames-kinect}"
[[ "$(uname -m)" == "aarch64" ]] || { echo "Requires ARM64; detected $(uname -m)" >&2; exit 1; }
[[ -f /etc/debian_version ]] || echo 'Warning: designed/tested against Debian 12.' >&2
for cmd in python3 gcc make cmake dpkg-deb apt curl; do command -v "$cmd" >/dev/null || { echo "Missing build tool: $cmd" >&2; exit 1; }; done
[[ -f "$SOURCE/CMakeLists.txt" ]] || { echo "Missing libfreenect source at $SOURCE; set KINECT_SOURCE=/path/to/libfreenect" >&2; exit 1; }
mkdir -p "$WORK" "$PREFIX/lib" "$PREFIX/include" "$HOME/.libfreenect" "$(dirname "$VENV")"
# Firmware must come from an existing user-owned copy; do not redownload without consent.
FIRMWARE="${KINECT_FIRMWARE:-}"
if [[ -z "$FIRMWARE" ]]; then
  for guess in "$HOME/.libfreenect/audios.bin" "$PREFIX/share/libfreenect/audios.bin" "$SOURCE/src/audios.bin"; do
    if [[ -s "$guess" ]]; then FIRMWARE="$guess"; break; fi
  done
fi
[[ -n "$FIRMWARE" && -s "$FIRMWARE" ]] || { echo 'Missing audios.bin. Set KINECT_FIRMWARE=/path/to/audios.bin' >&2; exit 1; }
if [[ "$FIRMWARE" != "$HOME/.libfreenect/audios.bin" ]]; then cp -n "$FIRMWARE" "$HOME/.libfreenect/audios.bin"; fi
# Recover the unversioned linker symlink and USB header files without root.
if [[ ! -e "$PREFIX/lib/libusb-1.0.so" || ! -f "$PREFIX/include/libusb-1.0/libusb.h" ]]; then
  cd "$WORK"
  apt download libusb-1.0-0-dev:arm64
  deb=$(find "$WORK" -maxdepth 1 -type f -name 'libusb-1.0-0-dev_*_arm64.deb' | sort | tail -1)
  mkdir -p "$WORK/usb-dev"
  dpkg-deb -x "$deb" "$WORK/usb-dev"
  cp -a "$WORK/usb-dev/usr/include/libusb-1.0" "$PREFIX/include/"
  if [[ -e /usr/lib/aarch64-linux-gnu/libusb-1.0.so.0 ]]; then
    ln -sfn /usr/lib/aarch64-linux-gnu/libusb-1.0.so.0 "$PREFIX/lib/libusb-1.0.so"
  else
    echo 'System libusb runtime is missing; cannot link.' >&2; exit 1
  fi
fi
export CPATH="$PREFIX/include:$PREFIX/include/libusb-1.0:$PREFIX/include/libfreenect:${CPATH:-}"
export LIBRARY_PATH="$PREFIX/lib:${LIBRARY_PATH:-}"
export LD_LIBRARY_PATH="$PREFIX/lib:${LD_LIBRARY_PATH:-}"
export CMAKE_PREFIX_PATH="$PREFIX:${CMAKE_PREFIX_PATH:-}"
# Compile on ext4, not on the removable FAT32 drive.
if [[ ! -d "$WORK/libfreenect" ]]; then cp -a "$SOURCE" "$WORK/libfreenect"; fi
SRC="$WORK/libfreenect/src/usb_libusb10.c"
python3 - "$SRC" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]); text = p.read_text()
a = text.index('FN_INTERNAL int fnusb_keep_alive_led(')
b = text.index('FN_INTERNAL int fnusb_open_subdevices(', a)
segment = text[a:b]
needle = 'libusb_reset_device(audioHandle);'
if needle in segment:
    backup = p.with_name(p.name + '.before-1473-reset-patch')
    if not backup.exists(): backup.write_text(text)
    assert segment.count(needle) == 1
    segment = segment.replace(needle, '/* diagnostic workaround: 1473 skip USB audio reset */', 1)
    p.write_text(text[:a] + segment + text[b:])
    print('Applied reversible 1473 USB reset workaround')
elif 'diagnostic workaround: 1473 skip USB audio reset' in segment or 'Diagnostic: skip USB reset' in segment:
    print('USB reset workaround already present')
else:
    raise SystemExit('Source changed; will not patch unknown implementation')
PY
cmake -S "$WORK/libfreenect" -B "$WORK/build" \
  -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DLIBUSB_1_INCLUDE_DIR="$PREFIX/include/libusb-1.0" \
  -DLIBUSB_1_LIBRARY="$PREFIX/lib/libusb-1.0.so" \
  -DBUILD_C_SYNC=ON -DBUILD_EXAMPLES=OFF -DBUILD_FAKENECT=OFF \
  -DBUILD_PYTHON=OFF -DBUILD_PYTHON2=OFF -DBUILD_PYTHON3=OFF
cmake --build "$WORK/build" -j2
cmake --install "$WORK/build"
if [[ ! -x "$VENV/bin/python" ]]; then python3 -m venv "$VENV"; fi
"$VENV/bin/python" -m pip install 'Cython==0.29.37' 'numpy==1.26.4' 'opencv-python==4.11.0.86'
cd "$WORK/libfreenect/wrappers/python"
rm -rf build
"$VENV/bin/python" setup.py build_ext --inplace
"$VENV/bin/python" - <<'PY'
from pathlib import Path
import shutil, sysconfig
modules = list(Path.cwd().glob('freenect*.so'))
assert len(modules) == 1, f'Expected one freenect extension, found {modules}'
dst = Path(sysconfig.get_paths()['platlib']); dst.mkdir(parents=True, exist_ok=True)
shutil.copy2(modules[0], dst / modules[0].name)
print('Copied wrapper to', dst / modules[0].name)
PY
"$VENV/bin/python" -c 'import freenect, cv2, numpy; print("Imports OK; NumPy", numpy.__version__, "OpenCV", cv2.__version__)'
cat <<EOM
SUCCESS: build/import test passed. Hardware must still be tested on this Pi.
Run:
  export LD_LIBRARY_PATH="$PREFIX/lib:\${LD_LIBRARY_PATH:-}"
  QT_QPA_PLATFORM=xcb "$VENV/bin/python" "$PROJECT/tests/test_kinect.py"
EOM
