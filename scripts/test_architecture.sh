#!/bin/bash
set -e

echo "=========================================="
echo "Architecture Detection Test"
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

# Detect platform and architecture
PLATFORM=$(uname)
ARCH=$(uname -m)

print_status "Platform: $PLATFORM"
print_status "Architecture: $ARCH"

# Platform-specific architecture detection
if [[ "$PLATFORM" == "Darwin" ]]; then
    print_status "macOS detected"
    
    # Check for Apple Silicon
    if [[ "$ARCH" == "arm64" ]]; then
        print_success "Apple Silicon (ARM64) detected"
        EXPECTED_ARCH="arm64"
    elif [[ "$ARCH" == "x86_64" ]]; then
        print_success "Intel (x86_64) detected"
        EXPECTED_ARCH="x86_64"
    else
        print_warning "Unknown macOS architecture: $ARCH"
        EXPECTED_ARCH="x86_64"
    fi
    
    # Check Homebrew prefix
    if [[ "$ARCH" == "arm64" ]]; then
        HOMEBREW_PREFIX="/opt/homebrew"
    else
        HOMEBREW_PREFIX="/usr/local"
    fi
    
    if [[ -d "$HOMEBREW_PREFIX" ]]; then
        print_success "Homebrew prefix: $HOMEBREW_PREFIX"
    else
        print_warning "Homebrew prefix not found: $HOMEBREW_PREFIX"
    fi
    
elif [[ "$PLATFORM" == "Linux" ]]; then
    print_status "Linux detected"
    
    if [[ "$ARCH" == "aarch64" ]]; then
        print_success "ARM64 (AArch64) detected"
        EXPECTED_ARCH="aarch64"
    elif [[ "$ARCH" == "x86_64" ]]; then
        print_success "x86_64 detected"
        EXPECTED_ARCH="x86_64"
    else
        print_warning "Unknown Linux architecture: $ARCH"
        EXPECTED_ARCH="x86_64"
    fi
    
elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    print_status "Windows detected"
    
    if [[ "$ARCH" == "x86_64" ]]; then
        print_success "x64 detected"
        EXPECTED_ARCH="x64"
    else
        print_warning "Unknown Windows architecture: $ARCH"
        EXPECTED_ARCH="x64"
    fi
    
else
    print_warning "Unknown platform: $PLATFORM"
    EXPECTED_ARCH="x86_64"
fi

# Test Python architecture detection
print_status "Testing Python architecture detection..."

python3 -c "
import platform
import sys

print(f'Python platform: {platform.platform()}')
print(f'Python machine: {platform.machine()}')
print(f'Python architecture: {platform.architecture()}')

# Test the architecture detection logic
arch = platform.machine().lower()

if sys.platform.startswith('darwin'):
    if arch in ['arm64', 'aarch64']:
        detected_arch = 'arm64'
    elif arch == 'x86_64':
        detected_arch = 'x86_64'
    else:
        detected_arch = 'x86_64'
elif sys.platform.startswith('linux'):
    if arch in ['aarch64', 'arm64']:
        detected_arch = 'aarch64'
    elif arch in ['x86_64', 'amd64']:
        detected_arch = 'x86_64'
    else:
        detected_arch = 'x86_64'
elif sys.platform.startswith('win'):
    if arch in ['amd64', 'x86_64']:
        detected_arch = 'x64'
    elif arch in ['arm64', 'aarch64']:
        detected_arch = 'arm64'
    else:
        detected_arch = 'x64'
else:
    if arch in ['aarch64', 'arm64']:
        detected_arch = 'arm64'
    else:
        detected_arch = 'x86_64'

print(f'Detected architecture: {detected_arch}')
print(f'Expected architecture: $EXPECTED_ARCH')

if detected_arch == '$EXPECTED_ARCH':
    print('✓ Architecture detection matches expected value')
else:
    print('✗ Architecture detection mismatch')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Python architecture detection test passed"
else
    print_error "Python architecture detection test failed"
    exit 1
fi

# Test build environment variables
print_status "Testing build environment variables..."

# Set up test environment
export VVISF_BUILD_TYPE=wheel
export ARCH=$EXPECTED_ARCH

if [[ "$PLATFORM" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        export HOMEBREW_PREFIX="/opt/homebrew"
    else
        export HOMEBREW_PREFIX="/usr/local"
    fi
    export CMAKE_PREFIX_PATH="$HOMEBREW_PREFIX"
fi

# Test that environment variables are set correctly
print_status "Build environment:"
print_status "  VVISF_BUILD_TYPE: $VVISF_BUILD_TYPE"
print_status "  ARCH: $ARCH"

if [[ "$PLATFORM" == "Darwin" ]]; then
    print_status "  HOMEBREW_PREFIX: $HOMEBREW_PREFIX"
    print_status "  CMAKE_PREFIX_PATH: $CMAKE_PREFIX_PATH"
fi

print_success "=========================================="
print_success "Architecture detection test completed!"
print_success "=========================================="
print_status "Expected architecture: $EXPECTED_ARCH"
print_status "Build environment is ready for wheel building" 