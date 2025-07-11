"""Refactored ISF shader renderer with separated concerns."""

import ctypes
import logging
import numpy as np
from typing import Dict, Any, Optional
import time as _time

import glfw

from .parser import ISFParser, ISFMetadata
from .types import ISFValue
from .errors import ISFError, ISFParseError, ShaderCompilationError, RenderingError, ContextError
from .shader_compiler import ShaderCompiler, ShaderSourceProcessor, ISFShaderProcessor
from .framebuffer_manager import FramebufferManager, MultiPassFramebufferManager, Framebuffer
from .input_manager import InputManager
from OpenGL.GL import glClearColor, glEnable, glGenVertexArrays, glBindVertexArray, glGenBuffers, glBindBuffer, glBufferData, glEnableVertexAttribArray, glVertexAttribPointer, glDeleteVertexArrays, glDeleteBuffers, glDrawArrays, GL_DEPTH_TEST, GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_FLOAT, GL_FALSE, GL_TRIANGLE_STRIP

logger = logging.getLogger(__name__)


class ShaderValidationError(ShaderCompilationError):
    """Raised when shader validation fails due to empty or invalid content."""
    pass


class GLContextManager:
    """Manages the creation and lifetime of a GLFW OpenGL context."""
    
    def __init__(self):
        self.window = None
        self.initialized = False
    
    def initialize(self, width: int = 1, height: int = 1):
        """Initialize GLFW and create an OpenGL context."""
        if self.initialized:
            return
            
        try:
            if not glfw.init():
                raise ContextError("Failed to initialize GLFW")
            
            # Configure GLFW
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.VISIBLE, glfw.TRUE)
            
            # Create window
            self.window = glfw.create_window(width, height, "ISF Renderer", None, None)
            if not self.window:
                glfw.terminate()
                raise ContextError("Failed to create GLFW window")
            
            glfw.make_context_current(self.window)
            
            # Initialize OpenGL
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glEnable(GL_DEPTH_TEST)
            
            self.initialized = True
            logger.info("GLFW context initialized successfully")
            
        except NameError:
            # GLFW not available - for testing purposes
            raise ContextError("Failed to create GLFW window")
    
    def make_current(self):
        """Make this OpenGL context current."""
        if self.window:
            try:
                glfw.make_context_current(self.window)
            except NameError:
                pass
    
    def cleanup(self):
        """Destroy the OpenGL context and release GLFW resources."""
        try:
            if self.window:
                glfw.destroy_window(self.window)
                self.window = None
            
            if self.initialized:
                glfw.terminate()
                self.initialized = False
        except NameError:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class RenderResult:
    """Wrapper for a rendered image result."""
    
    def __init__(self, array):
        self.array = array
    
    def to_pil_image(self):
        """Convert the result to a PIL Image."""
        from PIL import Image
        return Image.fromarray(self.array).convert('RGBA')
    
    def __array__(self):
        return self.array


class QuadRenderer:
    """Handles rendering a full-screen quad."""
    
    def __init__(self):
        self.vao = None
        self.vbo = None
        self.initialized = False
    
    def initialize(self):
        """Setup the quad geometry."""
        if self.initialized:
            return
            
        try:
            # Quad vertices (position, texcoord)
            vertices = np.array([
                # position    # texcoord
                -1.0, -1.0,   0.0, 0.0,  # bottom-left
                 1.0, -1.0,   1.0, 0.0,  # bottom-right
                -1.0,  1.0,   0.0, 1.0,  # top-left
                 1.0,  1.0,   1.0, 1.0,  # top-right
            ], dtype=np.float32)
            
            # Create VAO
            self.vao = glGenVertexArrays(1)
            glBindVertexArray(self.vao)
            
            # Create VBO
            self.vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            
            stride = 4 * vertices.itemsize  # 4 floats per vertex
            
            # Position attribute (location = 0)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            
            # TexCoord attribute (location = 1)
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * vertices.itemsize))
            
            glBindVertexArray(0)
            self.initialized = True
            
        except NameError:
            # OpenGL not available - for testing purposes
            self.vao = 1
            self.vbo = 1
            self.initialized = True
    
    def draw(self):
        """Draw the quad."""
        if not self.initialized:
            self.initialize()
            
        try:
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            glBindVertexArray(0)
        except NameError:
            pass
    
    def cleanup(self):
        """Clean up OpenGL resources."""
        try:
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
        except NameError:
            pass
        self.initialized = False


class ISFRenderer:
    """Main ISF shader renderer for Python (refactored)."""
    
    def __init__(self, shader_content: str = '', vertex_shader_content: str = '', glsl_version: str = '330'):
        """Initialize the ISFRenderer with shader content."""
        self.context = GLContextManager()
        self.parser = ISFParser()
        self.input_manager = InputManager(self.parser)
        self.shader_compiler = ShaderCompiler()
        self.isf_processor = ISFShaderProcessor()
        self.quad_renderer = QuadRenderer()
        self.framebuffer_manager = FramebufferManager()
        
        self.metadata: Optional[ISFMetadata] = None
        self._shader_content = shader_content or ''
        self._vertex_shader_content = vertex_shader_content or ''
        self._glsl_version = glsl_version
        
        # Validate and load shader
        if not self._shader_content.strip():
            raise ShaderValidationError(
                "Shader content is empty or only whitespace. Please provide valid ISF shader code.",
                shader_source=self._shader_content,
                shader_type="fragment"
            )
        
        try:
            self.metadata = self.load_shader_content(self._shader_content, self._vertex_shader_content)
        except (ISFParseError, ShaderCompilationError):
            raise
        except Exception as e:
            raise ShaderValidationError(
                f"Shader validation failed: {e}",
                shader_source=self._shader_content,
                shader_type="fragment"
            ) from e
    
    def set_input(self, name: str, value: Any):
        """Set the value of a shader input."""
        self.context.make_current()
        if self.metadata is None:
            raise ShaderValidationError("No shader metadata loaded.")
        self.input_manager.set_input(name, value, self.metadata)
    
    def set_inputs(self, inputs: dict):
        """Set multiple shader inputs at once."""
        self.context.make_current()
        if self.metadata is None:
            raise ShaderValidationError("No shader metadata loaded.")
        self.input_manager.set_inputs(inputs, self.metadata)
    
    def load_shader_content(self, content: str, vertex_shader_content: str = '') -> ISFMetadata:
        """Parse and compile ISF shader content."""
        if not content.strip():
            raise ShaderValidationError(
                "Shader content is empty or only whitespace.",
                shader_source=content,
                shader_type="fragment"
            )
        
        try:
            glsl_code, metadata = self.parser.parse_content(content)
        except ISFParseError:
            raise
        except Exception as e:
            raise ShaderValidationError(f"Shader parsing failed: {e}") from e
        
        if not self.context.initialized:
            self.context.initialize()
        
        # Process shaders
        vertex_source = vertex_shader_content or metadata.vertex_shader or self._default_vertex_shader()
        vertex_source = self._process_vertex_shader(vertex_source, metadata)
        fragment_source = self._process_fragment_shader(glsl_code, metadata)
        
        # Compile shaders
        expected_uniforms = [inp.name for inp in metadata.inputs] if metadata.inputs else []
        try:
            self.shader_compiler.create_program(vertex_source, fragment_source, expected_uniforms)
        except ShaderCompilationError as e:
            raise ShaderValidationError(f"Shader compilation failed: {e}") from e
        
        # Initialize quad renderer
        self.quad_renderer.initialize()
        
        return metadata
    
    def _process_vertex_shader(self, source: str, metadata: ISFMetadata) -> str:
        """Process vertex shader source using ISF processor."""
        # Use the new ISF processor for proper ISF shader handling
        processed_source = self.isf_processor.process_vertex_shader(source, metadata)
        
        # Add version directive if needed
        if "#version" not in processed_source:
            processed_source = f"#version {self._glsl_version}\n{processed_source}"
        
        return processed_source
    
    def _process_fragment_shader(self, source: str, metadata: ISFMetadata) -> str:
        """Process fragment shader source using ISF processor."""
        # Use the new ISF processor for proper ISF shader handling
        processed_source = self.isf_processor.process_fragment_shader(source, metadata)
        
        # Add version directive if needed
        if "#version" not in processed_source:
            processed_source = f"#version {self._glsl_version}\n{processed_source}"
        
        return processed_source
    
    def _extract_pass_targets(self, passes) -> list[str]:
        """Extract target names from passes."""
        targets = []
        for p in passes:
            target = None
            if hasattr(p, 'target'):
                target = getattr(p, 'target', None)
            elif isinstance(p, dict):
                target = p.get('target')
            
            if target and target not in targets and target != 'default':
                targets.append(target)
        
        return targets
    
    def _default_vertex_shader(self) -> str:
        """Get the default ISF vertex shader."""
        return "void main() {\n  isf_vertShaderInit();\n}\n"
    
    def render(self, width: int, height: int, inputs: Optional[Dict[str, Any]] = None, 
               metadata: Optional[ISFMetadata] = None, time_offset: float = 0.0) -> RenderResult:
        """Render the ISF shader to an offscreen buffer."""
        self.context.make_current()
        
        if not self.context.initialized:
            self.context.initialize(width, height)
        
        meta = metadata or self.metadata
        if meta is None:
            raise ShaderValidationError("No shader metadata loaded.")
        validated_inputs = self.input_manager.get_merged_inputs(inputs, meta)
        
        # Check for multi-pass rendering
        passes = getattr(meta, 'passes', None) if meta else None
        if passes and len(passes) > 1:
            return self._render_multipass(width, height, validated_inputs, meta, time_offset)
        else:
            return self._render_singlepass(width, height, validated_inputs, meta, time_offset)
    
    def _render_singlepass(self, width: int, height: int, validated_inputs: Dict[str, ISFValue],
                          metadata: ISFMetadata, time_offset: float) -> RenderResult:
        """Render single-pass shader."""
        framebuffer = self.framebuffer_manager.create_framebuffer(width, height)
        
        try:
            framebuffer.bind()
            self.framebuffer_manager.setup_viewport_and_clear(width, height)
            
            self.shader_compiler.use()
            self._set_standard_uniforms(width, height, time_offset)
            self._set_input_uniforms(validated_inputs)
            
            self.quad_renderer.draw()
            
            data = self.framebuffer_manager.read_pixels(width, height)
            arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4))
            arr = np.flipud(arr)  # OpenGL's origin is bottom-left
            
            return RenderResult(arr)
            
        finally:
            self.framebuffer_manager.cleanup_framebuffer(framebuffer)
    
    def _render_multipass(self, width: int, height: int, validated_inputs: Dict[str, ISFValue],
                         metadata: ISFMetadata, time_offset: float) -> RenderResult:
        """Render multi-pass shader."""
        mp_manager = MultiPassFramebufferManager()
        
        try:
            passes = metadata.passes
            pass_framebuffers = mp_manager.create_pass_framebuffers(passes, width, height)
            
            # Render each pass
            for pass_idx, pass_def in enumerate(passes):
                framebuffer = pass_framebuffers[pass_idx]
                
                # Create final framebuffer for last pass if needed
                if framebuffer is None:
                    framebuffer = mp_manager.create_framebuffer(width, height)
                    pass_framebuffers[pass_idx] = framebuffer
                
                framebuffer.bind()
                mp_manager.setup_viewport_and_clear(width, height)
                
                self.shader_compiler.use()
                self._set_standard_uniforms(width, height, time_offset, pass_idx)
                self._set_input_uniforms(validated_inputs)
                
                # Bind previous pass targets
                targets = self._extract_pass_targets(passes[:pass_idx])
                mp_manager.bind_target_textures(targets)
                self._set_target_uniforms(targets, mp_manager)
                
                self.quad_renderer.draw()
            
            # Read pixels from final pass
            final_framebuffer = pass_framebuffers[-1]
            if final_framebuffer is None:
                raise RenderingError("Final framebuffer is None in multipass rendering.")
            final_framebuffer.bind()
            data = mp_manager.read_pixels(width, height)
            arr = np.frombuffer(data, dtype=np.uint8).reshape((height, width, 4))
            arr = np.flipud(arr)
            
            return RenderResult(arr)
            
        finally:
            mp_manager.cleanup_all()
    
    def _set_standard_uniforms(self, width: int, height: int, time_offset: float, pass_index: int = 0):
        """Set standard ISF uniforms."""
        self.shader_compiler.set_uniform("PASSINDEX", pass_index)
        self.shader_compiler.set_uniform("RENDERSIZE", [width, height])
        self.shader_compiler.set_uniform("TIME", time_offset)
        self.shader_compiler.set_uniform("TIMEDELTA", 0.0)
        self.shader_compiler.set_uniform("DATE", [1970.0, 1.0, 1.0, 0.0])
        self.shader_compiler.set_uniform("FRAMEINDEX", 0)
    
    def _set_input_uniforms(self, inputs: Dict[str, ISFValue]):
        """Set input uniform values."""
        for name, value in inputs.items():
            self.shader_compiler.set_uniform(name, value)
    
    def _set_target_uniforms(self, targets: list[str], mp_manager: MultiPassFramebufferManager):
        """Set target uniform texture units."""
        tex_unit = 1
        for target_name in targets:
            self.shader_compiler.set_uniform(target_name, tex_unit)
            tex_unit += 1
    
    def render_to_window(self, width: int = 800, height: int = 600, inputs: Optional[Dict[str, Any]] = None,
                        metadata: Optional[ISFMetadata] = None, time_offset: float = 0.0, 
                        title: str = "ISF Shader Preview"):
        """Render the shader in a persistent window."""
        try:
            if not self.context.initialized:
                self.context.initialize(width, height)
            else:
                if self.context.window:
                    glfw.set_window_size(self.context.window, width, height)
            
            glfw.set_window_title(self.context.window, title)
            
            meta = metadata or self.metadata
            if meta is None:
                raise ShaderValidationError("No shader metadata loaded.")
            validated_inputs = self.input_manager.get_merged_inputs(inputs, meta)
            start_time = _time.time() - time_offset
            frame_index = 0
            
            while not glfw.window_should_close(self.context.window):
                glfw.poll_events()
                
                if glfw.get_key(self.context.window, glfw.KEY_ESCAPE) == glfw.PRESS:
                    glfw.set_window_should_close(self.context.window, True)
                    break
                
                fb_width, fb_height = glfw.get_framebuffer_size(self.context.window)
                self.framebuffer_manager.setup_viewport_and_clear(fb_width, fb_height)
                
                self.shader_compiler.use()
                elapsed = _time.time() - start_time
                self._set_standard_uniforms(width, height, elapsed)
                self.shader_compiler.set_uniform("FRAMEINDEX", frame_index)
                self._set_input_uniforms(validated_inputs)
                
                self.quad_renderer.draw()
                glfw.swap_buffers(self.context.window)
                frame_index += 1
                
        except NameError:
            raise RenderingError("GLFW not available for window rendering")
        finally:
            self.cleanup()
    
    def save_render(self, output_path: str, width: int = 1920, height: int = 1080,
                   inputs: Optional[Dict[str, Any]] = None, metadata: Optional[ISFMetadata] = None):
        """Render the shader and save to a file."""
        render_result = self.render(width, height, inputs, metadata)
        image = render_result.to_pil_image()
        image.save(output_path)
    
    def cleanup(self):
        """Clean up all resources."""
        self.shader_compiler.cleanup()
        self.quad_renderer.cleanup()
        self.framebuffer_manager.cleanup_all()
        self.context.cleanup()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()