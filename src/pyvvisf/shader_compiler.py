"""Shader compilation and source manipulation utilities."""

import re
from typing import List, Optional, Any, Dict
import logging

from .parser import ISFMetadata, ISFInput, ISFPass
from .errors import ShaderCompilationError

from OpenGL.GL import glCreateShader, glShaderSource, glCompileShader, glGetShaderiv, glGetShaderInfoLog, glDeleteShader, glCreateProgram, glAttachShader, glLinkProgram, glGetProgramiv, glGetProgramInfoLog, glUseProgram, glGetUniformLocation, glGetActiveUniform, glUniform1i, glUniform1f, glUniform2f, glUniform3f, glUniform4f, glDeleteProgram, GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_GEOMETRY_SHADER, GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS, GL_ACTIVE_UNIFORMS, glGetString, GL_VERSION, GL_SHADING_LANGUAGE_VERSION

logger = logging.getLogger(__name__)

# ISF Type to GLSL uniform type mapping (from JavaScript reference)
TYPE_UNIFORM_MAP = {
    'float': 'float',
    'image': 'sampler2D',
    'bool': 'bool',
    'event': 'bool',
    'long': 'int',
    'color': 'vec4',
    'point2D': 'vec2',
}

# ISF Fragment Shader Skeleton (modernized for GLSL 330+)
ISF_FRAGMENT_SHADER_SKELETON = """
precision highp float;
precision highp int;

uniform int PASSINDEX;
uniform vec2 RENDERSIZE;
in vec2 isf_FragNormCoord;
in vec2 isf_FragCoord;
uniform float TIME;
uniform float TIMEDELTA;
uniform int FRAMEINDEX;
uniform vec4 DATE;

[[uniforms]]

// ISF sampling functions (from JavaScript reference)
vec4 VVSAMPLER_2DBYPIXEL(sampler2D sampler, vec4 samplerImgRect, vec2 samplerImgSize, bool samplerFlip, vec2 loc) {
  return (samplerFlip)
    ? texture(sampler,vec2(((loc.x/samplerImgSize.x*samplerImgRect.z)+samplerImgRect.x), (samplerImgRect.w-(loc.y/samplerImgSize.y*samplerImgRect.w)+samplerImgRect.y)))
    : texture(sampler,vec2(((loc.x/samplerImgSize.x*samplerImgRect.z)+samplerImgRect.x), ((loc.y/samplerImgSize.y*samplerImgRect.w)+samplerImgRect.y)));
}
vec4 VVSAMPLER_2DBYNORM(sampler2D sampler, vec4 samplerImgRect, vec2 samplerImgSize, bool samplerFlip, vec2 normLoc)  {
  vec4 returnMe = VVSAMPLER_2DBYPIXEL(sampler,samplerImgRect,samplerImgSize,samplerFlip,vec2(normLoc.x*samplerImgSize.x, normLoc.y*samplerImgSize.y));
  return returnMe;
}

out vec4 fragColor;
#define gl_FragColor fragColor

[[main]]
"""

# ISF Vertex Shader Skeleton (modernized for GLSL 330+)
ISF_VERTEX_SHADER_SKELETON = """
precision highp float;
precision highp int;
void isf_vertShaderInit();

in vec2 isf_position; // -1..1

uniform int     PASSINDEX;
uniform vec2    RENDERSIZE;
out vec2    isf_FragNormCoord; // 0..1
vec2    isf_fragCoord; // Pixel Space

[[uniforms]]

[[main]]
void isf_vertShaderInit(void)  {
    gl_Position = vec4( isf_position, 0.0, 1.0 );
    isf_FragNormCoord = vec2((gl_Position.x+1.0)/2.0, 1.0 - (gl_Position.y+1.0)/2.0);
    isf_fragCoord = floor(isf_FragNormCoord * RENDERSIZE);
    [[functions]]
}
"""

# Default vertex shader (from JavaScript reference)
ISF_VERTEX_SHADER_DEFAULT = """
void main() {
  isf_vertShaderInit();
}
"""


def get_supported_glsl_versions() -> List[str]:
    """
    Detect and return a list of supported GLSL versions on the current system by actually compiling test shaders.
    Returns:
        List of supported GLSL version strings (e.g., ['110', '120', '130', ...])
    """
    candidate_versions = [
        '110', '120', '130', '140', '150',
        '330', '400', '410', '420', '430', '440', '450', '460'
    ]
    supported_versions = []
    try:
        gl_version_str = glGetString(GL_VERSION)
        glsl_version_str = glGetString(GL_SHADING_LANGUAGE_VERSION)
        if gl_version_str is None or glsl_version_str is None:
            logger.warning("Could not get OpenGL version information")
            return ['330', '400', '410', '420', '430', '440', '450']
        gl_version = gl_version_str.decode('utf-8')
        glsl_version = glsl_version_str.decode('utf-8')
        logger.info(f"OpenGL Version: {gl_version}")
        logger.info(f"GLSL Version: {glsl_version}")
        for version in candidate_versions:
            result = _test_glsl_version_support(version, return_error=True)
            ok, err = result if isinstance(result, tuple) else (result, None)
            if ok:
                supported_versions.append(version)
            else:
                logger.info(f"GLSL version {version} not supported: {err}")
        return supported_versions
    except Exception as e:
        logger.warning(f"Could not detect GLSL versions: {e}")
        return ['330', '400', '410', '420', '430', '440', '450']

def _test_glsl_version_support(version: str, return_error: bool = False):
    """
    Test if a specific GLSL version is actually supported by trying to compile a simple shader.
    Args:
        version: GLSL version string to test (e.g., '110', '330')
        return_error: If True, return (ok, error_message). If False, return bool only.
    Returns:
        True if the version is supported, False otherwise. If return_error, returns (ok, error_message).
    """
    try:
        if version == '110':
            vertex_source = f"""#version {version}
attribute vec2 position;
attribute vec2 texCoord;
varying vec2 isf_FragNormCoord;
void main() {{
    gl_Position = vec4(position, 0.0, 1.0);
    isf_FragNormCoord = vec2(texCoord.x, 1.0 - texCoord.y);
}}"""
            fragment_source = f"""#version {version}
varying vec2 isf_FragNormCoord;
void main() {{
    gl_FragColor = vec4(isf_FragNormCoord, 0.0, 1.0);
}}"""
        else:
            vertex_source = f"""#version {version}
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 texCoord;
out vec2 isf_FragNormCoord;
void main() {{
    gl_Position = vec4(position, 0.0, 1.0);
    isf_FragNormCoord = vec2(texCoord.x, 1.0 - texCoord.y);
}}"""
            fragment_source = f"""#version {version}
in vec2 isf_FragNormCoord;
out vec4 fragColor;
void main() {{
    fragColor = vec4(isf_FragNormCoord, 0.0, 1.0);
}}"""
        compiler = ShaderCompiler()
        try:
            compiler.create_program(vertex_source, fragment_source)
            if return_error:
                return True, None
            return True
        except ShaderCompilationError as e:
            if return_error:
                return False, str(e)
            return False
        finally:
            compiler.cleanup()
    except Exception as e:
        if return_error:
            return False, str(e)
        return False


class ShaderSourceProcessor:
    """Handles shader source code manipulation and injection."""
    
    @staticmethod
    def ensure_version_directive(source: str, version: str = '330') -> str:
        """Ensure the shader source starts with a #version directive, using the provided version string."""
        if "#version" not in source:
            return f"#version {version}\n" + source
        # Replace '#version XXX core' with '#version XXX' for compatibility
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


class ISFShaderProcessor:
    """ISF-specific shader processing based on JavaScript reference implementation."""
    
    def __init__(self):
        self.uniform_defs = ""
        self.isf_version = 2  # Default to ISF 2.0
    
    def process_fragment_shader(self, raw_fragment_shader: str, metadata: ISFMetadata) -> str:
        """Process fragment shader using ISF skeleton and special function replacement."""
        # Generate uniforms
        self._generate_uniforms(metadata)
        
        # Replace special functions in the main shader code
        main_code = self._replace_special_functions(raw_fragment_shader)
        
        # Build fragment shader using skeleton
        fragment_shader = ISF_FRAGMENT_SHADER_SKELETON.replace(
            '[[uniforms]]', self.uniform_defs
        ).replace('[[main]]', main_code)
        
        return fragment_shader
    
    def process_vertex_shader(self, raw_vertex_shader: str, metadata: ISFMetadata) -> str:
        """Process vertex shader using ISF skeleton."""
        # Generate uniforms for vertex shader
        self._generate_vertex_uniforms(metadata)
        
        # Generate texture coordinate functions for image inputs
        function_lines = self._generate_tex_coord_functions(metadata)
        
        # Build vertex shader using skeleton
        vertex_shader = ISF_VERTEX_SHADER_SKELETON.replace(
            '[[uniforms]]', self.uniform_defs
        ).replace('[[main]]', raw_vertex_shader or ISF_VERTEX_SHADER_DEFAULT).replace(
            '[[functions]]', function_lines
        )
        
        return vertex_shader
    
    def _generate_uniforms(self, metadata: ISFMetadata):
        """Generate uniform declarations for all inputs and passes."""
        self.uniform_defs = ""
        
        # Add input uniforms
        if metadata.inputs:
            for input_def in metadata.inputs:
                self._add_uniform(input_def)
        
        # Add pass target uniforms
        if metadata.passes:
            for pass_def in metadata.passes:
                if pass_def.target:
                    self._add_uniform({'name': pass_def.target, 'type': 'image'})
        
        # Add imported texture uniforms
        if metadata.imports:
            for import_name in metadata.imports:
                self._add_uniform({'name': import_name, 'type': 'image'})
    
    def _generate_vertex_uniforms(self, metadata: ISFMetadata):
        """Generate uniform declarations for vertex shader."""
        self.uniform_defs = ""
        
        # Add input uniforms
        if metadata.inputs:
            for input_def in metadata.inputs:
                self._add_vertex_uniform(input_def)
        
        # Add pass target uniforms
        if metadata.passes:
            for pass_def in metadata.passes:
                if pass_def.target:
                    self._add_vertex_uniform({'name': pass_def.target, 'type': 'image'})
        
        # Add imported texture uniforms
        if metadata.imports:
            for import_name in metadata.imports:
                self._add_vertex_uniform({'name': import_name, 'type': 'image'})
    
    def _add_uniform(self, input_def):
        """Add a uniform declaration."""
        # Handle both ISFInput objects and dictionaries
        if hasattr(input_def, 'type'):
            input_type = input_def.type
            input_name = input_def.name
        else:
            input_type = input_def.get('type', 'float')
            input_name = input_def.get('name', 'unknown')
        
        # Handle reserved GLSL keywords
        safe_name = self._make_safe_identifier(input_name)
        
        glsl_type = self._input_to_glsl_type(input_type)
        self.uniform_defs += f"uniform {glsl_type} {safe_name};\n"
        
        # Add texture-specific uniforms for image inputs
        if input_type == 'image':
            self.uniform_defs += self._sampler_uniforms(safe_name)
    
    def _add_vertex_uniform(self, input_def):
        """Add a uniform declaration for vertex shader."""
        # Handle both ISFInput objects and dictionaries
        if hasattr(input_def, 'type'):
            input_type = input_def.type
            input_name = input_def.name
        else:
            input_type = input_def.get('type', 'float')
            input_name = input_def.get('name', 'unknown')
        
        # Handle reserved GLSL keywords
        safe_name = self._make_safe_identifier(input_name)
        
        glsl_type = self._input_to_glsl_type(input_type)
        self.uniform_defs += f"uniform {glsl_type} {safe_name};\n"
        
        # Add texture-specific uniforms for image inputs (out for vertex shader)
        if input_type == 'image':
            self.uniform_defs += self._vertex_sampler_uniforms(safe_name)
    
    def _sampler_uniforms(self, name: str) -> str:
        """Generate sampler-specific uniforms for image inputs."""
        lines = ""
        lines += f"uniform vec4 _{name}_imgRect;\n"
        lines += f"uniform vec2 _{name}_imgSize;\n"
        lines += f"uniform bool _{name}_flip;\n"
        lines += f"in vec2 _{name}_normTexCoord;\n"
        lines += f"in vec2 _{name}_texCoord;\n"
        lines += "\n"
        return lines
    
    def _vertex_sampler_uniforms(self, name: str) -> str:
        """Generate sampler-specific uniforms for vertex shader (out for texture coordinates)."""
        lines = ""
        lines += f"uniform vec4 _{name}_imgRect;\n"
        lines += f"uniform vec2 _{name}_imgSize;\n"
        lines += f"uniform bool _{name}_flip;\n"
        lines += f"out vec2 _{name}_normTexCoord;\n"
        lines += f"out vec2 _{name}_texCoord;\n"
        lines += "\n"
        return lines
    
    def _generate_tex_coord_functions(self, metadata: ISFMetadata) -> str:
        """Generate texture coordinate functions for image inputs."""
        if not metadata.inputs:
            return ""
        
        function_lines = []
        for input_def in metadata.inputs:
            if input_def.type == 'image':
                function_lines.append(self._tex_coord_function(input_def.name))
        
        return '\n'.join(function_lines)
    
    def _tex_coord_function(self, name: str) -> str:
        """Generate texture coordinate function for a specific image input."""
        return f"""_{name}_texCoord =
    vec2(((isf_fragCoord.x / _{name}_imgSize.x * _{name}_imgRect.z) + _{name}_imgRect.x), 
          (isf_fragCoord.y / _{name}_imgSize.y * _{name}_imgRect.w) + _{name}_imgRect.y);

_{name}_normTexCoord =
  vec2((((isf_FragNormCoord.x * _{name}_imgSize.x) / _{name}_imgSize.x * _{name}_imgRect.z) + _{name}_imgRect.x),
          (((isf_FragNormCoord.y * _{name}_imgSize.y) / _{name}_imgSize.y * _{name}_imgRect.w) + _{name}_imgRect.y));"""
    
    def _replace_special_functions(self, source: str) -> str:
        """Replace ISF special functions with GLSL equivalents (modernized for GLSL 330+)."""
        # IMG_THIS_PIXEL
        source = re.sub(r'IMG_THIS_PIXEL\((.+?)\)', r'texture(\1, isf_FragNormCoord)', source)
        
        # IMG_THIS_NORM_PIXEL
        source = re.sub(r'IMG_THIS_NORM_PIXEL\((.+?)\)', r'texture(\1, isf_FragNormCoord)', source)
        
        # IMG_PIXEL
        source = re.sub(r'IMG_PIXEL\((.+?)\s?,\s?(.+?\)?\.?.*)\)', 
                       r'texture(\1, (\2) / RENDERSIZE)', source)
        
        # IMG_NORM_PIXEL
        source = re.sub(r'IMG_NORM_PIXEL\((.+?)\s?,\s?(.+?\)?\.?.*)\)',
                       r'VVSAMPLER_2DBYNORM(\1, _\1_imgRect, _\1_imgSize, _\1_flip, \2)', source)
        
        # IMG_SIZE
        source = re.sub(r'IMG_SIZE\((.+?)\)', r'_\1_imgSize', source)
        
        return source
    
    def _input_to_glsl_type(self, input_type: str) -> str:
        """Convert ISF input type to GLSL uniform type."""
        glsl_type = TYPE_UNIFORM_MAP.get(input_type)
        if not glsl_type:
            raise ShaderCompilationError(f"Unknown input type [{input_type}]")
        return glsl_type
    
    def _make_safe_identifier(self, name: str) -> str:
        """Convert a name to a safe GLSL identifier by prefixing reserved keywords."""
        # GLSL reserved keywords that need to be prefixed
        reserved_keywords = {
            'default', 'uniform', 'varying', 'attribute', 'in', 'out', 'inout',
            'const', 'highp', 'mediump', 'lowp', 'precision', 'invariant',
            'break', 'continue', 'do', 'for', 'while', 'switch', 'case',
            'if', 'else', 'discard', 'return', 'struct', 'void', 'bool',
            'int', 'float', 'double', 'vec2', 'vec3', 'vec4', 'bvec2', 'bvec3',
            'bvec4', 'ivec2', 'ivec3', 'ivec4', 'dvec2', 'dvec3', 'dvec4',
            'mat2', 'mat3', 'mat4', 'mat2x2', 'mat2x3', 'mat2x4', 'mat3x2',
            'mat3x3', 'mat3x4', 'mat4x2', 'mat4x3', 'mat4x4', 'dmat2', 'dmat3',
            'dmat4', 'dmat2x2', 'dmat2x3', 'dmat2x4', 'dmat3x2', 'dmat3x3',
            'dmat3x4', 'dmat4x2', 'dmat4x3', 'dmat4x4', 'sampler1D', 'sampler2D',
            'sampler3D', 'samplerCube', 'sampler1DShadow', 'sampler2DShadow',
            'sampler1DArray', 'sampler2DArray', 'sampler1DArrayShadow',
            'sampler2DArrayShadow', 'isampler1D', 'isampler2D', 'isampler3D',
            'isamplerCube', 'isampler1DArray', 'isampler2DArray', 'usampler1D',
            'usampler2D', 'usampler3D', 'usamplerCube', 'usampler1DArray',
            'usampler2DArray', 'sampler2DRect', 'sampler2DRectShadow',
            'isampler2DRect', 'usampler2DRect', 'samplerBuffer', 'isamplerBuffer',
            'usamplerBuffer', 'sampler2DMS', 'isampler2DMS', 'usampler2DMS',
            'sampler2DMSArray', 'isampler2DMSArray', 'usampler2DMSArray'
        }
        
        if name in reserved_keywords:
            return f"isf_{name}"
        return name
    
    def infer_isf_version(self, metadata: Dict, fragment_shader: str, vertex_shader: str) -> int:
        """Detect ISF version based on metadata and shader content."""
        version = 2  # Default to ISF 2.0
        
        # Check for ISF 1.0 indicators
        if (metadata.get('PERSISTENT_BUFFERS') or
            'vv_FragNormCoord' in fragment_shader or
            'vv_vertShaderInit' in vertex_shader or
            'vv_FragNormCoord' in vertex_shader):
            version = 1
        
        self.isf_version = version
        return version
    
    def infer_filter_type(self, metadata: ISFMetadata) -> str:
        """Infer the type of ISF shader (filter, transition, or generator)."""
        if not metadata.inputs:
            return 'generator'
        
        # Check for filter (has inputImage)
        has_input_image = any(
            input_def.type == 'image' and input_def.name == 'inputImage' 
            for input_def in metadata.inputs
        )
        
        if has_input_image:
            return 'filter'
        
        # Check for transition (has startImage, endImage, and progress)
        has_start_image = any(
            input_def.type == 'image' and input_def.name == 'startImage' 
            for input_def in metadata.inputs
        )
        has_end_image = any(
            input_def.type == 'image' and input_def.name == 'endImage' 
            for input_def in metadata.inputs
        )
        has_progress = any(
            input_def.type == 'float' and input_def.name == 'progress' 
            for input_def in metadata.inputs
        )
        
        if has_start_image and has_end_image and has_progress:
            return 'transition'
        
        return 'generator'


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

        from .types import ISFColor, ISFPoint2D, ISFFloat, ISFInt, ISFBool

        try:
            # Unwrap ISF value types to their underlying Python values
            if isinstance(value, ISFFloat):
                value = value.value
            elif isinstance(value, ISFInt):
                value = value.value
            elif isinstance(value, ISFBool):
                value = value.value
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