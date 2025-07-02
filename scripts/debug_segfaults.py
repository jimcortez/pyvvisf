#!/usr/bin/env python3
"""
Comprehensive debugging script for pyvvisf segmentation faults.

This script systematically tests different scenarios that can cause
segmentation faults and provides detailed logging to help identify
the root causes.
"""

import sys
import os
import traceback
import time
import subprocess
import signal
import psutil
from pathlib import Path
import logging
from contextlib import contextmanager

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('pyvvisf_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class SegfaultTester:
    """Test various scenarios that can cause segmentation faults."""
    
    def __init__(self):
        self.test_results = {}
        self.pyvvisf = None
        self.context_initialized = False
        
    def setup_pyvvisf(self):
        """Setup pyvvisf with comprehensive error handling."""
        try:
            import pyvvisf
            self.pyvvisf = pyvvisf
            logger.info("pyvvisf imported successfully")
            
            # Get initial GL info
            try:
                gl_info = pyvvisf.get_gl_info()
                logger.info(f"Initial GL info: {gl_info}")
            except Exception as e:
                logger.warning(f"Failed to get initial GL info: {e}")
            
            # Initialize context
            if pyvvisf.initialize_glfw_context():
                self.context_initialized = True
                logger.info("GLFW context initialized successfully")
                
                # Get GL info after initialization
                gl_info = pyvvisf.get_gl_info()
                logger.info(f"GL info after initialization: {gl_info}")
            else:
                logger.error("Failed to initialize GLFW context")
                return False
                
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import pyvvisf: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during pyvvisf setup: {e}")
            logger.error(traceback.format_exc())
            return False
    
    @contextmanager
    def safe_test(self, test_name):
        """Context manager for safe test execution with cleanup."""
        logger.info(f"Starting test: {test_name}")
        start_time = time.time()
        
        try:
            yield
            elapsed = time.time() - start_time
            logger.info(f"Test '{test_name}' completed successfully in {elapsed:.3f}s")
            self.test_results[test_name] = "PASS"
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Test '{test_name}' failed after {elapsed:.3f}s: {e}")
            logger.error(traceback.format_exc())
            self.test_results[test_name] = f"FAIL: {e}"
            
            # Force cleanup after failure
            self.emergency_cleanup()
    
    def emergency_cleanup(self):
        """Emergency cleanup to prevent resource leaks."""
        try:
            if self.pyvvisf and hasattr(self.pyvvisf, 'reset_gl_context_state'):
                self.pyvvisf.reset_gl_context_state()
                logger.info("Emergency: OpenGL context state reset")
        except Exception as e:
            logger.warning(f"Emergency cleanup failed: {e}")
    
    def test_basic_scene_creation(self):
        """Test basic scene creation without rendering."""
        with self.safe_test("basic_scene_creation"):
            scene = self.pyvvisf.CreateISFSceneRef()
            assert scene is not None
            logger.info("Scene created successfully")
            
            # Test scene properties
            context = scene.context()
            logger.info(f"Scene context: {context}")
    
    def test_document_creation(self):
        """Test ISF document creation and validation."""
        with self.safe_test("document_creation"):
            shader_content = '''/*{
                "DESCRIPTION": "Debug test shader",
                "CREDIT": "Debug",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
            }'''
            
            doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
            assert doc is not None
            logger.info("Document created successfully")
            
            # Test document properties
            name = doc.name()
            description = doc.description()
            logger.info(f"Document - Name: {name}, Description: {description}")
    
    def test_scene_with_document(self):
        """Test scene with document loaded."""
        with self.safe_test("scene_with_document"):
            shader_content = '''/*{
                "DESCRIPTION": "Debug test shader",
                "CREDIT": "Debug", 
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.0, 1.0, 0.0, 1.0);
            }'''
            
            doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
            scene = self.pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            logger.info("Scene and document linked successfully")
            
            # Verify scene has document
            scene_doc = scene.doc()
            assert scene_doc is not None
            logger.info("Scene document verification successful")
    
    def test_minimal_rendering(self):
        """Test minimal rendering operation."""
        with self.safe_test("minimal_rendering"):
            shader_content = '''/*{
                "DESCRIPTION": "Minimal render test",
                "CREDIT": "Debug",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.5, 0.5, 0.5, 1.0);
            }'''
            
            # Create and setup scene
            doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
            scene = self.pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            # Reset context state before rendering
            if hasattr(self.pyvvisf, 'reset_gl_context_state'):
                self.pyvvisf.reset_gl_context_state()
            
            # Very small render to minimize resource usage
            size = self.pyvvisf.Size(16, 16)
            
            logger.info(f"Attempting render with size {size.width}x{size.height}")
            buffer = scene.create_and_render_a_buffer(size)
            
            assert buffer is not None
            assert buffer.size.width == 16
            assert buffer.size.height == 16
            
            logger.info("Minimal rendering successful")
    
    def test_context_reinitialization(self):
        """Test context reinitialization without crashes."""
        with self.safe_test("context_reinitialization"):
            logger.info("Testing context reinitialization")
            
            # Get initial state
            initial_info = self.pyvvisf.get_gl_info()
            logger.info(f"Initial context info: {initial_info}")
            
            # Reinitialize context
            success = self.pyvvisf.reinitialize_glfw_context()
            assert success, "Context reinitialization failed"
            
            # Verify new state
            new_info = self.pyvvisf.get_gl_info()
            logger.info(f"New context info: {new_info}")
            
            # Test basic functionality after reinitialization
            scene = self.pyvvisf.CreateISFSceneRef()
            assert scene is not None
            
            logger.info("Context reinitialization successful")
    
    def test_multiple_scenes(self):
        """Test creating multiple scenes without interference."""
        with self.safe_test("multiple_scenes"):
            scenes = []
            
            for i in range(3):
                shader_content = f'''/*{{
                    "DESCRIPTION": "Multi-scene test {i}",
                    "CREDIT": "Debug",
                    "CATEGORIES": ["Test"],
                    "INPUTS": []
                }}*/
                void main() {{
                    gl_FragColor = vec4({i * 0.3}, 0.0, 0.0, 1.0);
                }}'''
                
                doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
                scene = self.pyvvisf.CreateISFSceneRef()
                scene.use_doc(doc)
                scenes.append(scene)
                
                logger.info(f"Created scene {i}")
            
            logger.info(f"Successfully created {len(scenes)} scenes")
    
    def test_buffer_conversion(self):
        """Test buffer to PIL image conversion."""
        with self.safe_test("buffer_conversion"):
            shader_content = '''/*{
                "DESCRIPTION": "Buffer conversion test",
                "CREDIT": "Debug",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.8, 0.2, 0.4, 1.0);
            }'''
            
            doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
            scene = self.pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            # Render small buffer
            size = self.pyvvisf.Size(32, 32)
            buffer = scene.create_and_render_a_buffer(size)
            
            # Convert to PIL image
            pil_image = buffer.to_pil_image()
            assert pil_image is not None
            
            # Verify image properties
            pil_size = pil_image.size
            pil_mode = pil_image.mode
            
            logger.info(f"PIL Image - Size: {pil_size}, Mode: {pil_mode}")
            assert pil_size == (32, 32)
            
            logger.info("Buffer conversion successful")
    
    def test_stress_rendering(self):
        """Stress test with multiple rapid renders."""
        with self.safe_test("stress_rendering"):
            shader_content = '''/*{
                "DESCRIPTION": "Stress test shader",
                "CREDIT": "Debug",
                "CATEGORIES": ["Test"],
                "INPUTS": []
            }*/
            void main() {
                gl_FragColor = vec4(0.1, 0.9, 0.1, 1.0);
            }'''
            
            doc = self.pyvvisf.CreateISFDocRefWith(shader_content)
            scene = self.pyvvisf.CreateISFSceneRef()
            scene.use_doc(doc)
            
            # Multiple rapid renders
            for i in range(10):
                if hasattr(self.pyvvisf, 'reset_gl_context_state'):
                    self.pyvvisf.reset_gl_context_state()
                
                size = self.pyvvisf.Size(24, 24)
                buffer = scene.create_and_render_a_buffer(size)
                assert buffer is not None
                
                # Small delay between renders
                time.sleep(0.01)
                
                if i % 3 == 0:
                    logger.info(f"Stress render {i+1}/10 completed")
            
            logger.info("Stress rendering completed successfully")
    
    def run_all_tests(self):
        """Run all tests systematically."""
        if not self.setup_pyvvisf():
            logger.error("Failed to setup pyvvisf, aborting tests")
            return False
        
        tests = [
            self.test_basic_scene_creation,
            self.test_document_creation,
            self.test_scene_with_document,
            self.test_minimal_rendering,
            self.test_context_reinitialization,
            self.test_multiple_scenes,
            self.test_buffer_conversion,
            self.test_stress_rendering
        ]
        
        logger.info(f"Running {len(tests)} segfault tests")
        
        for test in tests:
            try:
                test()
                # Small delay between tests
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Critical error in test {test.__name__}: {e}")
                self.emergency_cleanup()
        
        # Final cleanup
        try:
            if hasattr(self.pyvvisf, 'cleanup_glfw_context'):
                self.pyvvisf.cleanup_glfw_context()
                logger.info("Final GLFW context cleanup completed")
        except Exception as e:
            logger.warning(f"Final cleanup failed: {e}")
        
        self.print_results()
        return all(result == "PASS" for result in self.test_results.values())
    
    def print_results(self):
        """Print comprehensive test results."""
        logger.info("\n" + "="*60)
        logger.info("SEGMENTATION FAULT TEST RESULTS")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == "PASS")
        
        for test_name, result in self.test_results.items():
            status = "✓ PASS" if result == "PASS" else f"✗ {result}"
            logger.info(f"{test_name:<30} {status}")
        
        logger.info("-"*60)
        logger.info(f"Total: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - No segmentation faults detected!")
        else:
            logger.error("❌ SOME TESTS FAILED - Segmentation faults still present")
        
        logger.info("="*60)

def run_subprocess_test():
    """Test CLI-like subprocess execution to detect SIGBUS/SIGSEGV."""
    logger.info("Testing subprocess execution (CLI simulation)")
    
    test_script = '''
import sys
sys.path.insert(0, "src")
try:
    import pyvvisf
    pyvvisf.initialize_glfw_context()
    scene = pyvvisf.CreateISFSceneRef()
    shader = """/*{
        "DESCRIPTION": "CLI test", "CREDIT": "Test", "CATEGORIES": ["Test"], "INPUTS": []
    }*/
    void main() { gl_FragColor = vec4(1.0); }"""
    doc = pyvvisf.CreateISFDocRefWith(shader)
    scene.use_doc(doc)
    buffer = scene.create_and_render_a_buffer(pyvvisf.Size(64, 64))
    print("SUCCESS: Subprocess rendering completed")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    '''
    
    try:
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("✓ Subprocess test PASSED")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"✗ Subprocess test FAILED with return code {result.returncode}")
            logger.error(f"Stdout: {result.stdout}")
            logger.error(f"Stderr: {result.stderr}")
            
            # Check for specific signals
            if result.returncode == -signal.SIGBUS:
                logger.error("❌ SIGBUS detected in subprocess (Bus error)")
            elif result.returncode == -signal.SIGSEGV:
                logger.error("❌ SIGSEGV detected in subprocess (Segmentation fault)")
            
    except subprocess.TimeoutExpired:
        logger.error("✗ Subprocess test TIMEOUT - possible infinite loop or hang")
    except Exception as e:
        logger.error(f"✗ Subprocess test ERROR: {e}")

def main():
    """Main debugging function."""
    logger.info("Starting comprehensive pyvvisf segfault debugging")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    
    # Log system information
    try:
        import platform
        logger.info(f"System: {platform.system()} {platform.release()}")
        logger.info(f"Architecture: {platform.architecture()}")
        logger.info(f"Processor: {platform.processor()}")
    except:
        pass
    
    # Test subprocess first (CLI simulation)
    run_subprocess_test()
    
    # Run comprehensive in-process tests
    tester = SegfaultTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("🎉 All debugging tests passed! Segmentation faults appear to be resolved.")
        return 0
    else:
        logger.error("❌ Some tests failed. Segmentation faults still present.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 