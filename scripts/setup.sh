#!/bin/bash
set -e

echo "Setting up pyvvisf..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: Not in a git repository"
    echo "Please ensure you cloned this repository with git."
    exit 1
fi

# Initialize submodules (only VVISF-GL)
echo "Initializing git submodules..."
if ! git submodule update --init --recursive; then
    echo "Error: Failed to initialize submodules"
    echo "Please check your git configuration and try again."
    exit 1
fi

# Verify VVISF-GL submodule is properly initialized
if [ ! -f "external/VVISF-GL/README.md" ]; then
    echo "Error: VVISF-GL submodule not properly initialized"
    echo "The external/VVISF-GL directory appears to be empty."
    echo "Please try:"
    echo "  git submodule update --init --recursive"
    echo "  git submodule status"
    exit 1
fi

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v cmake &> /dev/null; then
    echo "Error: cmake not found. Please install cmake."
    echo "  macOS: brew install cmake"
    echo "  Ubuntu: sudo apt-get install cmake"
    echo "  Windows: Download from https://cmake.org/download/"
    exit 1
fi

if ! command -v make &> /dev/null; then
    echo "Error: make not found. Please install make."
    echo "  macOS: Install Xcode Command Line Tools: xcode-select --install"
    echo "  Ubuntu: sudo apt-get install make"
    echo "  Windows: Install via MinGW or Visual Studio"
    exit 1
fi

# Check for pyenv and Python
echo "Checking for pyenv and Python..."
if ! command -v pyenv &> /dev/null; then
    echo "Error: pyenv not found. Please install pyenv first."
    echo "  macOS: brew install pyenv"
    echo "  Ubuntu: curl https://pyenv.run | bash"
    echo "  Windows: Download from https://github.com/pyenv-win/pyenv-win"
    exit 1
fi

echo "✓ pyenv found"
PYENV_VERSION=$(pyenv version 2>/dev/null | cut -d' ' -f1)
echo "  Current pyenv version: $PYENV_VERSION"

# Check if .python-version file exists and use it
if [ -f ".python-version" ]; then
    REQUIRED_VERSION=$(cat .python-version)
    echo "  Required Python version: $REQUIRED_VERSION"
    
    # Check if the required version is installed
    if ! pyenv versions | grep -q "$REQUIRED_VERSION"; then
        echo "Installing Python $REQUIRED_VERSION..."
        pyenv install "$REQUIRED_VERSION"
    fi
    
    # Set local version
    pyenv local "$REQUIRED_VERSION"
    echo "✓ Set local Python version to $REQUIRED_VERSION"
else
    echo "Warning: No .python-version file found"
    echo "  Consider creating one with: pyenv local 3.11.7"
fi

# Get the Python executable
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

if [ -n "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    echo "✓ Python found: $PYTHON_VERSION"
    
    # Check if Python version is 3.8 or higher
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo "⚠ Warning: Python version $PYTHON_VERSION is older than recommended (3.8+)"
        echo "  Consider using pyenv to install Python 3.11.7:"
        echo "    pyenv install 3.11.7"
        echo "    pyenv local 3.11.7"
    fi
fi

# Check for GLFW and GLEW
echo "Checking for GLFW and GLEW..."
GLFW_FOUND=false
GLEW_FOUND=false

if pkg-config --exists glfw3 2>/dev/null; then
    GLFW_FOUND=true
    echo "✓ GLFW3 found via pkg-config"
elif [ -f "/opt/homebrew/include/GLFW/glfw3.h" ] || [ -f "/usr/local/include/GLFW/glfw3.h" ]; then
    GLFW_FOUND=true
    echo "✓ GLFW3 found in system include paths"
else
    echo "⚠ GLFW3 not found via pkg-config or in standard locations"
    echo "  macOS: brew install glfw"
    echo "  Ubuntu: sudo apt-get install libglfw3-dev"
    echo "  Windows: Install via vcpkg or build from source"
fi

if pkg-config --exists glew 2>/dev/null; then
    GLEW_FOUND=true
    echo "✓ GLEW found via pkg-config"
elif [ -f "/opt/homebrew/include/GL/glew.h" ] || [ -f "/usr/local/include/GL/glew.h" ]; then
    GLEW_FOUND=true
    echo "✓ GLEW found in system include paths"
else
    echo "⚠ GLEW not found via pkg-config or in standard locations"
    echo "  macOS: brew install glew"
    echo "  Ubuntu: sudo apt-get install libglew-dev"
    echo "  Windows: Install via vcpkg or build from source"
fi

if [ "$GLFW_FOUND" = false ] || [ "$GLEW_FOUND" = false ]; then
    echo ""
    echo "Warning: Some dependencies may be missing."
    echo "The build may fail if GLFW or GLEW are not properly installed."
    echo "Continuing anyway..."
    echo ""
fi

# Build VVISF-GL libraries
echo "Building VVISF-GL libraries..."
if ! ./scripts/build_vvisf.sh; then
    echo ""
    echo "Error: Failed to build VVISF-GL libraries"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Ensure GLFW and GLEW are installed:"
    echo "   macOS: brew install glfw glew"
    echo "   Ubuntu: sudo apt-get install libglfw3-dev libglew-dev"
    echo ""
    echo "2. Check if the patch was applied correctly:"
    echo "   grep -q 'VVGL_SDK_GLFW' external/VVISF-GL/VVGL/Makefile"
    echo "   grep -q 'VVGL_SDK_GLFW' external/VVISF-GL/VVISF/Makefile"
    echo ""
    echo "3. Try manual patch application:"
    echo "   cd external/VVISF-GL"
    echo "   patch -p1 < ../../patches/vvisf-glfw-support.patch"
    echo ""
    echo "4. Check architecture compatibility:"
    echo "   uname -m"
    echo "   (Should be 'arm64' or 'x86_64')"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if ! pip install -e ".[dev]"; then
    echo ""
    echo "Error: Failed to install Python dependencies"
    echo "Please check the pip output above for specific errors."
    exit 1
fi

# Build main project
echo "Building main project..."
mkdir -p build
cd build
if ! cmake ..; then
    echo ""
    echo "Error: CMake configuration failed"
    echo "Please check the CMake output above for specific errors."
    exit 1
fi

if ! make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4); then
    echo ""
    echo "Error: Build failed"
    echo "Please check the build output above for specific errors."
    exit 1
fi

echo "✓ Setup complete!"
echo ""
echo "To run tests:"
echo "  cd build && ./vvisf_test"
echo ""
echo "To build Python bindings:"
echo "  cd build && make pyvvisf"
echo ""
echo "To install in development mode:"
echo "  pip install -e ."
echo ""
echo "If you encounter any issues, please check the troubleshooting section"
echo "in the README.md file or run the setup script with verbose output." 