"""Tests for pyvvisf rendering functionality."""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_render_frame_basic():
    """Test basic rendering functionality - this may cause segmentation fault."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize GLFW context
    if not pyvvisf.initialize_glfw_context():
        pytest.skip("Failed to initialize GLFW context")
    
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
    
    # Create ISF document and scene
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Set up rendering parameters
    size = pyvvisf.Size(100, 100)
    
    # This line may cause segmentation fault in some contexts
    buffer = scene.create_and_render_a_buffer(size)
    
    # If we get here, rendering was successful
    assert buffer is not None
    assert buffer.size.width == 100
    assert buffer.size.height == 100


def test_render_frame_with_inputs():
    """Test rendering with shader inputs."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize GLFW context
    if not pyvvisf.initialize_glfw_context():
        pytest.skip("Failed to initialize GLFW context")
    
    # Create a shader with inputs
    shader_content = """
    /*{
        "DESCRIPTION": "Test shader with inputs",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
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
    
    # Create ISF document and scene
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Set shader inputs
    scene.set_value_for_input_named(pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0), "color")
    scene.set_value_for_input_named(pyvvisf.ISFFloatVal(0.8), "intensity")
    
    # Render
    size = pyvvisf.Size(200, 200)
    buffer = scene.create_and_render_a_buffer(size)
    
    assert buffer is not None
    assert buffer.size.width == 200
    assert buffer.size.height == 200


if __name__ == "__main__":
    pytest.main([__file__]) 