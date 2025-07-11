[![Read the Docs](https://readthedocs.org/projects/pyvvisf/badge/?version=latest)](https://pyvvisf.readthedocs.io/)
[![GitHub release](https://img.shields.io/github/v/release/jimcortez/pyvvisf?style=flat)](https://github.com/jimcortez/pyvvisf/releases)
[![PyPI version](https://img.shields.io/pypi/v/pyvvisf.svg)](https://pypi.org/project/pyvvisf/)

# pyvvisf

Python ISF shader renderer with PyOpenGL. Render images from your shaders, or visualize in a window.

## Overview

pyvvisf is a pure Python implementation for parsing and rendering ISF (Interactive Shader Format) shaders. It provides a modern, maintainable alternative to the [C++ VVISF-GL](https://github.com/mrRay/VVISF-GL) library with enhanced error reporting and cross-platform compatibility. The original version of this library tried to build VVISF-GL bindings, but that approach was abandoned.

This library tried to catch all the errors that would trigger the online ISF renderer here: https://editor.isf.video/. It will also try to provide compatibility warnings when appropriate.

The main use of this library is intended to be from https://github.com/jimcortez/ai-shader-tool, which provides ai's the ablility to validate, render, and inspect the results of shaders it generates.

The majority of code in this repository was built with AI.

## Features

- **Pure Python**: No C++ compilation required
- **Robust JSON parsing**: Uses json5 for comment support and trailing commas
- **Modern OpenGL**: PyOpenGL with GLFW for cross-platform context management
- **Enhanced error reporting**: Detailed Python-native error messages with context
- **Type safety**: Pydantic models for metadata validation
- **Auto-coercion**: Automatic type conversion for shader inputs
- **Context management**: Automatic resource cleanup
- **GLSL version support**: Automatic detection and support for multiple GLSL versions
- **ISF 2.0 compliance**: Full support for ISF 2.0 specification including multi-pass rendering and imports
- **ISF special functions**: Support for IMG_THIS_PIXEL, IMG_PIXEL, IMG_SIZE, and other ISF functions

## Installation

```bash
pip install pyvvisf
```

### Development Installation

```bash
git clone https://github.com/jimcortez/pyvvisf.git
cd pyvvisf
pip install -e .
```

## Quick Start

Here's a minimal example using a well-formed ISF shader:

```python
from pyvvisf import ISFRenderer

# A simple ISF shader (every pixel is the selected color)
test_shader = """
/*{
    \"DESCRIPTION\": \"Every pixel is the selected color.\",
    \"CREDIT\": \"pyvvisf example\",
    \"ISFVSN\": \"2.0\",
    \"CATEGORIES\": [\"Generator\"],
    \"INPUTS\": [
        {\"NAME\": \"color\", \"TYPE\": \"color\", \"DEFAULT\": [1.0, 0.0, 0.0, 1.0]}
    ]
}*/
void main() {
    gl_FragColor = color;
}
"""

with ISFRenderer(test_shader) as renderer:
    # Render with the default color (red)
    buffer = renderer.render(512, 512)
    image = buffer.to_pil_image()
    image.save("output_red.png")

    # Render with a custom color (green)
    renderer.set_input("color", (0.0, 1.0, 0.0, 1.0))
    buffer = renderer.render(512, 512)
    image = buffer.to_pil_image()
    image.save("output_green.png")
```

## GLSL Version Support

pyvvisf supports multiple GLSL versions and can automatically detect which versions are supported on your system:

```python
from pyvvisf import get_supported_glsl_versions, ISFRenderer

# Check which GLSL versions are supported
supported_versions = get_supported_glsl_versions()
print(f"Supported GLSL versions: {supported_versions}")

# Create renderer with specific GLSL version
renderer = ISFRenderer(shader_content, glsl_version='330')
```

The default GLSL version is '330', but you can specify any supported version. The library will automatically test shader compilation to ensure compatibility.

## Examples

See the `examples/` directory for complete examples:

- `isf_renderer_demo.py`: Render ISF shaders to images, set inputs, and save output.
- `isf_window_demo.py`: Render ISF shaders in a window (interactive display).
- `time_offset_demo.py`: Render shaders at different time offsets (for animation or frame capture).

Shader examples are in `examples/shaders/`:

- `simple_color_change.fs`: Single color input, fills the screen with the selected color.
- `simple_color_animation.fs`: Fades between two user-selected colors over time.
- `shapes.fs`: Animated shapes (moving circle, rotating rectangle, pulsating ring).
- `simple.fs`: Minimal shader, fills the screen with blue.

## Development

### Building

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
pyvvisf/
├── src/pyvvisf/
│   ├── renderer.py      # Main renderer
│   ├── parser.py        # ISF parser with json5
│   ├── types.py         # Value types
│   ├── errors.py        # Error handling
│   ├── shader_compiler.py # Shader compilation and processing
│   ├── framebuffer_manager.py # Framebuffer management
│   └── input_manager.py # Input validation and management
├── examples/
├── tests/
└── docs/
```

## License

MIT License - see LICENSE file for details.

## Special Thanks

- https://github.com/mrRay/VVISF-GL for initial reference implementation
- https://github.com/msfeldstein/interactive-shader-format-js for another reference implementation
- https://github.com/mcfletch/pyopengl for all the bindings
- https://github.com/FlorianRhiem/pyGLFW for the bindings