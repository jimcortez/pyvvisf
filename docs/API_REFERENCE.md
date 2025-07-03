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

## Factory Functions

### CreateISFSceneRef()

Create a new ISF scene.

```python
scene = pyvvisf.CreateISFSceneRef()
```

### CreateISFDocRefWith(content)

Create ISF document from shader content.

```python
doc = pyvvisf.CreateISFDocRefWith(shader_source_code)
```

### CreateGLBufferRef()

Create a new GL buffer.

```python
buffer = pyvvisf.CreateGLBufferRef()
```

## Utility Functions

### initialize_glfw_context()

Initialize GLFW and OpenGL context.

```python
success = pyvvisf.initialize_glfw_context()
```

### reinitialize_glfw_context()

Reinitialize the OpenGL context (useful for headless/batch environments).

```python
success = pyvvisf.reinitialize_glfw_context()
```

### get_gl_info()

Get information about the current OpenGL/GLFW context.

```python
info = pyvvisf.get_gl_info()
print(info)
```

### get_platform_info()

Get platform information.

```python
platform = pyvvisf.get_platform_info()
# Returns string like "GLFW (VVGL_SDK_GLFW)"
```

### is_vvisf_available()

Check if VVISF is working correctly.

```python
available = pyvvisf.is_vvisf_available()
```


### isf_val_type_to_string(type)

Convert ISF value type to string.

```python
type_str = pyvvisf.isf_val_type_to_string(pyvvisf.ISFValType_Bool)
```

### isf_file_type_to_string(type)

Convert ISF file type to string.

```python
file_type_str = pyvvisf.isf_file_type_to_string(pyvvisf.ISFFileType_None)
```

## Enums

### ISFValType

ISF value types.

```python
pyvvisf.ISFValType_Bool
pyvvisf.ISFValType_Long
pyvvisf.ISFValType_Float
pyvvisf.ISFValType_Point2D
pyvvisf.ISFValType_Color
pyvvisf.ISFValType_Image
pyvvisf.ISFValType_String
```

### ISFFileType

ISF file types.

```python
pyvvisf.ISFFileType_None
pyvvisf.ISFFileType_Fragment
pyvvisf.ISFFileType_Vertex
pyvvisf.ISFFileType_Geometry
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

## Memory Management

The C++ objects are automatically managed by Python's reference counting. However, for large buffers or long-running applications, you may want to explicitly clean up:

```python
# Scene cleanup
scene.prepare_to_be_deleted()

# Buffer pool cleanup (if available)
if hasattr(pool, 'cleanup'):
    pool.cleanup()
```

## Thread Safety

The VVISF bindings are not thread-safe. All operations should be performed from the same thread that initialized the OpenGL context. 

For more details, see the [main README](../README.md) and the `tests/` directory for working test examples. 