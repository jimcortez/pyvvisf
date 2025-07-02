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

# Debug platform detection
echo "Debug: Checking platform detection..."
echo "Debug: uname output: $(uname)"
echo "Debug: /etc/os-release content:"
if [ -f /etc/os-release ]; then
    cat /etc/os-release
else
    echo "Debug: /etc/os-release not found"
fi

# Check if Linux section is empty and apply configuration if needed
echo "Debug: Checking Linux section in VVGL Makefile..."
grep -A 5 "else ifeq (\$(shell uname),Linux)" VVGL/Makefile

if grep -A 1 "else ifeq (\$(shell uname),Linux)" VVGL/Makefile | grep -q "^else ifeq"; then
    echo "Linux section is empty, applying Linux configuration..."
    
    # Create a temporary file with the Linux configuration
    cat > /tmp/linux_config.txt << 'EOF'
	CXX = g++
	
	CPPFLAGS := -Wall -g -std=c++11 -fPIC -O3
	CPPFLAGS += -I./include/ -DVVGL_SDK_GLFW
	# Add GLFW and GLEW include paths
	CPPFLAGS += -I/usr/include
	CPPFLAGS += -I/usr/local/include
	CPPFLAGS += -I/opt/homebrew/include
	OBJCPPFLAGS := $(CPPFLAGS)
	
	CPPFLAGS += -x c++
	
	LDFLAGS := -lstdc++ -shared -fPIC
	# Add GLFW and GLEW libraries
	LDFLAGS += -L/usr/lib -L/usr/local/lib -L/opt/homebrew/lib
	LDFLAGS += -lglfw -lGLEW -lGL -lX11 -lXrandr -lXinerama -lXcursor -lm -ldl
	LDFLAGS += -lpthread
EOF
    
    # Apply to VVGL Makefile
    sed -i '/else ifeq ($(shell uname),Linux)/r /tmp/linux_config.txt' VVGL/Makefile
    
    # Apply to VVISF Makefile
    sed -i '/else ifeq ($(shell uname),Linux)/r /tmp/linux_config.txt' VVISF/Makefile
    
    rm /tmp/linux_config.txt
    echo "✓ Linux configuration applied"
else
    echo "✓ Linux configuration already present"
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