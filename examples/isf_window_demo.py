import sys
import os
from pathlib import Path

# Add src to path for development
# sys.path.insert(0, str(Path(__file__).parent.parent)) # This line is removed as per the edit hint.

import pyvvisf

def main():
    # Select a shader file from the examples/shaders directory
    # shader_path = Path(__file__).parent / "shaders" / "simple_color_animation.fs"
    # shader_path = Path(__file__).parent / "shaders" / "shapes.fs"
    shader_path = Path(__file__).parent / "shaders" / "simple_color_change.fs"
    # shader_path = Path(__file__).parent / "shaders" / "simple.fs"

    with open(shader_path, "r") as f:
        shader_code = f.read()
        
    with pyvvisf.ISFRenderer(shader_content=shader_code) as renderer:
        # Optionally set inputs here using Python primitives, e.g.:
        # renderer.set_input("colorA", (1.0, 0.0, 0.0, 1.0))
        renderer.render_to_window(width=800, height=600, title="ISF Window Demo")

if __name__ == "__main__":
    main() 