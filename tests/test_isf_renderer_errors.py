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
    
    def test_set_inputs_invalid_key_raises(self):
        """Test set_inputs raises RenderingError if a key is not a valid input name."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test set_inputs invalid key",
            "INPUTS": [
                {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]}
            ]
        }*/
        void main() {
            gl_FragColor = color;
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            with pytest.raises(pyvvisf.RenderingError):
                renderer.set_inputs({"not_a_real_input": 1.0})
    
    def test_set_inputs_non_dict_raises(self):
        """Test set_inputs raises TypeError if argument is not a dict."""
        shader_content = """
        /*{"DESCRIPTION": "Test set_inputs non-dict", "INPUTS": []}*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            with pytest.raises(TypeError):
                renderer.set_inputs("not a dict")  # type: ignore 

    def test_shader_with_syntax_error_fails(self, tmp_path):
        """Test that a shader with a syntax error fails with the expected GLSL error and does not generate an image file."""
        
        # Shader with syntax error that should definitely fail GLSL compilation
        failing_shader = """/*{
        "DESCRIPTION": "failing test",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        vec4 col = vec4(0.0);
        col = col + ;  // Syntax error: missing operand
        gl_FragColor = col;
    }"""

        output_path = tmp_path / "test_should_not_exist.png"

        # Shader compilation should fail, raising ShaderCompilationError
        with pytest.raises(ShaderCompilationError) as exc_info:
            with pyvvisf.ISFRenderer(failing_shader) as renderer:
                renderer.save_render(str(output_path), 64, 64)
        
        # Check that the error message indicates a shader compilation failure
        error_msg = str(exc_info.value)
        assert any(msg in error_msg for msg in ["Shader compilation failed", "Failed to compile shader"]), \
            f"Expected shader compilation error, got: {error_msg}"
        # Ensure no file was created
        assert not output_path.exists(), "No image file should be created for invalid shader" 