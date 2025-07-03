"""High-level ISF shader rendering interface for pyvvisf."""
import pprint

from . import vvisf_bindings as _vvisf
from .context import GLContextManager

# Import the classes and functions we need
Size = _vvisf.Size
CreateISFDocRefWith = _vvisf.CreateISFDocRefWith

# Import exception classes
ISFParseError = _vvisf.ISFParseError
ShaderCompilationError = _vvisf.ShaderCompilationError
ShaderRenderingError = _vvisf.ShaderRenderingError

# Import ISF value creation functions
ISFBoolVal = _vvisf.ISFBoolVal
ISFLongVal = _vvisf.ISFLongVal
ISFFloatVal = _vvisf.ISFFloatVal
ISFPoint2DVal = _vvisf.ISFPoint2DVal
ISFColorVal = _vvisf.ISFColorVal


def _coerce_to_isf_value(value, expected_type):
    """
    Coerce a Python primitive to an ISF value based on the expected type.
    
    Args:
        value: Python primitive (number, tuple, list, string, bool)
        expected_type: ISFValType enum value
        
    Returns:
        ISF value object of the appropriate type
        
    Raises:
        ValueError: If the value cannot be coerced to the expected type
    """
    # If it's already an ISF value, return it
    if hasattr(value, 'type') and callable(value.type):
        return value
    
    # Handle different expected types
    if expected_type == _vvisf.ISFValType_Bool:
        if isinstance(value, bool):
            return ISFBoolVal(value)
        elif isinstance(value, (int, float)):
            return ISFBoolVal(bool(value))
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to boolean")
    
    elif expected_type == _vvisf.ISFValType_Long:
        if isinstance(value, int):
            return ISFLongVal(value)
        elif isinstance(value, float):
            return ISFLongVal(int(value))
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to long")
    
    elif expected_type == _vvisf.ISFValType_Float:
        if isinstance(value, (int, float)):
            return ISFFloatVal(float(value))
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to float")
    
    elif expected_type == _vvisf.ISFValType_Point2D:
        if isinstance(value, (tuple, list)) and len(value) == 2:
            try:
                x, y = float(value[0]), float(value[1])
                return ISFPoint2DVal(x, y)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert {value} to Point2D - values must be numbers")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to Point2D - expected tuple/list with 2 numbers")
    
    elif expected_type == _vvisf.ISFValType_Color:
        if isinstance(value, (tuple, list)):
            if len(value) == 3:
                # RGB - add alpha = 1.0
                try:
                    r, g, b = float(value[0]), float(value[1]), float(value[2])
                    return ISFColorVal(r, g, b, 1.0)
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot convert {value} to Color - values must be numbers")
            elif len(value) == 4:
                # RGBA
                try:
                    r, g, b, a = float(value[0]), float(value[1]), float(value[2]), float(value[3])
                    return ISFColorVal(r, g, b, a)
                except (ValueError, TypeError):
                    raise ValueError(f"Cannot convert {value} to Color - values must be numbers")
            else:
                raise ValueError(f"Cannot convert {value} to Color - expected 3 or 4 numbers")
        else:
            raise ValueError(f"Cannot convert {type(value).__name__} to Color - expected tuple/list with 3 or 4 numbers")
    
    else:
        # For other types (Image, Audio, etc.), we can't auto-coerce
        raise ValueError(f"Auto-coercion not supported for type {expected_type}")


class ISFRenderer:
    """
    High-level convenience class for rendering ISF shaders.
    
    This class provides a simplified interface for working with ISF shaders,
    automatically handling OpenGL context management and providing convenient
    methods for setting shader inputs and rendering to buffers.
    
    Usage:
        with ISFRenderer(shader_content) as renderer:
            renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
            buffer = renderer.render(1920, 1080)
            image = buffer.to_pil_image()
            image.save("output.png")
    """
    
    def __init__(self, shader_content, auto_initialize=True, auto_cleanup=True, initial_inputs=None):
        """
        Initialize the ISF renderer.
        
        Args:
            shader_content (str): ISF shader source code (required)
            auto_initialize (bool): Whether to automatically initialize the GLFW context
            auto_cleanup (bool): Whether to automatically cleanup the context on exit
            initial_inputs (dict, optional): Dictionary of input values to set at creation
        """
        self.auto_initialize = auto_initialize
        self.auto_cleanup = auto_cleanup
        self._context_manager = None
        self._scene = None
        self._shader_content = shader_content
        self._current_inputs = {}
        self._initial_inputs = initial_inputs
    
    def __enter__(self):
        """Enter the context manager."""
        self._context_manager = GLContextManager(
            auto_initialize=self.auto_initialize,
            auto_cleanup=self.auto_cleanup
        )
        self._context_manager.__enter__()
        
        # Create scene with shader and handle compilation errors
        try:
            self._scene = self._context_manager.create_scene(self._shader_content)
            self._validate_shader_compilation()
        except Exception as e:
            # Clean up context manager on error
            self._context_manager.__exit__(type(e), e, e.__traceback__)
            raise
        
        # Set initial inputs if provided
        if self._initial_inputs:
            self.set_inputs(self._initial_inputs)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        try:
            if self._context_manager:
                self._context_manager.__exit__(exc_type, exc_val, exc_tb)
                self._context_manager = None
            self._scene = None
            self._shader_content = None
            self._current_inputs = {}
            
            # The underlying context manager handles cleanup automatically
            # No need for additional cleanup here as it can cause issues
                
        except Exception as e:
            # Re-raise the exception without additional cleanup
            raise e
            
        return False  # Don't suppress exceptions
    
    def _validate_shader_compilation(self):
        """Validate that the shader compiled successfully and extract any errors."""
        if not self._scene:
            raise RuntimeError("No scene available for validation")
        
        # Check if the scene has a valid document
        doc = self._scene.doc()
        if not doc:
            raise ISFParseError("Failed to parse ISF shader content")
        
        # Try to render a small test frame to trigger compilation and catch errors
        try:
            size = Size(1, 1)  # Minimal size for testing
            self._scene.create_and_render_a_buffer(size)
        except Exception as e:
            # Extract detailed error information
            error_details = self._extract_error_details()
            details_str = '\n' + pprint.pformat(error_details) if error_details else ''
            raise ShaderCompilationError(f"Shader compilation failed: {str(e)}{details_str}")
    
    def _extract_error_details(self):
        """Extract detailed error information from the scene."""
        error_details = {}
        
        try:
            # Get shader source for context
            if self._scene and self._scene.doc():
                doc = self._scene.doc()
                if hasattr(doc, 'frag_shader_source'):
                    error_details['fragment_shader_source'] = doc.frag_shader_source()
                if hasattr(doc, 'vert_shader_source'):
                    error_details['vertex_shader_source'] = doc.vert_shader_source()
                if hasattr(doc, 'json_source_string'):
                    error_details['json_source'] = doc.json_source_string()
        except Exception:
            pass
        
        # Try to get OpenGL error information
        try:
            if self._context_manager:
                self._context_manager.check_errors("shader compilation")
        except Exception as e:
            error_details['opengl_errors'] = str(e)
        
        return error_details
    
    def _check_rendering_errors(self, operation_name="rendering"):
        """Check for rendering errors and raise appropriate exceptions."""
        try:
            if self._context_manager:
                self._context_manager.check_errors(operation_name)
        except Exception as e:
            error_details = self._extract_error_details()
            raise ShaderRenderingError(
                f"Rendering failed during {operation_name}: {str(e)} | {error_details}"
            )
    
    def set_input(self, name, value):
        """
        Set a single input value.
        
        Args:
            name (str): Input name
            value: ISF value object (e.g., ISFColorVal, ISFFloatVal, etc.) or Python primitive
                  Python primitives will be automatically coerced to the appropriate ISF type:
                  - bool, int, float -> ISFBoolVal, ISFLongVal, ISFFloatVal
                  - tuple/list with 2 numbers -> ISFPoint2DVal
                  - tuple/list with 3-4 numbers -> ISFColorVal (3 = RGB+alpha=1.0, 4 = RGBA)
        """
        if not self._scene:
            raise RuntimeError("No shader loaded. Context not entered?")
        
        # Check if the input exists before trying to set it
        input_attr = self._scene.input_named(name)
        if input_attr is None:
            raise ShaderRenderingError(
                f"Failed to set input '{name}': Input does not exist in shader"
            )
        
        try:
            # Auto-coerce Python primitives to ISF values
            expected_type = input_attr.type()
            isf_value = _coerce_to_isf_value(value, expected_type)
            
            self._scene.set_value_for_input_named(isf_value, name)
            self._current_inputs[name] = isf_value
        except ValueError as e:
            raise ShaderRenderingError(
                f"Failed to set input '{name}': {str(e)}"
            )
        except Exception as e:
            raise ShaderRenderingError(
                f"Failed to set input '{name}': {str(e)}"
            )
    
    def set_inputs(self, inputs):
        """
        Set multiple input values at once.
        
        Args:
            inputs (dict): Dictionary of input values to set
                          Keys are input names, values are ISF value objects or Python primitives
                          Python primitives will be automatically coerced to appropriate ISF types
        """
        if not self._scene:
            raise RuntimeError("No shader loaded. Context not entered?")
        
        for name, value in inputs.items():
            self.set_input(name, value)
    
    def render(self, width, height, time_offset=0.0):
        """
        Render the shader to a GLBuffer.
        
        Args:
            width (int): Output buffer width
            height (int): Output buffer height
            time_offset (float, optional): Time offset in seconds to render the shader at.
                                         Defaults to 0.0 (current time).
            
        Returns:
            GLBuffer: Rendered buffer that can be converted to PIL Image or numpy array
            
        Raises:
            ShaderRenderingError: If rendering fails
        """
        if not self._scene:
            raise RuntimeError("No shader loaded. Context not entered?")
        
        try:
            size = Size(width, height)
            buffer = self._scene.create_and_render_a_buffer(size, time_offset)
            
            # Check for rendering errors
            self._check_rendering_errors("buffer creation")
            
            return buffer
            
        except Exception as e:
            error_details = self._extract_error_details()
            details_str = '\n' + pprint.pformat(error_details) if error_details else ''
            raise ShaderRenderingError(f"Failed to render to buffer: {str(e)}{details_str}")
    
    def get_shader_info(self):
        """
        Get information about the loaded shader.
        
        Returns:
            dict: Shader information including name, description, inputs, etc.
        """
        if not self._scene or not self._scene.doc():
            return None
        
        doc = self._scene.doc()
        return {
            'name': doc.name(),
            'description': doc.description(),
            'credit': doc.credit(),
            'version': doc.vsn(),
            'categories': doc.categories(),
            'inputs': [attr.name() for attr in doc.inputs()]
        }
    
    def get_current_inputs(self):
        """
        Get the currently set input values.
        
        Returns:
            dict: Dictionary of current input values
        """
        return self._current_inputs.copy()
    
    def check_errors(self, operation_name="operation"):
        """
        Check for OpenGL errors.
        
        Args:
            operation_name (str): Name of the operation for error reporting
        """
        if self._context_manager:
            self._context_manager.check_errors(operation_name)
    
    def is_valid(self):
        """
        Check if the renderer is in a valid state and the shader can be rendered.
        
        This method performs actual validation by attempting a test render to ensure
        the shader compiles and can be executed successfully. This catches issues
        like non-constant loop conditions that should fail according to the ISF specification.
        
        Returns:
            bool: True if the renderer is valid and the shader can be rendered
        """
        # Basic state checks
        if self._context_manager is None or self._scene is None:
            return False
        
        # Check if the scene has a valid document
        doc = self._scene.doc()
        if not doc:
            return False
        
        # Perform actual validation by attempting a test render
        try:
            # Try to render a minimal test frame to trigger compilation and catch errors
            size = Size(1, 1)  # Minimal size for testing
            self._scene.create_and_render_a_buffer(size)
            
            # Check for any OpenGL errors that might have occurred
            self._check_rendering_errors("validation test render")
            
            return True
            
        except Exception as e:
            # If any exception occurs during test rendering, the shader is not valid
            # This includes ShaderCompilationError, ShaderRenderingError, etc.
            return False 
    
    def get_error_log(self):
        """
        Get the shader compilation and linking error log (if any) from the underlying scene.
        Returns:
            dict: Error log dictionary from the OpenGL driver and VVISF library, or an empty dict if none.
        """
        if not self._scene:
            return {}
        try:
            return _vvisf.get_error_dict(self._scene)
        except Exception:
            return {} 