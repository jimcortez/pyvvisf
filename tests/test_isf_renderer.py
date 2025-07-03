#!/usr/bin/env python3
"""Tests for the ISFRenderer convenience API."""

import sys
from pathlib import Path

# Add the src directory to the path for the test
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import pyvvisf
from PIL import Image


class TestISFRenderer:
    """Test cases for the ISFRenderer convenience API."""
    
    def test_basic_initialization(self):
        """Test basic ISFRenderer initialization."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
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
            assert renderer is not None
            assert renderer.is_valid()
        with pyvvisf.ISFRenderer(shader_content) as renderer2:
            assert renderer2.is_valid()
    
    def test_set_input(self):
        """Test setting a single input."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
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
            renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
            inputs = renderer.get_current_inputs()
            assert 'color' in inputs
    
    def test_set_inputs(self):
        """Test setting multiple inputs at once."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                },
                {
                    "NAME": "intensity",
                    "TYPE": "float",
                    "DEFAULT": 1.0
                }
            ]
        }*/
        void main() {
            gl_FragColor = color * intensity;
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            renderer.set_inputs({
                "color": pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0),
                "intensity": pyvvisf.ISFFloatVal(0.5)
            })
            inputs = renderer.get_current_inputs()
            assert 'color' in inputs
            assert 'intensity' in inputs
    
    def test_render_to_pil_image(self):
        """Test rendering to PIL Image."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
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
            renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
            image = renderer.render_to_pil_image(100, 100)
            assert isinstance(image, Image.Image)
            assert image.size == (100, 100)
    
    def test_render_to_buffer(self):
        """Test rendering to GLBuffer."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
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
            renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
            buffer = renderer.render_to_buffer(100, 100)
            assert isinstance(buffer, pyvvisf.GLBuffer)
            assert buffer.size.width == 100
            assert buffer.size.height == 100
    
    def test_error_handling_no_shader(self):
        """Test error handling when context not entered."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
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
        renderer = pyvvisf.ISFRenderer(shader_content)
        with pytest.raises(RuntimeError, match="No shader loaded"):
            renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
        with pytest.raises(RuntimeError, match="No shader loaded"):
            renderer.render_to_pil_image(100, 100)
    
    def test_error_handling_outside_context(self):
        """Test error handling when used outside context manager."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
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
        renderer = pyvvisf.ISFRenderer(shader_content)
        with pytest.raises(RuntimeError, match="No shader loaded"):
            renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))


if __name__ == "__main__":
    pytest.main([__file__]) 