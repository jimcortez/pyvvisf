"""ISF shader renderer using PyOpenGL and pyglfw."""

import glfw
import numpy as np
import ctypes
from OpenGL.GL import *
from typing import Dict, Any, Optional
import logging

from .parser import ISFParser, ISFMetadata
from .types import ISFValue, ISFColor, ISFPoint2D
from .errors import (
    ISFError, ISFParseError, ShaderCompilationError, 
    RenderingError, ContextError
)

class ShaderValidationError(ShaderCompilationError):
    """Raised when shader validation fails due to empty or invalid content."""
    pass

from PIL import Image

logger = logging.getLogger(__name__)


class ShaderManager:
    """Manages OpenGL shader compilation and linking."""
    
    expected_input_uniforms: list[str] = []
    def __init__(self):
        self.program = None
        self.vertex_shader = None
        self.fragment_shader = None
        self.uniform_locations = {}
    
    def compile_shader(self, source: str, shader_type: int) -> int:
        """Compile GLSL shader with detailed error reporting."""
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        
        # Check compilation status
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            error_log = glGetShaderInfoLog(shader).decode('utf-8')
            glDeleteShader(shader)
            raise ShaderCompilationError(
                f"Shader compilation failed:\n{error_log}",
                shader_source=source,
                shader_type=self._shader_type_name(shader_type)
            )
        
        return shader
    
    def create_program(self, vertex_source: str, fragment_source: str) -> int:
        """Create and link shader program."""
        try:
            # Compile shaders
            self.vertex_shader = self.compile_shader(vertex_source, GL_VERTEX_SHADER)
            self.fragment_shader = self.compile_shader(fragment_source, GL_FRAGMENT_SHADER)
            
            # Create and link program
            self.program = glCreateProgram()
            glAttachShader(self.program, self.vertex_shader)
            glAttachShader(self.program, self.fragment_shader)
            glLinkProgram(self.program)
            
            # Check linking status
            if not glGetProgramiv(self.program, GL_LINK_STATUS):
                error_log = glGetProgramInfoLog(self.program).decode('utf-8')
                raise ShaderCompilationError(
                    f"Shader program linking failed:\n{error_log}",
                    shader_source=f"Vertex:\n{vertex_source}\n\nFragment:\n{fragment_source}"
                )
            
            # Bind the program before caching uniform locations
            glUseProgram(self.program)
            # Cache uniform locations
            self._cache_uniform_locations()
            
            return self.program
            
        except Exception as e:
            self.cleanup()
            raise e
    
    def _cache_uniform_locations(self):
        """Cache uniform locations for performance. Also include expected uniforms from fragment shader metadata."""
        self.uniform_locations = {}
        num_uniforms = glGetProgramiv(self.program, GL_ACTIVE_UNIFORMS)
        # Cache all active uniforms
        for i in range(num_uniforms):
            name, size, uniform_type = glGetActiveUniform(self.program, i)
            if hasattr(name, 'decode'):
                name = name.decode('utf-8')
            elif hasattr(name, 'tobytes'):
                name = name.tobytes().decode('utf-8').rstrip('\x00')
            else:
                name = str(name)
            location = glGetUniformLocation(self.program, name)
            self.uniform_locations[name] = location
        # Also try to cache any expected uniforms from ISF inputs and standard uniforms
        # (in case they are optimized out of the active list)
        expected_uniforms = [
            'PASSINDEX', 'RENDERSIZE', 'TIME', 'TIMEDELTA', 'DATE', 'FRAMEINDEX'
        ]
        # Add ISF input uniforms if available from metadata
        if hasattr(self, 'expected_input_uniforms'):
            expected_uniforms += self.expected_input_uniforms
        for name in expected_uniforms:
            if name not in self.uniform_locations:
                location = glGetUniformLocation(self.program, name)
                self.uniform_locations[name] = location
    
    def set_uniform(self, name: str, value: Any):
        """Set uniform value by name."""
        location = self.uniform_locations.get(name, -1)
        if location == -1:
            return
        self._set_uniform_value(location, value)
    
    def _set_uniform_value(self, location: int, value: Any):
        """Set uniform value based on type."""
        import OpenGL.GL as GL
        if isinstance(value, bool):
            glUniform1i(location, 1 if value else 0)
        elif isinstance(value, int):
            glUniform1i(location, value)
        elif isinstance(value, float):
            glUniform1f(location, value)
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                glUniform2f(location, value[0], value[1])
            elif len(value) == 3:
                glUniform3f(location, value[0], value[1], value[2])
            elif len(value) == 4:
                glUniform4f(location, value[0], value[1], value[2], value[3])
        elif isinstance(value, ISFColor):
            glUniform4f(location, value.r, value.g, value.b, value.a)
        elif isinstance(value, ISFPoint2D):
            glUniform2f(location, value.x, value.y)
        else:
            logger.warning(f"Unknown uniform type: {type(value)}")
    
    def use(self):
        """Use this shader program."""
        if self.program:
            glUseProgram(self.program)
    
    def cleanup(self):
        """Clean up shader resources."""
        if self.program:
            glDeleteProgram(self.program)
            self.program = None
        if self.vertex_shader:
            glDeleteShader(self.vertex_shader)
            self.vertex_shader = None
        if self.fragment_shader:
            glDeleteShader(self.fragment_shader)
            self.fragment_shader = None
        self.uniform_locations.clear()
    
    def _shader_type_name(self, shader_type: int) -> str:
        """Get shader type name for error messages."""
        return {
            GL_VERTEX_SHADER: "vertex",
            GL_FRAGMENT_SHADER: "fragment",
            GL_GEOMETRY_SHADER: "geometry",
            GL_TESS_CONTROL_SHADER: "tessellation control",
            GL_TESS_EVALUATION_SHADER: "tessellation evaluation",
        }.get(shader_type, f"unknown ({shader_type})")


class GLContextManager:
    """Manages GLFW OpenGL context."""
    
    def __init__(self):
        self.window = None
        self.initialized = False
    
    def initialize(self, width: int = 1, height: int = 1):
        """Initialize GLFW and create OpenGL context."""
        if self.initialized:
            return
        
        if not glfw.init():
            raise ContextError("Failed to initialize GLFW")
        
        # Configure GLFW
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.VISIBLE, glfw.TRUE)  # Make window visible for debugging
        
        # Create window (required for OpenGL context)
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
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status is not None and status != GL_FRAMEBUFFER_COMPLETE:
            logger.error("Framebuffer is not complete!")
    
    def cleanup(self):
        """Clean up GLFW resources."""
        if self.window:
            glfw.destroy_window(self.window)
            self.window = None
        
        if self.initialized:
            glfw.terminate()
            self.initialized = False
    
    def make_current(self):
        """Make this context current."""
        if self.window:
            glfw.make_context_current(self.window)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class RenderResult:
    def __init__(self, array):
        self.array = array
    def to_pil_image(self):
        return Image.fromarray(self.array).convert('RGBA')
    def __array__(self):
        return self.array

class ISFRenderer:
    """Main ISF shader renderer.
    
    Args:
        shader_content (str): The ISF fragment shader content (required).
        vertex_shader_content (str, optional): Optional GLSL vertex shader source. If not provided, uses the ISF default vertex shader.
    """
    
    def __init__(self, shader_content: str = '', vertex_shader_content: str = ''):
        self.context = GLContextManager()
        self.parser = ISFParser()
        self.shader_manager = None
        self.quad_vbo = None
        self.quad_vao = None
        self.metadata = None
        self._shader_content = shader_content or ''  # Store original shader content
        self._vertex_shader_content = vertex_shader_content or ''  # Store optional vertex shader content
        self._input_values = {}  # Store current input values
        
        # Early validation for empty shader content
        if not self._shader_content or not self._shader_content.strip():
            raise ShaderValidationError(
                "Shader content is empty or only whitespace. Please provide valid ISF shader code.",
                shader_source=self._shader_content,
                shader_type="fragment"
            )
        
        try:
            if self._vertex_shader_content:
                self.metadata = self.load_shader_content(self._shader_content, self._vertex_shader_content)
            else:
                self.metadata = self.load_shader_content(self._shader_content)
        except ISFParseError:
            # Let ISFParseError propagate directly
            raise
        except ShaderCompilationError as e:
            # Reraise with a clear message
            raise ShaderValidationError(
                f"Shader validation failed: {e}",
                shader_source=self._shader_content,
                shader_type="fragment"
            ) from e
        except Exception as e:
            # Catch-all for other unexpected errors
            raise ShaderValidationError(
                f"Shader validation failed: {e}",
                shader_source=self._shader_content,
                shader_type="fragment"
            ) from e

    def set_input(self, name: str, value: Any):
        """Set the value of an input. Reloads shader if input value changes."""
        if not self.metadata or not self.metadata.inputs:
            raise RenderingError("No shader loaded or shader has no inputs.")
        # Find input definition
        input_def = next((inp for inp in self.metadata.inputs if inp.name == name), None)
        if input_def is None:
            raise RenderingError(f"Input '{name}' not found in shader inputs.")
        try:
            # Validate and coerce value
            coerced_value = self.parser.validate_inputs(self.metadata, {name: value})[name]
        except Exception as e:
            raise RenderingError(f"Failed to set input '{name}': {e}")
        # Only reload if value changes
        if name not in self._input_values or self._input_values[name] != coerced_value:
            self._input_values[name] = coerced_value
            # Reload shader to update uniforms (if needed)
            if self._shader_content:
                if self._vertex_shader_content:
                    self.metadata = self.load_shader_content(self._shader_content, self._vertex_shader_content)
                else:
                    self.metadata = self.load_shader_content(self._shader_content)
        # else: value is the same, do nothing

    def _ensure_version_directive(self, source: str) -> str:
        """Ensure the shader source starts with a #version directive."""
        if "#version" not in source:
            return "#version 330\n" + source
        # Replace '#version 330 core' with '#version 330' for compatibility
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith('#version') and 'core' in line:
                lines[i] = line.replace('core', '').strip()
        return '\n'.join(lines)

    def _patch_legacy_gl_fragcolor(self, source: str) -> str:
        """Ensure the fragment shader uses 'out vec4 isf_FragColor;' as the output variable and assignments are to isf_FragColor."""
        lines = source.splitlines()
        # Insert after #version
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#version'):
                insert_idx = i + 1
                break
        # Always insert the out variable if not present
        if not any('out vec4 isf_FragColor;' in l for l in lines):
            lines.insert(insert_idx, 'out vec4 isf_FragColor;')
            insert_idx += 1
        # Remove any #define gl_FragColor isf_FragColor lines
        lines = [l for l in lines if '#define gl_FragColor isf_FragColor' not in l]
        # Replace all assignments to gl_FragColor and fragColor with isf_FragColor
        source = '\n'.join(lines)
        source = source.replace('gl_FragColor', 'isf_FragColor')
        source = source.replace('fragColor', 'isf_FragColor')
        return source

    def _inject_uniform_declarations(self, source: str, metadata: ISFMetadata) -> str:
        """Inject uniform declarations for all ISF inputs at the top of the shader."""
        if not metadata or not metadata.inputs:
            return source
        # Map ISF types to GLSL types
        type_map = {
            'bool': 'bool',
            'long': 'int',
            'float': 'float',
            'point2D': 'vec2',
            'color': 'vec4',
            'image': 'sampler2D',
            'audio': 'sampler2D',
            'audioFFT': 'sampler2D',
        }
        uniform_lines = []
        for inp in metadata.inputs:
            glsl_type = type_map.get(inp.type, 'float')
            uniform_lines.append(f'uniform {glsl_type} {inp.name};')
        # Insert after #version and any out variable
        lines = source.splitlines()
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#version'):
                insert_idx = i + 1
            elif line.strip().startswith('out vec4 fragColor;'):
                insert_idx = i + 1
        for j, uline in enumerate(uniform_lines):
            lines.insert(insert_idx + j, uline)
        return '\n'.join(lines)

    def _inject_standard_uniforms(self, source: str) -> str:
        """Inject standard ISF uniforms and isf_FragNormCoord if not already declared."""
        # According to ISF Spec, the standard uniforms are:
        # PASSINDEX (int), RENDERSIZE (vec2), TIME (float), TIMEDELTA (float), DATE (vec4), FRAMEINDEX (int)
        standard_uniforms = [
            ("int", "PASSINDEX"),
            ("vec2", "RENDERSIZE"),
            ("float", "TIME"),
            ("float", "TIMEDELTA"),
            ("vec4", "DATE"),
            ("int", "FRAMEINDEX"),
        ]
        lines = source.splitlines()
        # Find where to insert (after #version and any out variable)
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#version'):
                insert_idx = i + 1
            elif line.strip().startswith('out vec4 fragColor;'):
                insert_idx = i + 1
        # Only inject if not already present
        for dtype, name in standard_uniforms:
            if not any(f"uniform {dtype} {name}" in l or f"uniform {name}" in l for l in lines):
                lines.insert(insert_idx, f"uniform {dtype} {name};")
                insert_idx += 1
        # Inject isf_FragNormCoord as in/varying if not present
        # Only inject if referenced in the shader
        frag_norm_coord_needed = any('isf_FragNormCoord' in l for l in lines)
        if frag_norm_coord_needed and not any("in vec2 isf_FragNormCoord;" in l for l in lines):
            lines.insert(insert_idx, "in vec2 isf_FragNormCoord;")
            insert_idx += 1
        return '\n'.join(lines)

    def _inject_isf_vertShaderInit(self, source: str) -> str:
        """Inject a definition for isf_vertShaderInit() if referenced but not defined, and declare isf_FragNormCoord, position, and texCoord as needed with explicit locations."""
        needs_inject = 'isf_vertShaderInit' in source and 'void isf_vertShaderInit' not in source
        already_declared_frag_norm = 'out vec2 isf_FragNormCoord;' in source
        already_declared_position = 'layout(location = 0) in vec2 position;' in source
        already_declared_texcoord = 'layout(location = 1) in vec2 texCoord;' in source
        # Remove any old 'in vec2 position;' or 'in vec2 texCoord;' lines
        if needs_inject:
            lines = source.splitlines()
            # Remove old attribute declarations if present
            lines = [l for l in lines if l.strip() not in ('in vec2 position;', 'in vec2 texCoord;')]
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('#version'):
                    insert_idx = i + 1
                    break
            # Inject required declarations if not present
            if not already_declared_frag_norm:
                lines.insert(insert_idx, 'out vec2 isf_FragNormCoord;')
                insert_idx += 1
            if not already_declared_position:
                lines.insert(insert_idx, 'layout(location = 0) in vec2 position;')
                insert_idx += 1
            if not already_declared_texcoord:
                lines.insert(insert_idx, 'layout(location = 1) in vec2 texCoord;')
                insert_idx += 1
            # Inject the function
            inject_code = (
                "void isf_vertShaderInit() {\n"
                "    gl_Position = vec4(position, 0.0, 1.0);\n"
                "    isf_FragNormCoord = vec2(texCoord.x, 1.0 - texCoord.y);\n"
                "}\n"
            )
            lines.insert(insert_idx, inject_code)
            return '\n'.join(lines)
        return source

    def default_vertex_shader(self):
        # Literal ISF default vertex shader
        return (
            "void main() {\n"
            "  isf_vertShaderInit();\n"
            "}\n"
        )

    def _set_standard_uniforms(self, width: int, height: int, time_offset: float = 0.0):
        """Set standard ISF uniforms."""
        # Set all standard uniforms, using default values for those not tracked
        if self.shader_manager is not None:
            self.shader_manager.set_uniform("PASSINDEX", 0)
            self.shader_manager.set_uniform("RENDERSIZE", [width, height])
            self.shader_manager.set_uniform("TIME", time_offset)
            self.shader_manager.set_uniform("TIMEDELTA", 0.0)  # TODO: Calculate delta
            self.shader_manager.set_uniform("DATE", [1970.0, 1.0, 1.0, 0.0])  # Placeholder: UNIX epoch
            self.shader_manager.set_uniform("FRAMEINDEX", 0)   # TODO: Track frame index

    def load_shader(self, shader_path: str, vertex_shader_content: str = '') -> ISFMetadata:
        """Load and parse ISF shader file. Optionally takes a vertex shader source."""
        glsl_code, metadata = self.parser.parse_file(shader_path)
        # Initialize context if needed
        if not self.context.initialized:
            self.context.initialize()
        # Compile shaders
        if vertex_shader_content:
            vertex_source = vertex_shader_content
        else:
            vertex_source = metadata.vertex_shader or self.default_vertex_shader()
        vertex_source = self._ensure_version_directive(vertex_source)
        vertex_source = self._inject_isf_vertShaderInit(vertex_source)
        vertex_source = self._inject_uniform_declarations(vertex_source, metadata)
        glsl_code = self._ensure_version_directive(glsl_code)
        glsl_code = self._patch_legacy_gl_fragcolor(glsl_code)
        glsl_code = self._inject_uniform_declarations(glsl_code, metadata)
        glsl_code = self._inject_standard_uniforms(glsl_code)
        self.shader_manager = ShaderManager()
        # Provide expected input uniforms for caching
        if hasattr(metadata, 'inputs') and metadata.inputs:
            self.shader_manager.expected_input_uniforms = [inp.name for inp in metadata.inputs]
        self.shader_manager.create_program(vertex_source, glsl_code)
        # Setup rendering quad
        self._setup_quad()
        return metadata

    def load_shader_content(self, content: str, vertex_shader_content: str = '') -> ISFMetadata:
        """Load and parse ISF shader content. Optionally takes a vertex shader source."""
        # Early validation for empty shader content
        if not content or not content.strip():
            raise ShaderValidationError(
                "Shader content is empty or only whitespace. Please provide valid ISF shader code.",
                shader_source=content,
                shader_type="fragment"
            )
        try:
            glsl_code, metadata = self.parser.parse_content(content)
        except ISFParseError:
            # Let ISFParseError propagate directly
            raise
        except Exception as e:
            raise ShaderValidationError(
                f"Shader parsing failed: {e}",
                shader_source=content,
                shader_type="fragment"
            ) from e
        # Initialize context if needed
        if not self.context.initialized:
            self.context.initialize()
        # Compile shaders
        if vertex_shader_content:
            vertex_source = vertex_shader_content
        else:
            vertex_source = metadata.vertex_shader or self.default_vertex_shader()
        vertex_source = self._ensure_version_directive(vertex_source)
        vertex_source = self._inject_isf_vertShaderInit(vertex_source)
        vertex_source = self._inject_uniform_declarations(vertex_source, metadata)
        glsl_code = self._ensure_version_directive(glsl_code)
        glsl_code = self._patch_legacy_gl_fragcolor(glsl_code)
        glsl_code = self._inject_uniform_declarations(glsl_code, metadata)
        glsl_code = self._inject_standard_uniforms(glsl_code)
        logger.debug("Vertex Shader Source:\n" + vertex_source)
        logger.debug("Fragment Shader Source:\n" + glsl_code)
        self.shader_manager = ShaderManager()
        # Provide expected input uniforms for caching
        if hasattr(metadata, 'inputs') and metadata.inputs:
            self.shader_manager.expected_input_uniforms = [inp.name for inp in metadata.inputs]
        try:
            self.shader_manager.create_program(vertex_source, glsl_code)
        except ShaderCompilationError as e:
            raise ShaderValidationError(
                f"Shader compilation failed: {e}",
                shader_source=glsl_code,
                shader_type="fragment"
            ) from e
        # Setup rendering quad
        self._setup_quad()
        return metadata
    
    def render(self, 
               width: int = 1920, 
               height: int = 1080,
               inputs: Optional[Dict[str, Any]] = None,
               metadata: Optional[ISFMetadata] = None,
               time_offset: float = 0.0) -> 'RenderResult':
        """Render shader to numpy array (wrapped in RenderResult)."""
        if not self.shader_manager:
            raise RenderingError("No shader loaded. Call load_shader() first.")
        # Use self._input_values if inputs not provided
        if inputs is None:
            inputs = self._input_values
        # Use self.metadata if metadata not provided
        if metadata is None:
            metadata = self.metadata
        # Validate inputs
        if metadata and inputs:
            validated_inputs = self.parser.validate_inputs(metadata, inputs)
        else:
            validated_inputs = {}
        # --- Offscreen FBO/texture setup ---
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            glDeleteFramebuffers(1, [fbo])
            glDeleteTextures(1, [tex])
            raise RenderingError("Framebuffer is not complete for offscreen rendering.")
        # Set viewport
        glViewport(0, 0, width, height)
        glDisable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Use shader program
        self.shader_manager.use()
        # Set uniforms
        self._set_standard_uniforms(width, height, time_offset)
        self._set_input_uniforms(validated_inputs)
        # Draw the quad
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        glBindVertexArray(0)
        glFlush()
        glFinish()
        # Read pixels from FBO
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        data = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
        if isinstance(data, bytes):
            image_array = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 4)
            image_array = np.flipud(image_array)
            # Cleanup FBO/texture
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glDeleteFramebuffers(1, [fbo])
            glDeleteTextures(1, [tex])
            return RenderResult(image_array)
        else:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glDeleteFramebuffers(1, [fbo])
            glDeleteTextures(1, [tex])
            logger.error(f"glReadPixels failed or returned unexpected type: {type(data)} value: {data}")
            raise RenderingError("glReadPixels failed to return pixel data.")
    
    def _setup_quad(self):
        """Setup full-screen quad for rendering."""
        # Quad vertices (position, texcoord)
        # 4 vertices, each with (x, y, u, v)
        vertices = np.array([
            # position    # texcoord
            -1.0, -1.0,   0.0, 0.0,  # bottom-left
             1.0, -1.0,   1.0, 0.0,  # bottom-right
            -1.0,  1.0,   0.0, 1.0,  # top-left
             1.0,  1.0,   1.0, 1.0,  # top-right
        ], dtype=np.float32)
        # Create VAO
        self.quad_vao = glGenVertexArrays(1)
        glBindVertexArray(self.quad_vao)
        # Create VBO
        self.quad_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        stride = 4 * vertices.itemsize  # 4 floats per vertex
        # Position attribute (location = 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        # TexCoord attribute (location = 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(2 * vertices.itemsize))
        glBindVertexArray(0)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status is not None and status != GL_FRAMEBUFFER_COMPLETE:
            logger.error("Framebuffer is not complete after VAO/VBO setup!")

    def _set_input_uniforms(self, inputs: Dict[str, ISFValue]):
        """Set input uniform values."""
        if self.shader_manager is not None:
            for name, value in inputs.items():
                self.shader_manager.set_uniform(name, value)
    
    def save_render(self, 
                   output_path: str,
                   width: int = 1920,
                   height: int = 1080,
                   inputs: Optional[Dict[str, Any]] = None,
                   metadata: Optional[ISFMetadata] = None):
        """Render shader and save to file."""
        from PIL import Image
        
        render_result = self.render(width, height, inputs, metadata)
        image = render_result.to_pil_image()
        image.save(output_path)
    
    def cleanup(self):
        """Clean up all resources."""
        if self.shader_manager:
            self.shader_manager.cleanup()
            self.shader_manager = None
        
        if self.quad_vao:
            glDeleteVertexArrays(1, [self.quad_vao])
            self.quad_vao = None
        
        if self.quad_vbo:
            glDeleteBuffers(1, [self.quad_vbo])
            self.quad_vbo = None
        
        self.context.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 