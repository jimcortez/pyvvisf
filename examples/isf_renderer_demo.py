#!/usr/bin/env python3
"""Demonstration of the ISFRenderer convenience API."""

import sys
from pathlib import Path

# Add the src directory to the path for the example
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import pyvvisf
    from PIL import Image
except ImportError as e:
    print(f"Error importing pyvvisf: {e}")
    print("Please ensure pyvvisf is built and installed correctly.")
    sys.exit(1)


def main():
    """Main demonstration function."""
    print("pyvvisf ISFRenderer Demo")
    print("=" * 40)
    
    # Define a simple shader
    shader_content = """
    /*{
        "DESCRIPTION": "Simple color shader with intensity control",
        "CREDIT": "pyvvisf example",
        "CATEGORIES": ["Color Effect"],
        "INPUTS": [
            {
                "NAME": "color",
                "TYPE": "color",
                "DEFAULT": [1.0, 0.0, 0.0, 1.0]
            },
            {
                "NAME": "intensity",
                "TYPE": "float",
                "DEFAULT": 1.0,
                "MIN": 0.0,
                "MAX": 2.0
            }
        ]
    }*/
    
    void main() {
        gl_FragColor = color * intensity;
    }
    """
    
    # Use the ISFRenderer convenience API
    with pyvvisf.ISFRenderer(shader_content) as renderer:
        print("✓ ISFRenderer initialized")
        
        # Set initial input (green)
        renderer.set_input("color", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))
        print("✓ Set color input to green")
        
        # Get shader information
        info = renderer.get_shader_info()
        if info:
            print(f"Shader: {info['name']}")
            print(f"Description: {info['description']}")
            print(f"Inputs: {info['inputs']}")
        
        # Render green image
        image = renderer.render_to_pil_image(800, 600)
        output_path = Path(__file__).parent / "output_green.png"
        image.save(output_path)
        print(f"✓ Saved green image to: {output_path}")
        
        # Change color to red
        renderer.set_input("color", pyvvisf.ISFColorVal(1.0, 0.0, 0.0, 1.0))
        image = renderer.render_to_pil_image(800, 600)
        output_path = Path(__file__).parent / "output_red.png"
        image.save(output_path)
        print(f"✓ Saved red image to: {output_path}")
        
        # Set multiple inputs at once
        renderer.set_inputs({
            "color": pyvvisf.ISFColorVal(0.0, 0.0, 1.0, 1.0),  # Blue
            "intensity": pyvvisf.ISFFloatVal(0.5)  # Half intensity
        })
        image = renderer.render_to_pil_image(800, 600)
        output_path = Path(__file__).parent / "output_blue_half.png"
        image.save(output_path)
        print(f"✓ Saved blue half-intensity image to: {output_path}")
        
        # Show current inputs
        current_inputs = renderer.get_current_inputs()
        print(f"Current inputs: {current_inputs}")
        
        # Check for errors
        renderer.check_errors("rendering demo")
        print("✓ No OpenGL errors detected")
    
    print("✓ ISFRenderer cleanup completed")


if __name__ == "__main__":
    main() 