#!/usr/bin/env python3
"""Tests for ISFRenderer normal (non-error) cases."""

import sys
from pathlib import Path

# Add the src directory to the path for the test
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import pyvvisf
from PIL import Image
import numpy as np

class TestISFRenderer:
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
        void main() {
            gl_FragColor = myColor;
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            renderer.set_input("myColor", (0.8, 0.6, 0.4, 1.0))
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
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

    def test_set_inputs_multiple_valid(self):
        """Test set_inputs sets multiple valid inputs at once."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test set_inputs",
            "INPUTS": [
                {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]},
                {"NAME": "intensity", "TYPE": "float", "DEFAULT": 1.0, "MIN": 0.0, "MAX": 2.0}
            ]
        }*/
        void main() {
            gl_FragColor = color * vec4(intensity, intensity, intensity, 1.0);
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            renderer.set_inputs({
                "color": [0.0, 1.0, 0.0, 1.0],
                "intensity": 0.5
            })
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            assert arr.shape == (8, 8, 4)

    def test_set_inputs_equivalent_to_set_input_loop(self):
        """Test set_inputs is equivalent to calling set_input in a loop."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test set_inputs equivalence",
            "INPUTS": [
                {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]},
                {"NAME": "intensity", "TYPE": "float", "DEFAULT": 1.0}
            ]
        }*/
        void main() {
            gl_FragColor = color * vec4(intensity, intensity, intensity, 1.0);
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer1, pyvvisf.ISFRenderer(shader_content) as renderer2:
            # Use set_inputs
            renderer1.set_inputs({"color": [0.0, 0.0, 1.0, 1.0], "intensity": 0.7})
            arr1 = np.array(renderer1.render(8, 8).to_pil_image())
            # Use set_input in a loop
            renderer2.set_input("color", [0.0, 0.0, 1.0, 1.0])
            renderer2.set_input("intensity", 0.7)
            arr2 = np.array(renderer2.render(8, 8).to_pil_image())
            assert np.allclose(arr1, arr2)

    def test_shader_with_color_input_renders_default_red(self):
        """Test that a shader with a color input and default renders red if no input is set."""
        shader_content = """
        /*{
            "DESCRIPTION": "Every pixel is the selected color.",
            "CREDIT": "pyvvisf example",
            "ISFVSN": "2.0",
            "CATEGORIES": ["Generator"],
            "INPUTS": [
                {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]}
            ]
        }*/
        void main() {
            gl_FragColor = color;
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            # All pixels should be close to (255, 0, 0, 255)
            assert np.allclose(arr[..., 0], 255, atol=2), f"Red channel not as expected: {arr[..., 0]}"
            assert np.all(arr[..., 1] <= 2), f"Green channel not as expected: {arr[..., 1]}"
            assert np.all(arr[..., 2] <= 2), f"Blue channel not as expected: {arr[..., 2]}"
            assert np.all(arr[..., 3] == 255), f"Alpha channel not as expected: {arr[..., 3]}"

    def test_shader_with_color_input_renders_default_red_change_blue(self):
        """Test that a shader with a color input and default renders red if no input is set, and green if changed."""
        shader_content = """
        /*{
            "DESCRIPTION": "Every pixel is the selected color.",
            "CREDIT": "pyvvisf example",
            "ISFVSN": "2.0",
            "CATEGORIES": ["Generator"],
            "INPUTS": [
                {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]}
            ]
        }*/
        void main() {
            gl_FragColor = color;
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            # All pixels should be close to (255, 0, 0, 255)
            assert np.allclose(arr[..., 0], 255, atol=2), f"Red channel not as expected: {arr[..., 0]}"
            assert np.all(arr[..., 1] <= 2), f"Green channel not as expected: {arr[..., 1]}"
            assert np.all(arr[..., 2] <= 2), f"Blue channel not as expected: {arr[..., 2]}"
            assert np.all(arr[..., 3] == 255), f"Alpha channel not as expected: {arr[..., 3]}"

            renderer.set_input("color", (0.0, 1.0, 0.0, 1.0))
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            # All pixels should be close to (0, 255, 0, 255)
            assert np.allclose(arr[..., 0], 0, atol=2), f"Red channel not as expected: {arr[..., 0]}"
            assert np.allclose(arr[..., 1], 255, atol=2), f"Green channel not as expected: {arr[..., 1]}"
            assert np.all(arr[..., 2] <= 0), f"Blue channel not as expected: {arr[..., 2]}"
            assert np.all(arr[..., 3] == 255), f"Alpha channel not as expected: {arr[..., 3]}" 

    def test_multi_pass_shader(self):
        """Test that a simple multi-pass ISF shader can be loaded and rendered (should fail if not implemented)."""
        import pytest
        shader_content = """
        /*{
            "DESCRIPTION": "Simple multi-pass test shader",
            "CREDIT": "Test",
            "ISFVSN": "2.0",
            "PASSES": [
                {"TARGET": "bufferA", "WIDTH": 8, "HEIGHT": 8},
                {"TARGET": "default"}
            ]
        }*/
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 1.0, 1.0); // Magenta for test
        }
        """
        # Mark as expected to fail until multi-pass is implemented
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            assert image.size == (8, 8)
            assert image.mode == "RGBA" 

    def test_multi_pass_red_to_blue(self):
        """Test a multi-pass shader: first pass red, second swaps red/blue, output should be blue."""
        import pytest
        shader_content = """
        /*{
            "DESCRIPTION": "Multi-pass: red then swap red/blue to blue",
            "ISFVSN": "2.0",
            "PASSES": [
                {"TARGET": "redBuffer"},
                {}
            ]
        }*/
        void main() {
            if (PASSINDEX == 0) {
                gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); // Red
            } else if (PASSINDEX == 1) {
                vec4 c = IMG_THIS_NORM_PIXEL(redBuffer);
                gl_FragColor = vec4(c.b, c.g, c.r, c.a); // Swap R/B
            }
        }
        """
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            buffer = renderer.render(8, 8)
            image = buffer.to_pil_image()
            arr = np.array(image)
            # All pixels should be blue (0, 0, 255, 255)
            assert np.allclose(arr[..., 0], 0, atol=2), f"Red channel not as expected: {arr[..., 0]}"
            assert np.allclose(arr[..., 1], 0, atol=2), f"Green channel not as expected: {arr[..., 1]}"
            assert np.allclose(arr[..., 2], 255, atol=2), f"Blue channel not as expected: {arr[..., 2]}"
            assert np.all(arr[..., 3] == 255), f"Alpha channel not as expected: {arr[..., 3]}" 