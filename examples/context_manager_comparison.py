#!/usr/bin/env python3
"""
Comparison between manual context management and the new GLContextManager.

This script demonstrates the difference between the old manual approach
and the new convenient context manager approach for managing GLFW/OpenGL contexts.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def manual_context_management():
    """Demonstrate the old manual way of managing contexts."""
    print("OLD WAY: Manual Context Management")
    print("=" * 50)
    
    try:
        import pyvvisf
        
        # Manual initialization
        if not pyvvisf.initialize_glfw_context():
            raise RuntimeError("Failed to initialize GLFW context")
        print("✓ Context initialized manually")
        
        # Manual context acquisition
        pyvvisf.acquire_context_ref()
        print("✓ Context reference acquired manually")
        
        # Manual validation
        if not pyvvisf.validate_gl_context():
            raise RuntimeError("Context validation failed")
        print("✓ Context validated manually")
        
        # Manual state reset
        pyvvisf.reset_gl_context_state()
        print("✓ Context state reset manually")
        
        # Create and render
        shader_content = """
        /*{
            "DESCRIPTION": "Manual management test",
            "CREDIT": "Demo",
            "CATEGORIES": ["Test"],
            "INPUTS": []
        }*/
        void main() {
            gl_FragColor = vec4(0.8, 0.2, 0.6, 1.0);
        }
        """
        
        doc = pyvvisf.CreateISFDocRefWith(shader_content)
        scene = pyvvisf.CreateISFSceneRef()
        scene.use_doc(doc)
        
        buffer = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
        if buffer:
            print("✓ Rendering successful")
        else:
            print("✗ Rendering failed")
        
        # Manual error checking
        pyvvisf.check_gl_errors("manual rendering")
        print("✓ Error checking completed manually")
        
        # Manual cleanup (MUST NOT FORGET!)
        pyvvisf.release_context_ref()
        pyvvisf.cleanup_glfw_context()
        print("✓ Manual cleanup completed")
        
        print("\n⚠️  PROBLEMS WITH MANUAL APPROACH:")
        print("  - Easy to forget cleanup")
        print("  - Error handling is manual")
        print("  - No automatic resource management")
        print("  - Risk of segmentation faults")
        print("  - Verbose and error-prone")
        
        return True
        
    except Exception as e:
        print(f"✗ Manual approach failed: {e}")
        # Still need to cleanup even on error!
        try:
            pyvvisf.release_context_ref()
            pyvvisf.cleanup_glfw_context()
        except:
            pass
        return False

def context_manager_approach():
    """Demonstrate the new context manager approach."""
    print("\nNEW WAY: Context Manager Approach")
    print("=" * 50)
    
    try:
        import pyvvisf
        
        # Simple and clean with automatic management
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context automatically initialized and acquired")
            print("✓ Context automatically validated")
            print("✓ Context state automatically reset")
            
            # Create and render
            shader_content = """
            /*{
                "DESCRIPTION": "Context manager test",
                "CREDIT": "Demo",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.2, 0.8, 0.4, 1.0);
            }
            """
            
            doc = pyvvisf.CreateISFDocRefWith(shader_content)
            scene = pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            buffer = scene.create_and_render_a_buffer(pyvvisf.Size(128, 128))
            if buffer:
                print("✓ Rendering successful")
            else:
                print("✗ Rendering failed")
            
            # Convenient error checking
            ctx.check_errors("context manager rendering")
            print("✓ Error checking completed")
            
            # Context automatically cleaned up when exiting the block
            print("✓ Context will be automatically cleaned up")
        
        print("\n✅ BENEFITS OF CONTEXT MANAGER:")
        print("  - Automatic cleanup (no memory leaks)")
        print("  - Exception-safe resource management")
        print("  - Cleaner, more readable code")
        print("  - Built-in error handling")
        print("  - No risk of forgetting cleanup")
        print("  - Prevents segmentation faults")
        
        return True
        
    except Exception as e:
        print(f"✗ Context manager approach failed: {e}")
        return False

def demonstrate_nested_usage():
    """Demonstrate nested context manager usage."""
    print("\nNESTED CONTEXT MANAGER USAGE")
    print("=" * 50)
    
    try:
        import pyvvisf
        
        # Outer context
        with pyvvisf.GLContextManager(auto_cleanup=False) as outer_ctx:
            print("✓ Outer context established")
            
            # Inner context (reuses outer context)
            with pyvvisf.GLContextManager(auto_initialize=False, auto_cleanup=False) as inner_ctx:
                print("✓ Inner context established (reusing outer)")
                
                # Both contexts are valid
                if outer_ctx.is_valid() and inner_ctx.is_valid():
                    print("✓ Both contexts valid")
                
                # Render with inner context
                shader_content = """
                /*{
                    "DESCRIPTION": "Nested test",
                    "CREDIT": "Demo",
                    "CATEGORIES": ["Test"],
                    "INPUTS": []
                }*/
                void main() {
                    gl_FragColor = vec4(0.5, 0.5, 0.5, 1.0);
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
            
            print("✓ Inner context cleaned up, outer still active")
            
            # Outer context still valid
            if outer_ctx.is_valid():
                print("✓ Outer context remains valid")
        
        print("✓ All contexts cleaned up")
        return True
        
    except Exception as e:
        print(f"✗ Nested usage failed: {e}")
        return False

def demonstrate_batch_processing():
    """Demonstrate batch processing with context manager."""
    print("\nBATCH PROCESSING WITH CONTEXT MANAGER")
    print("=" * 50)
    
    try:
        import pyvvisf
        
        # Single context for multiple operations
        with pyvvisf.GLContextManager() as ctx:
            print("✓ Context established for batch processing")
            
            # Process multiple shaders
            shaders = [
                ("red", "vec4(1.0, 0.0, 0.0, 1.0)"),
                ("green", "vec4(0.0, 1.0, 0.0, 1.0)"),
                ("blue", "vec4(0.0, 0.0, 1.0, 1.0)"),
            ]
            
            results = []
            
            for name, color in shaders:
                print(f"  Processing {name} shader...")
                
                shader_content = f"""
                /*{{
                    "DESCRIPTION": "{name.capitalize()} shader",
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
                    results.append(name)
                    print(f"    ✓ {name} processed successfully")
                else:
                    print(f"    ✗ {name} processing failed")
                
                # Check for errors after each operation
                ctx.check_errors(f"{name} shader processing")
            
            print(f"✓ Batch processing completed: {len(results)}/3 successful")
        
        print("✓ Context automatically cleaned up after batch processing")
        return True
        
    except Exception as e:
        print(f"✗ Batch processing failed: {e}")
        return False

def main():
    """Run the comparison demonstrations."""
    print("pyvvisf Context Management Comparison")
    print("=" * 60)
    
    try:
        import pyvvisf
        print(f"✓ pyvvisf version {pyvvisf.__version__} loaded successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyvvisf: {e}")
        return 1
    
    # Run comparisons
    comparisons = [
        manual_context_management,
        context_manager_approach,
        demonstrate_nested_usage,
        demonstrate_batch_processing,
    ]
    
    passed = 0
    total = len(comparisons)
    
    for comparison in comparisons:
        try:
            if comparison():
                passed += 1
        except Exception as e:
            print(f"✗ Comparison failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎉 COMPARISON COMPLETED: {passed}/{total} demonstrations passed")
    print("=" * 60)
    
    if passed == total:
        print("\n📋 SUMMARY:")
        print("The GLContextManager provides a much safer and more convenient")
        print("way to manage GLFW/OpenGL contexts compared to manual management.")
        print("\nKey advantages:")
        print("  • Automatic resource cleanup")
        print("  • Exception safety")
        print("  • Cleaner, more readable code")
        print("  • Built-in error handling")
        print("  • Prevents common bugs and crashes")
        print("\nUse GLContextManager for all your pyvvisf rendering needs!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} demonstrations failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 