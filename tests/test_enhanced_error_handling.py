"""Test enhanced error handling for create_and_render_a_buffer function."""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestEnhancedErrorHandling:
    """Test cases for enhanced error handling in pyvvisf."""
    
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
            
        except ImportError as e:
            pytest.skip(f"pyvvisf not available: {e}")

    def test_invalid_dimensions_negative_width(self):
        """Test that negative width raises appropriate error."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test negative width
        size = self.pyvvisf.Size(-100, 100)
        
        with pytest.raises(Exception) as exc_info:
            scene.create_and_render_a_buffer(size)
        
        # Should get an error about invalid dimensions
        assert "Invalid size" in str(exc_info.value) or "width and height must be positive" in str(exc_info.value)

    def test_invalid_dimensions_negative_height(self):
        """Test that negative height raises appropriate error."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test negative height
        size = self.pyvvisf.Size(100, -100)
        
        with pytest.raises(Exception) as exc_info:
            scene.create_and_render_a_buffer(size)
        
        # Should get an error about invalid dimensions
        assert "Invalid size" in str(exc_info.value) or "width and height must be positive" in str(exc_info.value)

    def test_invalid_dimensions_zero_width(self):
        """Test that zero width raises appropriate error."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test zero width
        size = self.pyvvisf.Size(0, 100)
        
        with pytest.raises(Exception) as exc_info:
            scene.create_and_render_a_buffer(size)
        
        # Should get an error about invalid dimensions
        assert "Invalid size" in str(exc_info.value) or "width and height must be positive" in str(exc_info.value)

    def test_invalid_dimensions_zero_height(self):
        """Test that zero height raises appropriate error."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test zero height
        size = self.pyvvisf.Size(100, 0)
        
        with pytest.raises(Exception) as exc_info:
            scene.create_and_render_a_buffer(size)
        
        # Should get an error about invalid dimensions
        assert "Invalid size" in str(exc_info.value) or "width and height must be positive" in str(exc_info.value)

    def test_excessive_dimensions(self):
        """Test that excessive dimensions raise appropriate error."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test excessive dimensions (larger than 16K)
        size = self.pyvvisf.Size(20000, 20000)
        
        with pytest.raises(Exception) as exc_info:
            scene.create_and_render_a_buffer(size)
        
        # Should get an error about size being too large
        assert "Size too large" in str(exc_info.value) or "maximum dimension" in str(exc_info.value)

    def test_scene_without_document(self):
        """Test that scene without document raises appropriate error."""
        scene = self.pyvvisf.CreateISFSceneRef()
        # Note: NOT calling scene.use_doc() to leave scene without document
        
        size = self.pyvvisf.Size(640, 480)
        
        with pytest.raises(Exception) as exc_info:
            scene.create_and_render_a_buffer(size)
        
        # Should get an error about no document
        assert "no document" in str(exc_info.value).lower() or "doc" in str(exc_info.value).lower()

    def test_valid_small_dimensions(self):
        """Test that valid small dimensions work correctly."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test very small but valid dimensions
        size = self.pyvvisf.Size(1, 1)
        buffer = scene.create_and_render_a_buffer(size)
        
        assert buffer is not None
        assert buffer.size.width == 1
        assert buffer.size.height == 1

    def test_valid_large_dimensions(self):
        """Test that valid large dimensions work correctly."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test large but valid dimensions (below 16K limit)
        size = self.pyvvisf.Size(4096, 4096)
        buffer = scene.create_and_render_a_buffer(size)
        
        assert buffer is not None
        assert buffer.size.width == 4096
        assert buffer.size.height == 4096

    def test_original_bug_dimensions_still_work(self):
        """Test that the original bug report dimensions (640x480) still work."""
        shader_content = '''/*{
    "DESCRIPTION": "Test shader",
    "CREDIT": "Test", 
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/
void main() { gl_FragColor = vec4(1.0); }'''

        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # Test the exact dimensions from the bug report
        size = self.pyvvisf.Size(640, 480)
        buffer = scene.create_and_render_a_buffer(size)
        
        assert buffer is not None
        assert buffer.size.width == 640
        assert buffer.size.height == 480
        
        # Test PIL conversion as well
        pil_image = buffer.to_pil_image()
        assert pil_image is not None
        assert pil_image.size == (640, 480)

    def test_error_recovery_after_failed_render(self):
        """Test that the system recovers properly after a failed render attempt."""
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() { gl_FragColor = vec4(1.0); }
        """
        
        doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
        scene = self.pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        # First, try an invalid operation
        invalid_size = self.pyvvisf.Size(-100, -100)
        with pytest.raises(Exception):
            scene.create_and_render_a_buffer(invalid_size)
        
        # Then, try a valid operation to ensure recovery
        valid_size = self.pyvvisf.Size(640, 480)
        buffer = scene.create_and_render_a_buffer(valid_size)
        
        assert buffer is not None
        assert buffer.size.width == 640
        assert buffer.size.height == 480


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 