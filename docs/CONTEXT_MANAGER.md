# GLContextManager - Automatic GLFW/OpenGL Context Management

The `GLContextManager` provides a convenient and safe way to manage GLFW and OpenGL contexts using Python's context manager protocol. It automatically handles context initialization, validation, error checking, and cleanup, preventing common issues like segmentation faults and resource leaks.

## Quick Start

```python
import pyvvisf

# Simple usage with automatic cleanup
with pyvvisf.GLContextManager() as ctx:
    # Your rendering code here
    scene = pyvvisf.CreateISFSceneRef()
    buffer = scene.create_and_render_a_buffer(pyvvisf.Size(640, 480))
    # Context is automatically cleaned up when exiting the block
```

## Features

- **Automatic Context Management**: Initializes and cleans up GLFW/OpenGL contexts automatically
- **Exception Safety**: Ensures proper cleanup even when exceptions occur
- **Error Checking**: Built-in OpenGL error checking and validation
- **Flexible Configuration**: Customizable initialization and cleanup behavior
- **Nested Support**: Support for nested context managers
- **Context Reinitialization**: Ability to reinitialize contexts within a manager

## Basic Usage

### Simple Context Management

```python
import pyvvisf

with pyvvisf.GLContextManager() as ctx:
    # Context is automatically initialized and validated
    scene = pyvvisf.CreateISFSceneRef()
    
    # Load and use a shader
    shader_content = """
    /*{
        "DESCRIPTION": "My shader",
        "CREDIT": "Me",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
    """
    
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene.use_doc(doc)
    
    # Render
    buffer = scene.create_and_render_a_buffer(pyvvisf.Size(256, 256))
    
    # Check for errors
    ctx.check_errors("rendering operation")
    
    # Context is automatically cleaned up when exiting the block
```

### Error Handling and Validation

```python
with pyvvisf.GLContextManager(validate_on_enter=True) as ctx:
    # Context is validated on entry
    if ctx.is_valid():
        print("Context is valid")
    
    # Get context information
    gl_info = ctx.get_info()
    print(f"OpenGL Version: {gl_info.get('gl_version')}")
    
    # Check for errors after operations
    ctx.check_errors("my operation")
    
    # Reset context state if needed
    ctx.reset_state()
```

## Advanced Usage

### Custom Configuration

```python
# Context manager with custom settings
with pyvvisf.GLContextManager(
    auto_initialize=True,    # Automatically initialize context
    auto_cleanup=True,       # Automatically cleanup on exit
    validate_on_enter=False  # Skip validation on entry
) as ctx:
    # Your code here
    pass
```

### Context Reinitialization

```python
with pyvvisf.GLContextManager() as ctx:
    # Initial rendering
    buffer1 = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
    
    # Reinitialize context (useful for resetting state)
    ctx.reinitialize()
    
    # Render after reinitialization
    buffer2 = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
```

### Nested Context Managers

```python
# Outer context
with pyvvisf.GLContextManager(auto_cleanup=False) as outer_ctx:
    # Inner context (reuses outer context)
    with pyvvisf.GLContextManager(auto_initialize=False, auto_cleanup=False) as inner_ctx:
        # Both contexts are valid
        if outer_ctx.is_valid() and inner_ctx.is_valid():
            print("Both contexts valid")
        
        # Render with inner context
        buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
    
    # Outer context still active
    if outer_ctx.is_valid():
        print("Outer context remains valid")
```

### Batch Processing

```python
with pyvvisf.GLContextManager() as ctx:
    # Process multiple shaders in a single context
    shaders = [
        ("red", "vec4(1.0, 0.0, 0.0, 1.0)"),
        ("green", "vec4(0.0, 1.0, 0.0, 1.0)"),
        ("blue", "vec4(0.0, 0.0, 1.0, 1.0)"),
    ]
    
    for name, color in shaders:
        # Create shader
        shader_content = f"""
        /*{{
            "DESCRIPTION": "{name.capitalize()} shader",
            "CREDIT": "Demo",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }}*/
        void main() {{
            gl_FragColor = {color};
        }}
        """
        
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Render
        buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
        
        # Check for errors after each operation
        ctx.check_errors(f"{name} shader rendering")
```

## API Reference

### GLContextManager

#### Constructor

```python
GLContextManager(auto_initialize=True, auto_cleanup=True, validate_on_enter=True)
```

**Parameters:**
- `auto_initialize` (bool): Whether to automatically initialize the GLFW context
- `auto_cleanup` (bool): Whether to automatically cleanup the context on exit
- `validate_on_enter` (bool): Whether to validate the context when entering

#### Methods

##### `check_errors(operation_name="operation")`
Check for OpenGL errors.

**Parameters:**
- `operation_name` (str): Name of the operation for error reporting

##### `reset_state()`
Reset the OpenGL context state.

##### `is_valid()`
Check if the context is valid.

**Returns:** bool

##### `get_info()`
Get GL context information.

**Returns:** dict

##### `reinitialize()`
Reinitialize the GLFW context. Useful for resetting context state without exiting the manager.

## Comparison with Manual Management

### Manual Approach (Old Way)

```python
# Manual initialization
if not pyvvisf.initialize_glfw_context():
    raise RuntimeError("Failed to initialize GLFW context")

# Manual context acquisition
pyvvisf.acquire_context_ref()

# Manual validation
if not pyvvisf.validate_gl_context():
    raise RuntimeError("Context validation failed")

# Manual state reset
pyvvisf.reset_gl_context_state()

try:
    # Your rendering code here
    scene = pyvvisf.CreateISFSceneRef()
    buffer = scene.create_and_render_a_buffer(pyvvisf.Size(640, 480))
    
    # Manual error checking
    pyvvisf.check_gl_errors("rendering")
    
finally:
    # Manual cleanup (MUST NOT FORGET!)
    pyvvisf.release_context_ref()
    pyvvisf.cleanup_glfw_context()
```

### Context Manager Approach (New Way)

```python
# Simple and clean with automatic management
with pyvvisf.GLContextManager() as ctx:
    # Your rendering code here
    scene = pyvvisf.CreateISFSceneRef()
    buffer = scene.create_and_render_a_buffer(pyvvisf.Size(640, 480))
    
    # Convenient error checking
    ctx.check_errors("rendering")
    
    # Context automatically cleaned up when exiting the block
```

## Benefits

1. **Automatic Cleanup**: No risk of forgetting to cleanup resources
2. **Exception Safety**: Proper cleanup even when exceptions occur
3. **Cleaner Code**: Less boilerplate and more readable
4. **Built-in Error Handling**: Convenient error checking and validation
5. **Prevents Crashes**: Eliminates common causes of segmentation faults
6. **Resource Management**: Automatic resource lifecycle management

## Migration Guide

If you're currently using manual context management, here's how to migrate:

1. **Replace manual initialization/cleanup** with `GLContextManager`
2. **Move your rendering code** inside the `with` block
3. **Replace manual error checking** with `ctx.check_errors()`
4. **Remove manual cleanup code** - it's handled automatically

### Before (Manual)

```python
pyvvisf.initialize_glfw_context()
pyvvisf.acquire_context_ref()

try:
    # Your code here
    pass
finally:
    pyvvisf.release_context_ref()
    pyvvisf.cleanup_glfw_context()
```

### After (Context Manager)

```python
with pyvvisf.GLContextManager() as ctx:
    # Your code here
    pass
```

## Examples

See the following example files for complete demonstrations:

- `examples/context_manager_demo.py` - Comprehensive demonstration of all features
- `examples/context_manager_comparison.py` - Before/after comparison
- `examples/critical_fixes_demo.py` - Integration with existing functionality

## Notes

- The `GLContextManager` is designed to work alongside existing manual context management functions
- All existing functionality remains available for advanced use cases
- The context manager provides a safer, more convenient interface for most use cases
- Nested context managers are supported for complex scenarios
- Context reinitialization is available for resetting state without exiting the manager 