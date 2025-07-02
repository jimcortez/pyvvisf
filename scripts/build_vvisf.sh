#!/bin/bash
set -e

echo "Building VVISF-GL libraries with GLFW support..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VVISF_DIR="$PROJECT_ROOT/external/VVISF-GL"
GLFW_PATCH_FILE="$PROJECT_ROOT/patches/vvisf-glfw-support.patch"
LINUX_PATCH_FILE="$PROJECT_ROOT/patches/vvisf-linux-support.patch"

# Check if VVISF-GL submodule exists
if [ ! -f "$VVISF_DIR/README.md" ]; then
    echo "Error: VVISF-GL submodule not found at $VVISF_DIR"
    echo "Please run: git submodule update --init --recursive"
    exit 1
fi

# Check if patch files exist
if [ ! -f "$GLFW_PATCH_FILE" ]; then
    echo "Error: GLFW support patch not found at $GLFW_PATCH_FILE"
    echo "Please ensure the patch file exists and try again."
    exit 1
fi

if [ ! -f "$LINUX_PATCH_FILE" ]; then
    echo "Error: Linux support patch not found at $LINUX_PATCH_FILE"
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

# Apply patches
cd "$VVISF_DIR"
echo "Applying GLFW support patches..."

# Check if GLFW patches are already applied
if grep -q "VVGL_SDK_GLFW" VVGL/Makefile && grep -q "VVGL_SDK_GLFW" VVISF/Makefile; then
    echo "✓ GLFW patches already applied"
else
    # Apply the GLFW patch
    if patch -p1 < "$GLFW_PATCH_FILE"; then
        echo "✓ GLFW patches applied successfully"
    else
        echo "✗ Failed to apply GLFW patches"
        exit 1
    fi
fi

echo "Applying Linux support patches..."

# Check if Linux patches are already applied
if grep -q "else ifeq (\$(shell uname),Linux)" VVGL/Makefile && grep -q "CXX = g++" VVGL/Makefile; then
    echo "✓ Linux patches already applied"
else
    # Apply the Linux patch
    if patch -p1 < "$LINUX_PATCH_FILE"; then
        echo "✓ Linux patches applied successfully"
    else
        echo "✗ Failed to apply Linux patches"
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