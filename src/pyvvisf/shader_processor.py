"""ISF-specific shader source processing.

Translates raw ISF shader fragments into complete GLSL 330 vertex/fragment
shaders by combining them with the ISF skeletons and replacing ISF macros
(`IMG_PIXEL`, `IMG_THIS_PIXEL`, etc.) with their GLSL equivalents.
"""

import re

from .errors import ShaderCompilationError
from .parser import ISFMetadata
from .shader_skeletons import (
    ISF_FRAGMENT_SHADER_SKELETON,
    ISF_VERTEX_SHADER_DEFAULT,
    ISF_VERTEX_SHADER_SKELETON,
    TYPE_UNIFORM_MAP,
)

# GLSL reserved keywords that must not collide with ISF input names.
_GLSL_RESERVED_KEYWORDS = frozenset(
    {
        "default",
        "uniform",
        "varying",
        "attribute",
        "in",
        "out",
        "inout",
        "const",
        "highp",
        "mediump",
        "lowp",
        "precision",
        "invariant",
        "break",
        "continue",
        "do",
        "for",
        "while",
        "switch",
        "case",
        "if",
        "else",
        "discard",
        "return",
        "struct",
        "void",
        "bool",
        "int",
        "float",
        "double",
        "vec2",
        "vec3",
        "vec4",
        "bvec2",
        "bvec3",
        "bvec4",
        "ivec2",
        "ivec3",
        "ivec4",
        "dvec2",
        "dvec3",
        "dvec4",
        "mat2",
        "mat3",
        "mat4",
        "mat2x2",
        "mat2x3",
        "mat2x4",
        "mat3x2",
        "mat3x3",
        "mat3x4",
        "mat4x2",
        "mat4x3",
        "mat4x4",
        "dmat2",
        "dmat3",
        "dmat4",
        "dmat2x2",
        "dmat2x3",
        "dmat2x4",
        "dmat3x2",
        "dmat3x3",
        "dmat3x4",
        "dmat4x2",
        "dmat4x3",
        "dmat4x4",
        "sampler1D",
        "sampler2D",
        "sampler3D",
        "samplerCube",
        "sampler1DShadow",
        "sampler2DShadow",
        "sampler1DArray",
        "sampler2DArray",
        "sampler1DArrayShadow",
        "sampler2DArrayShadow",
        "isampler1D",
        "isampler2D",
        "isampler3D",
        "isamplerCube",
        "isampler1DArray",
        "isampler2DArray",
        "usampler1D",
        "usampler2D",
        "usampler3D",
        "usamplerCube",
        "usampler1DArray",
        "usampler2DArray",
        "sampler2DRect",
        "sampler2DRectShadow",
        "isampler2DRect",
        "usampler2DRect",
        "samplerBuffer",
        "isamplerBuffer",
        "usamplerBuffer",
        "sampler2DMS",
        "isampler2DMS",
        "usampler2DMS",
        "sampler2DMSArray",
        "isampler2DMSArray",
        "usampler2DMSArray",
    }
)


class ISFShaderProcessor:
    """ISF-specific shader processing based on the JavaScript reference implementation."""

    def __init__(self):
        self.uniform_defs = ""
        self.isf_version = 2  # Default to ISF 2.0

    def process_fragment_shader(self, raw_fragment_shader: str, metadata: ISFMetadata) -> str:
        """Process fragment shader using ISF skeleton and special function replacement."""
        self._generate_uniforms(metadata)
        main_code = self._replace_special_functions(raw_fragment_shader)

        return ISF_FRAGMENT_SHADER_SKELETON.replace("[[uniforms]]", self.uniform_defs).replace(
            "[[main]]", main_code
        )

    def process_vertex_shader(self, raw_vertex_shader: str, metadata: ISFMetadata) -> str:
        """Process vertex shader using ISF skeleton."""
        self._generate_vertex_uniforms(metadata)
        function_lines = self._generate_tex_coord_functions(metadata)

        return (
            ISF_VERTEX_SHADER_SKELETON.replace("[[uniforms]]", self.uniform_defs)
            .replace("[[main]]", raw_vertex_shader or ISF_VERTEX_SHADER_DEFAULT)
            .replace("[[functions]]", function_lines)
        )

    def _generate_uniforms(self, metadata: ISFMetadata):
        """Generate uniform declarations for all inputs and passes."""
        self.uniform_defs = ""

        if metadata.inputs:
            for input_def in metadata.inputs:
                self._add_uniform(input_def)

        if metadata.passes:
            for pass_def in metadata.passes:
                if pass_def.target:
                    self._add_uniform({"name": pass_def.target, "type": "image"})

        if metadata.imports:
            for import_name in metadata.imports:
                self._add_uniform({"name": import_name, "type": "image"})

    def _generate_vertex_uniforms(self, metadata: ISFMetadata):
        """Generate uniform declarations for vertex shader."""
        self.uniform_defs = ""

        if metadata.inputs:
            for input_def in metadata.inputs:
                self._add_vertex_uniform(input_def)

        if metadata.passes:
            for pass_def in metadata.passes:
                if pass_def.target:
                    self._add_vertex_uniform({"name": pass_def.target, "type": "image"})

        if metadata.imports:
            for import_name in metadata.imports:
                self._add_vertex_uniform({"name": import_name, "type": "image"})

    def _add_uniform(self, input_def):
        """Add a uniform declaration."""
        if hasattr(input_def, "type"):
            input_type = input_def.type
            input_name = input_def.name
        else:
            input_type = input_def.get("type", "float")
            input_name = input_def.get("name", "unknown")

        safe_name = self._make_safe_identifier(input_name)
        glsl_type = self._input_to_glsl_type(input_type)
        self.uniform_defs += f"uniform {glsl_type} {safe_name};\n"

        if input_type == "image":
            self.uniform_defs += self._sampler_uniforms(safe_name)

    def _add_vertex_uniform(self, input_def):
        """Add a uniform declaration for vertex shader."""
        if hasattr(input_def, "type"):
            input_type = input_def.type
            input_name = input_def.name
        else:
            input_type = input_def.get("type", "float")
            input_name = input_def.get("name", "unknown")

        safe_name = self._make_safe_identifier(input_name)
        glsl_type = self._input_to_glsl_type(input_type)
        self.uniform_defs += f"uniform {glsl_type} {safe_name};\n"

        if input_type == "image":
            self.uniform_defs += self._vertex_sampler_uniforms(safe_name)

    def _sampler_uniforms(self, name: str) -> str:
        """Generate sampler-specific uniforms for image inputs."""
        return (
            f"uniform vec4 _{name}_imgRect;\n"
            f"uniform vec2 _{name}_imgSize;\n"
            f"uniform bool _{name}_flip;\n"
            f"in vec2 _{name}_normTexCoord;\n"
            f"in vec2 _{name}_texCoord;\n\n"
        )

    def _vertex_sampler_uniforms(self, name: str) -> str:
        """Generate sampler-specific uniforms for vertex shader (out for tex coordinates)."""
        return (
            f"uniform vec4 _{name}_imgRect;\n"
            f"uniform vec2 _{name}_imgSize;\n"
            f"uniform bool _{name}_flip;\n"
            f"out vec2 _{name}_normTexCoord;\n"
            f"out vec2 _{name}_texCoord;\n\n"
        )

    def _generate_tex_coord_functions(self, metadata: ISFMetadata) -> str:
        """Generate texture coordinate functions for image inputs."""
        if not metadata.inputs:
            return ""

        function_lines = [
            self._tex_coord_function(input_def.name)
            for input_def in metadata.inputs
            if input_def.type == "image"
        ]
        return "\n".join(function_lines)

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
        source = re.sub(r"IMG_THIS_PIXEL\((.+?)\)", r"texture(\1, isf_FragNormCoord)", source)
        source = re.sub(r"IMG_THIS_NORM_PIXEL\((.+?)\)", r"texture(\1, isf_FragNormCoord)", source)
        source = re.sub(
            r"IMG_PIXEL\((.+?)\s?,\s?(.+?\)?\.?.*)\)", r"texture(\1, (\2) / RENDERSIZE)", source
        )
        source = re.sub(
            r"IMG_NORM_PIXEL\((.+?)\s?,\s?(.+?\)?\.?.*)\)",
            r"VVSAMPLER_2DBYNORM(\1, _\1_imgRect, _\1_imgSize, _\1_flip, \2)",
            source,
        )
        source = re.sub(r"IMG_SIZE\((.+?)\)", r"_\1_imgSize", source)
        return source

    def _input_to_glsl_type(self, input_type: str) -> str:
        """Convert ISF input type to GLSL uniform type."""
        glsl_type = TYPE_UNIFORM_MAP.get(input_type)
        if not glsl_type:
            raise ShaderCompilationError(f"Unknown input type [{input_type}]")
        return glsl_type

    def _make_safe_identifier(self, name: str) -> str:
        """Convert a name to a safe GLSL identifier by prefixing reserved keywords."""
        if name in _GLSL_RESERVED_KEYWORDS:
            return f"isf_{name}"
        return name

    def infer_isf_version(self, metadata: dict, fragment_shader: str, vertex_shader: str) -> int:
        """Detect ISF version based on metadata and shader content."""
        version = 2
        if (
            metadata.get("PERSISTENT_BUFFERS")
            or "vv_FragNormCoord" in fragment_shader
            or "vv_vertShaderInit" in vertex_shader
            or "vv_FragNormCoord" in vertex_shader
        ):
            version = 1
        self.isf_version = version
        return version

    def infer_filter_type(self, metadata: ISFMetadata) -> str:
        """Infer the type of ISF shader (filter, transition, or generator)."""
        if not metadata.inputs:
            return "generator"

        has_input_image = any(
            input_def.type == "image" and input_def.name == "inputImage"
            for input_def in metadata.inputs
        )
        if has_input_image:
            return "filter"

        has_start_image = any(
            input_def.type == "image" and input_def.name == "startImage"
            for input_def in metadata.inputs
        )
        has_end_image = any(
            input_def.type == "image" and input_def.name == "endImage"
            for input_def in metadata.inputs
        )
        has_progress = any(
            input_def.type == "float" and input_def.name == "progress"
            for input_def in metadata.inputs
        )
        if has_start_image and has_end_image and has_progress:
            return "transition"

        return "generator"
