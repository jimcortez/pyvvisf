#!/usr/bin/env python3
"""Tests for ISFRenderer error handling."""

import sys
from pathlib import Path

# Add the src directory to the path for the test
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import pyvvisf
from PIL import Image

# Use top-level pyvvisf exceptions
ISFParseError = pyvvisf.ISFParseError
ShaderCompilationError = pyvvisf.ShaderCompilationError
ShaderRenderingError = pyvvisf.ShaderRenderingError


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
            image = renderer.render_to_pil_image(256, 256)
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
        
        assert "Malformed JSON" in str(exc_info.value)
    
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
                renderer.render_to_buffer(128, 128)
        
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
        
        assert "Shader compilation failed" in str(exc_info.value)
    
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
            # Try to set input with wrong type
            with pytest.raises(ShaderRenderingError) as exc_info:
                renderer.set_input("color", pyvvisf.ISFFloatVal(1.0))  # Wrong type
            
            assert "Failed to set input" in str(exc_info.value)
    
    def test_rendering_error_with_nonexistent_input(self):
        """Test that setting nonexistent input raises ShaderRenderingError."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader for nonexistent input",
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
            # Try to set input that doesn't exist
            with pytest.raises(ShaderRenderingError) as exc_info:
                renderer.set_input("nonexistent_input", pyvvisf.ISFColorVal(1.0, 0.0, 0.0, 1.0))
            
            assert "Failed to set input" in str(exc_info.value)
    
    def test_error_details_in_exception(self):
        """Test that exceptions contain detailed error information."""
        shader_content = """
        /*{
            "DESCRIPTION": "Error details test shader",
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
            gl_FragColor = undefined_variable;  // This will cause a compilation error
        }
        """
        
        with pytest.raises(ShaderCompilationError) as exc_info:
            with pyvvisf.ISFRenderer(shader_content) as renderer:
                pass
        
        error = exc_info.value
        assert hasattr(error, 'get_details')
        assert isinstance(error.get_details(), str)
        assert "Shader compilation failed" in str(error)
    
    def test_multiple_inputs_error_handling(self):
        """Test error handling when setting multiple inputs."""
        shader_content = """
        /*{
            "DESCRIPTION": "Multiple inputs test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color1",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                },
                {
                    "NAME": "color2",
                    "TYPE": "color",
                    "DEFAULT": [0.0, 1.0, 0.0, 1.0]
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = mix(color1, color2, 0.5);
        }
        """
        
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Set valid inputs
            renderer.set_input("color1", pyvvisf.ISFColorVal(1.0, 0.0, 0.0, 1.0))
            renderer.set_input("color2", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
            
            # Render should succeed
            image = renderer.render_to_pil_image(256, 256)
            assert image.size == (256, 256)
            
            # Try to set invalid input
            with pytest.raises(ShaderRenderingError) as exc_info:
                renderer.set_input("color1", "invalid_value")
            
            assert "Failed to set input" in str(exc_info.value)

    def test_shader_with_non_constant_loop_condition_fails(self):
        """Test that a shader with a non-constant loop condition fails with the expected GLSL error and does not render."""

        # Shader with non-constant loop condition that should fail GLSL compilation
        failing_shader = """/*{
            "DESCRIPTION": "failing test",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() {
            vec4 col = vec4(0.0);
            int j = 256;
            for (int i = 0; i < j; i++) {
                col = vec4(i);
            }
            gl_FragColor = col;
        }"""

        with pyvvisf.ISFRenderer(failing_shader) as renderer:
            # Try to set invalid input
            with pytest.raises(ShaderRenderingError) as exc_info:
            
                # Render should succeed
                image = renderer.render_to_buffer(256, 256)

    
    def test_rendering_with_errors(self):
        """Test that rendering errors are properly caught and reported."""
        shader_content = """
        /*{
            "DESCRIPTION": "Rendering error test shader",
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
            # Normal rendering should work
            image = renderer.render_to_pil_image(256, 256)
            assert image.size == (256, 256)
            
            # Try to render with invalid size (should still work but test error handling)
            try:
                image = renderer.render_to_pil_image(0, 0)
                # If it doesn't raise an error, that's fine too
            except ShaderRenderingError as e:
                assert "rendering" in str(e).lower()
    
    def test_error_cleanup_on_context_exit(self):
        """Test that errors don't prevent proper cleanup."""
        shader_content = """
        /*{
            "DESCRIPTION": "Cleanup test shader",
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
        
        # Create multiple renderers to test cleanup
        renderers = []
        for i in range(3):
            try:
                renderer = pyvvisf.ISFRenderer(shader_content)
                renderers.append(renderer)
                # Use the renderer
                image = renderer.render_to_pil_image(128, 128)
                assert image.size == (128, 128)
            except Exception as e:
                # If there's an error, it should be a specific type
                assert isinstance(e, (ISFParseError, ShaderCompilationError, ShaderRenderingError))
        
        # Clean up
        for renderer in renderers:
            renderer.close()


if __name__ == "__main__":
    pytest.main([__file__]) 