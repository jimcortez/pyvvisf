# Architecture Improvements for Wheel Builds

This document summarizes the improvements made to ensure VVISF and VVGL have proper CPU architecture flags when building with wheels.

## Overview

The wheel build system has been enhanced with comprehensive architecture detection and support to ensure that VVISF and VVGL libraries are built with the correct CPU architecture flags for each target platform.

## Key Improvements

### 1. Enhanced Architecture Detection

**Before**: Basic architecture detection using `platform.machine()`
```python
arch = platform.machine()
if arch == 'arm64' or arch == 'aarch64':
    arch = 'arm64'
else:
    arch = 'x86_64'
```

**After**: Comprehensive architecture detection with platform-specific logic
```python
def _detect_architecture(self):
    # Check CI environment variables
    ci_arch = os.environ.get('CIBW_ARCHS')
    if ci_arch:
        return self._normalize_arch(ci_arch)
    
    # Check target architecture
    target_arch = os.environ.get('TARGET_ARCH')
    if target_arch:
        return target_arch
    
    # Platform-specific detection
    arch = platform.machine().lower()
    
    if sys.platform.startswith('darwin'):
        # macOS: arm64, x86_64, universal2
        if arch in ['arm64', 'aarch64']:
            return 'arm64'
        elif arch == 'x86_64':
            return 'universal2' if os.environ.get('BUILD_UNIVERSAL2') == 'true' else 'x86_64'
    elif sys.platform.startswith('linux'):
        # Linux: aarch64, x86_64
        if arch in ['aarch64', 'arm64']:
            return 'aarch64'
        elif arch in ['x86_64', 'amd64']:
            return 'x86_64'
    elif sys.platform.startswith('win'):
        # Windows: x64, arm64
        if arch in ['amd64', 'x86_64']:
            return 'x64'
        elif arch in ['arm64', 'aarch64']:
            return 'arm64'
```

### 2. Improved Makefile Support

**VVISF-GL Makefiles Enhanced**:
- Added architecture validation and normalization
- Support for universal2 builds on macOS
- Proper environment variable handling
- Cross-platform architecture flags

**Key Changes**:
```makefile
# Architecture detection and validation
ARCH ?= $(shell uname -m)
ARCH := $(shell echo $(ARCH) | tr '[:upper:]' '[:lower:]')

# Validate and normalize architecture
ifeq ($(ARCH),aarch64)
    ARCH := arm64
endif
ifeq ($(ARCH),amd64)
    ARCH := x86_64
endif
ifeq ($(ARCH),universal2)
    ARCH_FLAGS := -arch x86_64 -arch arm64
endif
```

### 3. CMake Integration

**Enhanced CMakeLists.txt**:
- Architecture-aware configuration
- Platform-specific compiler flags
- Proper CMAKE_OSX_ARCHITECTURES handling
- Linux architecture optimization

**Key Additions**:
```cmake
# Architecture detection and configuration
if(DEFINED ENV{ARCH})
    set(TARGET_ARCH $ENV{ARCH})
    
    if(APPLE)
        if(TARGET_ARCH STREQUAL "universal2")
            set(CMAKE_OSX_ARCHITECTURES "x86_64;arm64")
        else()
            set(CMAKE_OSX_ARCHITECTURES ${TARGET_ARCH})
        endif()
    elseif(UNIX AND NOT APPLE)
        if(TARGET_ARCH STREQUAL "aarch64")
            set(CMAKE_SYSTEM_PROCESSOR "aarch64")
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -march=native -mtune=native")
        endif()
    endif()
endif()
```

### 4. Build Environment Configuration

**Enhanced Environment Setup**:
- Platform-specific environment variables
- Architecture-aware dependency paths
- Proper compiler flag propagation

**macOS Example**:
```bash
if [[ "$ARCH" == "arm64" ]]; then
    export HOMEBREW_PREFIX="/opt/homebrew"
elif [[ "$ARCH" == "x86_64" ]]; then
    export HOMEBREW_PREFIX="/usr/local"
fi
export CMAKE_PREFIX_PATH="$HOMEBREW_PREFIX"
```

**Linux Example**:
```bash
if [[ "$ARCH" == "aarch64" ]]; then
    export CFLAGS="-march=native -mtune=native"
    export CXXFLAGS="-march=native -mtune=native"
fi
```

### 5. CI/CD Integration

**GitHub Actions Enhanced**:
- Architecture-specific build configurations
- Proper environment variable propagation
- Multi-architecture support

**Workflow Configuration**:
```yaml
env:
  CIBW_BEFORE_ALL: scripts/install_dependencies.sh
  CIBW_ENVIRONMENT: VVISF_BUILD_TYPE=wheel
  CIBW_BUILD: "cp38-* cp39-* cp310-* cp311-* cp312-*"
  CIBW_SKIP: "*-musllinux*"
  # Architecture-specific settings
  CIBW_MACOS_ARCHS: "x86_64 arm64 universal2"
  CIBW_LINUX_ARCHS: "x86_64 aarch64"
  CIBW_WINDOWS_ARCHS: "x64"
```

### 6. Testing and Validation

**New Test Scripts**:
- `scripts/test_architecture.sh`: Comprehensive architecture detection testing
- Integration with wheel build process
- Validation of build environment setup

**Test Coverage**:
- Platform detection
- Architecture detection
- Environment variable validation
- Build flag verification

## Supported Architectures

### macOS
- **x86_64**: Intel Macs
- **arm64**: Apple Silicon (M1/M2/M3)
- **universal2**: Universal binary (x86_64 + arm64)

### Linux
- **x86_64**: Standard x86_64 systems
- **aarch64**: ARM64 systems (Raspberry Pi 4, ARM servers)

### Windows
- **x64**: 64-bit Windows
- **arm64**: ARM64 Windows (when supported)

## Build Process Flow

1. **Architecture Detection**: Automatic detection with fallbacks
2. **Environment Setup**: Platform-specific environment variables
3. **Dependency Installation**: Architecture-aware dependency paths
4. **VVISF-GL Build**: Proper architecture flags for VVGL and VVISF
5. **Python Extension**: CMake with architecture-specific configuration
6. **Wheel Packaging**: Architecture-tagged wheel files

## Benefits

### For Users
- **Correct Architecture**: Wheels built for the right CPU architecture
- **Better Performance**: Optimized for target platform
- **Universal Support**: macOS universal2 binaries work on both Intel and Apple Silicon

### For Developers
- **Automated Detection**: No manual architecture specification needed
- **Cross-Platform Builds**: Easy building for multiple architectures
- **CI/CD Integration**: Automated multi-architecture builds

### For Maintainers
- **Reduced Support**: Fewer architecture-related issues
- **Better Coverage**: Support for more platforms and architectures
- **Future-Proof**: Ready for new architectures (ARM64 Windows, etc.)

## Usage Examples

### Local Development
```bash
# Automatic architecture detection
./scripts/build_wheel.sh

# Specific architecture
export ARCH=arm64
./scripts/build_wheel.sh

# Universal2 on macOS
export ARCH=universal2
./scripts/build_wheel.sh
```

### CI/CD
```bash
# GitHub Actions automatically handles:
# - Multiple architectures
# - Platform-specific builds
# - Proper environment setup
```

### Testing
```bash
# Test architecture detection
./scripts/test_architecture.sh

# Test wheel installation
pip install dist/pyvvisf-*.whl
python scripts/test_wheel.py
```

## Future Enhancements

1. **ARM64 Windows**: Full support when Python provides ARM64 Windows wheels
2. **Manylinux**: Enhanced Linux compatibility with manylinux wheels
3. **Static Linking**: Better portability with static linking options
4. **Docker Builds**: Consistent build environments across platforms
5. **Binary Distribution**: Pre-built VVISF libraries for faster builds

## Conclusion

The architecture improvements ensure that pyvvisf wheels are built with the correct CPU architecture flags, providing optimal performance and compatibility across all supported platforms. The automated detection and build process makes it easy for users to get the right wheel for their system while maintaining flexibility for developers and maintainers. 