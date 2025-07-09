# pyvvisf API Reference

This document provides a comprehensive reference for the pyvvisf Python bindings for VVISF.

## Core Classes



### ISFRenderer

High-level convenience class for rendering ISF shaders with automatic OpenGL context management.

```python
import pyvvisf

# Create renderer with shader content
with pyvvisf.ISFRenderer(shader_content) as renderer:
    # Set shader inputs
    renderer.set_input("color", pyvvisf.ISFColorVal(1.0, 0.0, 0.0, 1.0))
    renderer.set_input("intensity", pyvvisf.ISFFloatVal(0.8))
    
    # Render to buffer and convert to PIL Image
    buffer = renderer.render(1920, 1080)
    image = buffer.to_pil_image()
    image.save("output.png")
    
    # Render with time offset (for animated shaders)
    buffer = renderer.render(1920, 1080, time_offset=5.0)
    image = buffer.to_pil_image()
    image.save("output_5s.png")
    
    # Render to buffer (can be converted to PIL Image or numpy array)
    buffer = renderer.render(1920, 1080, time_offset=2.5)
    
    # Set multiple inputs at once
    renderer.set_inputs({
        "color": pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0),
        "speed": pyvvisf.ISFFloatVal(1.5)
    })
    
    # Get shader information
    info = renderer.get_shader_info()
    print(f"Shader: {info['name']}")
    print(f"Inputs: {info['inputs']}")
```

#### Methods

- `render(width, height, time_offset=0.0)` - Render to GLBuffer (can be converted to PIL Image or numpy array)
- `set_input(name, value)` - Set a single input value
- `set_inputs(inputs_dict)` - Set multiple input values
- `get_shader_info()` - Get information about the loaded shader
- `get_current_inputs()` - Get currently set input values
- `check_errors(operation_name)` - Check for OpenGL errors
- `is_valid()` - Check if renderer is in valid state

### Size and Rect

Utility classes for dimensions and rectangles.

```python
# Create size
size = pyvvisf.Size(width, height)

# Create rectangle
rect = pyvvisf.Rect(x, y, width, height)
```

## High-Level Interface

### ISFRenderer

The `ISFRenderer` class provides a convenient high-level interface for working with ISF shaders, including automatic OpenGL context management and input value coercion.

```python
import pyvvisf

shader_content = """
/*{
    "DESCRIPTION": "Simple shader",
    "INPUTS": [
        {
            "NAME": "color",
            "TYPE": "color",
            "DEFAULT": [1.0, 0.0, 0.0, 1.0]
        },
        {
            "NAME": "intensity",
            "TYPE": "float",
            "DEFAULT": 1.0
        }
    ]
}*/

void main() {
    gl_FragColor = color * intensity;
}
"""

with pyvvisf.ISFRenderer(shader_content) as renderer:
    # Auto-coercion: Python primitives are automatically converted
    renderer.set_input("color", (0.0, 1.0, 0.0))  # RGB tuple -> ISFColorVal
    renderer.set_input("intensity", 0.5)  # float -> ISFFloatVal
    
    buffer = renderer.render(1920, 1080)
    image = buffer.to_pil_image()
    image.save("output.png")
```

#### Auto-Coercion

The `ISFRenderer` automatically converts Python primitives to the appropriate ISF value types:

- **Numbers**: `bool`, `int`, `float` → `ISFBoolVal`, `ISFLongVal`, `ISFFloatVal`
- **Tuples/Lists**: 
  - 2 numbers → `ISFPoint2DVal`
  - 3 numbers → `ISFColorVal` (RGB + alpha=1.0)
  - 4 numbers → `ISFColorVal` (RGBA)

```python
# These are equivalent:
renderer.set_input("color", pyvvisf.ISFColorVal(1.0, 0.0, 0.0, 1.0))
renderer.set_input("color", (1.0, 0.0, 0.0, 1.0))

renderer.set_input("intensity", pyvvisf.ISFFloatVal(0.5))
renderer.set_input("intensity", 0.5)

# RGB to RGBA conversion:
renderer.set_input("color", (1.0, 0.0, 0.0))  # Automatically adds alpha=1.0
```

#### Methods

- `set_input(name, value)`: Set a single input value
- `set_inputs(inputs_dict)`: Set multiple input values at once
- `render(width, height, time_offset=0.0)`: Render the shader to a buffer
- `get_shader_info()`: Get information about the loaded shader
- `get_current_inputs()`: Get currently set input values

## Value Types

### ISFBoolVal

Boolean values for shader inputs.

```python
bool_val = pyvvisf.ISFBoolVal(True)
```

### ISFLongVal

Integer values for shader inputs.

```python
int_val = pyvvisf.ISFLongVal(42)
```

### ISFFloatVal

Float values for shader inputs.

```python
float_val = pyvvisf.ISFFloatVal(3.14)
```

### ISFPoint2DVal

2D point values for shader inputs.

```python
point_val = pyvvisf.ISFPoint2DVal(x, y)
```

### ISFColorVal

Color values (RGBA) for shader inputs.

```python
color_val = pyvvisf.ISFColorVal(r, g, b, a)
```

### ISFStringVal

String values for shader inputs.

```python
string_val = pyvvisf.ISFStringVal("text")
```

## Error Handling

Most functions will raise exceptions if they fail:

```python
try:
    scene = pyvvisf.CreateISFSceneRef()
    # ... use scene
except Exception as e:
    print(f"Error: {e}")
```

This library is now a pure Python implementation. No C++ compilation or bindings are required. See the README for migration notes. 