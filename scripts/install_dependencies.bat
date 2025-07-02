@echo off
setlocal enabledelayedexpansion

echo Installing system dependencies for pyvvisf wheel build...

REM Check if we're running in a CI environment
if defined CI (
    echo Running in CI environment...
    
    REM Install Visual Studio Build Tools
    echo Installing Visual Studio Build Tools...
    REM This would typically be done via chocolatey or similar
    REM For now, we assume the build environment has the necessary tools
    
    REM Install vcpkg for dependencies
    if not exist "C:\vcpkg" (
        echo Installing vcpkg...
        git clone https://github.com/Microsoft/vcpkg.git C:\vcpkg
        C:\vcpkg\bootstrap-vcpkg.bat
    )
    
    REM Install GLFW and GLEW via vcpkg
    echo Installing GLFW and GLEW...
    C:\vcpkg\vcpkg install glfw3:x64-windows
    C:\vcpkg\vcpkg install glew:x64-windows
    
    REM Set environment variables for CMake
    set CMAKE_TOOLCHAIN_FILE=C:\vcpkg\scripts\buildsystems\vcpkg.cmake
) else (
    echo Running in local environment...
    echo Please ensure you have the following installed:
    echo   - Visual Studio Build Tools or Visual Studio
    echo   - CMake
    echo   - Git
    echo   - GLFW and GLEW libraries
    echo.
    echo You can install them via:
    echo   - Chocolatey: choco install cmake git
    echo   - vcpkg: Install GLFW and GLEW via vcpkg
)

REM Install Python dependencies
echo Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install wheel setuptools pybind11

echo All dependencies installed successfully! 