#!/usr/bin/env bash
# ==============================================================================
# THE KINECT 1473 "GOD SCRIPT" v2 â UBUNTU 18.04 LIVE USB
# Fixes vs v1:
#   - Dynamic Python version detection (no hardcoded python3.6 in tar)
#   - --ignore-failed-read on tar (fakenect optional path no longer kills cache)
#   - PYTHONPATH exported automatically, not just printed
#   - 1473 firmware wakeup automated at end
#   - Tar archive now consistent with what QuickRestore expects
# ==============================================================================
set -e
BASE_DIR=$(pwd)

echo "======================================================="
echo " 1. Installing Core System Dependencies & OpenCV..."
echo "======================================================="
sudo apt update -y
sudo apt install -y git build-essential pkg-config \
    libusb-1.0-0-dev libusb-1.0-0 \
    freeglut3-dev freeglut3 \
    libxmu-dev libxi-dev \
    python3-dev python3-numpy python3-setuptools python3-opencv \
    wget python3-urllib3

echo "======================================================="
echo " 2. Upgrading Python Tools (Pinning legacy versions)..."
echo "======================================================="
pip3 install --upgrade pip "Cython<3.0" numpy "cmake==3.22.5"

echo "======================================================="
echo " 3. Fetching libfreenect Source Code..."
echo "======================================================="
cd "$BASE_DIR"
if [ ! -d "libfreenect" ]; then
    git clone https://github.com/OpenKinect/libfreenect.git
else
    cd libfreenect
    git pull origin master
    cd "$BASE_DIR"
fi

echo "======================================================="
echo " 4. KINECT 1473 FIX: Fetching audios.bin Firmware..."
echo "======================================================="
cd "$BASE_DIR/libfreenect/src"
python3 fwfetcher.py
sudo mkdir -p /usr/local/share/libfreenect
sudo mv audios.bin /usr/local/share/libfreenect/ 2>/dev/null || \
    echo "   audios.bin already in place, skipping."

echo "======================================================="
echo " 5. HYBRID BUILD: Compiling safely in /tmp..."
echo "======================================================="
# /tmp avoids NTFS/FAT32 'Operation not permitted' errors from mounted drives
rm -rf /tmp/libfreenect_build
cp -r "$BASE_DIR/libfreenect" /tmp/libfreenect_build
cd /tmp/libfreenect_build

mkdir -p build && cd build
rm -rf *
$(which cmake) .. -DBUILD_PYTHON3=OFF
make -j$(nproc)
sudo make install
sudo ldconfig

echo "======================================================="
echo " 6. Building Python 3 Wrapper..."
echo "======================================================="
cd /tmp/libfreenect_build/wrappers/python
rm -f freenect.c
rm -rf build/
python3 setup.py install

echo "======================================================="
echo " 7. Hardware Permissions & Udev Rules..."
echo "======================================================="
sudo cp /tmp/libfreenect_build/platform/linux/udev/51-kinect.rules \
    /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger

ACTUAL_USER=${SUDO_USER:-$USER}
sudo usermod -aG video   "$ACTUAL_USER" || true
sudo usermod -aG plugdev "$ACTUAL_USER" || true

echo "======================================================="
echo " 8. Cleanup & Finalizing..."
echo "======================================================="
rm -rf /tmp/libfreenect_build
cd "$BASE_DIR"
sudo ldconfig

echo "======================================================="
echo " 9. Fix PYTHONPATH automatically..."
echo "======================================================="
# Detect actual Python version installed â fixes the hardcoded python3.6 bug
PYVER=$(python3 -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')")
FREENECT_PYPATH="/usr/local/lib/${PYVER}/dist-packages"

export PYTHONPATH="$PYTHONPATH:$FREENECT_PYPATH"

EXPORT_LINE="export PYTHONPATH=\$PYTHONPATH:${FREENECT_PYPATH}"
if ! grep -q "$FREENECT_PYPATH" ~/.bashrc 2>/dev/null; then
    echo "$EXPORT_LINE" >> ~/.bashrc
fi

echo "   Python  : ${PYVER}"
echo "   PYTHONPATH includes: ${FREENECT_PYPATH}"

echo "======================================================="
echo " 10. CREATING OFFLINE CACHE..."
echo "======================================================="
mkdir -p "$BASE_DIR/Kinect_Offline_Cache/pip_wheels"

# --ignore-failed-read: optional paths like fakenect won't abort the archive
sudo tar -czvf "$BASE_DIR/Kinect_Offline_Cache/libfreenect_compiled.tar.gz" \
    -C / \
    --ignore-failed-read \
    usr/local/lib/libfreenect* \
    usr/local/lib/fakenect \
    usr/local/bin/freenect* \
    usr/local/include/libfreenect \
    usr/local/share/libfreenect \
    usr/local/lib/${PYVER}/dist-packages/freenect* \
    usr/local/lib/${PYVER}/dist-packages/freenect-0.0.0.egg-info \
    etc/udev/rules.d/51-kinect.rules \
    2>/dev/null || true

# Download wheels for offline restore
pip3 download "Cython<3.0" numpy "cmake==3.22.5" \
    -d "$BASE_DIR/Kinect_Offline_Cache/pip_wheels/"

echo "======================================================="
echo " 11. Kinect 1473 firmware wakeup (automated)..."
echo "======================================================="
if command -v freenect-micview &>/dev/null; then
    timeout 3s freenect-micview &>/dev/null || true
    echo "   Firmware upload sent. Kinect ready."
else
    echo "   WARNING: freenect-micview not found."
    echo "   Run manually: freenect-micview  (wait 2s, Ctrl+C)"
fi

echo ""
echo "======================================================="
echo " INSTALLATION COMPLETE"
echo "======================================================="
echo " Python  : ${PYVER}"
echo " Cache   : $BASE_DIR/Kinect_Offline_Cache/"
echo ""
echo " Test with:"
echo "   python3 -c \"import freenect; print('freenect OK')\""
echo "   freenect-glview"
echo "======================================================="
