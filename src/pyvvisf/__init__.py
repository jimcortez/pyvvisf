"""Pure Python ISF shader renderer with PyOpenGL and json5."""

from .renderer import ISFRenderer
from .parser import ISFParser, ISFMetadata
from .types import ISFColor, ISFPoint2D, ISFValue
from .errors import ISFError, ISFParseError, ShaderCompilationError, RenderingError
from .shader_compiler import get_supported_glsl_versions

# Version info
from ._version import __version__

__all__ = [
    # Main renderer
    'ISFRenderer',
    
    # Core components
    'ISFParser',
    'ISFMetadata',
    
    # Value types
    'ISFColor',
    'ISFPoint2D',
    'ISFValue',
    
    # Error types
    'ISFError',
    'ISFParseError',
    'ShaderCompilationError',
    'RenderingError',
    
    # Utility functions
    'get_supported_glsl_versions',
    
    # Version
    '__version__',
]
