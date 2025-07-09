# pyvvisf

Pure Python ISF shader renderer with PyOpenGL and json5.

## Overview

pyvvisf is a pure Python implementation for parsing and rendering ISF (Interactive Shader Format) shaders. It provides a modern, maintainable alternative to the C++ VVISF-GL library with enhanced error reporting and cross-platform compatibility.

## Features

- **Pure Python**: No C++ compilation required
- **Robust JSON parsing**: Uses json5 for comment support and trailing commas
- **Modern OpenGL**: PyOpenGL with GLFW for cross-platform context management
- **Enhanced error reporting**: Detailed Python-native error messages with context
- **Type safety**: Pydantic models for metadata validation
- **Auto-coercion**: Automatic type conversion for shader inputs
- **Context management**: Automatic resource cleanup

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

```python
from pyvvisf import ISFRenderer, ISFColor, ISFPoint2D

# Create a simple test shader
test_shader = """
/*{
    "NAME": "Test Shader",
    "INPUTS": [
        {
            "NAME": "color",
            "TYPE": "color",
            "DEFAULT": [1.0, 0.0, 0.0, 1.0]
        },
        {
            "NAME": "scale",
            "TYPE": "float",
            "DEFAULT": 1.0
        }
    ]
}*/

uniform vec2 RENDERSIZE;
uniform vec4 color;
uniform float scale;

out vec4 fragColor;

void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
    vec2 pos = (uv - 0.5) * scale;
    float dist = length(pos);
    float circle = smoothstep(0.5, 0.4, dist);
    fragColor = color * circle;
}
"""

# Render the shader
with ISFRenderer() as renderer:
    # Load shader
    metadata = renderer.load_shader_content(test_shader)
    
    # Render with default parameters
    image_array = renderer.render(width=512, height=512)
    
    # Render with custom parameters
    custom_inputs = {
        'color': ISFColor.from_rgb(0.0, 1.0, 0.0, 1.0),  # Green
        'scale': 2.0
    }
    
    image_array = renderer.render(
        width=512, height=512,
        inputs=custom_inputs,
        metadata=metadata
    )
    
    # Save to file
    renderer.save_render("output.png", width=512, height=512)
```

## API Reference

### Core Classes

#### `ISFRenderer`

Main renderer class for ISF shaders.

```python
renderer = ISFRenderer()
```

**Methods:**
- `load_shader(shader_path: str) -> ISFMetadata`: Load shader from file
- `load_shader_content(content: str) -> ISFMetadata`: Load shader from string
- `render(width, height, inputs=None, metadata=None) -> np.ndarray`: Render to numpy array
- `save_render(output_path, width, height, inputs=None, metadata=None)`: Render and save to file

#### `ISFParser`

Parser for ISF shader files using json5.

```python
parser = ISFParser()
glsl_code, metadata = parser.parse_file("shader.fs")
```

#### Value Types

- `ISFColor(r, g, b, a=1.0)`: RGBA color value
- `ISFPoint2D(x, y)`: 2D point value
- `ISFFloat(value)`: Float value
- `ISFInt(value)`: Integer value
- `ISFBool(value)`: Boolean value

### Error Handling

The library provides detailed error classes:

- `ISFError`: Base exception for ISF-related errors
- `ISFParseError`: Error parsing ISF shader content
- `ShaderCompilationError`: Error compiling or linking shaders
- `RenderingError`: Error during rendering process
- `ValidationError`: Error validating ISF metadata or inputs

## Examples

See the `examples/` directory for complete examples:

- `pure_python_demo.py`: Basic usage demonstration
- `isf_renderer_demo.py`: Advanced rendering examples

## Migration from VVISF-GL

This is a complete re-implementation and is not backward compatible with the previous VVISF-GL-based version. Key differences:

### Old API (VVISF-GL)
```python
from pyvvisf import ISFScene, CreateISFSceneRef

scene = CreateISFSceneRef()
doc = scene.createISFDocRefWith("shader.fs")
# ... complex C++-style API
```

### New API (Pure Python)
```python
from pyvvisf import ISFRenderer

with ISFRenderer() as renderer:
    metadata = renderer.load_shader("shader.fs")
    image = renderer.render(width=1920, height=1080)
```

## Development

### Building

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
pyvvisf/
├── src/pyvvisf/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── renderer.py      # Main renderer
│   │   ├── parser.py        # ISF parser with json5
│   │   ├── types.py         # Value types
│   │   └── errors.py        # Error handling
│   ├── __init__.py
│   └── _version.py
├── examples/
├── tests/
└── docs/
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 