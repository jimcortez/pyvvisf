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
    # Utility functions
    'reinitialize_glfw_context',
    'get_gl_info',
    'get_platform_info',
    'is_vvisf_available',
    'initialize_glfw_context',
    # Context management functions
    'cleanup_glfw_context',
    'acquire_context_ref',
    'release_context_ref',
    'validate_gl_context',
    'check_gl_errors',
    'reset_gl_context_state',
    # Context managers
    'GLContextManager',
    'ISFRenderer',
    # Error handling
    'ShaderCompilationError',
    'ShaderRenderingError',
    'ISFParseError',

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
    initialize_glfw_context = _vvisf.initialize_glfw_context
    # Context management functions
    cleanup_glfw_context = _vvisf.cleanup_glfw_context
    acquire_context_ref = _vvisf.acquire_context_ref
    release_context_ref = _vvisf.release_context_ref
    validate_gl_context = _vvisf.validate_gl_context
    check_gl_errors = _vvisf.check_gl_errors
    reset_gl_context_state = _vvisf.reset_gl_context_state

    isf_val_type_to_string = _vvisf.isf_val_type_to_string
    isf_file_type_to_string = _vvisf.isf_file_type_to_string
except AttributeError as e:
    # If some classes are not available, provide a helpful error
    raise ImportError(
        f"Some VVISF classes are not available: {e}\n"
        "This may indicate a version mismatch or incomplete build."
    ) from e

# Version info
from ._version import __version__

# Check if VVISF is available
def check_vvisf_availability():
    """Check if VVISF is properly initialized and available."""
    try:
        return is_vvisf_available()
    except Exception:
        return False

# Initialize GLFW context on import to prevent segmentation faults
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
                print("[pyvvisf] You may need to call initialize_glfw_context() manually before rendering")
    except Exception as e:
        print(f"[pyvvisf] Warning: Could not initialize GLFW context: {e}")
        print("[pyvvisf] You may need to call initialize_glfw_context() manually before rendering")

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

# Export ISFFileType_* at module level
ISFFileType_None = _vvisf.ISFFileType_None
ISFFileType_Source = _vvisf.ISFFileType_Source
ISFFileType_Filter = _vvisf.ISFFileType_Filter
ISFFileType_Transition = _vvisf.ISFFileType_Transition
ISFFileType_All = _vvisf.ISFFileType_All

# Export CreateGLBufferRef
CreateGLBufferRef = _vvisf.CreateGLBufferRef

# Try to initialize on import (after all imports are complete)
_initialize_on_import()

# Expose exception classes from the bindings at the top-level pyvvisf namespace
# Use true aliases so isinstance() checks work for both top-level and binding exceptions
from . import vvisf_bindings

# Create true aliases by assigning the binding exception classes to the top-level namespace
ISFParseError = vvisf_bindings.ISFParseError
ShaderCompilationError = vvisf_bindings.ShaderCompilationError
ShaderRenderingError = vvisf_bindings.ShaderRenderingError
VVISFError = vvisf_bindings.VVISFError

# Context Manager for GLFW/OpenGL lifecycle management
class GLContextManager:
    """
    Context manager for automatic GLFW/OpenGL context lifecycle management.
    
    This class provides a convenient way to manage GLFW and OpenGL contexts
    using Python's context manager protocol. It automatically handles:
    - Context initialization
    - Context validation
    - Error checking
    - Resource cleanup
    - Scene lifecycle management to prevent null context issues
    
    The key improvement is that this manager tracks ISFScene objects and ensures
    they are recreated with valid contexts when context reinitialization occurs,
    preventing the segmentation faults caused by stale context pointers.
    
    Usage:
        with GLContextManager() as ctx:
            # Your rendering code here
            scene = ctx.create_scene()  # Use this instead of CreateISFSceneRef()
            buffer = scene.create_and_render_a_buffer(Size(640, 480))
            # Context is automatically cleaned up when exiting the block
    """
    
    def __init__(self, auto_initialize=True, auto_cleanup=True, validate_on_enter=True):
        """
        Initialize the context manager.
        
        Args:
            auto_initialize (bool): Whether to automatically initialize the GLFW context
            auto_cleanup (bool): Whether to automatically cleanup the context on exit
            validate_on_enter (bool): Whether to validate the context when entering
        """
        self.auto_initialize = auto_initialize
        self.auto_cleanup = auto_cleanup
        self.validate_on_enter = validate_on_enter
        self._context_initialized = False
        self._context_acquired = False
        self._managed_scenes = []  # Track scenes created through this manager
        self._context_generation = 0  # Track context reinitializations
    
    def __enter__(self):
        """Enter the context manager."""
        try:
            # Initialize context if requested
            if self.auto_initialize:
                if not initialize_glfw_context():
                    raise RuntimeError("Failed to initialize GLFW context")
                self._context_initialized = True
            
            # Validate context if requested
            if self.validate_on_enter:
                if not validate_gl_context():
                    raise RuntimeError("GL context validation failed")
            
            # Acquire context reference
            acquire_context_ref()
            self._context_acquired = True
            
            # Reset context state to ensure clean state
            reset_gl_context_state()
            
            return self
            
        except Exception as e:
            # Clean up on error
            self._cleanup()
            raise e
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""
        self._cleanup()
        
        # Re-raise any exceptions that occurred
        return False  # Don't suppress exceptions
    
    def _cleanup(self):
        """Internal cleanup method."""
        try:
            # Clear managed scenes (they will be invalid after context cleanup)
            self._managed_scenes.clear()
            
            # Release context reference if acquired
            if self._context_acquired:
                release_context_ref()
                self._context_acquired = False
            
            # Cleanup context if initialized and cleanup is requested
            if self._context_initialized and self.auto_cleanup:
                cleanup_glfw_context()
                self._context_initialized = False
                
        except Exception as e:
            # Log cleanup errors but don't raise them
            print(f"Warning: Error during context cleanup: {e}")
    
    def create_scene(self, shader_content=None):
        """
        Create an ISFScene that is managed by this context manager.
        
        This method ensures that the scene is created with the current valid context
        and will be properly handled during context reinitialization.
        
        Args:
            shader_content (str, optional): ISF shader content to load into the scene
            
        Returns:
            ISFScene: A managed ISFScene instance
        """
        if not self._context_acquired:
            raise RuntimeError("Context not acquired. Use this method within a GLContextManager context.")
        
        # Create scene with current context
        scene = CreateISFSceneRef()
        
        # Load shader if provided
        if shader_content:
            doc = CreateISFDocRefWith(shader_content)
            scene.use_doc(doc)
        
        # Track the scene for lifecycle management
        self._managed_scenes.append(scene)
        
        return scene
    
    def reinitialize(self):
        """
        Reinitialize the GLFW context and recreate all managed scenes.
        
        This method properly handles context reinitialization by:
        1. Reinitializing the GLFW context
        2. Recreating all managed scenes with the new context
        3. Preserving shader content and state where possible
        
        This prevents the null context segmentation fault issue.
        """
        if not self._context_acquired:
            raise RuntimeError("Context not acquired. Use this method within a GLContextManager context.")
        
        # Store current scene states
        scene_states = []
        for scene in self._managed_scenes:
            state = {
                'doc': scene.doc() if hasattr(scene, 'doc') else None,
                'always_render_to_float': scene.always_render_to_float() if hasattr(scene, 'always_render_to_float') else False,
                'persistent_to_iosurface': scene.persistent_to_iosurface() if hasattr(scene, 'persistent_to_iosurface') else False,
            }
            scene_states.append(state)
        
        # Release current context reference
        if self._context_acquired:
            release_context_ref()
            self._context_acquired = False
        
        # Cleanup current context
        if self._context_initialized:
            cleanup_glfw_context()
            self._context_initialized = False
        
        # Reinitialize context
        if not reinitialize_glfw_context():
            raise RuntimeError("Failed to reinitialize GLFW context")
        
        self._context_initialized = True
        acquire_context_ref()
        self._context_acquired = True
        reset_gl_context_state()
        
        # Increment context generation
        self._context_generation += 1
        
        # Recreate all managed scenes with new context
        new_scenes = []
        for i, state in enumerate(scene_states):
            try:
                # Create new scene
                new_scene = CreateISFSceneRef()
                
                # Restore state
                if state['doc']:
                    new_scene.use_doc(state['doc'])
                if hasattr(new_scene, 'set_always_render_to_float'):
                    new_scene.set_always_render_to_float(state['always_render_to_float'])
                if hasattr(new_scene, 'set_persistent_to_iosurface'):
                    new_scene.set_persistent_to_iosurface(state['persistent_to_iosurface'])
                
                new_scenes.append(new_scene)
                
            except Exception as e:
                print(f"Warning: Failed to recreate scene {i}: {e}")
                # Create a basic scene as fallback
                new_scenes.append(CreateISFSceneRef())
        
        # Replace managed scenes
        self._managed_scenes = new_scenes
        
        return self._managed_scenes
    
    def get_managed_scenes(self):
        """
        Get all scenes managed by this context manager.
        
        Returns:
            list: List of managed ISFScene instances
        """
        return self._managed_scenes.copy()
    
    def check_errors(self, operation_name="operation"):
        """
        Check for OpenGL errors.
        
        Args:
            operation_name (str): Name of the operation for error reporting
        """
        check_gl_errors(operation_name)
    
    def reset_state(self):
        """Reset the OpenGL context state."""
        reset_gl_context_state()
    
    def is_valid(self):
        """Check if the context is valid."""
        return validate_gl_context()
    
    def get_info(self):
        """Get GL context information."""
        return get_gl_info()
    
    def get_context_generation(self):
        """
        Get the current context generation number.
        
        This number increments each time the context is reinitialized,
        which can be useful for detecting when scenes need to be recreated.
        
        Returns:
            int: Current context generation number
        """
        return self._context_generation


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
        if self._context_manager:
            self._context_manager.__exit__(exc_type, exc_val, exc_tb)
            self._context_manager = None
        self._scene = None
        self._shader_content = None
        self._current_inputs = {}
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