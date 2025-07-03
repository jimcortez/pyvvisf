"""Utility functions for pyvvisf."""

from . import vvisf_bindings as _vvisf

# Utility functions
reinitialize_glfw_context = _vvisf.reinitialize_glfw_context
get_gl_info = _vvisf.get_gl_info
get_platform_info = _vvisf.get_platform_info
is_vvisf_available = _vvisf.is_vvisf_available
initialize_glfw_context = _vvisf.initialize_glfw_context
cleanup_glfw_context = _vvisf.cleanup_glfw_context
acquire_context_ref = _vvisf.acquire_context_ref
release_context_ref = _vvisf.release_context_ref
validate_gl_context = _vvisf.validate_gl_context
check_gl_errors = _vvisf.check_gl_errors
reset_gl_context_state = _vvisf.reset_gl_context_state
CreateGLBufferRef = _vvisf.CreateGLBufferRef


def check_vvisf_availability():
    """Check if VVISF is properly initialized and available."""
    try:
        return is_vvisf_available()
    except Exception:
        return False


def _initialize_on_import():
    """Initialize GLFW context when the module is imported."""
    try:
        # Check if GLFW is already initialized
        gl_info = get_gl_info()
        if not gl_info.get('glfw_initialized', False):
            # Initialize GLFW context automatically
            if initialize_glfw_context():
                print("[pyvvisf] GLFW context initialized automatically")
            else:
                print("[pyvvisf] Warning: Failed to initialize GLFW context automatically")
                print("[pyvvisf] You may need to call initialize_glfw_context() manually before rendering")
    except Exception as e:
        print(f"[pyvvisf] Warning: Could not initialize GLFW context: {e}")
        print("[pyvvisf] You may need to call initialize_glfw_context() manually before rendering") 