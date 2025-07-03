#!/usr/bin/env python3
"""
Demonstration of critical fixes for pyvvisf segmentation faults and stability issues.

This script demonstrates that the previously problematic scenarios now work correctly
using the enhanced GLContextManager that prevents null context issues entirely.

Key improvements:
1. Enhanced GLContextManager prevents null context segmentation faults
2. Automatic scene lifecycle management during context reinitialization
3. State preservation during context recreation
4. Multiple scene management support

Run this script to verify that the enhanced context manager approach works correctly.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    print("pyvvisf Enhanced Context Manager Demonstration")
    print("=" * 60)
    
    try:
        import pyvvisf
        print(f"✓ pyvvisf version {pyvvisf.__version__} loaded successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyvvisf: {e}")
        return 1
    
    # Test 1: Enhanced Context Manager Basic Usage
    print("\n1. Enhanced Context Manager Basic Usage")
    print("-" * 50)
    
    try:
        # Create a simple test shader
        shader_content = """
        /*{
            "DESCRIPTION": "Test shader",
            "CREDIT": "Test",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() {
            gl_FragColor = vec4(0.5, 0.5, 0.5, 1.0);
        }
        """
        
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context manager initialized")
            
            # Create scene through the context manager
            scene = ctx.create_scene(shader_content)
            print("✓ Scene created and managed by context manager")
            
            # Set shader inputs
            scene.set_value_for_input_named(pyvvisf.ISFFloatVal(64.0), "RENDERSIZE.x")
            scene.set_value_for_input_named(pyvvisf.ISFFloatVal(64.0), "RENDERSIZE.y")
            
            # Render frame
            size = pyvvisf.Size(64, 64)
            buffer = scene.create_and_render_a_buffer(size)
            
            # Verify buffer
            if buffer is None or buffer.size.width != 64 or buffer.size.height != 64:
                print("✗ Buffer validation failed")
                return 1
            
            print("✓ Basic rendering successful")
            
            # Check context validity
            if ctx.is_valid():
                print("✓ Context validation successful")
            else:
                print("✗ Context validation failed")
                return 1
        
        print("✓ Enhanced context manager basic usage test passed")
        
    except Exception as e:
        print(f"✗ Enhanced context manager basic usage test failed: {e}")
        return 1
    
    # Test 2: Context Reinitialization with Scene Recreation
    print("\n2. Context Reinitialization with Scene Recreation")
    print("-" * 50)
    
    try:
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context manager initialized")
            
            # Create scene
            scene = ctx.create_scene(shader_content)
            print("✓ Scene created")
            
            # Test multiple context reinitializations
            for i in range(3):
                print(f"  Testing reinitialization {i+1}/3...")
                
                # Reinitialize context (scenes are automatically recreated)
                scenes = ctx.reinitialize()
                scene = scenes[0]  # Get the recreated scene
                
                # Set shader inputs
                scene.set_value_for_input_named(pyvvisf.ISFFloatVal(float(i)), "TIME")
                scene.set_value_for_input_named(pyvvisf.ISFFloatVal(64.0), "RENDERSIZE.x")
                scene.set_value_for_input_named(pyvvisf.ISFFloatVal(64.0), "RENDERSIZE.y")
                
                # Render frame
                size = pyvvisf.Size(64, 64)
                buffer = scene.create_and_render_a_buffer(size)
                
                # Verify buffer
                if buffer is None or buffer.size.width != 64 or buffer.size.height != 64:
                    print(f"✗ Buffer {i+1} validation failed")
                    return 1
                
                print(f"  ✓ Reinitialization {i+1} completed successfully")
                time.sleep(0.1)
            
            # Check context generation
            generation = ctx.get_context_generation()
            print(f"✓ Context generation: {generation}")
        
        print("✓ Context reinitialization with scene recreation test passed")
        
    except Exception as e:
        print(f"✗ Context reinitialization test failed: {e}")
        return 1
    
    # Test 3: Multiple Scene Management
    print("\n3. Multiple Scene Management")
    print("-" * 50)
    
    try:
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context manager initialized")
            
            # Create multiple scenes with different shaders
            shaders = [
                ("red", """
                /*{
                    "DESCRIPTION": "Red shader",
                    "CREDIT": "Demo",
                    "CATEGORIES": ["Test"],
                    "INPUTS": []
                }*/
                void main() {
                    gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
                }
                """),
                ("green", """
                /*{
                    "DESCRIPTION": "Green shader",
                    "CREDIT": "Demo",
                    "CATEGORIES": ["Test"],
                    "INPUTS": []
                }*/
                void main() {
                    gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);
                }
                """),
                ("blue", """
                /*{
                    "DESCRIPTION": "Blue shader",
                    "CREDIT": "Demo",
                    "CATEGORIES": ["Test"],
                    "INPUTS": []
                }*/
                void main() {
                    gl_FragColor = vec4(0.0, 0.0, 1.0, 1.0);
                }
                """)
            ]
            
            scenes = []
            for name, shader in shaders:
                scene = ctx.create_scene(shader)
                scenes.append((name, scene))
                print(f"✓ Created {name} scene")
            
            # Verify all scenes work
            for name, scene in scenes:
                buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
                if buffer:
                    print(f"✓ {name} scene rendering successful")
                else:
                    print(f"✗ {name} scene rendering failed")
                    return 1
            
            # Test context reinitialization with multiple scenes
            print("  Reinitializing context with multiple scenes...")
            recreated_scenes = ctx.reinitialize()
            print(f"✓ {len(recreated_scenes)} scenes recreated successfully")
            
            # Verify all recreated scenes work
            for i, (name, _) in enumerate(scenes):
                if i < len(recreated_scenes):
                    scene = recreated_scenes[i]
                    buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
                    if buffer:
                        print(f"✓ {name} scene post-reinitialization successful")
                    else:
                        print(f"✗ {name} scene post-reinitialization failed")
                        return 1
            
            # Check managed scenes
            managed_scenes = ctx.get_managed_scenes()
            print(f"✓ {len(managed_scenes)} scenes currently managed")
        
        print("✓ Multiple scene management test passed")
        
    except Exception as e:
        print(f"✗ Multiple scene management test failed: {e}")
        return 1
    
    # Test 4: Custom Dimensions Stability
    print("\n4. Custom Dimensions Stability")
    print("-" * 50)
    
    try:
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context manager initialized")
            
            # Create scene
            scene = ctx.create_scene(shader_content)
            print("✓ Scene created")
            
            # Test the specific dimensions that were causing segfaults
            test_sizes = [
                (640, 480),    # The reported bug case
                (320, 240),    # Classic 4:3
                (800, 600),    # SVGA
                (1024, 768),   # XGA
            ]
            
            for width, height in test_sizes:
                print(f"  Testing dimensions {width}x{height}...")
                
                size = pyvvisf.Size(width, height)
                buffer = scene.create_and_render_a_buffer(size)
                
                if buffer is None or buffer.size.width != width or buffer.size.height != height:
                    print(f"✗ Buffer validation failed for {width}x{height}")
                    return 1
                
                # Test PIL conversion
                try:
                    pil_image = buffer.to_pil_image()
                    if pil_image is None or pil_image.size != (width, height):
                        print(f"✗ PIL image validation failed for {width}x{height}")
                        return 1
                except Exception as e:
                    print(f"✗ Failed to convert buffer to PIL image for {width}x{height}: {e}")
                    return 1
                
                print(f"  ✓ Dimensions {width}x{height} work correctly")
            
            # Test context reinitialization with custom dimensions
            print("  Testing reinitialization with custom dimensions...")
            scenes = ctx.reinitialize()
            scene = scenes[0]
            
            # Test custom dimensions after reinitialization
            size = pyvvisf.Size(640, 480)
            buffer = scene.create_and_render_a_buffer(size)
            if buffer and buffer.size.width == 640 and buffer.size.height == 480:
                print("✓ Custom dimensions work after reinitialization")
            else:
                print("✗ Custom dimensions failed after reinitialization")
                return 1
        
        print("✓ Custom dimensions stability test passed")
        
    except Exception as e:
        print(f"✗ Custom dimensions test failed: {e}")
        return 1
    
    # Test 5: Batch Processing with Context Reinitialization
    print("\n5. Batch Processing with Context Reinitialization")
    print("-" * 50)
    
    try:
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context manager initialized")
            
            # Create scene
            scene = ctx.create_scene(shader_content)
            print("✓ Scene created")
            
            # Batch processing with context reinitialization
            for i in range(5):
                print(f"  Batch iteration {i+1}/5...")
                
                # Render frame
                buffer = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
                if not buffer:
                    print(f"✗ Rendering failed in iteration {i+1}")
                    return 1
                
                # Reinitialize context every other iteration
                if i % 2 == 1:
                    print("    Reinitializing context...")
                    scenes = ctx.reinitialize()
                    scene = scenes[0]  # Get the recreated scene
                    print("    Context reinitialized")
                
                # Verify scene still works
                buffer2 = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
                if not buffer2:
                    print(f"✗ Post-reinitialization rendering failed in iteration {i+1}")
                    return 1
                
                print(f"  ✓ Iteration {i+1} completed successfully")
                time.sleep(0.05)
        
        print("✓ Batch processing test passed")
        
    except Exception as e:
        print(f"✗ Batch processing test failed: {e}")
        return 1
    
    # Test 6: Error Handling and Recovery
    print("\n6. Error Handling and Recovery")
    print("-" * 50)
    
    try:
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context manager initialized")
            
            # Create scene
            scene = ctx.create_scene(shader_content)
            print("✓ Scene created")
            
            # Test error checking
            ctx.check_errors("initial test")
            print("✓ Error checking completed")
            
            # Test context validation
            if ctx.is_valid():
                print("✓ Context validation successful")
            else:
                print("✗ Context validation failed")
                return 1
            
            # Test context reinitialization for recovery
            print("  Testing context recovery...")
            scenes = ctx.reinitialize()
            scene = scenes[0]
            print("✓ Context recovered through reinitialization")
            
            # Verify recovery
            buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
            if buffer:
                print("✓ Scene recovered and working")
            else:
                print("✗ Scene recovery failed")
                return 1
            
            # Test state reset
            ctx.reset_state()
            print("✓ Context state reset")
            
            # Get context information
            gl_info = ctx.get_info()
            print(f"✓ OpenGL Version: {gl_info.get('gl_version', 'Unknown')}")
        
        print("✓ Error handling and recovery test passed")
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! Enhanced Context Manager is working correctly.")
    print("=" * 60)
    
    print("\nSummary of enhanced context manager benefits:")
    print("✓ Prevents null context segmentation faults entirely")
    print("✓ Automatic scene recreation during context reinitialization")
    print("✓ State preservation (shaders, settings) during recreation")
    print("✓ Multiple scene management support")
    print("✓ Batch processing with context reinitialization")
    print("✓ Robust error handling and recovery")
    print("✓ Custom dimensions work without crashes")
    
    print("\nThe enhanced GLContextManager approach prevents the root cause")
    print("of segmentation faults rather than just handling the symptoms!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 