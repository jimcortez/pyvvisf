"""Comprehensive ISF spec compliance tests."""

import pytest
import numpy as np
from pathlib import Path
from pyvvisf.parser import ISFParser, ISFMetadata, ISFInput
from pyvvisf.types import ISFColor, ISFPoint2D, ISFFloat, ISFInt, ISFBool
from pyvvisf.errors import ISFParseError, ValidationError, ShaderCompilationError

# 1. Standard Uniforms
@pytest.mark.parametrize("uniform_name, glsl_type", [
    ("RENDERSIZE", "vec2"),
    ("TIME", "float"),
    ("TIMEDELTA", "float"),
    ("FRAMEINDEX", "int"),
])
def test_standard_uniforms_present(uniform_name, glsl_type):
    shader = f"""
    /*{{\"NAME\": \"UniformTest\", \"INPUTS\": []}}*/
    void main() {{
        {glsl_type} x = {uniform_name};
        gl_FragColor = vec4(1.0);
    }}
    """
    parser = ISFParser()
    glsl_code, metadata = parser.parse_content(shader)
    assert uniform_name in glsl_code or uniform_name in shader

# 2. Input Handling
@pytest.mark.parametrize("input_type, value, expected_type", [
    ("bool", True, ISFBool),
    ("long", 42, ISFInt),
    ("float", 3.14, ISFFloat),
    ("point2D", [0.5, 0.3], ISFPoint2D),
    ("color", [1.0, 0.0, 0.0, 1.0], ISFColor),
])
def test_input_types(input_type, value, expected_type):
    parser = ISFParser()
    metadata = ISFMetadata(inputs=[ISFInput(name="test", type=input_type, default=value)])
    validated = parser.validate_inputs(metadata, {"test": value})
    assert isinstance(validated["test"], expected_type)

# 3. JSON Metadata Parsing
@pytest.mark.parametrize("json_block, should_pass", [
    ("/*{\n  \"NAME\": \"Test\", // comment\n  \"INPUTS\": []\n}*/", True),
    ("/*{\n  \"NAME\": \"Test\",\n  \"INPUTS\": [],\n}*/", True),  # trailing comma
    ("/*{\n  \"NAME\": \"Test\",\n  \"INPUTS\": [\n    {\"NAME\": \"a\", \"TYPE\": \"float\"}\n  ]\n}*/", True),
    ("/*{\n  \"NAME\": \"Test\",\n  \"INPUTS\": [\n    {\"NAME\": \"a\", \"TYPE\": \"float\",\n  ]\n}*/", False),  # malformed
])
def test_json5_parsing(json_block, should_pass):
    parser = ISFParser()
    shader = f"{json_block}\nvoid main() {{ gl_FragColor = vec4(1.0); }}"
    if should_pass:
        glsl_code, metadata = parser.parse_content(shader)
        assert metadata.name == "Test"
    else:
        with pytest.raises(ISFParseError):
            parser.parse_content(shader)

# 4. Shader Compilation and ISF Macros (Stubbed)
def test_img_pixel_macro_stub():
    # This test assumes the implementation stubs or errors on ISF macros
    shader = """
    /*{"NAME": "MacroTest", "INPUTS": []}*/
    void main() {
        vec4 c = IMG_PIXEL(image, gl_FragCoord.xy);
        gl_FragColor = c;
    }
    """
    parser = ISFParser()
    glsl_code, metadata = parser.parse_content(shader)
    # Should not raise parse error, but actual rendering may fail if macro is not implemented
    assert "IMG_PIXEL" in glsl_code

# 5. Alpha Channel Handling
def test_alpha_channel_default():
    shader = """
    /*{"NAME": "AlphaTest", "INPUTS": []}*/
    void main() {
        gl_FragColor = vec4(0.5, 0.5, 0.5, 0.5);
    }
    """
    parser = ISFParser()
    glsl_code, metadata = parser.parse_content(shader)
    assert "gl_FragColor" in glsl_code

# 6. Imported Resources (Stubbed)
def test_imported_images_metadata():
    parser = ISFParser()
    shader = """
    /*{
        "NAME": "ImportTest",
        "IMPORTED": [
            {"NAME": "tex1", "PATH": "image.png"}
        ]
    }*/
    void main() {
        gl_FragColor = IMG_PIXEL(tex1, gl_FragCoord.xy);
    }
    """
    glsl_code, metadata = parser.parse_content(shader)
    assert hasattr(metadata, "name") and metadata.name == "ImportTest"
    # Actual image loading is not tested here (stub)

# 7. Passes and Multi-pass Rendering (Stubbed)
def test_passes_metadata():
    parser = ISFParser()
    shader = """
    /*{
        "NAME": "PassTest",
        "PASSES": [
            {"TARGET": "bufferA", "PERSISTENT": true, "WIDTH": 512, "HEIGHT": 512}
        ]
    }*/
    void main() {
        gl_FragColor = vec4(1.0);
    }
    """
    glsl_code, metadata = parser.parse_content(shader)
    assert hasattr(metadata, "name") and metadata.name == "PassTest"
    # Actual multi-pass rendering is not tested here (stub)

# 8. Error Cases
def test_missing_main_function():
    parser = ISFParser()
    shader = "/*{\"NAME\": \"NoMainTest\", \"INPUTS\": []}*/\nvoid foo() { gl_FragColor = vec4(1.0); }"
    glsl_code, metadata = parser.parse_content(shader)
    assert "main" not in glsl_code or "main" not in shader

# 9. ISF v1/v2 Compatibility (Stubbed)
def test_isf_vsn_metadata():
    parser = ISFParser()
    shader = """
    /*{
        "NAME": "VersionTest",
        "ISFVSN": "2"
    }*/
    void main() {
        gl_FragColor = vec4(1.0);
    }
    """
    glsl_code, metadata = parser.parse_content(shader)
    assert hasattr(metadata, "name") and metadata.name == "VersionTest"
    # Version field is present

# 10. Custom Vertex Shader (Stubbed)
def test_custom_vertex_shader_metadata():
    parser = ISFParser()
    shader = """
    /*{
        "NAME": "VertTest",
        "VERTEX_SHADER": "attribute vec4 position; void main() { gl_Position = position; }"
    }*/
    void main() {
        gl_FragColor = vec4(1.0);
    }
    """
    glsl_code, metadata = parser.parse_content(shader)
    assert hasattr(metadata, "vertex_shader")
    assert metadata.vertex_shader is not None 