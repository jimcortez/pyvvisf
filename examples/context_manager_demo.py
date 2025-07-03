#!/usr/bin/env python3
"""
Demonstration of the new GLContextManager for automatic GLFW/OpenGL context management.

This script shows how to use the GLContextManager to simplify context lifecycle management
and prevent common issues like segmentation faults and resource leaks.

Key features demonstrated:
1. Basic context management with 'with' statements
2. Automatic cleanup and error handling
3. Context reinitialization within a manager
4. Error checking and validation
5. Nested context managers
6. Custom configuration options
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def demo_basic_usage():
    """Demonstrate basic context manager usage."""
    print("1. Basic Context Manager Usage")
    print("-" * 40)
    
    try:
        import pyvvisf
        
        # Simple usage with automatic initialization and cleanup
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context initialized and acquired")
            
            # Create a simple test shader
            shader_content = """
            /*{
                "DESCRIPTION": "Basic test shader",
                "CREDIT": "Demo",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.2, 0.4, 0.8, 1.0);
            }
            """
            
            # Create ISF document and scene
            doc = pyvvisf.CreateISFDocRefWith(shader_content)
            scene = pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            # Render a frame
            size = pyvvisf.Size(256, 256)
            buffer = scene.create_and_render_a_buffer(size)
            
            if buffer and buffer.size.width == 256 and buffer.size.height == 256:
                print("✓ Rendering successful")
            else:
                print("✗ Rendering failed")
            
            # Check for OpenGL errors
            ctx.check_errors("basic rendering")
            
            print("✓ Context will be automatically cleaned up")
        
        print("✓ Basic usage demo completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Basic usage demo failed: {e}")
        return False

def demo_error_handling():
    """Demonstrate error handling and validation."""
    print("\n2. Error Handling and Validation")
    print("-" * 40)
    
    try:
        import pyvvisf
        
        with pyvvisf.GLContextManager(validate_on_enter=True) as ctx:
            print("✓ Context validated on entry")
            
            # Check context validity
            if ctx.is_valid():
                print("✓ Context is valid")
            else:
                print("✗ Context is invalid")
            
            # Get context information
            gl_info = ctx.get_info()
            print(f"✓ OpenGL Version: {gl_info.get('gl_version', 'Unknown')}")
            print(f"✓ GLFW Initialized: {gl_info.get('glfw_initialized', False)}")
            
            # Demonstrate error checking
            ctx.check_errors("validation check")
            print("✓ Error checking completed")
            
            # Reset context state
            ctx.reset_state()
            print("✓ Context state reset")
        
        print("✓ Error handling demo completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error handling demo failed: {e}")
        return False

def demo_context_reinitialization():
    """Demonstrate context reinitialization within a manager."""
    print("\n3. Context Reinitialization")
    print("-" * 40)
    
    try:
        import pyvvisf
        
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Initial context established")
            
            # Create a test shader
            shader_content = """
            /*{
                "DESCRIPTION": "Reinitialization test shader",
                "CREDIT": "Demo",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.8, 0.2, 0.4, 1.0);
            }
            """
            
            doc = pyvvisf.CreateISFDocRefWith(shader_content)
            scene = pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            # Render initial frame
            buffer1 = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
            print("✓ Initial render completed")
            
            # Reinitialize context
            print("  Reinitializing context...")
            ctx.reinitialize()
            print("✓ Context reinitialized")
            
            # Render after reinitialization
            buffer2 = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
            print("✓ Post-reinitialization render completed")
            
            # Verify both buffers are valid
            if buffer1 and buffer2:
                print("✓ Both renders successful")
            else:
                print("✗ One or both renders failed")
        
        print("✓ Context reinitialization demo completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Context reinitialization demo failed: {e}")
        return False

def demo_nested_contexts():
    """Demonstrate nested context managers."""
    print("\n4. Nested Context Managers")
    print("-" * 40)
    
    try:
        import pyvvisf
        
        # Outer context manager
        with pyvvisf.GLContextManager(auto_cleanup=False) as outer_ctx:
            print("✓ Outer context established")
            
            # Inner context manager (no auto-initialization since outer already did)
            with pyvvisf.GLContextManager(auto_initialize=False, auto_cleanup=False) as inner_ctx:
                print("✓ Inner context established")
                
                # Both contexts should be valid
                if outer_ctx.is_valid() and inner_ctx.is_valid():
                    print("✓ Both contexts are valid")
                else:
                    print("✗ One or both contexts are invalid")
                
                # Render with inner context
                shader_content = """
                /*{
                    "DESCRIPTION": "Nested context test shader",
                    "CREDIT": "Demo",
                    "CATEGORIES": ["Test"],
                    "INPUTS": []
                }*/
                void main() {
                    gl_FragColor = vec4(0.4, 0.8, 0.2, 1.0);
                }
                """
                
                doc = pyvvisf.CreateISFDocRefWith(shader_content)
                scene = pyvvisf.CreateISFSceneRef()
                scene.use_doc(doc)
                
                buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
                if buffer:
                    print("✓ Nested rendering successful")
                else:
                    print("✗ Nested rendering failed")
                
                print("✓ Inner context will be cleaned up")
            
            print("✓ Outer context still active")
            
            # Outer context should still be valid
            if outer_ctx.is_valid():
                print("✓ Outer context remains valid after inner cleanup")
            else:
                print("✗ Outer context became invalid")
        
        print("✓ Nested contexts demo completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Nested contexts demo failed: {e}")
        return False

def demo_custom_configuration():
    """Demonstrate custom configuration options."""
    print("\n5. Custom Configuration Options")
    print("-" * 40)
    
    try:
        import pyvvisf
        
        # Context manager with custom settings
        with pyvvisf.GLContextManager(
            auto_initialize=True,
            auto_cleanup=True,
            validate_on_enter=False  # Skip validation for demo
        ) as ctx:
            print("✓ Custom context established (no validation on entry)")
            
            # Manually validate
            if ctx.is_valid():
                print("✓ Manual validation successful")
            else:
                print("✗ Manual validation failed")
            
            # Test rendering
            shader_content = """
            /*{
                "DESCRIPTION": "Custom config test shader",
                "CREDIT": "Demo",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.6, 0.6, 0.6, 1.0);
            }
            """
            
            doc = pyvvisf.CreateISFDocRefWith(shader_content)
            scene = pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            buffer = scene.create_and_render_a_buffer(pyvvisf.Size(96, 96))
            if buffer:
                print("✓ Custom config rendering successful")
            else:
                print("✗ Custom config rendering failed")
        
        print("✓ Custom configuration demo completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Custom configuration demo failed: {e}")
        return False

def demo_batch_operations():
    """Demonstrate batch operations with context management."""
    print("\n6. Batch Operations")
    print("-" * 40)
    
    try:
        import pyvvisf
        
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context established for batch operations")
            
            # Create multiple shaders and render them
            shaders = [
                ("red", "vec4(1.0, 0.0, 0.0, 1.0)"),
                ("green", "vec4(0.0, 1.0, 0.0, 1.0)"),
                ("blue", "vec4(0.0, 0.0, 1.0, 1.0)"),
            ]
            
            buffers = []
            
            for name, color in shaders:
                print(f"  Rendering {name} shader...")
                
                shader_content = f"""
                /*{{
                    "DESCRIPTION": "{name.capitalize()} test shader",
                    "CREDIT": "Demo",
                    "CATEGORIES": ["Test"],
                    "INPUTS": []
                }}*/
                void main() {{
                    gl_FragColor = {color};
                }}
                """
                
                doc = pyvvisf.CreateISFDocRefWith(shader_content)
                scene = pyvvisf.CreateISFSceneRef()
                scene.use_doc(doc)
                
                buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
                if buffer:
                    buffers.append((name, buffer))
                    print(f"    ✓ {name} render successful")
                else:
                    print(f"    ✗ {name} render failed")
                
                # Check for errors after each render
                ctx.check_errors(f"{name} shader render")
            
            print(f"✓ Batch operations completed: {len(buffers)}/3 successful")
            return True
        
    except Exception as e:
        print(f"✗ Batch operations demo failed: {e}")
        return False

def main():
    """Run all context manager demonstrations."""
    print("pyvvisf GLContextManager Demonstration")
    print("=" * 50)
    
    try:
        import pyvvisf
        print(f"✓ pyvvisf version {pyvvisf.__version__} loaded successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyvvisf: {e}")
        return 1
    
    # Run all demos
    demos = [
        demo_basic_usage,
        demo_error_handling,
        demo_context_reinitialization,
        demo_nested_contexts,
        demo_custom_configuration,
        demo_batch_operations,
    ]
    
    passed = 0
    total = len(demos)
    
    for demo in demos:
        try:
            if demo():
                passed += 1
        except Exception as e:
            print(f"✗ Demo failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎉 DEMONSTRATION COMPLETED: {passed}/{total} demos passed")
    print("=" * 50)
    
    if passed == total:
        print("\nSummary of GLContextManager features:")
        print("✓ Automatic context initialization and cleanup")
        print("✓ Error handling and validation")
        print("✓ Context reinitialization within manager")
        print("✓ Nested context management")
        print("✓ Custom configuration options")
        print("✓ Batch operation support")
        print("\nThe GLContextManager provides a safe and convenient way")
        print("to manage GLFW/OpenGL contexts without manual cleanup!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} demos failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 