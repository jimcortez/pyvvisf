"""Error handling for ISF rendering."""

from typing import Dict, Any, Optional


class ISFError(Exception):
    """Base exception for ISF-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
    
    def __str__(self):
        msg = super().__str__()
        if self.context:
            context_str = "\n".join(f"  {k}: {v}" for k, v in self.context.items())
            msg += f"\nContext:\n{context_str}"
        return msg


class ISFParseError(ISFError):
    """Error parsing ISF shader content."""
    
    def __init__(self, message: str, json_block: str = "", line_info: Optional[Dict[str, Any]] = None):
        context = {}
        if json_block:
            context['json_block'] = json_block
        if line_info:
            context.update(line_info)
        super().__init__(message, context)


class ShaderCompilationError(ISFError):
    """Error compiling or linking shaders."""
    
    def __init__(self, message: str, shader_source: str = "", shader_type: str = ""):
        context = {}
        if shader_source:
            context['shader_source'] = shader_source
        if shader_type:
            context['shader_type'] = shader_type
        super().__init__(message, context)


class RenderingError(ISFError):
    """Error during rendering process."""
    
    def __init__(self, message: str, operation: str = ""):
        context = {}
        if operation:
            context['operation'] = operation
        super().__init__(message, context)


class ContextError(ISFError):
    """Error with OpenGL context management."""
    
    def __init__(self, message: str, platform_info: Optional[Dict[str, Any]] = None):
        context = {}
        if platform_info:
            context.update(platform_info)
        super().__init__(message, context)


class ValidationError(ISFError):
    """Error validating ISF metadata or inputs."""
    
    def __init__(self, message: str, field: str = "", value: Any = None):
        context = {}
        if field:
            context['field'] = field
        if value is not None:
            context['value'] = value
        super().__init__(message, context) 