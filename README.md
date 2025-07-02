# pyvvisf

Python bindings for VVISF (Vidvox Interactive Shader Format) using pybind11.

## Overview

pyvvisf provides Python bindings for the VVISF library, allowing you to work with Interactive Shader Format (ISF) files in Python. This includes:

- Loading and parsing ISF shaders
- Rendering ISF shaders to images
- Managing OpenGL contexts and buffers
- Working with shader inputs and parameters

## Prerequisites

### Python Environment

This project uses **pyenv** for Python version management. The required Python version is specified in `.python-version`.

#### Install pyenv

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

#### Set up Python environment
```bash
# Install the required Python version (if not already installed)
pyenv install 3.11.7

# Set the local version for this project
pyenv local 3.11.7
```

### System Dependencies

#### macOS
```bash
# Install Homebrew if you haven't already
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required dependencies
brew install cmake glfw glew
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install cmake libglfw3-dev libglew-dev python3-dev python3-pip
```

#### Windows
- Install Visual Studio 2019 or later with C++ development tools
- Install CMake from https://cmake.org/download/
- Install GLFW and GLEW via vcpkg or build from source

### Python Dependencies

The project automatically installs required Python dependencies including pybind11.

## Installation

### From Source

1. **Clone the repository and initialize submodules**:
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

   This will:
   - Install the required Python version (3.11.7)
   - Build VVISF-GL libraries
   - Install Python dependencies
   - Build the Python extension

3. **Alternative manual setup**:
   ```bash
   # Set Python version
   pyenv local 3.11.7
   
   # Build VVISF libraries
   ./scripts/build_vvisf.sh
   
   # Install Python package
   pip install -e .
   ```

### Development Installation

For development, you can install with additional tools:

```bash
pip install -e ".[dev]"
```

## Usage

### Basic Example

```python
import pyvvisf
from PIL import Image

# Initialize GLFW context
pyvvisf.initialize_glfw_context()

# Create an ISF scene
scene = pyvvisf.CreateISFSceneRef()

# Load an ISF shader
shader_content = """
/*{
    "DESCRIPTION": "Simple color shader",
    "CREDIT": "Example",
    "CATEGORIES": ["Color Effect"],
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

# Create ISF document from shader content
doc = pyvvisf.CreateISFDocRefWith(shader_content)
scene.use_doc(doc)

# Set shader inputs
scene.set_value_for_input_named(pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0), "color")

# Render to a buffer
size = pyvvisf.Size(1920, 1080)
buffer = scene.create_and_render_a_buffer(size)

# Convert to PIL Image
image = buffer.to_pil_image()
image.save("output.png")
```

### Working with ISF Files

```python
import pyvvisf

# Check if a file is an ISF file
if pyvvisf.file_is_probably_isf("shader.fs"):
    print("This looks like an ISF file!")

# Scan for ISF files in a directory
isf_files = pyvvisf.scan_for_isf_files("./shaders", recursive=True)
print(f"Found {len(isf_files)} ISF files")

# Get default ISF files
default_files = pyvvisf.get_default_isf_files()
print(f"Default ISF files: {default_files}")
```

### Managing OpenGL Context

```python
import pyvvisf

# Get platform and OpenGL information
print(f"Platform: {pyvvisf.get_platform_info()}")
print(f"OpenGL Info: {pyvvisf.get_gl_info()}")

# Reinitialize context if needed
pyvvisf.reinitialize_glfw_context()

# Check if VVISF is available
if pyvvisf.is_vvisf_available():
    print("VVISF is working correctly!")
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

### Project Structure

```
pyvvisf/
├── src/pyvvisf/           # Python package
│   ├── __init__.py        # Package initialization
│   └── vvisf_bindings.cpp # C++ bindings source
├── external/              # External dependencies
│   └── VVISF-GL/         # VVISF-GL submodule
├── scripts/              # Build scripts
├── tests/                # Test files
├── examples/             # Usage examples
├── docs/                 # Documentation
├── CMakeLists.txt        # CMake configuration
├── setup.py              # Python setup
├── pyproject.toml        # Project configuration
├── .python-version       # Python version specification
└── Makefile              # Build automation
```

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

# Get detailed system information
print(f"Platform: {pyvvisf.get_platform_info()}")
print(f"OpenGL Info: {pyvvisf.get_gl_info()}")
print(f"VVISF Available: {pyvvisf.is_vvisf_available()}")
```

### Environment Setup

If you're having issues with the Python environment:

```bash
# Check current Python version
python --version

# Check pyenv versions
pyenv versions

# Install required version if missing
pyenv install 3.11.7

# Set local version
pyenv local 3.11.7

# Verify installation
python --version
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Acknowledgments

- VVISF-GL: The underlying C++ library for ISF support
- pybind11: Python binding library
- GLFW: OpenGL context management
- GLEW: OpenGL extension loading 