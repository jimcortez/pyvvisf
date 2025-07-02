# pyvvisf API Reference

> **Note:** As of July 2024, all batch rendering and OpenGL context bugs have been fixed. All tests pass on all supported platforms. The API below is current and stable.

This document provides a comprehensive reference for the pyvvisf Python bindings for VVISF.

## Core Classes

### ISFScene

The main class for rendering ISF shaders.

```python
import pyvvisf

# Create a scene
scene = pyvvisf.CreateISFSceneRef()

# Use a document
scene.use_doc(doc)

# Set input values
scene.set_value_for_input_named(value, "input_name")

# Render to buffer
buffer = scene.create_and_render_a_buffer(size)

# Set buffer for image input
scene.set_buffer_for_input_named(buffer, "image_input_name")
```

### ISFDoc

Represents an ISF document/shader.

```python
# Create from shader content
doc = pyvvisf.CreateISFDocRefWith(shader_content)

# Access document properties
name = doc.name()
description = doc.description()
credit = doc.credit()
version = doc.vsn()
categories = doc.categories()

# Get inputs
inputs = doc.inputs()
for input_attr in inputs:
    print(f"Input: {input_attr.name()}, Type: {input_attr.type()}")
```

### ISFAttr

Represents shader attributes/inputs.

```python
# Access input properties
input_name = attr.name()
input_type = attr.type()
input_description = attr.description()
```

### GLBuffer

OpenGL buffer for image data.

```python
# Create buffer
buffer = pyvvisf.CreateGLBufferRef()

# Get buffer properties
size = buffer.size
name = buffer.name

# Convert to PIL Image
image = buffer.to_pil_image()

# Create from PIL Image
buffer = pyvvisf.GLBuffer.from_pil_image(pil_image)
```

### GLBufferPool

Pool for managing GL buffers.

```python
# Create buffer pool
pool = pyvvisf.GLBufferPool()

# Create buffer from pool
buffer = pool.create_buffer(size)
```

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