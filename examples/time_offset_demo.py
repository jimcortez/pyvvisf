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

# A simple animated shader that changes color over time
shader_content = """
/*{
    "DESCRIPTION": "Time-based color animation",
    "CREDIT": "pyvvisf example",
    "CATEGORIES": ["Color Effect"],
    "INPUTS": [
        {
            "NAME": "speed",
            "TYPE": "float",
            "DEFAULT": 1.0,
            "MIN": 0.0,
            "MAX": 5.0
        }
    ]
}*/

void main() {
    // Create a color that changes over time
    float time = TIME * speed;
    vec3 color = vec3(
        0.5 + 0.5 * sin(time),
        0.5 + 0.5 * sin(time + 2.094), // 2π/3
        0.5 + 0.5 * sin(time + 4.189)  // 4π/3
    );
    
    gl_FragColor = vec4(color, 1.0);
}
"""

def main():
    print("Rendering shader at different time offsets...")
    
    with pyvvisf.ISFRenderer(shader_content) as renderer:
        # Set a moderate animation speed
        renderer.set_input("speed", pyvvisf.ISFFloatVal(0.5))
        
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
        
        print("\nAll images saved! You should see different colors for each time offset.")
        print("The shader creates a smooth color animation that cycles through RGB values.")

if __name__ == "__main__":
    main() 