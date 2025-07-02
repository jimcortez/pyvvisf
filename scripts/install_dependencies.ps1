# Windows PowerShell script for installing dependencies during wheel builds
# This script is used by cibuildwheel on Windows

Write-Host "Installing system dependencies for pyvvisf wheel build on Windows..."

# Set error action preference to stop on errors
$ErrorActionPreference = "Stop"

try {
    # Check if we're running in a cibuildwheel environment
    if ($env:CIBW_PLATFORM -eq "windows") {
        Write-Host "Detected cibuildwheel Windows environment"
        
        # Install Visual Studio Build Tools if not already available
        # cibuildwheel should provide these, but we can check
        Write-Host "Checking for Visual Studio Build Tools..."
        
        # Check for MSVC compiler
        try {
            $clOutput = & cl 2>&1
            Write-Host "MSVC compiler found"
        } catch {
            Write-Host "MSVC compiler not found in PATH"
        }
        
        # Check for CMake
        try {
            $cmakeVersion = & cmake --version 2>&1
            Write-Host "CMake found: $cmakeVersion"
        } catch {
            Write-Host "CMake not found, installing via winget..."
            & winget install Kitware.CMake
        }
        
        # Install Python dependencies
        Write-Host "Installing Python dependencies..."
        & python -m pip install --upgrade pip
        & python -m pip install wheel setuptools pybind11
        
        # Build VVISF libraries for Windows
        Write-Host "Building VVISF libraries for Windows..."
        $BuildScript = Join-Path $PSScriptRoot "build_vvisf.ps1"
        if (Test-Path $BuildScript) {
            Write-Host "Running VVISF build script: $BuildScript"
            & $BuildScript -Configuration "Release" -Platform "x64"
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to build VVISF libraries"
            }
            Write-Host "✓ VVISF libraries built successfully"
        } else {
            throw "VVISF build script not found: $BuildScript"
        }
        
        # Set environment variables for the build
        Write-Host "Setting up environment variables..."
        $env:VVISF_BUILD_TYPE = "wheel"
        $env:CMAKE_GENERATOR = "Visual Studio 17 2022"
        
        # For Windows, we need to ensure we have the right architecture
        if ($env:CIBW_ARCHS -eq "x64") {
            $env:CMAKE_GENERATOR_PLATFORM = "x64"
        } elseif ($env:CIBW_ARCHS -eq "x86") {
            $env:CMAKE_GENERATOR_PLATFORM = "Win32"
        }
        
        Write-Host "Environment setup complete"
        Write-Host "CMAKE_GENERATOR: $env:CMAKE_GENERATOR"
        Write-Host "CMAKE_GENERATOR_PLATFORM: $env:CMAKE_GENERATOR_PLATFORM"
        
    } else {
        Write-Host "Not running in cibuildwheel environment, skipping Windows-specific setup"
    }
    
} catch {
    Write-Host "Error during Windows dependency installation: $_"
    exit 1
}

Write-Host "Windows dependencies installed successfully!" 