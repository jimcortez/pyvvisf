# pyvvisf Segmentation Fault Fix

## Problem Summary

The pyvvisf package was experiencing segmentation faults during OpenGL rendering operations, particularly in test environments and complex applications. The issue was caused by improper GLFW context management and thread safety issues.

## Root Causes Identified

1. **GLFW Context Not Initialized**: The OpenGL context was not properly initialized before rendering operations
2. **Thread Safety Issues**: GLFW contexts are not thread-safe, and the global variables were not protected
3. **Deadlock in Context Reinitialization**: The `reinitialize_glfw_context()` function had a deadlock issue
4. **Insufficient Error Handling**: OpenGL operations lacked proper error checking
5. **Resource Management**: Potential memory leaks and improper cleanup

## Fixes Implemented

### 1. Automatic GLFW Initialization

**Problem**: GLFW context was not initialized on module import, causing segmentation faults during rendering.

**Solution**: Added automatic GLFW initialization in `__init__.py`:

```python
def _initialize_on_import():
    """Initialize GLFW context when the module is imported."""
    try:
        # Check if GLFW is already initialized
        gl_info = get_gl_info()
        if not gl_info.get('glfw_initialized', False):
            # Initialize GLFW context automatically
            if initialize_glfw_context():
                print("[pyvvisf] GLFW context initialized automatically")
            else:
                print("[pyvvisf] Warning: Failed to initialize GLFW context automatically")
    except Exception as e:
        print(f"[pyvvisf] Warning: Could not initialize GLFW context: {e}")
```

### 2. Thread Safety Improvements

**Problem**: Global GLFW variables were not protected, causing race conditions.

**Solution**: Added mutex protection to all GLFW operations:

```cpp
// Global GLFW window for OpenGL context with thread safety
static GLFWwindow* g_glfw_window = nullptr;
static bool g_glfw_initialized = false;
static std::mutex g_glfw_mutex;

bool initialize_glfw_context() {
    std::lock_guard<std::mutex> lock(g_glfw_mutex);
    // ... initialization code
}
```

### 3. Deadlock Fix in Context Reinitialization

**Problem**: `reinitialize_glfw_context()` caused deadlock by calling `initialize_glfw_context()` while holding the mutex.

**Solution**: Restructured the function to release the lock before reinitializing:

```cpp
bool reinitialize_glfw_context() {
    // Clean up existing context
    {
        std::lock_guard<std::mutex> lock(g_glfw_mutex);
        if (g_glfw_window) {
            glfwDestroyWindow(g_glfw_window);
            g_glfw_window = nullptr;
        }
        g_glfw_initialized = false;
    }
    
    // Now initialize new context (this will acquire the lock internally)
    return initialize_glfw_context();
}
```

### 4. Enhanced Error Handling

**Problem**: Insufficient error checking during OpenGL operations.

**Solution**: Added comprehensive error checking:

```cpp
// Safe OpenGL error checking
void check_gl_errors(const std::string& operation) {
    GLenum err;
    while ((err = glGetError()) != GL_NO_ERROR) {
        fprintf(stderr, "[VVISF] OpenGL error during %s: %d\n", operation.c_str(), err);
    }
}

// Enhanced GLEW initialization
GLenum glew_result = glewInit();
if (glew_result != GLEW_OK) {
    fprintf(stderr, "[VVISF] Failed to initialize GLEW: %s\n", glewGetErrorString(glew_result));
    // ... cleanup code
}
```

### 5. Resource Cleanup Function

**Problem**: No way to properly clean up GLFW resources.

**Solution**: Added cleanup function:

```cpp
void cleanup_glfw_context() {
    std::lock_guard<std::mutex> lock(g_glfw_mutex);
    
    if (g_glfw_window) {
        glfwDestroyWindow(g_glfw_window);
        g_glfw_window = nullptr;
    }
    g_glfw_initialized = false;
}
```

## Testing Results

### Before Fix
- Segmentation faults during rendering operations
- Bus errors in pytest environment
- Context switching failures
- Inconsistent behavior between isolated scripts and test environments

### After Fix
- ✅ Basic rendering works without explicit initialization
- ✅ Multiple scene creation and rendering
- ✅ Threaded rendering operations
- ✅ Memory pressure scenarios
- ✅ Safe rendering tests pass in pytest environment

**Note**: Context switching operations (`reinitialize_glfw_context()`) may still cause issues in certain test environments due to the complexity of OpenGL context management in multi-process scenarios.

## Usage Recommendations

### For Production Applications

1. **Automatic Initialization**: The module now automatically initializes GLFW on import, so no manual initialization is required for basic usage.

2. **Error Handling**: Always check return values and handle exceptions:

```python
import pyvvisf

# GLFW is automatically initialized
scene = pyvvisf.CreateISFSceneRef()
doc = pyvvisf.CreateISFDocRefWith(shader_content)
scene.use_doc(doc)

try:
    buffer = scene.create_and_render_a_buffer(pyvvisf.Size(100, 100))
    # Process buffer...
except Exception as e:
    print(f"Rendering failed: {e}")
```

3. **Resource Management**: Use context managers or explicit cleanup when needed:

```python
# For applications that need to clean up resources
pyvvisf.cleanup_glfw_context()
```

### For Testing Environments

1. **Avoid Context Switching**: The `reinitialize_glfw_context()` function may cause issues in test environments. Use the safe rendering tests as a template.

2. **Use Safe Tests**: The `tests/test_safe_rendering.py` file provides examples of safe testing patterns.

3. **Test Isolation**: Each test should create its own scene and avoid sharing OpenGL contexts between tests.

### For Complex Applications

1. **Thread Safety**: The improved thread safety allows for multi-threaded rendering, but be aware of OpenGL context limitations.

2. **Memory Management**: Monitor memory usage when creating large buffers or many scenes.

3. **Error Recovery**: Implement proper error recovery mechanisms for production applications.

## API Changes

### New Functions
- `cleanup_glfw_context()`: Clean up GLFW resources
- Enhanced `get_gl_info()`: Now includes OpenGL vendor and renderer information

### Behavior Changes
- Automatic GLFW initialization on module import
- Improved error messages and logging
- Thread-safe context management

## Known Limitations

1. **Context Switching**: The `reinitialize_glfw_context()` function may still cause issues in certain test environments due to the complexity of OpenGL context management.

2. **Test Environment Compatibility**: Some test runners may have issues with OpenGL contexts. Use the safe rendering tests as a reference.

3. **Platform Differences**: The fix has been tested on macOS. Other platforms may require additional testing.

## Conclusion

The segmentation fault issue has been resolved for the majority of use cases. The automatic GLFW initialization, improved thread safety, and enhanced error handling make pyvvisf much more robust and reliable for production use.

For applications that require context switching or have specific OpenGL requirements, additional testing and potentially platform-specific adjustments may be needed. 