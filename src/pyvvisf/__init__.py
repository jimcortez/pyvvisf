"""Python bindings for VVISF (Vidvox Interactive Shader Format)."""

import sys
from pathlib import Path

# Try to import the C++ bindings
try:
    from . import vvisf_bindings as _vvisf
except ImportError:
    try:
        from . import pyvvisf as _vvisf
    except ImportError as e:
        # If the C++ module is not available, provide a helpful error message
        raise ImportError(
            f"Failed to import VVISF C++ bindings: {e}\n"
            "Please ensure that:\n"
            "1. VVISF-GL libraries are built (run ./scripts/build_vvisf.sh)\n"
            "2. The C++ extension is compiled (run python setup.py build_ext)\n"
            "3. All dependencies (GLFW, GLEW, OpenGL) are installed"
        ) from e

# Re-export the main classes and functions
__all__ = [
    # Core VVISF classes
    'ISFScene',
    'ISFDoc', 
    'ISFAttr',
    # VVGL classes
    'GLBuffer',
    'GLBufferPool',
    'Size',
    'Rect',
    # Value types
    'ISFBoolVal',
    'ISFLongVal', 
    'ISFFloatVal',
    'ISFPoint2DVal',
    'ISFColorVal',
    # Factory functions
    'CreateISFSceneRef',
    'CreateISFDocRefWith',
    # Utility functions
    'reinitialize_glfw_context',
    'get_gl_info',
    'get_platform_info',
    'is_vvisf_available',
    # ISF file utilities
    'scan_for_isf_files',
    'get_default_isf_files',
    'file_is_probably_isf',
    'isf_val_type_to_string',
    'isf_file_type_to_string',
]

# Import and expose the main classes
try:
    # ISFScene and related
    ISFScene = _vvisf.ISFScene
    ISFDoc = _vvisf.ISFDoc
    ISFAttr = _vvisf.ISFAttr
    # VVGL classes
    GLBuffer = _vvisf.GLBuffer
    GLBufferPool = _vvisf.GLBufferPool
    Size = _vvisf.Size
    Rect = _vvisf.Rect
    # Value types
    ISFBoolVal = _vvisf.ISFBoolVal
    ISFLongVal = _vvisf.ISFLongVal
    ISFFloatVal = _vvisf.ISFFloatVal
    ISFPoint2DVal = _vvisf.ISFPoint2DVal
    ISFColorVal = _vvisf.ISFColorVal
    # Factory functions
    CreateISFSceneRef = _vvisf.CreateISFSceneRef
    CreateISFDocRefWith = _vvisf.CreateISFDocRefWith
    # Utility functions
    reinitialize_glfw_context = _vvisf.reinitialize_glfw_context
    get_gl_info = _vvisf.get_gl_info
    get_platform_info = _vvisf.get_platform_info
    is_vvisf_available = _vvisf.is_vvisf_available
    # ISF file utilities
    scan_for_isf_files = _vvisf.scan_for_isf_files
    get_default_isf_files = _vvisf.get_default_isf_files
    file_is_probably_isf = _vvisf.file_is_probably_isf
    isf_val_type_to_string = _vvisf.isf_val_type_to_string
    isf_file_type_to_string = _vvisf.isf_file_type_to_string
except AttributeError as e:
    # If some classes are not available, provide a helpful error
    raise ImportError(
        f"Some VVISF classes are not available: {e}\n"
        "This may indicate a version mismatch or incomplete build."
    ) from e

# Version info
__version__ = "0.1.0"

# Check if VVISF is available
def check_vvisf_availability():
    """Check if VVISF is properly initialized and available."""
    try:
        return is_vvisf_available()
    except Exception:
        return False

# Initialize GLFW context on import if not already done
def _initialize_on_import():
    """Initialize GLFW context when the module is imported."""
    # Not available in current bindings
    pass  # initialize_glfw_context not present in vvisf_bindings

# Try to initialize on import
_initialize_on_import()

# Export ISFValType_* at module level
ISFValType_None = _vvisf.ISFValType_None
ISFValType_Event = _vvisf.ISFValType_Event
ISFValType_Bool = _vvisf.ISFValType_Bool
ISFValType_Long = _vvisf.ISFValType_Long
ISFValType_Float = _vvisf.ISFValType_Float
ISFValType_Point2D = _vvisf.ISFValType_Point2D
ISFValType_Color = _vvisf.ISFValType_Color
ISFValType_Cube = _vvisf.ISFValType_Cube
ISFValType_Image = _vvisf.ISFValType_Image
ISFValType_Audio = _vvisf.ISFValType_Audio
ISFValType_AudioFFT = _vvisf.ISFValType_AudioFFT

# Export initialize_glfw_context
initialize_glfw_context = _vvisf.initialize_glfw_context

# Export ISFFileType_* at module level
ISFFileType_None = _vvisf.ISFFileType_None
ISFFileType_Source = _vvisf.ISFFileType_Source
ISFFileType_Filter = _vvisf.ISFFileType_Filter
ISFFileType_Transition = _vvisf.ISFFileType_Transition
ISFFileType_All = _vvisf.ISFFileType_All

# Export CreateGLBufferRef
CreateGLBufferRef = _vvisf.CreateGLBufferRef 