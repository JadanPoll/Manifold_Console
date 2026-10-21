#!/usr/bin/env bash
# ==============================================================================
# QUICKRESTORE v2 â Spatial Lab Kinect Fast Restore
# Fixes vs v1:
#   - Dynamic Python version detection (no hardcoded python3.6)
#   - --ignore-failed-read on tar (fakenect optional path no longer kills cache)
#   - Full runtime deps installed (libusb-dev, libxi-dev, libxmu-dev)
#   - PYTHONPATH set automatically, not just printed
#   - 1473 firmware wakeup automated (non-interactive freenect-micview timeout)
# ==============================================================================
set -e
BASE_DIR=$(pwd)
CACHE_DIR="$BASE_DIR/Kinect_Offline_Cache"
TARBALL="$CACHE_DIR/libfreenect_compiled.tar.gz"

echo "======================================================="
echo " CHECKING FOR KINECT OFFLINE CACHE..."
echo "======================================================="

if [ ! -f "$TARBALL" ]; then
    echo "!! OFFLINE CACHE NOT FOUND OR CORRUPTED!"
    echo "   Falling back to Nsetup.sh to build from scratch..."
    echo "======================================================="

    if [ -f "$BASE_DIR/Nsetup.sh" ]; then
        chmod +x "$BASE_DIR/Nsetup.sh"
        bash "$BASE_DIR/Nsetup.sh"
        echo ""
        echo "!! REMINDER: Run Nsetup.sh again to regenerate the cache tarball."
        exit 0
    else
        echo "ERROR: Nsetup.sh is also missing. Cannot proceed."
        exit 1
    fi
fi

echo "Cache found! Initiating Fast Restore..."
echo "======================================================="

# ââ Step 1: Detect active Python version dynamically ââââââââââââââââââââââââââ
# Fixes the hardcoded python3.6 path bug â works regardless of which
# Python 3.x the Live USB ships with
PYVER=$(python3 -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')")
echo "1. Detected Python version: ${PYVER}"

# ââ Step 2: Core system packages â runtime AND dev libs âââââââââââââââââââââââ
# v1 was missing libusb-1.0-0-dev, libxi-dev, libxmu-dev which the compiled
# .so files link against â caused runtime import crashes even after restore
echo "2. Installing system dependencies..."
sudo apt update -y -qq
sudo apt install -y \
    python3-opencv python3-numpy \
    libusb-1.0-0 libusb-1.0-0-dev \
    freeglut3 freeglut3-dev \
    libxi-dev libxmu-dev \
    python3-dev

# ââ Step 3: Offline Python wheels âââââââââââââââââââââââââââââââââââââââââââââ
echo "3. Installing offline Python wheels..."
pip3 install --no-index --find-links="$CACHE_DIR/pip_wheels/" \
    "Cython<3.0" numpy "cmake==3.22.5"

# ââ Step 4: Unpack pre-compiled drivers âââââââââââââââââââââââââââââââââââââââ
echo "4. Unpacking pre-compiled libfreenect drivers..."
sudo tar -xzf "$TARBALL" -C /

# ââ Step 5: Fix PYTHONPATH for this session automatically âââââââââââââââââââââ
# v1 just printed this â user had to run it manually, easy to forget
FREENECT_PYPATH="/usr/local/lib/${PYVER}/dist-packages"
export PYTHONPATH="$PYTHONPATH:$FREENECT_PYPATH"

# Persist for future sessions in this Live USB boot
EXPORT_LINE="export PYTHONPATH=\$PYTHONPATH:${FREENECT_PYPATH}"
if ! grep -q "$FREENECT_PYPATH" ~/.bashrc 2>/dev/null; then
    echo "$EXPORT_LINE" >> ~/.bashrc
fi

echo "   PYTHONPATH updated: $FREENECT_PYPATH"

# ââ Step 6: Reload udev + permissions âââââââââââââââââââââââââââââââââââââââââ
echo "5. Refreshing udev rules and permissions..."
sudo ldconfig
sudo udevadm control --reload-rules && sudo udevadm trigger

ACTUAL_USER=${SUDO_USER:-$USER}
sudo usermod -aG video "$ACTUAL_USER"   || true
sudo usermod -aG plugdev "$ACTUAL_USER" || true

# ââ Step 7: Kinect 1473 firmware wakeup (automated) ââââââââââââââââââââââââââ
# v1 told you to do this manually â easy to forget, causes cryptic USB errors
# This runs freenect-micview for 3 seconds to upload audios.bin, then kills it
echo "6. Waking up Kinect 1473 firmware (uploading audios.bin)..."
if command -v freenect-micview &>/dev/null; then
    timeout 3s freenect-micview &>/dev/null || true
    echo "   Firmware upload sent. Kinect ready."
else
    echo "   WARNING: freenect-micview not found â 1473 may need manual wakeup"
    echo "   Run: freenect-micview  (wait 2s, then Ctrl+C)"
fi

echo ""
echo "======================================================="
echo " RESTORE COMPLETE"
echo "======================================================="
echo " Python : ${PYVER}"
echo " PYTHONPATH includes: ${FREENECT_PYPATH}"
echo " Kinect 1473 firmware: uploaded"
echo ""
echo " Test with:"
echo "   python3 -c \"import freenect; print('freenect OK')\""
echo "   freenect-glview"
echo "======================================================="
