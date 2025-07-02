#!/usr/bin/env python3
"""
Comprehensive test script to verify segmentation fault fix in pyvvisf.

This script tests various scenarios that previously caused segmentation faults:
1. Basic rendering without explicit GLFW initialization
2. Multiple scene creation and rendering
3. Context switching and reinitialization
4. Threaded rendering operations
5. Memory pressure scenarios
"""

import sys
import threading
import time
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_rendering():
    """Test basic rendering functionality."""
    print("Testing basic rendering...")
    
    import pyvvisf
    
    # Check GLFW status
    gl_info = pyvvisf.get_gl_info()
    print(f"GL Info: {gl_info}")
    
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
    
    # This should not cause segmentation fault
    buffer = scene.create_and_render_a_buffer(size)
    
    print("✓ Basic rendering successful")
    return buffer

def test_multiple_scenes():
    """Test creating multiple scenes."""
    print("Testing multiple scenes...")
    
    import pyvvisf
    
    buffers = []
    for i in range(3):
        shader_content = f"""
        /*{{
            "DESCRIPTION": "Test shader {i}",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }}*/
        void main() {{
            gl_FragColor = vec4({i * 0.3}, 0.0, 0.0, 1.0);
        }}
        """
        
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        size = pyvvisf.Size(50, 50)
        buffer = scene.create_and_render_a_buffer(size)
        buffers.append(buffer)
    
    print(f"✓ Created {len(buffers)} scenes successfully")
    return buffers

def test_context_switching():
    """Test context switching and reinitialization."""
    print("Testing context switching...")
    
    import pyvvisf
    
    # Reinitialize context multiple times
    for i in range(3):
        pyvvisf.reinitialize_glfw_context()
        
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
        
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        size = pyvvisf.Size(100, 100)
        buffer = scene.create_and_render_a_buffer(size)
        
        print(f"  ✓ Context {i} rendering successful")
    
    print("✓ Context switching successful")

def test_threaded_rendering():
    """Test threaded rendering operations."""
    print("Testing threaded rendering...")
    
    import pyvvisf
    
    def render_in_thread(thread_id):
        """Render function for a thread."""
        try:
            shader_content = f"""
            /*{{
                "DESCRIPTION": "Thread test shader {thread_id}",
                "CREDIT": "Test",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }}*/
            void main() {{
                gl_FragColor = vec4({thread_id * 0.2}, 0.0, 0.0, 1.0);
            }}
            """
            
            doc = pyvvisf.CreateISFDocRefWith(shader_content)
            scene = pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            size = pyvvisf.Size(50, 50)
            buffer = scene.create_and_render_a_buffer(size)
            
            return True
        except Exception as e:
            print(f"  ✗ Thread {thread_id} failed: {e}")
            return False
    
    # Create multiple threads
    threads = []
    results = []
    
    for i in range(3):
        thread = threading.Thread(target=lambda i=i: results.append(render_in_thread(i)))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    successful = sum(results)
    print(f"✓ {successful}/3 threads completed successfully")

def test_memory_pressure():
    """Test rendering under memory pressure."""
    print("Testing memory pressure...")
    
    import pyvvisf
    
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
        size = pyvvisf.Size(512, 512)  # Large buffers
        buffer = scene.create_and_render_a_buffer(size)
        buffers.append(buffer)
        print(f"  ✓ Created buffer {i+1}/5")
    
    print(f"✓ Created {len(buffers)} large buffers successfully")

def main():
    """Run all tests."""
    print("pyvvisf Segmentation Fault Fix Test")
    print("=" * 40)
    
    try:
        # Test 1: Basic rendering
        test_basic_rendering()
        
        # Test 2: Multiple scenes
        test_multiple_scenes()
        
        # Test 3: Context switching
        test_context_switching()
        
        # Test 4: Threaded rendering
        test_threaded_rendering()
        
        # Test 5: Memory pressure
        test_memory_pressure()
        
        print("\n" + "=" * 40)
        print("✓ All tests passed! Segmentation fault issue appears to be resolved.")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 