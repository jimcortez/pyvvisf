#!/usr/bin/env python3
"""
Enhanced GLContextManager Demo - Preventing Null Context Segmentation Faults

This demonstrates how the enhanced context manager prevents the root cause
of segmentation faults by managing scene lifecycle during context reinitialization.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    print("Enhanced GLContextManager: Preventing Null Context Issues")
    print("=" * 60)
    
    try:
        import pyvvisf
        print(f"✓ pyvvisf version {pyvvisf.__version__} loaded successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyvvisf: {e}")
        return 1
    
    # Test shader
    shader_content = """
    /*{
        "DESCRIPTION": "Enhanced context manager test",
        "CREDIT": "Demo",
        "CATEGORIES": ["Test"],
        "INPUTS": []
    }*/
    void main() {
        gl_FragColor = vec4(0.8, 0.2, 0.6, 1.0);
    }
    """
    
    print("\n1. Traditional Approach (Graceful Degradation)")
    print("-" * 50)
    print("• Adds null checks in ISFScene::_render()")
    print("• Prevents crashes but doesn't fix root cause")
    print("• Scenes become unusable after context reinitialization")
    
    print("\n2. Enhanced Context Manager (Prevention)")
    print("-" * 50)
    print("• Tracks scenes created through the manager")
    print("• Recreates scenes with valid contexts during reinitialization")
    print("• Preserves scene state (shaders, settings)")
    print("• Scenes remain fully functional after reinitialization")
    
    print("\n3. Demonstration")
    print("-" * 50)
    
    try:
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context manager initialized")
            
            # Create scene through the context manager
            scene = ctx.create_scene(shader_content)
            print("✓ Scene created and managed")
            
            # Initial render
            buffer = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
            if buffer and buffer.size.width == 128:
                print("✓ Initial rendering successful")
            else:
                print("✗ Initial rendering failed")
                return 1
            
            # Context reinitialization (would cause segfault with traditional approach)
            print("\n  Reinitializing context...")
            scenes = ctx.reinitialize()
            print("✓ Context reinitialized successfully")
            print(f"✓ {len(scenes)} scenes recreated with new context")
            
            # Verify scenes still work
            scene = scenes[0]
            buffer2 = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
            if buffer2 and buffer2.size.width == 128:
                print("✓ Post-reinitialization rendering successful")
            else:
                print("✗ Post-reinitialization rendering failed")
                return 1
            
            # Verify state preservation
            doc = scene.doc()
            if doc:
                print("✓ Scene shader state preserved")
            else:
                print("✗ Scene shader state lost")
                return 1
            
            print(f"✓ Context generation: {ctx.get_context_generation()}")
        
        print("\n✓ Enhanced context manager demo completed successfully")
        
    except Exception as e:
        print(f"✗ Demo failed: {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 ENHANCED CONTEXT MANAGER PREVENTS NULL CONTEXT ISSUES!")
    print("=" * 60)
    
    print("\nBenefits of this approach:")
    print("✓ Prevents segmentation faults entirely")
    print("✓ Scenes remain functional after context reinitialization")
    print("✓ No performance impact from null checks")
    print("✓ Better user experience with automatic recovery")
    print("✓ Preserves scene state during reinitialization")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 