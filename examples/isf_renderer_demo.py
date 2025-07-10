#!/usr/bin/env python3
"""Demonstration of the ISFRenderer API (updated for latest version)."""

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
    print("pyvvisf ISFRenderer Demo (Updated)")
    print("=" * 40)

    # Select a shader file from the examples/shaders directory
    shader_path = Path(__file__).parent / "shaders" / "simple_color_change.fs"
    # shader_path = Path(__file__).parent / "shaders" / "simple_color_animation.fs"
    # shader_path = Path(__file__).parent / "shaders" / "shapes.fs"
    # shader_path = Path(__file__).parent / "shaders" / "simple.fs"

    with open(shader_path, "r") as f:
        shader_content = f.read()

    with pyvvisf.ISFRenderer(shader_content) as renderer:
        # Render with different color inputs (using Python primitives)
        renderer.set_input("color", (0.0, 1.0, 0.0, 1.0))  # Green
        buffer = renderer.render(800, 600)
        image = buffer.to_pil_image()
        output_path = Path(__file__).parent / "output_green.png"
        image.save(output_path)
        print(f"Saved green image to: {output_path}")

        renderer.set_input("color", (1.0, 0.0, 0.0, 1.0))  # Red
        buffer = renderer.render(800, 600)
        image = buffer.to_pil_image()
        output_path = Path(__file__).parent / "output_red.png"
        image.save(output_path)
        print(f"Saved red image to: {output_path}")

        renderer.set_input("color", (0.0, 0.0, 1.0, 1.0))  # Blue
        buffer = renderer.render(800, 600)
        image = buffer.to_pil_image()
        output_path = Path(__file__).parent / "output_blue.png"
        image.save(output_path)
        print(f"Saved blue image to: {output_path}")

    print("Demo completed.")


if __name__ == "__main__":
    main() 