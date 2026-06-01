"""Full-screen quad geometry for ISF shaders."""

import ctypes

import numpy as np
from OpenGL import GL


class QuadRenderer:
    """Handles rendering a full-screen quad."""

    def __init__(self):
        self.vao = None
        self.vbo = None
        self.initialized = False

    def initialize(self):
        """Setup the quad geometry."""
        if self.initialized:
            return

        # fmt: off
        vertices = np.array([
            # position    # texcoord
            -1.0, -1.0,   0.0, 0.0,  # bottom-left
             1.0, -1.0,   1.0, 0.0,  # bottom-right
            -1.0,  1.0,   0.0, 1.0,  # top-left
             1.0,  1.0,   1.0, 1.0,  # top-right
        ], dtype=np.float32)
        # fmt: on

        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)

        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)

        stride = 4 * vertices.itemsize  # 4 floats per vertex

        # Position attribute (location = 0)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, stride, ctypes.c_void_p(0))

        # TexCoord attribute (location = 1)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(
            1, 2, GL.GL_FLOAT, GL.GL_FALSE, stride, ctypes.c_void_p(2 * vertices.itemsize)
        )

        GL.glBindVertexArray(0)
        self.initialized = True

    def draw(self):
        """Draw the quad."""
        if not self.initialized:
            self.initialize()

        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)
        GL.glBindVertexArray(0)

    def cleanup(self):
        """Clean up OpenGL resources."""
        if self.vao:
            GL.glDeleteVertexArrays(1, [self.vao])
            self.vao = None
        if self.vbo:
            GL.glDeleteBuffers(1, [self.vbo])
            self.vbo = None
        self.initialized = False
