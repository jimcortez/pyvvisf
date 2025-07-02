"""Test to verify the batch rendering fix prevents texture corruption and segmentation faults."""

import pytest
import sys
import time
import threading
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_batch_rendering_basic():
    """Test basic batch rendering functionality."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize context
    pyvvisf.initialize_glfw_context()
    
    # Create a simple test shader
    shader_content = """
    /*{
        "DESCRIPTION": "Batch rendering test shader",
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
    
    # Perform batch rendering with cleanup between frames
    for i in range(5):
        print(f"Rendering frame {i+1}/5")
        
        # Render frame
        buffer = scene.create_and_render_a_buffer(size)
        assert buffer is not None, f"Buffer {i} is None"
        assert buffer.size.width == 100, f"Buffer {i} width mismatch"
        assert buffer.size.height == 100, f"Buffer {i} height mismatch"
        
        # Convert to PIL image to test texture reading
        try:
            pil_image = buffer.to_pil_image()
            assert pil_image is not None, f"PIL image {i} is None"
            assert pil_image.size == (100, 100), f"PIL image {i} size mismatch"
            
            # Verify image has content (not empty)
            pixel_data = list(pil_image.getdata())
            assert len(pixel_data) > 0, f"PIL image {i} has no pixel data"
            
            # Check that we have some non-zero pixels (red color from shader)
            red_pixels = sum(1 for pixel in pixel_data if pixel[0] > 0)
            assert red_pixels > 0, f"PIL image {i} has no red pixels"
            
        except Exception as e:
            pytest.fail(f"Failed to convert buffer {i} to PIL image: {e}")
        
        # Perform cleanup between frames to prevent texture corruption
        if hasattr(scene, 'cleanup'):
            scene.cleanup()
        
        # Small delay to allow GPU operations to complete
        time.sleep(0.01)
    
    print("Batch rendering test completed successfully")


def test_texture_validation():
    """Test that texture validation works correctly."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize context
    pyvvisf.initialize_glfw_context()
    
    # Test with a basic shader
    shader_content = """
    /*{
        "DESCRIPTION": "Texture validation test",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);
    }
    """
    
    # Create scene
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Render with different sizes to test texture creation
    sizes = [pyvvisf.Size(50, 50), pyvvisf.Size(100, 100), pyvvisf.Size(200, 200)]
    
    for size in sizes:
        buffer = scene.create_and_render_a_buffer(size)
        assert buffer is not None, f"Buffer is None for size {size.width}x{size.height}"
        
        # Test texture to PIL conversion
        try:
            pil_image = buffer.to_pil_image()
            assert pil_image is not None, f"PIL image is None for size {size.width}x{size.height}"
            assert pil_image.size == (size.width, size.height), f"PIL image size mismatch"
        except Exception as e:
            pytest.fail(f"Texture validation failed for size {size.width}x{size.height}: {e}")
    
    # Cleanup
    if hasattr(scene, 'cleanup'):
        scene.cleanup()
    
    print("Texture validation test completed successfully")


def test_context_state_management():
    """Test that OpenGL context state management works correctly."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize context
    pyvvisf.initialize_glfw_context()
    
    # Create and render multiple scenes to test context state management
    for i in range(3):
        print(f"Creating scene {i+1}/3")
        
        # Create shader
        shader_content = f"""
        /*{{
            "DESCRIPTION": "Context state test shader {i}",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }}*/
        void main() {{
            gl_FragColor = vec4({i * 0.2}, 0.0, 0.0, 1.0);
        }}
        """
        
        # Create scene
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Render frame
        size = pyvvisf.Size(80, 80)
        buffer = scene.create_and_render_a_buffer(size)
        assert buffer is not None, f"Buffer {i} is None"
        
        # Convert to PIL image
        pil_image = buffer.to_pil_image()
        assert pil_image is not None, f"PIL image {i} is None"
        
        # Reset context state between scenes if function exists
        if hasattr(pyvvisf, 'reset_gl_context_state'):
            pyvvisf.reset_gl_context_state()
        
        # Cleanup scene if method exists
        if hasattr(scene, 'cleanup'):
            scene.cleanup()
    
    print("Context state management test completed successfully")


if __name__ == "__main__":
    test_batch_rendering_basic()
    test_texture_validation()
    test_context_state_management() 