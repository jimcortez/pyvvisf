"""High-level ISF shader rendering interface for pyvvisf."""

from . import vvisf_bindings as _vvisf
from .context import GLContextManager

# Import the classes and functions we need
Size = _vvisf.Size
CreateISFDocRefWith = _vvisf.CreateISFDocRefWith

# Import exception classes
ISFParseError = _vvisf.ISFParseError
ShaderCompilationError = _vvisf.ShaderCompilationError
ShaderRenderingError = _vvisf.ShaderRenderingError


class ISFRenderer:
    """
    High-level convenience class for rendering ISF shaders.
    
    This class provides a simplified interface for working with ISF shaders,
    automatically handling OpenGL context management and providing convenient
    methods for setting shader inputs and rendering to images.
    
    Usage:
        with ISFRenderer(shader_content) as renderer:
            renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
            image = renderer.render_to_pil_image(1920, 1080)
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
            raise ShaderCompilationError(f"Shader compilation failed: {str(e)}")
    
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
                f"Rendering failed during {operation_name}: {str(e)}"
            )
    
    def set_input(self, name, value):
        """
        Set a single input value.
        
        Args:
            name (str): Input name
            value: ISF value object (e.g., ISFColorVal, ISFFloatVal, etc.)
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
            self._scene.set_value_for_input_named(value, name)
            self._current_inputs[name] = value
        except Exception as e:
            raise ShaderRenderingError(
                f"Failed to set input '{name}': {str(e)}"
            )
    
    def set_inputs(self, inputs):
        """
        Set multiple input values at once.
        
        Args:
            inputs (dict): Dictionary of input values to set
                          Keys are input names, values are ISF value objects
        """
        if not self._scene:
            raise RuntimeError("No shader loaded. Context not entered?")
        
        for name, value in inputs.items():
            self.set_input(name, value)
    
    def render_to_pil_image(self, width, height):
        """
        Render the shader to a PIL Image.
        
        Args:
            width (int): Output image width
            height (int): Output image height
            
        Returns:
            PIL.Image: Rendered image
            
        Raises:
            ShaderRenderingError: If rendering fails
        """
        if not self._scene:
            raise RuntimeError("No shader loaded. Context not entered?")
        
        try:
            size = Size(width, height)
            buffer = self._scene.create_and_render_a_buffer(size)
            
            # Check for rendering errors
            self._check_rendering_errors("buffer creation")
            
            # Convert to PIL Image
            try:
                return buffer.to_pil_image()
            except Exception:
                return buffer.create_pil_image()
                
        except Exception as e:
            error_details = self._extract_error_details()
            raise ShaderRenderingError(
                f"Failed to render to PIL image: {str(e)}"
            )
    
    def render_to_buffer(self, width, height):
        """
        Render the shader to a GLBuffer.
        
        Args:
            width (int): Output buffer width
            height (int): Output buffer height
            
        Returns:
            GLBuffer: Rendered buffer
            
        Raises:
            ShaderRenderingError: If rendering fails
        """
        if not self._scene:
            raise RuntimeError("No shader loaded. Context not entered?")
        
        try:
            size = Size(width, height)
            buffer = self._scene.create_and_render_a_buffer(size)
            
            # Check for rendering errors
            self._check_rendering_errors("buffer creation")
            
            return buffer
            
        except Exception as e:
            error_details = self._extract_error_details()
            raise ShaderRenderingError(
                f"Failed to render to buffer: {str(e)}"
            )
    
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
        Check if the renderer is in a valid state.
        
        Returns:
            bool: True if the renderer is valid and ready to render
        """
        return (self._context_manager is not None and self._scene is not None) 