"""OpenGL shader compilation and program linking."""

import logging
from typing import Any

from OpenGL import GL

from .errors import ShaderCompilationError

logger = logging.getLogger(__name__)


class ShaderCompiler:
    """Handles OpenGL shader compilation and program creation."""

    def __init__(self):
        self.program: int | None = None
        self.vertex_shader: int | None = None
        self.fragment_shader: int | None = None
        self.uniform_locations: dict[str, int] = {}

    def compile_shader(self, source: str, shader_type: int) -> int:
        """Compile a GLSL shader and check for errors."""
        shader = GL.glCreateShader(shader_type)

        if shader is None or shader == 0:
            raise ShaderCompilationError(
                f"Failed to create shader object (type {self._shader_type_name(shader_type)}).",
                shader_source=source,
                shader_type=self._shader_type_name(shader_type),
            )

        GL.glShaderSource(shader, source)
        GL.glCompileShader(shader)

        if not GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS):
            error_log = GL.glGetShaderInfoLog(shader).decode("utf-8")
            GL.glDeleteShader(shader)
            raise ShaderCompilationError(
                f"Shader compilation failed:\n{error_log}",
                shader_source=source,
                shader_type=self._shader_type_name(shader_type),
            )

        return int(shader)

    def create_program(
        self, vertex_source: str, fragment_source: str, expected_uniforms: list[str] | None = None
    ) -> int:
        """Create and link a shader program."""
        try:
            self.vertex_shader = self.compile_shader(vertex_source, GL.GL_VERTEX_SHADER)
            self.fragment_shader = self.compile_shader(fragment_source, GL.GL_FRAGMENT_SHADER)

            self.program = GL.glCreateProgram()

            if self.program is None or self.program == 0:
                raise ShaderCompilationError("Failed to create shader program object.")

            GL.glAttachShader(self.program, self.vertex_shader)
            GL.glAttachShader(self.program, self.fragment_shader)
            GL.glLinkProgram(self.program)

            if not GL.glGetProgramiv(self.program, GL.GL_LINK_STATUS):
                error_log = GL.glGetProgramInfoLog(self.program).decode("utf-8")
                raise ShaderCompilationError(f"Shader program linking failed:\n{error_log}")

            GL.glUseProgram(self.program)
            self._cache_uniform_locations(expected_uniforms or [])

            return int(self.program)

        except Exception:
            self.cleanup()
            raise

    def _cache_uniform_locations(self, expected_uniforms: list[str]):
        """Cache uniform locations for performance."""
        self.uniform_locations = {}

        num_uniforms = GL.glGetProgramiv(self.program, GL.GL_ACTIVE_UNIFORMS)
        for i in range(num_uniforms):
            name, _size, _uniform_type = GL.glGetActiveUniform(self.program, i)
            if hasattr(name, "decode"):
                name = name.decode("utf-8")
            elif hasattr(name, "tobytes"):
                name = name.tobytes().decode("utf-8").rstrip("\x00")
            else:
                name = str(name)
            location = GL.glGetUniformLocation(self.program, name)
            self.uniform_locations[name] = location

        standard_uniforms = ["PASSINDEX", "RENDERSIZE", "TIME", "TIMEDELTA", "DATE", "FRAMEINDEX"]
        all_expected = standard_uniforms + expected_uniforms

        for name in all_expected:
            if name not in self.uniform_locations:
                location = GL.glGetUniformLocation(self.program, name)
                self.uniform_locations[name] = location

    def set_uniform(self, name: str, value: Any):
        """Set the value of a uniform variable."""
        location = self.uniform_locations.get(name, -1)
        if location == -1:
            return

        from .types import ISFBool, ISFColor, ISFFloat, ISFInt, ISFPoint2D

        if isinstance(value, (ISFFloat, ISFInt, ISFBool)):
            value = value.value
        if isinstance(value, bool):
            GL.glUniform1i(location, 1 if value else 0)
        elif isinstance(value, int):
            GL.glUniform1i(location, value)
        elif isinstance(value, float):
            GL.glUniform1f(location, value)
        elif isinstance(value, (list, tuple)):
            if len(value) == 2:
                GL.glUniform2f(location, value[0], value[1])
            elif len(value) == 3:
                GL.glUniform3f(location, value[0], value[1], value[2])
            elif len(value) == 4:
                GL.glUniform4f(location, value[0], value[1], value[2], value[3])
        elif isinstance(value, ISFColor):
            GL.glUniform4f(location, value.r, value.g, value.b, value.a)
        elif isinstance(value, ISFPoint2D):
            GL.glUniform2f(location, value.x, value.y)
        else:
            logger.warning(f"Unknown uniform type: {type(value)}")

    def use(self):
        """Activate this shader program."""
        if self.program:
            GL.glUseProgram(self.program)

    def cleanup(self):
        """Delete all OpenGL resources."""
        if self.program:
            GL.glDeleteProgram(self.program)
            self.program = None
        if self.vertex_shader:
            GL.glDeleteShader(self.vertex_shader)
            self.vertex_shader = None
        if self.fragment_shader:
            GL.glDeleteShader(self.fragment_shader)
            self.fragment_shader = None
        self.uniform_locations.clear()

    def _shader_type_name(self, shader_type: int) -> str:
        """Get shader type name for error messages."""
        return {
            GL.GL_VERTEX_SHADER: "vertex",
            GL.GL_FRAGMENT_SHADER: "fragment",
            GL.GL_GEOMETRY_SHADER: "geometry",
            GL.GL_TESS_CONTROL_SHADER: "tessellation control",
            GL.GL_TESS_EVALUATION_SHADER: "tessellation evaluation",
        }.get(shader_type, f"unknown ({shader_type})")
