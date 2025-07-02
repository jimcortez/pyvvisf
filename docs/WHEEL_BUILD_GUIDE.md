# Wheel Build Guide

This document explains how pyvvisf's wheel build system works and how to use it for multiplatform distribution.

## Overview

pyvvisf supports building Python wheels for multiplatform distribution. This allows users to install the package without needing to compile from source, making installation much easier across different platforms.

## Architecture

The wheel build system consists of several components:

1. **Build System Configuration** (`pyproject.toml`, `setup.py`)
2. **Platform-specific Dependency Scripts** (`scripts/install_dependencies.sh`, `scripts/install_dependencies.bat`)
3. **CI/CD Workflows** (`.github/workflows/build-wheels.yml`)
4. **Local Build Scripts** (`scripts/build_wheel.sh`)

## Build Process

### 1. Development Build vs Wheel Build

The build system detects whether it's building for development or for wheel distribution:

- **Development Build**: Uses pre-built VVISF libraries, requires manual setup
- **Wheel Build**: Automatically clones VVISF-GL, applies patches, and builds libraries

### 2. Wheel Build Process

When building a wheel (`VVISF_BUILD_TYPE=wheel`):

1. **Clone VVISF-GL**: Downloads the VVISF-GL repository if not present
2. **Apply Patches**: Applies GLFW support patches
3. **Build Libraries**: Compiles VVGL and VVISF libraries for the target platform
4. **Build Extension**: Compiles the Python extension using CMake
5. **Package Wheel**: Creates the final wheel file

### 3. Platform Support

The wheel build system supports:

- **Linux**: Ubuntu 20.04+ (x86_64, aarch64)
- **macOS**: 10.15+ (x86_64, arm64, universal2)
- **Windows**: Windows 2019+ (x64, arm64)

### 4. Architecture Support

The build system includes enhanced architecture detection and support:

- **Automatic Detection**: Detects current platform architecture
- **Cross-Platform Builds**: Supports building for different architectures
- **Universal Binaries**: macOS universal2 support for x86_64 + arm64
- **CI/CD Integration**: Proper architecture flags in automated builds

## Local Wheel Building

### Prerequisites

1. **Python 3.8+**
2. **Build tools**: `build`, `wheel`, `setuptools_scm`, `pybind11`
3. **System dependencies** (see [Building Guide](BUILDING.md) for details)

### Building a Wheel

```bash
# Install build dependencies
pip install build wheel setuptools_scm[toml] pybind11

# Test architecture detection (optional)
./scripts/test_architecture.sh

# Build wheel
./scripts/build_wheel.sh
```

The build script will automatically:
1. Test architecture detection
2. Install build dependencies
3. Set up proper environment variables
4. Build VVISF libraries with correct architecture flags
5. Build the Python wheel

### Testing the Wheel

```bash
# Install the wheel
pip install dist/pyvvisf-*.whl

# Test installation
python scripts/test_wheel.py
```

## Platform-Specific Dependencies

For detailed system dependency installation instructions, see the [Building Guide](BUILDING.md).

## CI/CD Integration

### GitHub Actions

The project includes GitHub Actions workflows that automatically build wheels:

- **Triggers**: Push to main/develop, pull requests, releases
- **Platforms**: Ubuntu 20.04, Windows 2019, macOS 10.15
- **Python versions**: 3.8, 3.9, 3.10, 3.11, 3.12

### Workflow Configuration

The workflow uses `cibuildwheel` for cross-platform wheel building:

```yaml
env:
  CIBW_BEFORE_ALL: scripts/install_dependencies.sh
  CIBW_ENVIRONMENT: VVISF_BUILD_TYPE=wheel
  CIBW_BUILD: "cp38-* cp39-* cp310-* cp311-* cp312-*"
  CIBW_SKIP: "*-musllinux*"
```

### Manual CI/CD

To build wheels manually using `cibuildwheel`:

```bash
# Install cibuildwheel
pip install cibuildwheel

# Build for current platform
cibuildwheel --platform auto

# Build for specific platform
cibuildwheel --platform linux
cibuildwheel --platform macos
cibuildwheel --platform windows
```

### Architecture-specific builds

You can build for specific architectures:

```bash
# Build for specific architecture
export ARCH=arm64
export VVISF_BUILD_TYPE=wheel
python -m build --wheel

# Build universal2 on macOS
export ARCH=universal2
export VVISF_BUILD_TYPE=wheel
python -m build --wheel

# Build for ARM64 Linux
export ARCH=aarch64
export VVISF_BUILD_TYPE=wheel
python -m build --wheel
```

### Testing architecture detection

Before building, you can test the architecture detection:

```bash
# Test architecture detection
./scripts/test_architecture.sh

# This will show:
# - Platform detection
# - Architecture detection
# - Expected build flags
# - Environment setup
```

## Troubleshooting

### Common Issues

1. **VVISF-GL not found**
   - Ensure git submodules are initialized
   - Check network connectivity for cloning

2. **Library build failures**
   - Verify system dependencies are installed
   - Check compiler version compatibility
   - Ensure sufficient disk space

3. **CMake configuration errors**
   - Verify pybind11 is installed
   - Check CMake version (requires 3.15+)
   - Ensure platform-specific libraries are available

4. **Wheel installation failures**
   - Check Python version compatibility
   - Verify wheel was built for correct platform
   - Check for missing runtime dependencies

### Debug Mode

To enable verbose output during wheel building:

```bash
# Set verbose mode
export CMAKE_VERBOSE_MAKEFILE=ON
export VVISF_BUILD_TYPE=wheel

# Build with verbose output
python -m build --wheel --verbose
```

### Platform-Specific Debugging

#### Linux
```bash
# Check OpenGL libraries
ldconfig -p | grep -i gl

# Check GLFW installation
pkg-config --modversion glfw3

# Check GLEW installation
pkg-config --modversion glew
```

#### macOS
```bash
# Check Homebrew packages
brew list | grep -E "(glfw|glew|cmake)"

# Check library paths
otool -L /opt/homebrew/lib/libglfw.dylib
```

#### Windows
```bash
# Check vcpkg installation
C:\vcpkg\vcpkg list

# Check Visual Studio installation
where cl.exe
```

## Distribution

### PyPI Upload

Wheels are automatically uploaded to PyPI when a release is created:

1. Create a release tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. Create a GitHub release with the same tag

3. Wheels will be automatically built and uploaded to PyPI

### Manual PyPI Upload

To manually upload wheels to PyPI:

```bash
# Install twine
pip install twine

# Upload wheels
twine upload dist/*
```

### Local Distribution

To distribute wheels locally:

```bash
# Build wheels
./scripts/build_wheel.sh

# Share the dist/ directory
# Users can install with: pip install pyvvisf-*.whl
```

## Best Practices

1. **Version Management**: Use `setuptools_scm` for automatic versioning
2. **Dependency Management**: Keep system dependencies minimal and well-documented
3. **Testing**: Always test wheels on target platforms before distribution
4. **Documentation**: Keep build instructions up to date
5. **CI/CD**: Use automated workflows for consistent builds

## Future Improvements

Potential enhancements to the wheel build system:

1. **Manylinux Support**: Add support for manylinux wheels
2. **ARM64 Support**: Improve ARM64 support across all platforms
3. **Static Linking**: Consider static linking for better portability
4. **Docker Builds**: Add Docker-based build environments
5. **Binary Distribution**: Consider distributing pre-built VVISF libraries

## Related Documentation

- **[Building Guide](BUILDING.md)** - General build instructions and prerequisites
- **[Development Guide](DEVELOPMENT.md)** - Guide for contributors
- **[Architecture Improvements](ARCHITECTURE_IMPROVEMENTS.md)** - Detailed architecture detection information 