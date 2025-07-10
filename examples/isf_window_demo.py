import sys
import os
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pyvvisf.renderer import ISFRenderer

def main():
    with open("examples/shaders/simple_color_animation.fs", "r") as f:
        shader_code = f.read()
        
    with ISFRenderer(shader_content=shader_code) as renderer:

        # Show in window
        renderer.render_to_window(width=800, height=600, title="ISF Window Demo")

if __name__ == "__main__":
    main() 