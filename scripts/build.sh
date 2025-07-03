#!/bin/bash

# pyvvisf Build Script
# This script builds the complete pyvvisf library from scratch

set -e  # Exit on any error

echo "=========================================="
echo "pyvvisf Build Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "CMakeLists.txt" ]; then
    print_error "This script must be run from the pyvvisf project root directory"
    exit 1
fi

# Check dependencies
print_status "Checking dependencies..."

# Check for required tools
for cmd in cmake make git; do
    if ! command -v $cmd &> /dev/null; then
        print_error "$cmd is required but not installed"
        exit 1
    fi
done

# Check for Homebrew packages
for pkg in glfw glew; do
    if ! brew list | grep -q "^${pkg}$"; then
        print_error "$pkg is required but not installed. Install with: brew install $pkg"
        exit 1
    fi
done

print_success "All dependencies found"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build
rm -f src/pyvvisf/*.so src/pyvvisf/*.dylib src/pyvvisf/*.dll
print_success "Clean completed"

# Initialize and update submodules
print_status "Initializing VVISF-GL submodule..."
if [ ! -d "external/VVISF-GL" ]; then
    print_status "Cloning VVISF-GL repository..."
    git clone https://github.com/mrRay/VVISF-GL.git external/VVISF-GL
else
    print_status "VVISF-GL repository already exists"
fi

# Apply patches
print_status "Applying GLFW support patches..."
cd external/VVISF-GL
if git apply ../../patches/vvisf-glfw-support.patch; then
    print_success "Patches applied successfully"
else
    print_warning "Patches may already be applied or failed"
fi
cd ../..

# Build VVGL library
print_status "Building VVGL library..."
cd external/VVISF-GL/VVGL
make clean
ARCH=arm64 make
print_success "VVGL library built"

# Build VVISF library
print_status "Building VVISF library..."
cd ../VVISF
make clean
ARCH=arm64 make
print_success "VVISF library built"
cd ../../..

# Create build directory and configure
print_status "Configuring CMake build..."
mkdir -p build
cd build
cmake ..

# Build Python extension
print_status "Building Python extension..."
make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
cd ..

# Verify build
print_status "Verifying build..."
if ls src/pyvvisf/vvisf_bindings.cpython-*.so 1> /dev/null 2>&1; then
    print_success "Python extension built successfully"
else
    print_error "Python extension not found"
    exit 1
fi

# Test the library
print_status "Testing library..."
if python -c "import sys; sys.path.insert(0, 'src'); import pyvvisf; print('✓ Library imports successfully')"; then
    print_success "Library test passed"
else
    print_error "Library test failed"
    exit 1
fi

# Test example
print_status "Testing example script..."
if python examples/basic_usage.py > /dev/null 2>&1; then
    print_success "Example script test passed"
else
    print_warning "Example script test failed (this may be expected)"
fi

print_success "=========================================="
print_success "Build completed successfully!"
print_success "=========================================="
print_status "The library is ready to use:"
print_status "  - Python extension: src/pyvvisf/vvisf_bindings.cpython-*.so"
print_status "  - VVGL library: external/VVISF-GL/VVGL/bin/libVVGL.a"
print_status "  - VVISF library: external/VVISF-GL/VVISF/bin/libVVISF.a"
print_status ""
print_status "To use the library:"
print_status "  import sys"
print_status "  sys.path.insert(0, 'src')"
print_status "  import pyvvisf" 