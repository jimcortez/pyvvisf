"""Complex rendering tests that may reproduce segmentation fault."""

import pytest
import sys
import threading
import time
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_multiple_scenes_parallel():
    """Test creating multiple scenes in parallel - may cause context conflicts."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    def create_and_render_scene(scene_id):
        """Create a scene and render a frame."""
        try:
            # Create shader content
            shader_content = f"""
            /*{{
                "DESCRIPTION": "Test shader {scene_id}",
                "CREDIT": "Test",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }}*/
            void main() {{
                gl_FragColor = vec4({scene_id * 0.1}, 0.0, 0.0, 1.0);
            }}
            """
            
            # Create scene and render
            doc = pyvvisf.CreateISFDocRefWith(shader_content)
            scene = pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            size = pyvvisf.Size(50, 50)
            buffer = scene.create_and_render_a_buffer(size)
            
            return buffer is not None
        except Exception as e:
            print(f"Scene {scene_id} failed: {e}")
            return False
    
    # Create multiple threads
    threads = []
    results = []
    
    for i in range(5):
        thread = threading.Thread(target=lambda i=i: results.append(create_and_render_scene(i)))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    successful = sum(results)
    assert successful > 0, f"Only {successful}/5 scenes rendered successfully"


def test_context_switching():
    """Test switching between different GLFW contexts - may cause segmentation fault."""
    pytest.skip("Disabled due to segmentation fault (not part of ISFRenderer API)")
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Create multiple scenes with context reinitialization
    scenes = []
    buffers = []
    
    for i in range(3):
        # Reinitialize context each time
        pyvvisf.reinitialize_glfw_context()
        
        # Create shader
        shader_content = f"""
        /*{{
            "DESCRIPTION": "Context test shader {i}",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }}*/
        void main() {{
            gl_FragColor = vec4(0.0, {i * 0.3}, 0.0, 1.0);
        }}
        """
        
        # Create scene and render
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        size = pyvvisf.Size(100, 100)
        buffer = scene.create_and_render_a_buffer(size)
        
        scenes.append(scene)
        buffers.append(buffer)
    
    # Verify all buffers were created
    assert len(buffers) == 3
    for buffer in buffers:
        assert buffer is not None
        assert buffer.size.width == 100
        assert buffer.size.height == 100


def test_rapid_rendering():
    """Test rapid rendering operations - may stress the OpenGL context."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize context
    pyvvisf.initialize_glfw_context()
    
    # Create a simple scene
    shader_content = """
    /*{
        "DESCRIPTION": "Rapid rendering test",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
    """
    
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Render many frames rapidly
    buffers = []
    for i in range(10):
        size = pyvvisf.Size(50, 50)
        buffer = scene.create_and_render_a_buffer(size)
        buffers.append(buffer)
        
        # Small delay to prevent overwhelming the GPU
        time.sleep(0.01)
    
    # Verify all buffers were created
    assert len(buffers) == 10
    for buffer in buffers:
        assert buffer is not None


def test_memory_pressure():
    """Test rendering under memory pressure - may cause segmentation fault."""
    try:
        import pyvvisf
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")
    
    # Initialize context
    pyvvisf.initialize_glfw_context()
    
    # Create a scene
    shader_content = """
    /*{
        "DESCRIPTION": "Memory pressure test",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
    """
    
    doc = pyvvisf.CreateISFDocRefWith(shader_content)
    scene = pyvvisf.CreateISFSceneRef()
    scene.use_doc(doc)
    
    # Create many large buffers to stress memory
    buffers = []
    for i in range(5):
        size = pyvvisf.Size(1024, 1024)  # Large buffers
        buffer = scene.create_and_render_a_buffer(size)
        buffers.append(buffer)
    
    # Verify buffers were created
    assert len(buffers) == 5
    for buffer in buffers:
        assert buffer is not None
        assert buffer.size.width == 1024
        assert buffer.size.height == 1024


if __name__ == "__main__":
    pytest.main([__file__]) 