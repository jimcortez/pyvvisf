#!/usr/bin/env python3
"""
Example demonstrating time offset functionality in pyvvisf.

This example shows how to render a shader at different time offsets,
which is useful for creating animations or rendering specific frames
from time-based shaders.
"""

import pyvvisf
from PIL import Image
from pathlib import Path

# Select a shader file from the examples/shaders directory
shader_path = Path(__file__).parent / "shaders" / "simple_color_animation.fs"
# shader_path = Path(__file__).parent / "shaders" / "shapes.fs"
# shader_path = Path(__file__).parent / "shaders" / "simple_color_change.fs"
# shader_path = Path(__file__).parent / "shaders" / "simple.fs"

with open(shader_path, "r") as f:
    shader_content = f.read()

def main():
    print("Rendering shader at different time offsets...")
    
    with pyvvisf.ISFRenderer(shader_content) as renderer:
        # Set a moderate animation speed if the shader has a 'speed' input
        try:
            renderer.set_input("speed", 0.5)
        except Exception:
            pass  # Not all shaders have a 'speed' input
        
        # Render at different time offsets
        time_offsets = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
        
        for i, time_offset in enumerate(time_offsets):
            print(f"Rendering at {time_offset}s...")
            buffer = renderer.render(800, 600, time_offset=time_offset)
            image = buffer.to_pil_image()
            
            # Save the image
            output_path = Path(__file__).parent / f"output_time_{time_offset}s.png"
            image.save(output_path)
            print(f"✓ Saved image to: {output_path}")
        
        print("\nAll images saved! You should see different results for each time offset.")

if __name__ == "__main__":
    main() 