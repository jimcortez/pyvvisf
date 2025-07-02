#!/bin/bash
set -e

echo "Installing system dependencies for pyvvisf wheel build..."

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ -n "$WINDIR" ]]; then
    PLATFORM="windows"
else
    echo "Unsupported platform: $OSTYPE"
    exit 1
fi

echo "Detected platform: $PLATFORM"

# Install dependencies based on platform
if [[ "$PLATFORM" == "linux" ]]; then
    # For Linux, we need to install system packages
    # This script assumes we're running in a Docker container with apt
    
    # Detect architecture for Linux
    ARCH=$(uname -m)
    echo "Detected Linux architecture: $ARCH"
    
    if command -v apt-get &> /dev/null; then
        echo "Installing Linux dependencies via apt..."
        apt-get update
        
        # Base dependencies
        apt-get install -y \
            build-essential \
            cmake \
            git \
            libgl1-mesa-dev \
            libglfw3-dev \
            libglew-dev \
            pkg-config \
            python3-dev \
            python3-pip
        
        # Architecture-specific dependencies
        if [[ "$ARCH" == "aarch64" ]]; then
            echo "Installing ARM64-specific dependencies..."
            apt-get install -y \
                gcc-aarch64-linux-gnu \
                g++-aarch64-linux-gnu
        fi
        
    elif command -v yum &> /dev/null; then
        echo "Installing Linux dependencies via yum..."
        yum install -y \
            gcc \
            gcc-c++ \
            cmake \
            git \
            mesa-libGL-devel \
            glfw-devel \
            glew-devel \
            pkgconfig \
            python3-devel \
            python3-pip
        
        # Architecture-specific dependencies for yum
        if [[ "$ARCH" == "aarch64" ]]; then
            echo "Installing ARM64-specific dependencies..."
            yum install -y \
                gcc-aarch64-linux-gnu \
                gcc-c++-aarch64-linux-gnu
        fi
    else
        echo "Unsupported package manager. Please install manually:"
        echo "  - build-essential/cmake/git"
        echo "  - libgl1-mesa-dev/libglfw3-dev/libglew-dev"
        echo "  - python3-dev"
        exit 1
    fi

elif [[ "$PLATFORM" == "macos" ]]; then
    # For macOS, we need to install Homebrew packages
    
    # Detect architecture for macOS
    ARCH=$(uname -m)
    echo "Detected macOS architecture: $ARCH"
    
    if command -v brew &> /dev/null; then
        echo "Installing macOS dependencies via Homebrew..."
        
        # Install base dependencies
        brew install \
            cmake \
            glfw \
            glew \
            pkg-config
        
        # Architecture-specific setup
        if [[ "$ARCH" == "arm64" ]]; then
            echo "Setting up ARM64 (Apple Silicon) environment..."
            # Ensure we're using the right Homebrew prefix
            export HOMEBREW_PREFIX="/opt/homebrew"
        elif [[ "$ARCH" == "x86_64" ]]; then
            echo "Setting up x86_64 (Intel) environment..."
            # Ensure we're using the right Homebrew prefix
            export HOMEBREW_PREFIX="/usr/local"
        fi
        
        # Set environment variables for the build
        echo "export HOMEBREW_PREFIX=$HOMEBREW_PREFIX" >> $GITHUB_ENV
        echo "export CMAKE_PREFIX_PATH=$HOMEBREW_PREFIX" >> $GITHUB_ENV
        
    else
        echo "Homebrew not found. Please install manually:"
        echo "  brew install cmake glfw glew pkg-config"
        exit 1
    fi

elif [[ "$PLATFORM" == "windows" ]]; then
    # For Windows, we need to use PowerShell
    echo "Detected Windows platform"
    
    # Check if we're in a cibuildwheel environment
    if [[ -n "$CIBW_PLATFORM" ]]; then
        echo "Running in cibuildwheel environment, using PowerShell script..."
        # Call the PowerShell script for Windows-specific setup
        if [[ -f "scripts/install_dependencies.ps1" ]]; then
            powershell -ExecutionPolicy Bypass -File scripts/install_dependencies.ps1
        else
            echo "Windows PowerShell script not found: scripts/install_dependencies.ps1"
            exit 1
        fi
    else
        echo "Not in cibuildwheel environment, skipping Windows-specific setup"
    fi
fi

echo "System dependencies installed successfully!"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install wheel setuptools pybind11

echo "All dependencies installed successfully!" 