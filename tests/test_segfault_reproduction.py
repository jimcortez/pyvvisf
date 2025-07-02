"""Test to reproduce the segmentation fault bug reported with custom dimensions."""

import pytest
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestSegfaultReproduction:
    """Test cases to reproduce the segmentation fault with custom dimensions."""
    
    @pytest.fixture(autouse=True)
    def setup_pyvvisf(self):
        """Setup pyvvisf for each test."""
        try:
            import pyvvisf
            
            # Initialize GLFW context
            if not pyvvisf.initialize_glfw_context():
                pytest.skip("Failed to initialize GLFW context")
            
            self.pyvvisf = pyvvisf
            yield
            
            # Note: GLFW context cleanup is handled automatically
                
        except ImportError as e:
            pytest.skip(f"pyvvisf not available: {e}")

    def test_default_dimensions_should_work(self):
        """Test that default dimensions (1920x1080) work correctly."""
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
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Use default dimensions (should work)
        size = self.pyvvisf.Size(1920, 1080)
        buffer = scene.create_and_render_a_buffer(size)
        
        # Verify buffer was created successfully
        assert buffer is not None
        assert buffer.size.width == 1920
        assert buffer.size.height == 1080

    def test_custom_dimensions_640x480_segfault_bug(self):
        """Test custom dimensions (640x480) - this reproduces the segfault."""
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
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Use custom dimensions (this triggers the segfault)
        size = self.pyvvisf.Size(640, 480)
        
        # This line causes the segmentation fault
        buffer = scene.create_and_render_a_buffer(size)
        
        # If we get here, the bug is fixed
        assert buffer is not None
        assert buffer.size.width == 640
        assert buffer.size.height == 480

    def test_various_custom_dimensions(self):
        """Test various custom dimensions to identify problematic sizes."""
        test_sizes = [
            (100, 100),    # Small square
            (320, 240),    # Classic 4:3
            (640, 480),    # Standard VGA (the reported bug case)
            (800, 600),    # SVGA
            (1024, 768),   # XGA
            (1280, 720),   # HD 720p
            (512, 512),    # Power of 2 square
            (1000, 1000),  # Large square
        ]
        
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() {
            gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);
        }
        """
        
        for width, height in test_sizes:
            # Create fresh scene for each test
            doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
            scene = self.pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            size = self.pyvvisf.Size(width, height)
            
            # This should not crash
            buffer = scene.create_and_render_a_buffer(size)
            
            assert buffer is not None, f"Buffer creation failed for size {width}x{height}"
            assert buffer.size.width == width
            assert buffer.size.height == height

    def test_with_shader_inputs_custom_dimensions(self):
        """Test custom dimensions with shaders that have inputs."""
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
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Set shader inputs
        scene.set_value_for_input_named(
            self.pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0), "color"
        )
        scene.set_value_for_input_named(
            self.pyvvisf.ISFFloatVal(0.8), "intensity"
        )
        
        # Use custom dimensions (this might also trigger the segfault)
        size = self.pyvvisf.Size(640, 480)
        buffer = scene.create_and_render_a_buffer(size)
        
        assert buffer is not None
        assert buffer.size.width == 640
        assert buffer.size.height == 480

    def test_batch_rendering_custom_dimensions(self):
        """Test batch rendering with custom dimensions - stress test."""
        shader_content = """
        /*{
            "DESCRIPTION": "Batch test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() {
            gl_FragColor = vec4(1.0, 1.0, 0.0, 1.0);
        }
        """
        
        # Create ISF document and scene
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Render multiple frames with custom dimensions
        size = self.pyvvisf.Size(640, 480)
        
        for i in range(5):
            buffer = scene.create_and_render_a_buffer(size)
            assert buffer is not None
            assert buffer.size.width == 640
            assert buffer.size.height == 480

    def test_minimal_reproduction_case(self):
        """Minimal reproduction case as described in the bug report."""
        # Simple ISF shader (exactly as in the bug report)
        shader_content = '''/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test", 
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(1.0); }'''

        # Create ISF document and scene
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Use the exact dimensions from the bug report
        size = self.pyvvisf.Size(640, 480)
        
        # This line is where the segmentation fault occurs
        buffer = scene.create_and_render_a_buffer(size)
        
        # If we reach this point, the bug is fixed
        assert buffer is not None
        assert buffer.size.width == 640
        assert buffer.size.height == 480
        
        # Optional: Verify we can convert to PIL Image
        try:
            pil_image = buffer.to_pil_image()
            assert pil_image is not None
            assert pil_image.size == (640, 480)
        except Exception as e:
            pytest.fail(f"Failed to convert buffer to PIL image: {e}")


if __name__ == "__main__":
    # Run just this test file
    pytest.main([__file__, "-v"]) 