import glfw
from OpenGL.GL import *
import numpy as np
import ctypes

VERTEX_SHADER = """
#version 330
layout(location = 0) in vec2 position;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330
uniform vec4 uColor;
out vec4 fragColor;
void main() {
    fragColor = uColor;
}
"""

def main():
    if not glfw.init():
        raise RuntimeError("Failed to initialize GLFW")
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    window = glfw.create_window(256, 256, "Uniform Test", None, None)
    if not window:
        glfw.terminate()
        raise RuntimeError("Failed to create window")
    glfw.make_context_current(window)

    # Compile shaders
    vs = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vs, VERTEX_SHADER)
    glCompileShader(vs)
    if not glGetShaderiv(vs, GL_COMPILE_STATUS):
        print(glGetShaderInfoLog(vs).decode())
        raise RuntimeError("Vertex shader compilation failed")
    fs = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fs, FRAGMENT_SHADER)
    glCompileShader(fs)
    if not glGetShaderiv(fs, GL_COMPILE_STATUS):
        print(glGetShaderInfoLog(fs).decode())
        raise RuntimeError("Fragment shader compilation failed")
    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glLinkProgram(prog)
    if not glGetProgramiv(prog, GL_LINK_STATUS):
        print(glGetProgramInfoLog(prog).decode())
        raise RuntimeError("Program linking failed")
    glUseProgram(prog)

    # Setup quad
    vertices = np.array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
         1.0,  1.0,
    ], dtype=np.float32)
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

    # Set uniform
    color_loc = glGetUniformLocation(prog, "uColor")
    print("Uniform location for uColor:", color_loc)
    glUniform4f(color_loc, 0.8, 0.6, 0.4, 1.0)
    print("glGetError after glUniform4f:", glGetError())

    # Render
    glClearColor(0, 0, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT)
    glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
    glFlush()
    glFinish()

    # Read pixels
    data = glReadPixels(0, 0, 256, 256, GL_RGBA, GL_UNSIGNED_BYTE)
    if not isinstance(data, bytes):
        data = bytes(data)
    arr = np.frombuffer(data, dtype=np.uint8).reshape(256, 256, 4)
    print("Top-left pixel RGBA:", arr[0, 0, :])
    print("Center pixel RGBA:", arr[128, 128, :])
    print("Bottom-right pixel RGBA:", arr[-1, -1, :])

    glfw.destroy_window(window)
    glfw.terminate()

if __name__ == "__main__":
    main() 