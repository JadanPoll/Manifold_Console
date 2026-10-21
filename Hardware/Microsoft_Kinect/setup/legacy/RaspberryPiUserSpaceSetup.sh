#!/usr/bin/env bash
# ==============================================================================
# USER-SPACE RESTORE - No 'sudo' required
# Extracts the compiled libfreenect cache into ~/.local and wires up paths.
# ==============================================================================
set -e

BASE_DIR=$(pwd)
TARBALL="$BASE_DIR/Kinect_Offline_Cache/libfreenect_compiled.tar.gz"

if [ ! -f "$TARBALL" ]; then
    echo "Error: Could not find $TARBALL"
    exit 1
fi

echo "======================================================="
echo " 1. Unpacking to User Space (~/.local)..."
echo "======================================================="
mkdir -p "$HOME/.local"
tar -xzf "$TARBALL" --strip-components=2 -C "$HOME/.local" usr/local/

echo "======================================================="
echo " 2. Wiring up Library and Python Paths..."
echo "======================================================="
PY_DIST=$(find "$HOME/.local" -type d -name "dist-packages" | head -n 1)

# Persist to ~/.bashrc so you don't have to do this every time you log in
if ! grep -q "$HOME/.local/lib" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Kinect User-Space Paths" >> ~/.bashrc
    echo "export LD_LIBRARY_PATH=\"\$HOME/.local/lib:\$LD_LIBRARY_PATH\"" >> ~/.bashrc
fi

if ! grep -q "$PY_DIST" ~/.bashrc 2>/dev/null; then
    echo "export PYTHONPATH=\"\$PYTHONPATH:$PY_DIST\"" >> ~/.bashrc
fi

# Export for this immediate script execution
export LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="$PYTHONPATH:$PY_DIST"

echo "Paths injected into ~/.bashrc."

echo "======================================================="
echo " 3. Waking up Kinect 1473 Firmware..."
echo "======================================================="
if [ -f "$HOME/.local/bin/freenect-micview" ]; then
    timeout 3s "$HOME/.local/bin/freenect-micview" &>/dev/null || true
    echo "Firmware upload sent."
else
    echo "Warning: freenect-micview not found in local bin."
fi

echo "======================================================="
echo " SETUP COMPLETE."
echo "======================================================="
echo "To apply the path changes to your current terminal, run:"
echo "    source ~/.bashrc"
echo ""
echo "Then test your sensor:"
echo "    python3 test_kinect.py"
echo "======================================================="
