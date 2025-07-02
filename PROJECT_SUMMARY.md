# pyvvisf Project Summary

## Overview

The `pyvvisf` project is a standalone Python library that provides Python bindings for VVISF (Vidvox Interactive Shader Format) using pybind11. This project was extracted from the original `ai-shader-tool` project to simplify the build process and create a reusable library.

## Project Structure

```
pyvvisf/
├── src/pyvvisf/              # Python package source
│   ├── __init__.py           # Package initialization and API
│   └── vvisf_bindings.cpp    # C++ bindings source
├── external/                 # External dependencies
│   └── VVISF-GL/            # VVISF-GL submodule
├── scripts/                  # Build scripts
│   ├── build_vvisf.sh       # VVISF-GL build script
│   └── setup.sh             # Setup script
├── patches/                  # Build patches
│   └── vvisf-glfw-support.patch
├── tests/                    # Test files
│   └── test_pyvvisf.py      # Basic tests
├── examples/                 # Usage examples
│   └── basic_usage.py       # Basic usage example
├── docs/                     # Documentation
│   └── API_REFERENCE.md     # API reference
├── CMakeLists.txt           # CMake configuration
├── setup.py                 # Python setup script
├── pyproject.toml           # Project configuration
├── .python-version          # Python version specification
├── Makefile                 # Build automation
├── README.md                # Project documentation
├── LICENSE                  # MIT license
└── .gitignore              # Git ignore patterns
```

## Key Features

### Core Functionality
- **ISF Shader Loading**: Load and parse ISF shader files
- **Shader Rendering**: Render ISF shaders to images
- **OpenGL Context Management**: Manage GLFW/OpenGL contexts
- **Buffer Management**: Handle OpenGL buffers and image conversion
- **Input Parameter Management**: Set shader inputs and parameters

### Python API
- **Clean Python Interface**: Easy-to-use Python API
- **PIL Integration**: Convert between OpenGL buffers and PIL Images
- **Type Safety**: Proper type handling for all ISF value types
- **Error Handling**: Comprehensive error handling and reporting

### Build System
- **CMake Integration**: Uses CMake for C++ compilation
- **pybind11 as Dependency**: Uses pybind11 as a proper Python dependency
- **pyenv Integration**: Uses pyenv for Python version management
- **Cross-Platform**: Supports macOS, Linux, and Windows
- **GLFW Support**: Uses GLFW for OpenGL context management

## Installation

### Prerequisites

#### Python Environment
This project uses **pyenv** for Python version management:
```bash
# Install pyenv
brew install pyenv  # macOS
curl https://pyenv.run | bash  # Ubuntu/Debian

# Set up Python environment
pyenv install 3.11.7
pyenv local 3.11.7
```

#### System Dependencies
- **macOS**: `brew install cmake glfw glew`
- **Ubuntu/Debian**: `sudo apt-get install cmake libglfw3-dev libglew-dev python3-dev`
- **Windows**: Visual Studio 2019+, CMake, GLFW/GLEW via vcpkg

#### Python Dependencies
The project automatically installs required dependencies including pybind11.

### Installation Steps

1. **Clone and Setup**:
   ```bash
   git clone https://github.com/yourusername/pyvvisf.git
   cd pyvvisf
   git submodule update --init --recursive
   ```

2. **Set up Python environment**:
   ```bash
   # Install pyenv if not already installed
   make install-pyenv
   
   # Set up the development environment
   make setup
   ```

3. **Alternative manual setup**:
   ```bash
   pyenv local 3.11.7
   ./scripts/build_vvisf.sh
   pip install -e .
   ```

## Usage

### Basic Example

```python
import pyvvisf
from PIL import Image

# Initialize context
pyvvisf.initialize_glfw_context()

# Create scene and load shader
scene = pyvvisf.CreateISFSceneRef()
shader_content = """
/*{
    "DESCRIPTION": "Simple color shader",
    "INPUTS": [
        {
            "NAME": "color",
            "TYPE": "color",
            "DEFAULT": [1.0, 0.0, 0.0, 1.0]
        }
    ]
}*/
void main() {
    gl_FragColor = INPUTS_color;
}
"""

doc = pyvvisf.CreateISFDocRefWith(shader_content)
scene.use_doc(doc)

# Set inputs and render
scene.set_value_for_input_named(pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0), "color")
size = pyvvisf.Size(800, 600)
buffer = scene.create_and_render_a_buffer(size)

# Convert to PIL Image and save
image = buffer.to_pil_image()
image.save("output.png")
```

## Development

### Building from Source

```bash
# Set up development environment
make setup

# Build the project
make build

# Run tests
make test

# Clean build artifacts
make clean
```

### Development Tools

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
make lint

# Format code
make format

# Check dependencies
make check-deps
```

## Integration with Original Project

The original `ai-shader-tool` project can now use `pyvvisf` as a dependency instead of building the VVISF bindings directly. This simplifies the build process and reduces complexity.

### Benefits for Original Project

1. **Simplified Build**: No need to manage VVISF-GL submodule and build scripts
2. **Cleaner Architecture**: Separation of concerns between shader rendering and tool logic
3. **Reusability**: The VVISF bindings can be used by other projects
4. **Easier Maintenance**: Focus on tool functionality rather than binding complexity
5. **Better Testing**: Isolated testing of the VVISF bindings
6. **Modern Dependencies**: Uses pybind11 as a proper dependency instead of a submodule

### Migration Path

To use `pyvvisf` in the original project:

1. **Install pyvvisf**:
   ```bash
   pip install pyvvisf
   ```

2. **Update imports**:
   ```python
   # Old: from . import vvisf_bindings as vvisf
   # New:
   import pyvvisf as vvisf
   ```

3. **Remove build complexity** from your original project:
   - Remove VVISF-GL submodule
   - Remove C++ build scripts
   - Simplify CMakeLists.txt
   - Remove vvisf_bindings.cpp

## Key Changes from Original

### Dependency Management
- **pybind11**: Now uses pybind11 as a proper Python dependency instead of a submodule
- **pyenv**: Integrated pyenv for Python version management
- **Simplified Submodules**: Only VVISF-GL remains as a submodule

### Build System
- **Modern CMake**: Uses `find_package(pybind11)` instead of subdirectory inclusion
- **Automated Setup**: Enhanced setup scripts with pyenv integration
- **Better Error Handling**: Improved dependency checking and error messages

### Development Workflow
- **Python Version Management**: Automatic Python version setup via pyenv
- **Dependency Installation**: Automated installation of Python dependencies
- **Build Automation**: Enhanced Makefile with pyenv support

## Troubleshooting

### Common Issues

1. **pyenv not found**: Install pyenv using the instructions above
2. **Python version mismatch**: Run `pyenv local 3.11.7` in the project directory
3. **GLFW/GLEW not found**: Ensure system dependencies are installed
4. **VVISF libraries not built**: Run `./scripts/build_vvisf.sh`
5. **OpenGL context issues**: Try `reinitialize_glfw_context()`
6. **Import errors**: Ensure the C++ extension is built

### Debug Information

```python
import pyvvisf

# Get system information
print(f"Platform: {pyvvisf.get_platform_info()}")
print(f"OpenGL Info: {pyvvisf.get_gl_info()}")
print(f"VVISF Available: {pyvvisf.is_vvisf_available()}")
```

## Future Enhancements

1. **Wheels**: Pre-built wheels for common platforms
2. **Documentation**: Sphinx documentation with examples
3. **CI/CD**: Automated testing and deployment
4. **Performance**: Optimizations for large-scale rendering
5. **Features**: Additional VVISF functionality

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request 