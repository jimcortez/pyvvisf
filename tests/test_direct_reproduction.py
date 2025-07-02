#!/usr/bin/env python3
"""
Direct reproduction of the segfault issue based on the user's script
This tries to mimic the exact scenario described in the bug report
"""

import tempfile
import sys
from pathlib import Path
import pytest

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_direct_reproduction_scenario():
    """Directly reproduce the scenario from the bug report"""
    print("=" * 60)
    print("pyvvisf Segmentation Fault Direct Reproduction")
    print("=" * 60)
    print("Setting up test configuration...")
    
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize GLFW context
    if not pyvvisf.initialize_glfw_context():
        pytest.skip("Failed to initialize GLFW context")
    
    # Simple ISF shader (exactly as in the bug report)
    shader_content = '''/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test", 
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(1.0); }'''

    print("Creating temporary output file...")
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        output_path = Path(f.name)
    
    try:
        print("Creating ISF scene and document...")
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        print("Setting up custom dimensions (640x480)...")
        size = pyvvisf.Size(640, 480)  # Custom dimensions from bug report
        
        print("Attempting to render frame (this may crash)...")
        print("If you see a segmentation fault after this line, the bug is reproduced.")
        print("-" * 60)
        
        # This is the equivalent of what the render_frame was trying to do
        buffer = scene.create_and_render_a_buffer(size)
        
        print("-" * 60)
        print("SUCCESS: No crash occurred!")
        
        if buffer is not None:
            print(f"Buffer created successfully: {buffer.size.width}x{buffer.size.height}")
            
            # Try to convert to PIL and save (similar to what render_frame would do)
            try:
                pil_image = buffer.to_pil_image()
                if pil_image:
                    pil_image.save(output_path)
                    print(f"Output file created: {output_path}")
                    print(f"File size: {output_path.stat().st_size} bytes")
                else:
                    print("ERROR: Failed to convert buffer to PIL image")
            except Exception as e:
                print(f"ERROR: Exception during PIL conversion: {e}")
        else:
            print("ERROR: No buffer created")
            
    except Exception as e:
        print("-" * 60)
        print(f"EXCEPTION CAUGHT: {type(e).__name__}: {e}")
        print("This is better than a segfault, but still indicates an issue.")
        raise  # Re-raise for pytest
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()
            print(f"Cleaned up temporary file: {output_path}")
        print("Cleanup completed")
        print("=" * 60)


def test_stress_test_multiple_renders():
    """Stress test with multiple renders using custom dimensions"""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize GLFW context
    if not pyvvisf.initialize_glfw_context():
        pytest.skip("Failed to initialize GLFW context")
    
    shader_content = '''/*{
    "DESCRIPTION": "Stress test shader",
    "CREDIT": "Test", 
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(0.5, 0.5, 0.5, 1.0); }'''

    # Create ISF document and scene
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Test multiple renders with the problematic dimensions
    size = pyvvisf.Size(640, 480)
    
    print("Performing stress test with multiple renders...")
    for i in range(10):
        print(f"Render {i+1}/10...")
        buffer = scene.create_and_render_a_buffer(size)
        assert buffer is not None, f"Render {i+1} failed"
        assert buffer.size.width == 640
        assert buffer.size.height == 480
        
        # Try converting to PIL each time
        pil_image = buffer.to_pil_image()
        assert pil_image is not None, f"PIL conversion failed on render {i+1}"
        assert pil_image.size == (640, 480)
    
    print("Stress test completed successfully!")


def test_various_problematic_dimensions():
    """Test various dimensions that might be problematic"""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize GLFW context
    if not pyvvisf.initialize_glfw_context():
        pytest.skip("Failed to initialize GLFW context")
    
    shader_content = '''/*{
    "DESCRIPTION": "Dimension test shader",
    "CREDIT": "Test", 
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(0.8, 0.2, 0.2, 1.0); }'''

    # Create ISF document and scene
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Test dimensions that might be problematic
    problematic_dimensions = [
        (640, 480),    # Original bug report
        (320, 240),    # Half size
        (1280, 960),   # Double size
        (800, 600),    # Similar aspect ratio
        (1024, 768),   # Common resolution
        (512, 384),    # Power of 2 nearby
        (720, 540),    # 3/4 ratio
        (160, 120),    # Very small
    ]
    
    for width, height in problematic_dimensions:
        print(f"Testing dimensions: {width}x{height}")
        size = pyvvisf.Size(width, height)
        
        buffer = scene.create_and_render_a_buffer(size)
        assert buffer is not None, f"Render failed for {width}x{height}"
        assert buffer.size.width == width, f"Width mismatch for {width}x{height}"
        assert buffer.size.height == height, f"Height mismatch for {width}x{height}"
        
        # Test PIL conversion
        pil_image = buffer.to_pil_image()
        assert pil_image is not None, f"PIL conversion failed for {width}x{height}"
        assert pil_image.size == (width, height), f"PIL size mismatch for {width}x{height}"


if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Run the direct reproduction test
    test_direct_reproduction_scenario()
    test_stress_test_multiple_renders()
    test_various_problematic_dimensions()
    
    print("All tests completed successfully!") 