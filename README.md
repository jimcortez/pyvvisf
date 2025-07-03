# pyvvisf

Python bindings for VVISF (Vidvox Interactive Shader Format) using pybind11.

## Overview

pyvvisf provides Python bindings for the VVISF library, allowing you to work with Interactive Shader Format (ISF) files in Python. This includes:

- Loading and parsing ISF shaders
- Rendering ISF shaders to images
- Managing OpenGL contexts and buffers
- Working with shader inputs and parameters

## Quick Start

### Installation

**Recommended: Install from wheels (easiest)**

```bash
pip install pyvvisf
```

**From source (for development)**

```bash
git clone https://github.com/jimcortez/pyvvisf.git
cd pyvvisf
pip install -e .
```

### Basic Usage

```python
import pyvvisf
from PIL import Image

# Use the context manager for automatic GLFW/OpenGL context management
with pyvvisf.GLContextManager() as ctx:
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
    
    # Context is automatically cleaned up when exiting the block
```

```python
import pyvvisf
from PIL import Image

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
        },
        {
            "NAME": "intensity",
            "TYPE": "float",
            "DEFAULT": 1.0,
            "MIN": 0.0,
            "MAX": 1.0
        }
    ]
}*/

void main() {
    gl_FragColor = color * intensity;
}
"""

with pyvvisf.ISFRenderer(shader_content) as renderer:
    renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
    image = renderer.render_to_pil_image(1920, 1080)
    image.save("output_green.png")

    renderer.set_input("color", pyvvisf.ISFColorVal(1.0, 0.0, 0.0, 1.0))
    image = renderer.render_to_pil_image(1920, 1080)
    image.save("output_red.png")

    renderer.set_inputs({
        "color": pyvvisf.ISFColorVal(0.0, 0.0, 1.0, 1.0),
        "intensity": pyvvisf.ISFFloatVal(0.5)
    })
    image = renderer.render_to_pil_image(1920, 1080)
    image.save("output_blue_half_intense.png")

```

## Platform Support

pyvvisf supports the following platforms:

- **Linux**: Ubuntu 20.04+ (x86_64, aarch64)
- **macOS**: 10.15+ (x86_64, arm64, universal2)
- **Windows**: Windows 2019+ (x64)

Python versions: 3.8, 3.9, 3.10, 3.11, 3.12

## Dependencies

### Runtime Dependencies
- `pillow>=9.0.0`

### Optional Dependencies
- `numpy>=1.21.0` - For numpy array integration (optional)

### System Dependencies
- **Linux**: GLFW, GLEW, OpenGL development libraries
- **macOS**: GLFW, GLEW (via Homebrew)
- **Windows**: GLFW, GLEW (via vcpkg)

These are automatically handled when installing from wheels.

## Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Context Manager Guide](docs/CONTEXT_MANAGER.md)** - Automatic GLFW/OpenGL context management
- **[Building from Source](docs/BUILDING.md)** - Detailed build instructions
- **[Development Guide](docs/DEVELOPMENT.md)** - Guide for contributors
- **[Full Documentation](docs/README.md)** - Complete documentation index

## Examples

See the `examples/` directory for more usage examples:

```bash
# Run the basic usage example
python examples/basic_usage.py
```

## Contributing

We welcome contributions! Please see our [Development Guide](docs/DEVELOPMENT.md) for details on:

- Setting up a development environment
- Building from source
- Running tests
- Submitting pull requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [VVISF](https://isf.video/) - The Interactive Shader Format specification
- [VVGL](https://github.com/mrRay/VVISF-GL) - The underlying C++ library
- [pybind11](https://pybind11.readthedocs.io/) - Python binding framework 