#!/bin/bash
set -e

echo "Building VVISF-GL libraries with GLFW support..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VVISF_DIR="$PROJECT_ROOT/external/VVISF-GL"
PATCH_FILE="$PROJECT_ROOT/patches/vvisf-glfw-support.patch"

# Check if VVISF-GL submodule exists
if [ ! -f "$VVISF_DIR/README.md" ]; then
    echo "Error: VVISF-GL submodule not found at $VVISF_DIR"
    echo "Please run: git submodule update --init --recursive"
    exit 1
fi

# Check if patch file exists
if [ ! -f "$PATCH_FILE" ]; then
    echo "Error: GLFW support patch not found at $PATCH_FILE"
    echo "Please ensure the patch file exists and try again."
    exit 1
fi

# Detect architecture
if [[ $(uname -m) == "arm64" ]]; then
    ARCH="arm64"
    echo "Detected ARM64 architecture"
else
    ARCH="x86_64"
    echo "Detected x86_64 architecture"
fi

# Apply GLFW patches
cd "$VVISF_DIR"
echo "Applying GLFW support patches..."

# Check if patches are already applied
if grep -q "VVGL_SDK_GLFW" VVGL/Makefile && grep -q "VVGL_SDK_GLFW" VVISF/Makefile; then
    echo "✓ GLFW patches already applied"
else
    # Apply the patch
    if patch -p1 < "$PATCH_FILE"; then
        echo "✓ GLFW patches applied successfully"
    else
        echo "✗ Failed to apply GLFW patches"
        echo ""
        echo "Manual patch application required:"
        echo "1. Edit external/VVISF-GL/VVGL/Makefile:"
        echo "   - Change '-DVVGL_SDK_MAC' to '-DVVGL_SDK_GLFW'"
        echo "   - Add '-I/opt/homebrew/include' to CPPFLAGS"
        echo "   - Add '-L/opt/homebrew/lib -lglfw -lGLEW' to LDFLAGS"
        echo ""
        echo "2. Edit external/VVISF-GL/VVISF/Makefile:"
        echo "   - Change '-DVVGL_SDK_MAC' to '-DVVGL_SDK_GLFW'"
        echo "   - Add '-I/opt/homebrew/include' to CPPFLAGS"
        echo "   - Add '-L/opt/homebrew/lib -lglfw -lGLEW' to LDFLAGS"
        echo ""
        echo "Then run this script again."
        exit 1
    fi
fi

# Build VVGL with GLFW support
echo "Building VVGL..."
cd VVGL
make clean
ARCH=$ARCH make
echo "✓ VVGL built successfully"

# Build VVISF with GLFW support
echo "Building VVISF..."
cd ../VVISF
make clean
ARCH=$ARCH make
echo "✓ VVISF built successfully"

echo "VVISF-GL libraries built successfully!"
echo "Libraries location:"
echo "  VVGL: $VVISF_DIR/VVGL/bin/libVVGL.a"
echo "  VVISF: $VVISF_DIR/VVISF/bin/libVVISF.a" 