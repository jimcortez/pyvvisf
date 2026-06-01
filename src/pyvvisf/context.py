"""GLFW window/OpenGL context lifecycle management."""

import logging
import sys

import glfw
from OpenGL import GL

from .errors import ContextError

logger = logging.getLogger(__name__)

# GLFW init/terminate are process-global. Multiple ISFRenderer instances must
# share a single init() and only the last one to clean up should terminate().
_glfw_init_refcount = 0


def _glfw_error_callback(error: int, description):
    """Forward GLFW errors into our logger so init/create-window failures
    don't surface as the bare 'Failed to create GLFW window' message."""
    if isinstance(description, bytes):
        description = description.decode("utf-8", errors="replace")
    logger.warning("GLFW error 0x%X: %s", error, description)


def _glfw_acquire():
    """Initialize GLFW (if needed) and bump the refcount."""
    global _glfw_init_refcount
    if _glfw_init_refcount == 0:
        glfw.set_error_callback(_glfw_error_callback)
        if not glfw.init():
            raise ContextError("Failed to initialize GLFW")
    _glfw_init_refcount += 1


def _glfw_release():
    """Decrement the refcount and call glfw.terminate() when it hits zero."""
    global _glfw_init_refcount
    if _glfw_init_refcount <= 0:
        return
    _glfw_init_refcount -= 1
    if _glfw_init_refcount == 0:
        glfw.terminate()


class GLContextManager:
    """Manages the creation and lifetime of a GLFW OpenGL context."""

    def __init__(self):
        self.window = None
        self.initialized = False
        self.visible = False

    def initialize(self, width: int = 1, height: int = 1, visible: bool = False):
        """Initialize GLFW and create an OpenGL context.

        The window is hidden by default so that offscreen rendering does not
        flash a visible window on macOS/Windows. Pass ``visible=True`` (or call
        :meth:`show_window` later) when you need an interactive window.
        """
        if self.initialized:
            return

        _glfw_acquire()

        try:
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            # macOS requires OPENGL_FORWARD_COMPAT for any core profile context.
            # Setting it everywhere is harmless and makes behavior consistent.
            if sys.platform == "darwin":
                glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
            glfw.window_hint(glfw.VISIBLE, glfw.TRUE if visible else glfw.FALSE)

            self.window = glfw.create_window(width, height, "ISF Renderer", None, None)
            if not self.window:
                raise ContextError(
                    "Failed to create GLFW window. "
                    "On macOS this often means the runner has no graphics "
                    "session; on Linux, no DISPLAY / Xvfb is available."
                )

            glfw.make_context_current(self.window)

            GL.glClearColor(0.0, 0.0, 0.0, 1.0)
            GL.glEnable(GL.GL_DEPTH_TEST)

            self.initialized = True
            self.visible = visible
            logger.info("GLFW context initialized successfully")
        except Exception:
            _glfw_release()
            raise

    def show_window(self):
        """Make the window visible (used when entering interactive window mode)."""
        if self.window and not self.visible:
            glfw.show_window(self.window)
            self.visible = True

    def make_current(self):
        """Make this OpenGL context current."""
        if self.window:
            glfw.make_context_current(self.window)

    def cleanup(self):
        """Destroy the OpenGL context and release GLFW resources."""
        if self.window:
            glfw.destroy_window(self.window)
            self.window = None

        if self.initialized:
            _glfw_release()
            self.initialized = False
            self.visible = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
