# Wheel Migration Summary

This document summarizes the changes made to convert pyvvisf from a manual build system to a Python wheel-based multiplatform distribution system.

## Overview

The project has been converted from a manual build process to a modern Python wheel build system that supports:
- **Multiplatform distribution** (Linux, macOS, Windows)
- **Automated CI/CD** via GitHub Actions
- **Local wheel building** for development and testing
- **PyPI distribution** for easy installation

## Files Added

### Build System Configuration
- **`pyproject.toml`** (updated): Modern Python packaging configuration with wheel support
- **`setup.py`** (updated): Enhanced build system with wheel and development build modes
- **`src/pyvvisf/_version.py`**: Version file for setuptools_scm

### Platform-Specific Scripts
- **`scripts/install_dependencies.sh`**: Linux/macOS dependency installation
- **`scripts/install_dependencies.bat`**: Windows dependency installation
- **`scripts/build_wheel.sh`**: Local wheel building script
- **`scripts/test_wheel.py`**: Wheel installation test script

### CI/CD Configuration
- **`.github/workflows/build-wheels.yml`**: GitHub Actions workflow for automated wheel building

### Documentation
- **`docs/WHEEL_BUILD_GUIDE.md`**: Comprehensive wheel build documentation
- **`README.md`** (updated): Added wheel installation instructions

## Files Modified

### Core Build Files
- **`CMakeLists.txt`**: Added wheel build detection and improved error handling
- **`pyproject.toml`**: Complete rewrite for modern Python packaging
- **`setup.py`**: Complete rewrite with wheel build support

### Documentation
- **`README.md`**: Added wheel installation section and updated build instructions

## Key Changes

### 1. Build System Modernization

**Before**: Manual build process requiring:
- Manual VVISF-GL setup
- Manual library compilation
- Manual CMake configuration
- Platform-specific build instructions

**After**: Automated wheel build system with:
- Automatic dependency management
- Cross-platform compilation
- CI/CD integration
- Standard Python packaging

### 2. Multiplatform Support

**Before**: Limited to development platform
**After**: Support for:
- Linux (Ubuntu 20.04+, x86_64, aarch64)
- macOS (10.15+, x86_64, arm64, universal2)
- Windows (2019+, x64)

### 3. Installation Simplification

**Before**: Users needed to:
1. Install system dependencies
2. Clone repository
3. Initialize submodules
4. Apply patches
5. Build libraries
6. Build Python extension
7. Install package

**After**: Users can simply:
```bash
pip install pyvvisf
```

### 4. CI/CD Integration

**Before**: Manual builds only
**After**: Automated builds on:
- Push to main/develop branches
- Pull requests
- Release creation
- Automatic PyPI upload

## Build Modes

The new build system supports two modes:

### Development Mode
- Uses pre-built VVISF libraries
- Requires manual setup (original workflow)
- Faster for development
- Command: `pip install -e .`

### Wheel Mode
- Automatically clones and builds VVISF-GL
- Self-contained build process
- Suitable for distribution
- Command: `./scripts/build_wheel.sh`

## Platform Support Matrix

| Platform | Python Versions | Architectures | CI/CD | Local Build |
|----------|----------------|---------------|-------|-------------|
| Linux    | 3.8-3.12       | x86_64, aarch64 | ✅    | ✅          |
| macOS    | 3.8-3.12       | x86_64, arm64   | ✅    | ✅          |
| Windows  | 3.8-3.12       | x64            | ✅    | ✅          |

## Dependencies

### Build Dependencies
- `setuptools>=61.0`
- `wheel`
- `pybind11>=2.6.0`
- `setuptools_scm[toml]>=6.2`
- `ninja>=1.10.0`

### Runtime Dependencies
- `numpy>=1.21.0`
- `pillow>=9.0.0`

### System Dependencies
- **Linux**: GLFW, GLEW, OpenGL development libraries
- **macOS**: GLFW, GLEW (via Homebrew)
- **Windows**: GLFW, GLEW (via vcpkg)

## Migration Benefits

### For Users
1. **Simplified Installation**: One command installation
2. **No Compilation Required**: Pre-built wheels for all platforms
3. **Better Compatibility**: Tested on multiple platforms
4. **Version Management**: Automatic version detection

### For Developers
1. **Automated Builds**: CI/CD handles multiplatform builds
2. **Reduced Maintenance**: Standard Python packaging
3. **Better Testing**: Automated testing across platforms
4. **Easier Distribution**: PyPI integration

### For Maintainers
1. **Reduced Support Burden**: Fewer installation issues
2. **Better Quality**: Automated testing and builds
3. **Wider Adoption**: Easier installation encourages usage
4. **Modern Standards**: Follows Python packaging best practices

## Backward Compatibility

The migration maintains backward compatibility:
- Original build scripts still work for development
- Development installation (`pip install -e .`) unchanged
- All existing functionality preserved
- Gradual migration path available

## Testing

### Local Testing
```bash
# Build wheel
./scripts/build_wheel.sh

# Test installation
pip install dist/pyvvisf-*.whl
python scripts/test_wheel.py
```

### CI/CD Testing
- Automated builds on multiple platforms
- Automated testing of wheel installation
- Automated PyPI upload on releases

## Future Enhancements

Potential improvements for the wheel build system:
1. **Manylinux Support**: For better Linux compatibility
2. **Static Linking**: For better portability
3. **Docker Builds**: For consistent build environments
4. **Binary Distribution**: Pre-built VVISF libraries
5. **ARM64 Windows**: When supported by Python

## Conclusion

The migration to wheel builds significantly improves the user experience while maintaining developer flexibility. The automated CI/CD system ensures consistent, high-quality builds across all supported platforms, making pyvvisf more accessible to a wider audience. 