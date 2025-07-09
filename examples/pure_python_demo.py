#!/usr/bin/env python3
"""Example demonstrating the new pure Python ISF renderer."""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyvvisf import ISFRenderer, ISFColor, ISFPoint2D


def main():
    """Demonstrate the new pure Python ISF renderer."""
    
    # Create a simple test shader
    test_shader = """
    /*{
        "NAME": "Test Shader",
        "DESCRIPTION": "A simple test shader for the new renderer",
        "INPUTS": [
            {
                "NAME": "color",
                "TYPE": "color",
                "DEFAULT": [1.0, 0.0, 0.0, 1.0]
            },
            {
                "NAME": "scale",
                "TYPE": "float",
                "DEFAULT": 1.0,
                "MIN": 0.1,
                "MAX": 5.0
            },
            {
                "NAME": "offset",
                "TYPE": "point2D",
                "DEFAULT": [0.0, 0.0]
            }
        ]
    }*/
    
    uniform vec2 RENDERSIZE;
    uniform float TIME;
    uniform vec4 color;
    uniform float scale;
    uniform vec2 offset;
    
    out vec4 fragColor;
    
    void main() {
        vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
        vec2 pos = (uv - 0.5) * scale + offset;
        
        float dist = length(pos);
        float circle = smoothstep(0.5, 0.4, dist);
        
        vec4 final_color = color * circle;
        fragColor = final_color;
    }
    """
    
    print("Creating ISF renderer...")
    
    # Create renderer
    with ISFRenderer() as renderer:
        print("Loading shader...")
        
        # Load shader content
        metadata = renderer.load_shader_content(test_shader)
        print(f"Loaded shader: {metadata.name}")
        print(f"Description: {metadata.description}")
        print(f"Inputs: {[input_.name for input_ in metadata.inputs] if metadata.inputs else 'None'}")
        
        # Render with default parameters
        print("Rendering with default parameters...")
        image_array = renderer.render(width=512, height=512)
        print(f"Rendered image shape: {image_array.shape}")
        
        # Save the result
        output_path = "test_render_default.png"
        renderer.save_render(output_path, width=512, height=512)
        print(f"Saved default render to: {output_path}")
        
        # Render with custom parameters
        print("Rendering with custom parameters...")
        custom_inputs = {
            'color': ISFColor.from_rgb(0.0, 1.0, 0.0, 1.0),  # Green
            'scale': 2.0,
            'offset': ISFPoint2D(0.2, 0.1)
        }
        
        image_array = renderer.render(
            width=512, height=512,
            inputs=custom_inputs,
            metadata=metadata
        )
        
        # Save custom render
        output_path = "test_render_custom.png"
        renderer.save_render(
            output_path, 
            width=512, height=512,
            inputs=custom_inputs,
            metadata=metadata
        )
        print(f"Saved custom render to: {output_path}")
        
        # Test different input types
        print("Testing different input types...")
        
        # Test tuple inputs (auto-coercion)
        tuple_inputs = {
            'color': (0.0, 0.0, 1.0, 1.0),  # Blue
            'scale': 1.5,
            'offset': (0.0, 0.0)
        }
        
        image_array = renderer.render(
            width=512, height=512,
            inputs=tuple_inputs,
            metadata=metadata
        )
        
        output_path = "test_render_tuples.png"
        renderer.save_render(
            output_path,
            width=512, height=512,
            inputs=tuple_inputs,
            metadata=metadata
        )
        print(f"Saved tuple render to: {output_path}")
    
    print("Rendering complete!")


if __name__ == "__main__":
    main() 