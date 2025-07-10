"""Tests for the pure Python ISF renderer."""

import pytest
import numpy as np
from pathlib import Path

# Import the new implementation
from pyvvisf.parser import ISFParser, ISFMetadata
from pyvvisf.types import ISFColor, ISFPoint2D, ISFFloat, ISFInt, ISFBool
from pyvvisf.errors import ISFParseError, ValidationError


class TestISFParser:
    """Test ISF parser functionality."""
    
    def setup_method(self):
        self.parser = ISFParser()
    
    def test_parse_simple_shader(self):
        """Test parsing a simple shader without metadata."""
        shader_content = """
        /*{"NAME": "SimpleTest", "INPUTS": []}*/
        uniform vec2 RENDERSIZE;
        
        void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
        }
        """
        
        glsl_code, metadata = self.parser.parse_content(shader_content)
        
        assert "gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);" in glsl_code
        assert metadata.name is not None
        assert metadata.inputs is not None
    
    def test_parse_shader_with_metadata(self):
        """Test parsing a shader with JSON metadata."""
        shader_content = """
        /*{
            "NAME": "Test Shader",
            "DESCRIPTION": "A test shader",
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0]
                },
                {
                    "NAME": "scale",
                    "TYPE": "float",
                    "DEFAULT": 1.0,
                    "MIN": 0.1,
                    "MAX": 5.0
                }
            ]
        }*/
        
        uniform vec2 RENDERSIZE;
        uniform vec4 color;
        uniform float scale;
        
        void main() {
            gl_FragColor = color * scale;
        }
        """
        
        glsl_code, metadata = self.parser.parse_content(shader_content)
        
        assert metadata.name == "Test Shader"
        assert metadata.description == "A test shader"
        assert metadata.inputs is not None
        assert len(metadata.inputs) == 2
        assert metadata.inputs[0].name == "color"
        assert metadata.inputs[0].type == "color"
        assert metadata.inputs[1].name == "scale"
        assert metadata.inputs[1].type == "float"
        assert metadata.inputs[1].min == 0.1
        assert metadata.inputs[1].max == 5.0
        
        # Check that JSON was removed from GLSL
        assert "/*{" not in glsl_code
        assert "}*/" not in glsl_code
        assert "gl_FragColor = color * scale;" in glsl_code
    
    def test_parse_invalid_json(self):
        """Test parsing with invalid JSON metadata."""
        shader_content = """
        /*{
            "NAME": "Test Shader",
            "INPUTS": [
                {
                    "NAME": "color",
                    "TYPE": "color",
                    "DEFAULT": [1.0, 0.0, 0.0, 1.0,  // Missing closing bracket
                }
            ]
        }*/
        
        void main() {
            gl_FragColor = vec4(1.0);
        }
        """
        
        with pytest.raises(ISFParseError):
            self.parser.parse_content(shader_content)
    
    def test_validate_inputs(self):
        """Test input validation."""
        from pyvvisf.parser import ISFInput
        
        metadata = ISFMetadata(
            inputs=[
                ISFInput(
                    name='color',
                    type='color',
                    default=[1.0, 0.0, 0.0, 1.0],
                    min=None,
                    max=None
                ),
                ISFInput(
                    name='scale',
                    type='float',
                    default=1.0,
                    min=0.1,
                    max=5.0
                )
            ]
        )
        
        # Test valid inputs
        inputs = {
            'color': [0.0, 1.0, 0.0, 1.0],
            'scale': 2.0
        }
        
        validated = self.parser.validate_inputs(metadata, inputs)
        assert 'color' in validated
        assert 'scale' in validated
        assert isinstance(validated['color'], ISFColor)
        assert isinstance(validated['scale'], ISFFloat)
        assert validated['scale'].value == 2.0
        
        # Test invalid range
        inputs = {'scale': 10.0}  # Above max
        from pyvvisf.errors import ShaderCompilationError
        with pytest.raises(ShaderCompilationError):
            self.parser.validate_inputs(metadata, inputs)


class TestISFTypes:
    """Test ISF value types."""
    
    def test_isf_color(self):
        """Test ISFColor type."""
        color = ISFColor(1.0, 0.5, 0.0, 1.0)
        assert color.r == 1.0
        assert color.g == 0.5
        assert color.b == 0.0
        assert color.a == 1.0
        
        # Test clamping
        color = ISFColor(2.0, -1.0, 0.5, 1.0)
        assert color.r == 1.0  # Clamped
        assert color.g == 0.0  # Clamped
        assert color.b == 0.5
        
        # Test from_tuple
        color = ISFColor.from_tuple([0.0, 1.0, 0.0, 0.5])
        assert color.r == 0.0
        assert color.g == 1.0
        assert color.b == 0.0
        assert color.a == 0.5
        
        # Test RGB only
        color = ISFColor.from_tuple([0.0, 1.0, 0.0])
        assert color.a == 1.0  # Default alpha
    
    def test_isf_point2d(self):
        """Test ISFPoint2D type."""
        point = ISFPoint2D(0.5, 0.3)
        assert point.x == 0.5
        assert point.y == 0.3
        
        # Test from_tuple
        point = ISFPoint2D.from_tuple([0.1, 0.9])
        assert point.x == 0.1
        assert point.y == 0.9
        
        # Test invalid tuple
        with pytest.raises(ValueError):
            ISFPoint2D.from_tuple([0.1, 0.9, 0.5])  # Too many values
    
    def test_isf_numeric_types(self):
        """Test numeric ISF types."""
        # Float
        float_val = ISFFloat(3.14)
        assert float_val.value == 3.14
        assert float(float_val) == 3.14
        assert int(float_val) == 3
        
        # Int
        int_val = ISFInt(42)
        assert int_val.value == 42
        assert int(int_val) == 42
        assert float(int_val) == 42.0
        
        # Bool
        bool_val = ISFBool(True)
        assert bool_val.value is True
        assert bool(bool_val) is True
    
    def test_coerce_to_isf_value(self):
        """Test value coercion."""
        from pyvvisf.types import coerce_to_isf_value
        
        # Test auto-coercion
        assert isinstance(coerce_to_isf_value([1.0, 0.0, 0.0]), ISFColor)
        assert isinstance(coerce_to_isf_value([0.5, 0.3]), ISFPoint2D)
        assert isinstance(coerce_to_isf_value(3.14), ISFFloat)
        assert isinstance(coerce_to_isf_value(42), ISFInt)
        assert isinstance(coerce_to_isf_value(True), ISFBool)
        
        # Test explicit coercion
        assert isinstance(coerce_to_isf_value([1.0, 0.0, 0.0], "color"), ISFColor)
        assert isinstance(coerce_to_isf_value([0.5, 0.3], "point2D"), ISFPoint2D)
        assert isinstance(coerce_to_isf_value(3.14, "float"), ISFFloat)
        assert isinstance(coerce_to_isf_value(42, "long"), ISFInt)
        assert isinstance(coerce_to_isf_value(True, "bool"), ISFBool)


class TestErrorHandling:
    """Test error handling."""
    
    def test_isf_error_with_context(self):
        """Test ISFError with context."""
        from pyvvisf.errors import ISFError
        
        error = ISFError("Test error", {"file": "test.fs", "line": 10})
        assert "Test error" in str(error)
        assert "file: test.fs" in str(error)
        assert "line: 10" in str(error)
    
    def test_parse_error(self):
        """Test ISFParseError."""
        error = ISFParseError("Parse failed", "invalid json", {"line": 5})
        assert "Parse failed" in str(error)
        assert "invalid json" in str(error)
        assert "line: 5" in str(error)
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid value", "scale", 10.0)
        assert "Invalid value" in str(error)
        assert "field: scale" in str(error)
        assert "value: 10.0" in str(error) 