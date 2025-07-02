# Building pyvvisf

This guide covers all aspects of building pyvvisf from source, including development builds, wheel builds, and CI/CD.

## Quick Start

### Prerequisites

#### Python Environment

This project uses **pyenv** for Python version management. The required Python version is specified in `.python-version`.

**Install pyenv:**

**macOS:**
```bash
brew install pyenv
```

**Ubuntu/Debian:**
```bash
curl https://pyenv.run | bash
```

**Windows:**
Download from [pyenv-win](https://github.com/pyenv-win/pyenv-win)

**Set up Python environment:**
```bash
# Install the required Python version (if not already installed)
pyenv install 3.11.7

# Set the local version for this project
pyenv local 3.11.7
```

#### System Dependencies

**macOS:**
```bash
# Install Homebrew if you haven't already
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required dependencies
brew install cmake glfw glew
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install cmake libglfw3-dev libglew-dev python3-dev python3-pip
```

**Windows:**
- Install Visual Studio 2019 or later with C++ development tools
- Install CMake from https://cmake.org/download/
- Install GLFW and GLEW via vcpkg or build from source

## Installation Methods

### 1. Development Installation (Recommended for Contributors)

```bash
# Clone the repository and initialize submodules
git clone https://github.com/jimcortez/pyvvisf.git
cd pyvvisf
git submodule update --init --recursive

# Install in development mode
pip install -e ".[dev]"
```

### 2. Quick Build (Automated)

```bash
# Use the automated build script
./scripts/build.sh
```

This script will:
- Check all dependencies
- Clean previous builds
- Clone and patch VVISF-GL
- Build VVGL and VVISF libraries
- Build the Python extension
- Run basic tests

### 3. Manual Build

```bash
# Set Python version
pyenv local 3.11.7

# Apply GLFW support patches
cd external/VVISF-GL
git apply ../../patches/vvisf-glfw-support.patch
cd ../..

# Build VVGL and VVISF libraries
cd external/VVISF-GL/VVGL
make clean
ARCH=arm64 make  # or ARCH=x86_64
cd ../VVISF
make clean
ARCH=arm64 make  # or ARCH=x86_64
cd ../..

# Build Python extension
mkdir build && cd build
cmake ..
make
cd ..
```

## Wheel Building

### Local Wheel Building

For creating distributable wheels:

```bash
# Build wheel for current platform
./scripts/build_wheel.sh
```

This will:
1. Test architecture detection
2. Install build dependencies
3. Set up proper environment variables
4. Build VVISF libraries with correct architecture flags
5. Build the Python wheel

### Architecture-Specific Builds

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

### Testing Architecture Detection

Before building, you can test the architecture detection:

```bash
# Test architecture detection
./scripts/test_architecture.sh
```

This will show:
- Platform detection
- Architecture detection
- Expected build flags
- Environment setup

## Platform Support

### Supported Platforms

- **Linux**: Ubuntu 20.04+ (x86_64, aarch64)
- **macOS**: 10.15+ (x86_64, arm64, universal2)
- **Windows**: Windows 2019+ (x64)

### Python Versions

- Python 3.8, 3.9, 3.10, 3.11, 3.12

## CI/CD Integration

### GitHub Actions

The project includes automated GitHub Actions workflows that build wheels for:

- **Triggers**: Push to main/develop, pull requests, releases
- **Platforms**: Ubuntu 20.04, Windows 2019, macOS 10.15
- **Python versions**: 3.8, 3.9, 3.10, 3.11, 3.12

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

## Build System Details

### Architecture Detection

The build system includes enhanced architecture detection:

- **Automatic Detection**: Detects current platform architecture
- **Cross-Platform Builds**: Supports building for different architectures
- **Universal Binaries**: macOS universal2 support for x86_64 + arm64
- **CI/CD Integration**: Proper architecture flags in automated builds

### Build Modes

The system supports two build modes:

1. **Development Mode**: Uses pre-built VVISF libraries, requires manual setup
2. **Wheel Mode**: Automatically clones VVISF-GL, applies patches, and builds libraries

### Environment Variables

Key environment variables for building:

- `VVISF_BUILD_TYPE=wheel`: Enables wheel build mode
- `ARCH=<architecture>`: Specifies target architecture
- `BUILD_UNIVERSAL2=true`: Enables universal2 builds on macOS

## Troubleshooting

### Common Issues

1. **VVISF-GL not found**
   - Ensure git submodules are initialized: `git submodule update --init --recursive`
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

To enable verbose output during building:

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

## Advanced Topics

### Cross-Compilation

For cross-compilation scenarios, set the appropriate environment variables:

```bash
# For cross-compiling to ARM64
export ARCH=aarch64
export CROSS_COMPILE=aarch64-linux-gnu-
export VVISF_BUILD_TYPE=wheel
```

### Custom Build Configurations

You can customize the build process by modifying:

- `CMakeLists.txt`: CMake configuration
- `setup.py`: Python build configuration
- `patches/`: VVISF-GL patches
- `scripts/`: Build scripts

### Performance Optimization

For optimized builds:

```bash
# Enable optimizations
export CMAKE_BUILD_TYPE=Release
export CFLAGS="-O3 -march=native"
export CXXFLAGS="-O3 -march=native"

# Build with optimizations
python -m build --wheel
```

## Related Documentation

- **[Wheel Build Guide](WHEEL_BUILD_GUIDE.md)** - Detailed wheel building information
- **[Architecture Improvements](ARCHITECTURE_IMPROVEMENTS.md)** - Architecture detection details
- **[Development Guide](DEVELOPMENT.md)** - Guide for contributors 