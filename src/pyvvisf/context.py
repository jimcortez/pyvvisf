"""GLFW window/OpenGL context lifecycle management."""

import logging

import glfw
from OpenGL import GL

from .errors import ContextError

logger = logging.getLogger(__name__)


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

        if not glfw.init():
            raise ContextError("Failed to initialize GLFW")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.VISIBLE, glfw.TRUE if visible else glfw.FALSE)

        self.window = glfw.create_window(width, height, "ISF Renderer", None, None)
        if not self.window:
            glfw.terminate()
            raise ContextError("Failed to create GLFW window")

        glfw.make_context_current(self.window)

        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)

        self.initialized = True
        self.visible = visible
        logger.info("GLFW context initialized successfully")

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
            glfw.terminate()
            self.initialized = False
            self.visible = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
