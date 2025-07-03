"""Test auto-coercion of Python primitives to ISF values."""

import pytest
import pyvvisf


def test_auto_coercion_basic_types():
    """Test that Python primitives are automatically coerced to ISF values."""
    
    # Simple shader with various input types
    shader_content = """
/*{
    "DESCRIPTION": "Test shader for auto-coercion",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": [
        {
            "NAME": "bool_input",
            "TYPE": "bool",
            "DEFAULT": false
        },
        {
            "NAME": "long_input", 
            "TYPE": "long",
            "DEFAULT": 0
        },
        {
            "NAME": "float_input",
            "TYPE": "float", 
            "DEFAULT": 0.0
        },
        {
            "NAME": "point_input",
            "TYPE": "point2D",
            "DEFAULT": [0.0, 0.0]
        },
        {
            "NAME": "color_input",
            "TYPE": "color",
            "DEFAULT": [0.0, 0.0, 0.0, 1.0]
        }
    ]
}*/

void main() {
    gl_FragColor = vec4(float(bool_input), float(long_input), float(float_input), 1.0);
}
"""
    
    try:
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Test boolean coercion
            renderer.set_input("bool_input", True)
            renderer.set_input("bool_input", 1)  # Should convert to True
            renderer.set_input("bool_input", 0.0)  # Should convert to False
            
            # Test long coercion
            renderer.set_input("long_input", 42)
            renderer.set_input("long_input", 3.14)  # Should convert to 3
            
            # Test float coercion
            renderer.set_input("float_input", 3.14)
            renderer.set_input("float_input", 42)  # Should convert to 42.0
            
            # Test point2D coercion
            renderer.set_input("point_input", (100.0, 200.0))
            renderer.set_input("point_input", [50.0, 75.0])
            
            # Test color coercion
            renderer.set_input("color_input", (1.0, 0.0, 0.0))  # RGB -> RGBA with alpha=1.0
            renderer.set_input("color_input", (0.0, 1.0, 0.0, 0.5))  # RGBA
            
            # Test that rendering works
            buffer = renderer.render(100, 100)
            assert buffer is not None
            
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_auto_coercion_error_handling():
    """Test that invalid types raise appropriate errors."""
    
    shader_content = """
/*{
    "DESCRIPTION": "Test shader for error handling",
    "CREDIT": "Test", 
    "CATEGORIES": ["Test"],
    "INPUTS": [
        {
            "NAME": "float_input",
            "TYPE": "float",
            "DEFAULT": 0.0
        },
        {
            "NAME": "color_input",
            "TYPE": "color", 
            "DEFAULT": [0.0, 0.0, 0.0, 1.0]
        }
    ]
}*/

void main() {
    gl_FragColor = vec4(float_input, 0.0, 0.0, 1.0);
}
"""
    
    try:
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Test invalid type for float
            with pytest.raises(pyvvisf.ShaderRenderingError) as exc_info:
                renderer.set_input("float_input", "not a number")
            assert "Cannot convert str to float" in str(exc_info.value)
            
            # Test invalid tuple for color
            with pytest.raises(pyvvisf.ShaderRenderingError) as exc_info:
                renderer.set_input("color_input", (1.0, 2.0))  # Only 2 values, need 3 or 4
            assert "Cannot convert" in str(exc_info.value) and "Color" in str(exc_info.value)
            
            # Test invalid tuple for color with wrong types
            with pytest.raises(pyvvisf.ShaderRenderingError) as exc_info:
                renderer.set_input("color_input", ("red", "green", "blue"))
            assert "values must be numbers" in str(exc_info.value)
            
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_auto_coercion_with_set_inputs():
    """Test that set_inputs works with Python primitives."""
    
    shader_content = """
/*{
    "DESCRIPTION": "Test shader for set_inputs",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"], 
    "INPUTS": [
        {
            "NAME": "bool_input",
            "TYPE": "bool",
            "DEFAULT": false
        },
        {
            "NAME": "float_input",
            "TYPE": "float",
            "DEFAULT": 0.0
        },
        {
            "NAME": "color_input",
            "TYPE": "color",
            "DEFAULT": [0.0, 0.0, 0.0, 1.0]
        }
    ]
}*/

void main() {
    gl_FragColor = vec4(float(bool_input), float_input, 0.0, 1.0);
}
"""
    
    try:
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Test setting multiple inputs with Python primitives
            renderer.set_inputs({
                "bool_input": True,
                "float_input": 0.5,
                "color_input": (1.0, 0.0, 0.0)  # RGB -> RGBA
            })
            
            # Verify the inputs were set correctly
            current_inputs = renderer.get_current_inputs()
            assert "bool_input" in current_inputs
            assert "float_input" in current_inputs
            assert "color_input" in current_inputs
            
            # Test that rendering works
            buffer = renderer.render(100, 100)
            assert buffer is not None
            
    except ImportError:
        pytest.skip("pyvvisf not available")


def test_auto_coercion_mixed_types():
    """Test mixing ISF values and Python primitives."""
    
    shader_content = """
/*{
    "DESCRIPTION": "Test shader for mixed types",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": [
        {
            "NAME": "float_input",
            "TYPE": "float",
            "DEFAULT": 0.0
        },
        {
            "NAME": "color_input",
            "TYPE": "color",
            "DEFAULT": [0.0, 0.0, 0.0, 1.0]
        }
    ]
}*/

void main() {
    gl_FragColor = color_input;
}
"""
    
    try:
        with pyvvisf.ISFRenderer(shader_content) as renderer:
            # Mix ISF values and Python primitives
            renderer.set_input("float_input", 0.5)  # Python primitive
            renderer.set_input("color_input", pyvvisf.ISFColorVal(0.0, 1.0, 0.0, 1.0))  # ISF value
            
            # Test that rendering works
            buffer = renderer.render(100, 100)
            assert buffer is not None
            
    except ImportError:
        pytest.skip("pyvvisf not available")


if __name__ == "__main__":
    # Run tests if executed directly
    test_auto_coercion_basic_types()
    test_auto_coercion_error_handling()
    test_auto_coercion_with_set_inputs()
    test_auto_coercion_mixed_types()
    print("All auto-coercion tests passed!") 