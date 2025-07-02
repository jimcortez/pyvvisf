#!/bin/bash
set -e

echo "=========================================="
echo "pyvvisf Wheel Build Script"
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
if [ ! -f "pyproject.toml" ]; then
    print_error "This script must be run from the pyvvisf project root directory"
    exit 1
fi

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build dist *.egg-info wheelhouse
print_success "Clean completed"

# Test architecture detection
print_status "Testing architecture detection..."
./scripts/test_architecture.sh

# Install build dependencies
print_status "Installing build dependencies..."
pip install --upgrade pip
pip install build wheel setuptools_scm[toml] pybind11
print_success "Build dependencies installed"

# Build wheel
print_status "Building wheel..."
export VVISF_BUILD_TYPE=wheel
python -m build --wheel

# Check if wheel was created
if [ -f "dist/pyvvisf-*.whl" ]; then
    print_success "Wheel built successfully!"
    print_status "Wheel location: dist/"
    ls -la dist/
else
    print_error "Wheel not found in dist/"
    exit 1
fi

print_success "=========================================="
print_success "Wheel build completed successfully!"
print_success "=========================================="
print_status "To install the wheel:"
print_status "  pip install dist/pyvvisf-*.whl"
print_status ""
print_status "To test the wheel:"
print_status "  pip install dist/pyvvisf-*.whl"
print_status "  python -c \"import pyvvisf; print('✓ Library imports successfully')\"" 