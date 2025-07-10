#!/usr/bin/env python3
"""Tests for ISFRenderer error handling."""

import sys
from pathlib import Path

# Add the src directory to the path for the test
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import pyvvisf
from PIL import Image
import numpy as np

# Use top-level pyvvisf exceptions
ISFParseError = pyvvisf.ISFParseError
ShaderCompilationError = pyvvisf.ShaderCompilationError
ShaderRenderingError = pyvvisf.RenderingError


class TestISFRendererErrors:
    """Test cases for ISFRenderer error handling."""
    
    def test_valid_shader_compiles_successfully(self):
        """Test that a valid shader compiles without errors."""
        shader_content = """
        /*{
            "DESCRIPTION": "Valid test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = color;
        }
        """
        
        # This should not raise any exceptions
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Test that we can render
            buffer = renderer.render(256, 256)
            image = buffer.to_pil_image()
            assert image.size == (256, 256)
            assert image.mode == "RGBA"
    
    def test_malformed_json_raises_parse_error(self):
        """Test that malformed JSON raises ISFParseError."""
        shader_content = """
        /*{
            "DESCRIPTION": "Malformed JSON shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = color;
        }
        """
        
        with pytest.raises(ISFParseError) as exc_info:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                pass
        
        assert "Malformed JSON" in str(exc_info.value)
    
    def test_missing_json_comment_raises_parse_error(self):
        """Test that missing JSON comment block raises ISFParseError."""
        shader_content = """
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
        }
        """
        
        with pytest.raises(ISFParseError) as exc_info:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                pass
        
        assert "No ISF JSON metadata block found" in str(exc_info.value)
    
    def test_syntax_error_raises_compilation_error(self):
        """Test that GLSL syntax errors raise ShaderCompilationError."""
        shader_content = """
        /*{
            "DESCRIPTION": "Syntax error shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = color + ;  // Syntax error: missing operand
        }
        """
        
        with pytest.raises(ShaderCompilationError) as exc_info:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                renderer.render(128, 128)
        
        # Check that the error message indicates a shader compilation failure
        assert "Shader compilation failed" in str(exc_info.value)
    
    def test_undefined_variable_raises_compilation_error(self):
        """Test that undefined variables raise ShaderCompilationError."""
        shader_content = """
        /*{
            "DESCRIPTION": "Undefined variable shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = undefined_variable;  // Undefined variable
        }
        """
        
        with pytest.raises(ShaderCompilationError) as exc_info:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                pass
        
        assert "Shader compilation failed" in str(exc_info.value)
    
    def test_invalid_input_type_raises_compilation_error(self):
        """Test that invalid input types raise ShaderCompilationError."""
        shader_content = """
        /*{
            "DESCRIPTION": "Invalid input type shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "invalid_type",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = color;
        }
        """
        
        with pytest.raises(ShaderCompilationError) as exc_info:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                pass

        assert "Failed to compile shader due to invalid ISF metadata" in str(exc_info.value)
    
    def test_rendering_error_with_invalid_input(self):
        """Test that setting invalid input values raises ShaderRenderingError."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader for input errors",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = color;
        }
        """
        
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Setting input with wrong type should raise an exception
            with pytest.raises(ShaderRenderingError) as exc_info:
                renderer.set_input("color", 1.0)  # Wrong type
            assert "Failed to set input" in str(exc_info.value) 

    def test_isf_standard_variable_and_uniform_injection(self):
        """Test that isf_FragNormCoord and custom uniforms are injected and set correctly."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test ISF variable and uniform injection",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "myColor",
                    "TYPE": "color",
                    "DEFAULT": [0.2, 0.4, 0.6, 1.0]
                }
            ]
        }*/
        out vec4 isf_FragColor;
        void main() {
            isf_FragColor = myColor;
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            renderer.set_input("myColor", (0.8, 0.6, 0.4, 1.0))
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            print("[DEBUG] Output pixel array:", arr)
            print("[DEBUG] Max pixel value:", arr.max())
            assert arr[..., 0].max() > 10, f"Red channel is all zeros: max={arr[..., 0].max()}"

    def test_isf_frag_norm_coord_varying(self):
        """Test that isf_FragNormCoord varying is passed from vertex to fragment shader."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test isf_FragNormCoord varying only",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"]
        }*/
        void main() {
            // Output isf_FragNormCoord as RG, B=0, A=1
            gl_FragColor = vec4(isf_FragNormCoord, 0.0, 1.0);
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            # Print the full pixel array for the top row and left column for debugging
            print("[DEBUG] Top row RGBA:", arr[0, :, :])
            print("[DEBUG] Left column RGBA:", arr[:, 0, :])
            # The top-left pixel should be close to zero in RG, bottom-right should be close to 255
            assert arr[0,0,0] <= 20 and arr[0,0,1] <= 20, f"Top-left pixel not close to zero: {arr[0,0,:2]}"
            assert arr[-1,-1,0] >= 235 and arr[-1,-1,1] >= 235, f"Bottom-right pixel not bright: {arr[-1,-1,:2]}"
            assert arr[0,0,3] == 255 and arr[-1,-1,3] == 255, "Alpha should be 255 everywhere"

    def test_constant_color_pipeline(self):
        """Test that a constant color is rendered, verifying the pipeline works."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test constant color pipeline",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"]
        }*/
        void main() {
            gl_FragColor = vec4(0.1, 0.2, 0.3, 1.0);
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            # All pixels should be close to (26, 51, 76, 255)
            assert np.allclose(arr[..., 0], 26, atol=2), f"Red channel not as expected: {arr[..., 0]}"
            assert np.allclose(arr[..., 1], 51, atol=2), f"Green channel not as expected: {arr[..., 1]}"
            assert np.allclose(arr[..., 2], 76, atol=2), f"Blue channel not as expected: {arr[..., 2]}"
            assert np.all(arr[..., 3] == 255), f"Alpha channel not as expected: {arr[..., 3]}"

    def test_primitive_types_are_accepted_for_inputs(self):
        """Test that primitive Python types are accepted and coerced for shader inputs."""
        shader_content = """
        /*{
            "DESCRIPTION": "Primitive input types test",
            "INPUTS": [
                {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]},
                {"NAME": "point", "TYPE": "point2D", "DEFAULT": [0.5, 0.5]},
                {"NAME": "scale", "TYPE": "float", "DEFAULT": 1.0},
                {"NAME": "count", "TYPE": "long", "DEFAULT": 2},
                {"NAME": "flag", "TYPE": "bool", "DEFAULT": true}
            ]
        }*/
        void main() {
            gl_FragColor = color;
        }
        """
        import pyvvisf
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Accept tuple for color
            renderer.set_input("color", (0.2, 0.4, 0.6, 1.0))
            # Accept list for point2D
            renderer.set_input("point", [0.1, 0.9])
            # Accept float for float
            renderer.set_input("scale", 2.5)
            # Accept int for long
            renderer.set_input("count", 7)
            # Accept bool for bool
            renderer.set_input("flag", False)
            # Accept tuple for point2D
            renderer.set_input("point", (0.3, 0.7))
            # Accept list for color (3 elements, should default alpha to 1.0)
            renderer.set_input("color", [0.1, 0.2, 0.3])
            # Accept int for float (should coerce)
            renderer.set_input("scale", 3)
            # Accept bool for int (should coerce to int 1 or 0)
            renderer.set_input("count", True)
            # Accept int for bool (should coerce to bool)
            renderer.set_input("flag", 0)
            # Render should not raise
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            assert image.size == (8, 8)

    # def test_shader_with_non_constant_loop_condition_fails(self, tmp_path):
    #     """Test that a shader with a non-constant loop condition fails with the expected GLSL error and does not generate an image file."""
        
    #     # Shader with non-constant loop condition that should fail GLSL compilation
    #     failing_shader = """/*{
    #     "DESCRIPTION": "failing test",
    #     "CREDIT": "Test",
    #     "CATEGORIES": ["Test"],
    #     "INPUTS": []
    # }*/
    # void main() {
    #     vec4 col = vec4(0.0);
    #     int j = 256;
    #     for (int i = 0; i < j; i++) {
    #         col = vec4(i);
    #     }
    #     gl_FragColor = col;
    # }"""

    #     output_path = tmp_path / "test_should_not_exist.png"

    #     # Shader compilation should fail, raising ShaderCompilationError
    #     with pytest.raises(ShaderCompilationError) as exc_info:
    #         with pyvvisf.ISFRenderer(failing_shader) as renderer:
    #             renderer.save_render(str(output_path), 64, 64)
        
    #     # Check that the error message indicates a shader compilation failure
    #     assert "Shader compilation failed" in str(exc_info.value)
    #     # Ensure no file was created
    #     assert not output_path.exists(), "No image file should be created for invalid shader" 

def test_debug_isf_frag_norm_coord_output():
    """Debug test: output isf_FragNormCoord as color and print pixel values."""
    shader_content = """
    /*{
        "DESCRIPTION": "Debug isf_FragNormCoord output",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"]
    }*/
    void main() {
        gl_FragColor = vec4(isf_FragNormCoord, 0.0, 1.0);
    }
    """
    import pyvvisf
    import numpy as np
    with pyvvisf.ISFRenderer(shader_content) as renderer:
        buffer = renderer.render(8, 8)
        image = buffer.to_pil_image()
        arr = np.array(image)
        print("[DEBUG] Top row RGBA:", arr[0, :, :])
        print("[DEBUG] Left column RGBA:", arr[:, 0, :])
        # Optionally, assert that the top-left and bottom-right are in expected ranges
        assert arr[0,0,0] <= 20 and arr[0,0,1] <= 20, f"Top-left pixel not close to zero: {arr[0,0,:2]}"
        assert arr[-1,-1,0] >= 235 and arr[-1,-1,1] >= 235, f"Bottom-right pixel not bright: {arr[-1,-1,:2]}"
        assert arr[0,0,3] == 255 and arr[-1,-1,3] == 255, "Alpha should be 255 everywhere" 

def test_minimal_uniform_pipeline():
    """Test ISFRenderer with a minimal pipeline and a single vec4 uniform."""
    vertex_shader = """
    #version 330
    layout(location = 0) in vec2 position;
    void main() {
        gl_Position = vec4(position, 0.0, 1.0);
    }
    """
    fragment_shader = """
    /*{
        "DESCRIPTION": "Minimal ISF input uniform test",
        "INPUTS": [
            {
                "NAME": "myColor",
                "TYPE": "color",
                "DEFAULT": [0.8, 0.6, 0.4, 1.0]
            }
        ]
    }*/
    #version 330
    uniform vec2 RENDERSIZE;
    void main() {
        fragColor = myColor;
    }
    """
    with pyvvisf.ISFRenderer(shader_content=fragment_shader, vertex_shader_content=vertex_shader) as renderer:
        renderer.render(8, 8)
        assert renderer.shader_manager is not None, "shader_manager should be initialized after first render"
        renderer.set_input("myColor", (0.8, 0.6, 0.4, 1.0))
        buffer = renderer.render(8, 8)
        arr = np.array(buffer.to_pil_image())
        print("[DEBUG] Minimal ISF input uniform output:", arr)
        print("[DEBUG] Max pixel value:", arr.max())
        assert arr[..., 0].max() > 200, f"Red channel is too low: max={arr[..., 0].max()}"
        assert arr[..., 1].max() > 140, f"Green channel is too low: max={arr[..., 1].max()}"
        assert arr[..., 2].max() > 90, f"Blue channel is too low: max={arr[..., 2].max()}"
        assert arr[..., 3].min() == 255, f"Alpha channel is not 255: min={arr[..., 3].min()}" 