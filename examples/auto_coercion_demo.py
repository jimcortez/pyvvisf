#!/usr/bin/env python3
"""
Demo of pyvvisf's auto-coercion feature.

This example shows how Python primitives are automatically converted to ISF values,
making it much easier to work with shader inputs.
"""

import pyvvisf
from PIL import Image

def main():
    # Simple shader with various input types
    shader_content = """
/*{
    "DESCRIPTION": "Auto-coercion demo shader",
    "CREDIT": "pyvvisf demo",
    "CATEGORIES": ["Demo"],
    "INPUTS": [
        {
            "NAME": "use_red",
            "TYPE": "bool",
            "DEFAULT": false
        },
        {
            "NAME": "intensity",
            "TYPE": "float",
            "DEFAULT": 0.5,
            "MIN": 0.0,
            "MAX": 1.0
        },
        {
            "NAME": "position",
            "TYPE": "point2D",
            "DEFAULT": [0.5, 0.5]
        },
        {
            "NAME": "color",
            "TYPE": "color",
            "DEFAULT": [1.0, 1.0, 1.0, 1.0]
        }
    ]
}*/

void main() {
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
    vec2 center = position;
    float dist = distance(uv, center);
    
    vec4 final_color = color;
    if (use_red) {
        final_color = vec4(1.0, 0.0, 0.0, 1.0);
    }
    
    // Create a circular gradient
    float circle = smoothstep(0.3, 0.0, dist);
    final_color *= circle * intensity;
    
    gl_FragColor = final_color;
}
"""

    print("pyvvisf Auto-Coercion Demo")
    print("=" * 40)
    
    try:
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            print("✓ Shader loaded successfully")
            
            # Demo 1: Basic auto-coercion
            print("\n1. Basic auto-coercion:")
            renderer.set_input("use_red", True)  # bool -> ISFBoolVal
            renderer.set_input("intensity", 0.8)  # float -> ISFFloatVal
            renderer.set_input("position", (0.3, 0.7))  # tuple -> ISFPoint2DVal
            renderer.set_input("color", (0.0, 1.0, 0.0, 0.8))  # tuple -> ISFColorVal
            
            buffer = renderer.render(400, 300)
            image = buffer.to_pil_image()
            image.save("auto_coercion_demo_1.png")
            print("   ✓ Saved auto_coercion_demo_1.png")
            
            # Demo 2: RGB to RGBA conversion
            print("\n2. RGB to RGBA conversion:")
            renderer.set_input("color", (1.0, 0.0, 1.0))  # RGB -> RGBA with alpha=1.0
            renderer.set_input("use_red", False)
            
            buffer = renderer.render(400, 300)
            image = buffer.to_pil_image()
            image.save("auto_coercion_demo_2.png")
            print("   ✓ Saved auto_coercion_demo_2.png")
            
            # Demo 3: Using set_inputs with mixed types
            print("\n3. Mixed types with set_inputs:")
            renderer.set_inputs({
                "use_red": 1,  # int -> ISFBoolVal (True)
                "intensity": 0.3,  # float -> ISFFloatVal
                "position": [0.8, 0.2],  # list -> ISFPoint2DVal
                "color": (0.0, 0.0, 1.0)  # RGB tuple -> ISFColorVal
            })
            
            buffer = renderer.render(400, 300)
            image = buffer.to_pil_image()
            image.save("auto_coercion_demo_3.png")
            print("   ✓ Saved auto_coercion_demo_3.png")
            
            # Demo 4: Mixing ISF values and Python primitives
            print("\n4. Mixing ISF values and Python primitives:")
            renderer.set_input("use_red", pyvvisf.ISFBoolVal(False))  # Explicit ISF value
            renderer.set_input("intensity", 1.0)  # Python primitive
            renderer.set_input("position", pyvvisf.ISFPoint2DVal(0.5, 0.5))  # Explicit ISF value
            renderer.set_input("color", (1.0, 1.0, 0.0))  # Python primitive
            
            buffer = renderer.render(400, 300)
            image = buffer.to_pil_image()
            image.save("auto_coercion_demo_4.png")
            print("   ✓ Saved auto_coercion_demo_4.png")
            
            print("\n✓ All demos completed successfully!")
            print("\nGenerated files:")
            print("  - auto_coercion_demo_1.png (Green circle)")
            print("  - auto_coercion_demo_2.png (Magenta circle)")
            print("  - auto_coercion_demo_3.png (Blue circle)")
            print("  - auto_coercion_demo_4.png (Yellow circle)")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 