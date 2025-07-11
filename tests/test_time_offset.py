#!/usr/bin/env python3
"""
Test time offset functionality in pyvvisf.
"""

import pytest
import pyvvisf
from PIL import Image
import numpy as np

# Simple animated shader for testing
TEST_SHADER = """
/*{
    "DESCRIPTION": "Time-based test shader",
    "CREDIT": "Test",
    "CATEGORIES": ["Test"],
    "INPUTS": []
}*/

void main() {
    // Create a simple time-based pattern
    float time = TIME;
    vec2 uv = gl_FragCoord.xy / RENDERSIZE.xy;
    
    // Create a moving gradient based on time
    float gradient = sin(uv.x * 10.0 + time) * cos(uv.y * 10.0 + time * 0.5);
    
    // Create different colors for different time ranges
    vec3 color;
    if (time < 2.0) {
        color = vec3(1.0, 0.0, 0.0); // Red for 0-2s
    } else if (time < 4.0) {
        color = vec3(0.0, 1.0, 0.0); // Green for 2-4s
    } else if (time < 6.0) {
        color = vec3(0.0, 0.0, 1.0); // Blue for 4-6s
    } else {
        color = vec3(1.0, 1.0, 0.0); // Yellow for 6s+
    }
    
    gl_FragColor = vec4(color * (0.5 + 0.5 * gradient), 1.0);
}
"""

def test_time_offset_basic():
    """Test basic time offset functionality."""
    with pyvvisf.ISFRenderer(TEST_SHADER) as renderer:
        # Render at different time offsets
        buffer_0s = renderer.render(100, 100, time_offset=0.0)
        img_0s = buffer_0s.to_pil_image()
        buffer_3s = renderer.render(100, 100, time_offset=3.0)
        img_3s = buffer_3s.to_pil_image()
        buffer_5s = renderer.render(100, 100, time_offset=5.0)
        img_5s = buffer_5s.to_pil_image()
        buffer_7s = renderer.render(100, 100, time_offset=7.0)
        img_7s = buffer_7s.to_pil_image()
        
        # Convert to numpy arrays for comparison
        arr_0s = np.array(img_0s)
        arr_3s = np.array(img_3s)
        arr_5s = np.array(img_5s)
        arr_7s = np.array(img_7s)
        
        # Check that images are different (different time offsets produce different results)
        assert not np.array_equal(arr_0s, arr_3s), "Images at 0s and 3s should be different"
        assert not np.array_equal(arr_3s, arr_5s), "Images at 3s and 5s should be different"
        assert not np.array_equal(arr_5s, arr_7s), "Images at 5s and 7s should be different"
        
        # Check that images have the expected dimensions
        assert arr_0s.shape == (100, 100, 4), f"Expected shape (100, 100, 4), got {arr_0s.shape}"
        assert arr_3s.shape == (100, 100, 4), f"Expected shape (100, 100, 4), got {arr_3s.shape}"

def test_time_offset_default():
    """Test that default time_offset=0.0 works correctly."""
    with pyvvisf.ISFRenderer(TEST_SHADER) as renderer:
        # Render with explicit 0.0 and default (should be the same)
        buffer_explicit = renderer.render(50, 50, time_offset=0.0)
        img_explicit = buffer_explicit.to_pil_image()
        buffer_default = renderer.render(50, 50)  # Default time_offset=0.0
        img_default = buffer_default.to_pil_image()
        
        # Convert to numpy arrays
        arr_explicit = np.array(img_explicit)
        arr_default = np.array(img_default)
        
        # Should be identical
        assert np.array_equal(arr_explicit, arr_default), "Default and explicit time_offset=0.0 should be identical"

def test_time_offset_buffer():
    """Test time offset with render method."""
    with pyvvisf.ISFRenderer(TEST_SHADER) as renderer:
        # Render to buffer with different time offsets
        buffer_0s = renderer.render(64, 64, time_offset=0.0)
        buffer_4s = renderer.render(64, 64, time_offset=4.0)
        
        # Convert buffers to PIL images
        img_0s = buffer_0s.to_pil_image()
        img_4s = buffer_4s.to_pil_image()
        
        # Convert to numpy arrays
        arr_0s = np.array(img_0s)
        arr_4s = np.array(img_4s)
        
        # Should be different due to different time offsets
        assert not np.array_equal(arr_0s, arr_4s), "Buffers at different time offsets should be different"
        
        # Check dimensions
        assert arr_0s.shape == (64, 64, 4), f"Expected shape (64, 64, 4), got {arr_0s.shape}"

def test_time_offset_negative():
    """Test negative time offset values."""
    with pyvvisf.ISFRenderer(TEST_SHADER) as renderer:
        # Render with negative time offset
        buffer_neg = renderer.render(32, 32, time_offset=-1.0)
        img_neg = buffer_neg.to_pil_image()
        buffer_zero = renderer.render(32, 32, time_offset=0.0)
        img_zero = buffer_zero.to_pil_image()
        
        # Convert to numpy arrays
        arr_neg = np.array(img_neg)
        arr_zero = np.array(img_zero)
        
        # Should be different (negative time should produce different result)
        assert not np.array_equal(arr_neg, arr_zero), "Negative time offset should produce different result"

def test_time_offset_large():
    """Test large time offset values."""
    with pyvvisf.ISFRenderer(TEST_SHADER) as renderer:
        # Render with large time offset
        buffer_large = renderer.render(32, 32, time_offset=100.0)
        img_large = buffer_large.to_pil_image()
        
        # Convert to numpy array
        arr_large = np.array(img_large)
        
        # Should have correct dimensions
        assert arr_large.shape == (32, 32, 4), f"Expected shape (32, 32, 4), got {arr_large.shape}"
        
        # Should not be all zeros or all ones (should have some variation)
        assert not np.all(arr_large == 0), "Image should not be all zeros"
        assert not np.all(arr_large == 255), "Image should not be all ones"


def test_color_matches_expected_at_timecodes():
    """Test that rendering at specific time codes produces the expected solid color output."""
    # Shader: red at t<1, green at 1<=t<2, blue at 2<=t<3, white at t>=3
    color_shader = """
    /*{
        "DESCRIPTION": "Solid color changes with time",
        "CREDIT": "Test",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        float t = TIME;
        vec4 color;
        if (t < 1.0) {
            color = vec4(1.0, 0.0, 0.0, 1.0); // Red
        } else if (t < 2.0) {
            color = vec4(0.0, 1.0, 0.0, 1.0); // Green
        } else if (t < 3.0) {
            color = vec4(0.0, 0.0, 1.0, 1.0); // Blue
        } else {
            color = vec4(1.0, 1.0, 1.0, 1.0); // White
        }
        gl_FragColor = color;
    }
    """
    expected_colors = [
        (0.0, [255, 0, 0, 255]),    # t=0.0, red
        (1.0, [0, 255, 0, 255]),    # t=1.0, green
        (2.0, [0, 0, 255, 255]),    # t=2.0, blue
        (3.0, [255, 255, 255, 255]) # t=3.0, white
    ]
    with pyvvisf.ISFRenderer(color_shader) as renderer:
        for t, expected in expected_colors:
            buffer = renderer.render(4, 4, time_offset=t)
            img = buffer.to_pil_image()
            arr = np.array(img)
            # Check that all pixels match expected color (allowing for small rounding error)
            for i, channel in enumerate(['R', 'G', 'B', 'A']):
                assert np.allclose(arr[..., i], expected[i], atol=2), \
                    f"At t={t}, channel {channel} not as expected: got {arr[..., i]}, expected {expected[i]}"

if __name__ == "__main__":
    # Run tests
    test_time_offset_basic()
    test_time_offset_default()
    test_time_offset_buffer()
    test_time_offset_negative()
    test_time_offset_large() 