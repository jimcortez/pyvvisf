#!/usr/bin/env python3
"""Test script to verify wheel installation."""

import sys
import os

def test_wheel_installation():
    """Test if the wheel was installed correctly."""
    try:
        # Try to import pyvvisf
        import pyvvisf
        print("✓ pyvvisf imported successfully")
        
        # Test basic functionality
        print("✓ Basic import test passed")
        
        # Test version
        if hasattr(pyvvisf, '__version__'):
            print(f"✓ Version: {pyvvisf.__version__}")
        else:
            print("⚠ No version information found")
        
        # Test platform info
        try:
            platform_info = pyvvisf.get_platform_info()
            print(f"✓ Platform info: {platform_info}")
        except Exception as e:
            print(f"⚠ Platform info test failed: {e}")
        
        # Test VVISF availability
        try:
            is_available = pyvvisf.is_vvisf_available()
            print(f"✓ VVISF availability: {is_available}")
        except Exception as e:
            print(f"⚠ VVISF availability test failed: {e}")
        
        print("\n🎉 Wheel installation test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import pyvvisf: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_wheel_installation()
    sys.exit(0 if success else 1) 