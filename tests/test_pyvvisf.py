"""Tests for pyvvisf package."""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_import_pyvvisf():
    """Test that pyvvisf can be imported."""
    try:
        import pyvvisf
        assert pyvvisf is not None
    except ImportError as e:
        pytest.skip(f"pyvvisf not available: {e}")


def test_platform_info():
    """Test that platform info can be retrieved."""
    try:
        import pyvvisf
        platform_info = pyvvisf.get_platform_info()
        assert isinstance(platform_info, str)
        assert len(platform_info) > 0
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_gl_info():
    """Test that OpenGL info can be retrieved."""
    try:
        import pyvvisf
        gl_info = pyvvisf.get_gl_info()
        assert isinstance(gl_info, dict)
        assert "glfw_initialized" in gl_info
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_vvisf_availability():
    """Test that VVISF availability can be checked."""
    try:
        import pyvvisf
        available = pyvvisf.is_vvisf_available()
        assert isinstance(available, bool)
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_isf_val_types():
    """Test that ISF value types can be created."""
    try:
        import pyvvisf
        
        # Test boolean value
        bool_val = pyvvisf.ISFBoolVal(True)
        assert bool_val is not None
        
        # Test integer value
        int_val = pyvvisf.ISFLongVal(42)
        assert int_val is not None
        
        # Test float value
        float_val = pyvvisf.ISFFloatVal(3.14)
        assert float_val is not None
        
        # Test color value
        color_val = pyvvisf.ISFColorVal(1.0, 0.0, 0.0, 1.0)
        assert color_val is not None
        
        # Test point value
        point_val = pyvvisf.ISFPoint2DVal(100.0, 200.0)
        assert point_val is not None
        
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_isf_scene_creation():
    """Test that ISF scene can be created."""
    try:
        import pyvvisf
        
        # Initialize context
        if not pyvvisf.initialize_glfw_context():
            pytest.skip("Failed to initialize GLFW context")
        
        # Create scene
        scene = pyvvisf.CreateISFSceneRef()
        assert scene is not None
        
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_isf_doc_creation():
    """Test that ISF document can be created from shader content."""
    try:
        import pyvvisf
        
        # Simple test shader
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
        
        # Create document
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        assert doc is not None
        
        # Check document properties
        assert doc.name() is not None
        assert doc.description() is not None
        
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_gl_buffer_creation():
    """Test that GL buffer can be created."""
    try:
        import pyvvisf
        
        # Initialize context
        if not pyvvisf.initialize_glfw_context():
            pytest.skip("Failed to initialize GLFW context")
        
        # Create size
        size = pyvvisf.Size(100, 100)
        assert size is not None
        assert size.width == 100
        assert size.height == 100
        
        # Create buffer
        buffer = pyvvisf.CreateGLBufferRef()
        assert buffer is not None
        
    except ImportError:
        pytest.skip("pyvvisf not available")



def test_isf_val_type_strings():
    """Test ISF value type string conversion."""
    try:
        import pyvvisf
        
        # Test value type to string conversion
        type_str = pyvvisf.isf_val_type_to_string(pyvvisf.ISFValType_Bool)
        assert isinstance(type_str, str)
        assert len(type_str) > 0
        
        # Test file type to string conversion
        file_type_str = pyvvisf.isf_file_type_to_string(pyvvisf.ISFFileType_None)
        assert isinstance(file_type_str, str)
        assert len(file_type_str) > 0
        
    except ImportError:
        pytest.skip("pyvvisf not available")


if __name__ == "__main__":
    pytest.main([__file__]) 