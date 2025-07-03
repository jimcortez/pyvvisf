"""Python bindings for VVISF (Vidvox Interactive Shader Format)."""

import sys
from pathlib import Path

from . import vvisf_bindings as _vvisf

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
    # Context managers
    'GLContextManager',
    'ISFRenderer',
    # Error handling
    'ShaderCompilationError',
    'ShaderRenderingError',
    'ISFParseError',
    'VVISFError',
    # Constants and types
    'ISFValType_None',
    'ISFValType_Event',
    'ISFValType_Bool',
    'ISFValType_Long',
    'ISFValType_Float',
    'ISFValType_Point2D',
    'ISFValType_Color',
    'ISFValType_Cube',
    'ISFValType_Image',
    'ISFValType_Audio',
    'ISFValType_AudioFFT',
    'ISFFileType_None',
    'ISFFileType_Source',
    'ISFFileType_Filter',
    'ISFFileType_Transition',
    'ISFFileType_All',
    # Utility functions
    'reinitialize_glfw_context',
    'get_gl_info',
    'get_platform_info',
    'is_vvisf_available',
    'initialize_glfw_context',
    'cleanup_glfw_context',
    'acquire_context_ref',
    'release_context_ref',
    'validate_gl_context',
    'check_gl_errors',
    'reset_gl_context_state',
    'CreateGLBufferRef',
    'isf_val_type_to_string',
    'isf_file_type_to_string',
    'check_vvisf_availability',
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
except AttributeError as e:
    # If some classes are not available, provide a helpful error
    raise ImportError(
        f"Some VVISF classes are not available: {e}\n"
        "This may indicate a version mismatch or incomplete build."
    ) from e

# Version info
from ._version import __version__

# Import from our new modules
from .context import GLContextManager
from .renderer import ISFRenderer
from .constants import (
    ISFValType_None, ISFValType_Event, ISFValType_Bool, ISFValType_Long,
    ISFValType_Float, ISFValType_Point2D, ISFValType_Color, ISFValType_Cube,
    ISFValType_Image, ISFValType_Audio, ISFValType_AudioFFT,
    ISFFileType_None, ISFFileType_Source, ISFFileType_Filter,
    ISFFileType_Transition, ISFFileType_All,
    isf_val_type_to_string, isf_file_type_to_string
)
from .utils import (
    reinitialize_glfw_context, get_gl_info, get_platform_info,
    is_vvisf_available, initialize_glfw_context, cleanup_glfw_context,
    acquire_context_ref, release_context_ref, validate_gl_context,
    check_gl_errors, reset_gl_context_state, CreateGLBufferRef,
    check_vvisf_availability, _initialize_on_import
)

# Create true aliases by assigning the binding exception classes to the top-level namespace
ISFParseError = _vvisf.ISFParseError
ShaderCompilationError = _vvisf.ShaderCompilationError
ShaderRenderingError = _vvisf.ShaderRenderingError
VVISFError = _vvisf.VVISFError

# Try to initialize on import (after all imports are complete)
_initialize_on_import() 