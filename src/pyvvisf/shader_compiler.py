"""Shader compilation and source manipulation utilities."""

import re
from typing import List, Optional, Any
import logging

from .parser import ISFMetadata
from .errors import ShaderCompilationError

from OpenGL.GL import glCreateShader, glShaderSource, glCompileShader, glGetShaderiv, glGetShaderInfoLog, glDeleteShader, glCreateProgram, glAttachShader, glLinkProgram, glGetProgramiv, glGetProgramInfoLog, glUseProgram, glGetUniformLocation, glGetActiveUniform, glUniform1i, glUniform1f, glUniform2f, glUniform3f, glUniform4f, glDeleteProgram, GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_GEOMETRY_SHADER, GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS, GL_ACTIVE_UNIFORMS

logger = logging.getLogger(__name__)


class ShaderSourceProcessor:
    """Handles shader source code manipulation and injection."""
    
    @staticmethod
    def ensure_version_directive(source: str) -> str:
        """Ensure the shader source starts with a #version directive."""
        if "#version" not in source:
            return "#version 330\n" + source
        # Replace '#version 330 core' with '#version 330' for compatibility
        lines = source.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith('#version') and 'core' in line:
                lines[i] = line.replace('core', '').strip()
        return '\n'.join(lines)
    
    @staticmethod
    def patch_legacy_gl_fragcolor(source: str) -> str:
        """Patch fragment shader to support legacy gl_FragColor in GLSL 330+."""
        lines = source.splitlines()
        version_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('#version'):
                version_idx = i
                break
                
        uses_gl_fragcolor = any('gl_FragColor' in l for l in lines)
        already_has_out = any('out vec4' in l for l in lines)
        already_has_define = any('#define gl_FragColor' in l for l in lines)
        
        if uses_gl_fragcolor:
            insert_idx = version_idx + 1 if version_idx is not None else 0
            if not already_has_out:
                lines.insert(insert_idx, 'out vec4 fragColor;')
                insert_idx += 1
            if not already_has_define:
                lines.insert(insert_idx, '#define gl_FragColor fragColor')
                
            # Replace all assignments to gl_FragColor with fragColor
            for i, line in enumerate(lines):
                if 'gl_FragColor' in line and not line.strip().startswith('#define'):
                    lines[i] = line.replace('gl_FragColor', 'fragColor')
                     
        return '\n'.join(lines)
    
    @staticmethod
    def find_insertion_point(lines: List[str]) -> int:
        """Find the best insertion point for uniform declarations."""
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#version'):
                insert_idx = i + 1
            elif line.strip().startswith('out vec4 fragColor;'):
                insert_idx = i + 1
        return insert_idx
    
    @staticmethod
    def inject_uniform_declarations(source: str, metadata: ISFMetadata) -> str:
        """Inject uniform declarations for all ISF inputs."""
        if not metadata or not metadata.inputs:
            return source
            
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
             
        lines = source.splitlines()
        insert_idx = ShaderSourceProcessor.find_insertion_point(lines)
        
        for j, uline in enumerate(uniform_lines):
            lines.insert(insert_idx + j, uline)
            
        return '\n'.join(lines)
    
    @staticmethod
    def inject_standard_uniforms(source: str) -> str:
        """Inject standard ISF uniforms."""
        standard_uniforms = [
            ("int", "PASSINDEX"),
            ("vec2", "RENDERSIZE"), 
            ("float", "TIME"),
            ("float", "TIMEDELTA"),
            ("vec4", "DATE"),
            ("int", "FRAMEINDEX"),
        ]
        
        lines = source.splitlines()
        insert_idx = ShaderSourceProcessor.find_insertion_point(lines)
        
        for dtype, name in standard_uniforms:
            if not any(f"uniform {dtype} {name}" in l or f"uniform {name}" in l for l in lines):
                lines.insert(insert_idx, f"uniform {dtype} {name};")
                insert_idx += 1
                
        # Inject isf_FragNormCoord if referenced
        frag_norm_coord_needed = any('isf_FragNormCoord' in l or 'IMG_THIS_NORM_PIXEL' in l for l in lines)
        if frag_norm_coord_needed and not any("in vec2 isf_FragNormCoord;" in l for l in lines):
            lines.insert(insert_idx, "in vec2 isf_FragNormCoord;")
            
        return '\n'.join(lines)
    
    @staticmethod
    def inject_isf_macros(source: str) -> str:
        """Inject ISF macros if referenced."""
        lines = source.splitlines()
        insert_idx = ShaderSourceProcessor.find_insertion_point(lines)
        
        macro_defs = [
            ('IMG_NORM_PIXEL', '#define IMG_NORM_PIXEL(image, normCoord) texture(image, normCoord)'),
            ('IMG_THIS_NORM_PIXEL', '#define IMG_THIS_NORM_PIXEL(image) IMG_NORM_PIXEL(image, isf_FragNormCoord)'),
            ('IMG_PIXEL', '#define IMG_PIXEL(image, coord) texture(image, (coord) / RENDERSIZE)'),
            ('IMG_THIS_PIXEL', '#define IMG_THIS_PIXEL(image) IMG_PIXEL(image, gl_FragCoord.xy)'),
            ('IMG_SIZE', '#define IMG_SIZE(image) RENDERSIZE'),
        ]
        
        macro_names = [name for name, _ in macro_defs]
        if any(any(macro in l for macro in macro_names) for l in lines):
            for _, macro in macro_defs:
                lines.insert(insert_idx, macro)
                insert_idx += 1
                
        return '\n'.join(lines)
    
    @staticmethod
    def inject_vertex_shader_init(source: str) -> str:
        """Inject isf_vertShaderInit() if referenced but not defined."""
        needs_inject = 'isf_vertShaderInit' in source and 'void isf_vertShaderInit' not in source
        
        if not needs_inject:
            return source
            
        lines = source.splitlines()
        # Remove old attribute declarations
        lines = [l for l in lines if l.strip() not in ('in vec2 position;', 'in vec2 texCoord;')]
        
        insert_idx = ShaderSourceProcessor.find_insertion_point(lines)
        
        # Inject required declarations
        if 'out vec2 isf_FragNormCoord;' not in source:
            lines.insert(insert_idx, 'out vec2 isf_FragNormCoord;')
            insert_idx += 1
        if 'layout(location = 0) in vec2 position;' not in source:
            lines.insert(insert_idx, 'layout(location = 0) in vec2 position;')
            insert_idx += 1
        if 'layout(location = 1) in vec2 texCoord;' not in source:
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
    
    @staticmethod
    def inject_pass_target_uniforms(source: str, targets: List[str]) -> str:
        """Inject uniform declarations for pass targets."""
        if not targets:
            return source
            
        uniform_lines = [f"uniform sampler2D {target_name};" for target_name in targets]
        
        lines = source.splitlines()
        insert_idx = ShaderSourceProcessor.find_insertion_point(lines)
        
        for j, uline in enumerate(uniform_lines):
            lines.insert(insert_idx + j, uline)
            
        return '\n'.join(lines)


class ShaderCompiler:
    """Handles OpenGL shader compilation and program creation."""
    
    def __init__(self):
        self.program: Optional[int] = None
        self.vertex_shader: Optional[int] = None
        self.fragment_shader: Optional[int] = None
        self.uniform_locations: dict[str, int] = {}
        
    def compile_shader(self, source: str, shader_type: int) -> int:
        """Compile a GLSL shader and check for errors."""
        try:
            shader = glCreateShader(shader_type)
        except NameError:
            # OpenGL not available - for testing purposes
            return 1
            
        if shader is None or shader == 0:
            raise ShaderCompilationError(
                f"Failed to create shader object (type {self._shader_type_name(shader_type)}).",
                shader_source=source,
                shader_type=self._shader_type_name(shader_type)
            )
            
        try:
            glShaderSource(shader, source)
            glCompileShader(shader)
            
            if not glGetShaderiv(shader, GL_COMPILE_STATUS):
                error_log = glGetShaderInfoLog(shader).decode('utf-8')
                glDeleteShader(shader)
                raise ShaderCompilationError(
                    f"Shader compilation failed:\n{error_log}",
                    shader_source=source,
                    shader_type=self._shader_type_name(shader_type)
                )
        except NameError:
            # OpenGL not available - for testing purposes
            pass
            
        return int(shader)
    
    def create_program(self, vertex_source: str, fragment_source: str, expected_uniforms: Optional[List[str]] = None) -> int:
        """Create and link a shader program."""
        try:
            self.vertex_shader = self.compile_shader(vertex_source, GL_VERTEX_SHADER)
            self.fragment_shader = self.compile_shader(fragment_source, GL_FRAGMENT_SHADER)
            
            try:
                self.program = glCreateProgram()
            except NameError:
                # OpenGL not available - for testing purposes
                self.program = 1
                return 1
                
            if self.program is None or self.program == 0:
                raise ShaderCompilationError("Failed to create shader program object.")
                
            glAttachShader(self.program, self.vertex_shader)
            glAttachShader(self.program, self.fragment_shader)
            glLinkProgram(self.program)
            
            if not glGetProgramiv(self.program, GL_LINK_STATUS):
                error_log = glGetProgramInfoLog(self.program).decode('utf-8')
                raise ShaderCompilationError(f"Shader program linking failed:\n{error_log}")
                
            glUseProgram(self.program)
            self._cache_uniform_locations(expected_uniforms or [])
            
            return int(self.program)
            
        except Exception as e:
            self.cleanup()
            raise e
    
    def _cache_uniform_locations(self, expected_uniforms: List[str]):
        """Cache uniform locations for performance."""
        self.uniform_locations = {}
        
        try:
            # Cache active uniforms
            num_uniforms = glGetProgramiv(self.program, GL_ACTIVE_UNIFORMS)
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
        except NameError:
            # OpenGL not available - for testing purposes
            pass
            
        # Cache expected uniforms
        standard_uniforms = ['PASSINDEX', 'RENDERSIZE', 'TIME', 'TIMEDELTA', 'DATE', 'FRAMEINDEX']
        all_expected = standard_uniforms + expected_uniforms
        
        for name in all_expected:
            if name not in self.uniform_locations:
                try:
                    location = glGetUniformLocation(self.program, name)
                    self.uniform_locations[name] = location
                except NameError:
                    # OpenGL not available - for testing purposes
                    self.uniform_locations[name] = -1
    
    def set_uniform(self, name: str, value: Any):
        """Set the value of a uniform variable."""
        location = self.uniform_locations.get(name, -1)
        if location == -1:
            return
            
        from .types import ISFColor, ISFPoint2D
        
        try:
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
        except NameError:
            # OpenGL not available - for testing purposes
            pass
    
    def use(self):
        """Activate this shader program."""
        if self.program:
            try:
                glUseProgram(self.program)
            except NameError:
                # OpenGL not available - for testing purposes
                pass
    
    def cleanup(self):
        """Delete all OpenGL resources."""
        try:
            if self.program:
                glDeleteProgram(self.program)
                self.program = None
            if self.vertex_shader:
                glDeleteShader(self.vertex_shader)
                self.vertex_shader = None
            if self.fragment_shader:
                glDeleteShader(self.fragment_shader)
                self.fragment_shader = None
        except NameError:
            # OpenGL not available - for testing purposes
            pass
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