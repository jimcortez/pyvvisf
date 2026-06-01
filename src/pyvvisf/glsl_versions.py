"""Runtime detection of supported GLSL versions on the active OpenGL context."""

import logging

from OpenGL import GL

from .errors import ShaderCompilationError

logger = logging.getLogger(__name__)

# Versions to probe, ordered ascending. 110-150 use the legacy
# attribute/varying syntax; 330+ use the modern in/out + layout-location form.
CANDIDATE_VERSIONS = [
    "110", "120", "130", "140", "150",
    "330", "400", "410", "420", "430", "440", "450", "460",
]

# Conservative fallback when the GL context refuses to report version info.
_FALLBACK_VERSIONS = ["330", "400", "410", "420", "430", "440", "450"]


def get_supported_glsl_versions() -> list[str]:
    """Return GLSL versions supported by the current GL context.

    Each candidate version is verified by actually compiling a small probe
    shader, so the returned list reflects what the driver will actually accept.
    """
    supported_versions: list[str] = []
    try:
        gl_version_str = GL.glGetString(GL.GL_VERSION)
        glsl_version_str = GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION)
        if gl_version_str is None or glsl_version_str is None:
            logger.warning("Could not get OpenGL version information")
            return list(_FALLBACK_VERSIONS)
        gl_version = gl_version_str.decode("utf-8")
        glsl_version = glsl_version_str.decode("utf-8")
        logger.info(f"OpenGL Version: {gl_version}")
        logger.info(f"GLSL Version: {glsl_version}")
        for version in CANDIDATE_VERSIONS:
            ok, err = _test_glsl_version_support(version)
            if ok:
                supported_versions.append(version)
            else:
                logger.info(f"GLSL version {version} not supported: {err}")
        return supported_versions
    except Exception as e:
        logger.warning(f"Could not detect GLSL versions: {e}")
        return list(_FALLBACK_VERSIONS)


def _test_glsl_version_support(version: str) -> tuple[bool, str | None]:
    """Probe a single GLSL version by compiling a minimal shader pair.

    Returns ``(supported, error_message)``. ``error_message`` is ``None`` on
    success or a string describing the compile failure.
    """
    # Imported lazily to avoid an import cycle: shader_compiler imports nothing
    # from this module, but ShaderCompiler is the load-bearing dependency here.
    from .shader_compiler import ShaderCompiler

    try:
        if version == "110":
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
            return True, None
        except ShaderCompilationError as e:
            return False, str(e)
        finally:
            compiler.cleanup()
    except Exception as e:
        return False, str(e)
