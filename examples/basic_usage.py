#!/usr/bin/env python3
"""Basic usage example for pyvvisf."""

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
    """Main example function."""
    print("pyvvisf Basic Usage Example")
    print("=" * 40)
    
    # Get platform and OpenGL information
    print(f"Platform: {pyvvisf.get_platform_info()}")
    print(f"OpenGL Info: {pyvvisf.get_gl_info()}")
    
    # Check if VVISF is available
    if not pyvvisf.is_vvisf_available():
        print("Error: VVISF is not available")
        return
    
    print("✓ VVISF is available")
    
    # Initialize GLFW context
    if not pyvvisf.initialize_glfw_context():
        print("Error: Failed to initialize GLFW context")
        return
    
    print("✓ GLFW context initialized")
    
    # Create a simple test shader
    shader_content = """
    /*{
        "DESCRIPTION": "Simple color shader",
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
    
    try:
        # Create ISF document
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        print(f"✓ Created ISF document: {doc.name()}")
        print(f"  Description: {doc.description()}")
        print(f"  Categories: {doc.categories()}")
        
        # Create ISF scene
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        print("✓ Created ISF scene")
        
        # Set shader inputs
        scene.set_value_for_input_named(pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0), "color")
        scene.set_value_for_input_named(pyvvisf.ISFFloatVal(0.8), "intensity")
        print("✓ Set shader inputs")
        
        # Render to a buffer
        size = pyvvisf.Size(800, 600)
        buffer = scene.create_and_render_a_buffer(size)
        print(f"✓ Rendered buffer: {buffer.size.width}x{buffer.size.height}")
        
        # Print buffer details before converting to PIL
        print(f"Buffer details:")
        print(f"  Size: {buffer.size.width}x{buffer.size.height}")
        print(f"  Name: {buffer.name}")
        print(f"  Type: {type(buffer)}")
        print(f"  Dir: {[attr for attr in dir(buffer) if not attr.startswith('_')]}")
        
        # Convert to PIL Image
        try:
            image = buffer.to_pil_image()
        except Exception as e:
            print(f"to_pil_image() failed: {e}")
            print("Trying create_pil_image() instead...")
            image = buffer.create_pil_image()
        print("✓ Converted to PIL Image")
        
        # Save the image
        output_path = Path(__file__).parent / "output.png"
        image.save(output_path)
        print(f"✓ Saved image to: {output_path}")
        
        # Display image info
        print(f"  Image size: {image.size}")
        print(f"  Image mode: {image.mode}")
        
    except Exception as e:
        print(f"Error during rendering: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 