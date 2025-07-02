"""Test to reproduce segmentation fault without explicit GLFW initialization."""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_render_without_glfw_init():
    """Test rendering without explicit GLFW initialization - may cause segmentation fault."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Check GLFW status before any operations
    gl_info = pyvvisf.get_gl_info()
    print(f"GL Info before operations: {gl_info}")
    
    # Create a simple test shader
    shader_content = """
    /*{
        "DESCRIPTION": "Test shader",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
    """
    
    # Create ISF document and scene without explicit GLFW init
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Set up rendering parameters
    size = pyvvisf.Size(100, 100)
    
    # This line may cause segmentation fault if GLFW is not properly initialized
    buffer = scene.create_and_render_a_buffer(size)
    
    # If we get here, rendering was successful
    assert buffer is not None
    assert buffer.size.width == 100
    assert buffer.size.height == 100


if __name__ == "__main__":
    pytest.main([__file__]) 