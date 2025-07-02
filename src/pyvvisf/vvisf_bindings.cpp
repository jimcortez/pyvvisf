#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <string>
#include <memory>
#include <vector>
#include <map>
#include <optional>
#include <mutex>
#include <thread>
#include <chrono>

// VVISF includes
#include "VVISF.hpp"
#include "VVGL.hpp"
#include "GLBuffer_Enums_GLFW.h"
#include "ISFPassTarget.hpp"

// OpenGL includes for pixel operations
#include <GL/glew.h>

// GLFW for OpenGL context management
#include <GLFW/glfw3.h>

// PIL Image conversion utilities
#include <cstring>

namespace py = pybind11;

// Platform detection function
std::string get_platform_info() {
#ifdef VVGL_SDK_MAC
    return std::string("macOS (VVGL_SDK_MAC)");
#elif defined(VVGL_SDK_GLFW)
    return std::string("GLFW (VVGL_SDK_GLFW)");
#elif defined(VVGL_SDK_RPI)
    return std::string("Raspberry Pi (VVGL_SDK_RPI)");
#else
    return std::string("Unknown platform");
#endif
}

// Check if VVISF is available
bool is_vvisf_available() {
    try {
        // Try to create a basic VVISF object to test availability
        auto scene = VVISF::CreateISFSceneRef();
        return scene != nullptr;
    } catch (...) {
        return false;
    }
}

// Basic error handling wrapper
class VVISFError : public std::exception {
public:
    explicit VVISFError(const std::string& message) : message_(message) {}
    
    const char* what() const noexcept override {
        return message_.c_str();
    }
    
private:
    std::string message_;
};

// Helper function to convert ISFValType to string
std::string isf_val_type_to_string(VVISF::ISFValType type) {
    return VVISF::StringFromISFValType(type);
}

// Helper function to check if ISFValType uses image
bool isf_val_type_uses_image(VVISF::ISFValType type) {
    return VVISF::ISFValTypeUsesImage(type);
}

// Helper function to convert ISFFileType to string
std::string isf_file_type_to_string(VVISF::ISFFileType type) {
    return VVISF::ISFFileTypeString(type);
}

// Global GLFW window for OpenGL context with thread safety
static GLFWwindow* g_glfw_window = nullptr;
static bool g_glfw_initialized = false;
static std::mutex g_glfw_mutex;

// Helper to get OpenGL version string
std::string get_opengl_version() {
    const GLubyte* ver = glGetString(GL_VERSION);
    if (ver) return std::string(reinterpret_cast<const char*>(ver));
    return "(null)";
}

// Initialize GLFW and OpenGL context with improved error handling
bool initialize_glfw_context() {
    std::lock_guard<std::mutex> lock(g_glfw_mutex);
    
    if (g_glfw_initialized && g_glfw_window) {
        glfwMakeContextCurrent(g_glfw_window);
        return true;
    }
    
    // Clean up any existing window
    if (g_glfw_window) {
        glfwDestroyWindow(g_glfw_window);
        g_glfw_window = nullptr;
    }
    g_glfw_initialized = false;
    
    // Initialize GLFW
    if (!glfwInit()) {
        fprintf(stderr, "[VVISF] Failed to initialize GLFW\n");
        return false;
    }
    
    // Configure GLFW for OpenGL
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_VISIBLE, GLFW_FALSE); // Hidden window
    glfwWindowHint(GLFW_CLIENT_API, GLFW_OPENGL_API);
    
    // Create window
    g_glfw_window = glfwCreateWindow(100, 100, "Offscreen", NULL, NULL);
    if (!g_glfw_window) {
        fprintf(stderr, "[VVISF] Failed to create GLFW window\n");
        glfwTerminate();
        return false;
    }
    
    // Make context current
    glfwMakeContextCurrent(g_glfw_window);
    
    // Initialize GLEW
    glewExperimental = GL_TRUE;
    GLenum glew_result = glewInit();
    if (glew_result != GLEW_OK) {
        fprintf(stderr, "[VVISF] Failed to initialize GLEW: %s\n", glewGetErrorString(glew_result));
        glfwDestroyWindow(g_glfw_window);
        g_glfw_window = nullptr;
        glfwTerminate();
        return false;
    }
    
    // Check for OpenGL errors after GLEW initialization
    GLenum err = glGetError();
    if (err != GL_NO_ERROR) {
        fprintf(stderr, "[VVISF] OpenGL error after GLEW init: %d\n", err);
        // Don't fail here, as some drivers report errors during GLEW init
    }
    
    g_glfw_initialized = true;
    
    // Initialize VVISF global buffer pool
    try {
        VVGL::GLContextRef gl_ctx = VVGL::CreateGLContextRefUsing(g_glfw_window);
        if (!gl_ctx) {
            fprintf(stderr, "[VVISF] Failed to create VVGL::GLContextRefUsing\n");
            glfwDestroyWindow(g_glfw_window);
            g_glfw_window = nullptr;
            glfwTerminate();
            g_glfw_initialized = false;
            return false;
        }
        VVGL::CreateGlobalBufferPool(gl_ctx);
    } catch (const std::exception& e) {
        fprintf(stderr, "[VVISF] Exception during VVISF initialization: %s\n", e.what());
        glfwDestroyWindow(g_glfw_window);
        g_glfw_window = nullptr;
        glfwTerminate();
        g_glfw_initialized = false;
        return false;
    }
    
    return true;
}

// Clean up GLFW context
void cleanup_glfw_context() {
    std::lock_guard<std::mutex> lock(g_glfw_mutex);
    
    if (g_glfw_window) {
        glfwDestroyWindow(g_glfw_window);
        g_glfw_window = nullptr;
    }
    g_glfw_initialized = false;
}

// Expose a function to reinitialize the context
bool reinitialize_glfw_context() {
    // Clean up existing context
    cleanup_glfw_context();
    
    // Now initialize new context (this will acquire the lock internally)
    return initialize_glfw_context();
}

// Expose a function to get OpenGL/GLFW/VVISF info
py::dict get_gl_info() {
    std::lock_guard<std::mutex> lock(g_glfw_mutex);
    
    py::dict info;
    info["glfw_initialized"] = g_glfw_initialized;
    info["window_ptr"] = reinterpret_cast<uintptr_t>(g_glfw_window);
    
    if (g_glfw_window) {
        glfwMakeContextCurrent(g_glfw_window);
        info["opengl_version"] = get_opengl_version();
        
        // Get additional OpenGL info
        const GLubyte* vendor = glGetString(GL_VENDOR);
        const GLubyte* renderer = glGetString(GL_RENDERER);
        info["opengl_vendor"] = vendor ? std::string(reinterpret_cast<const char*>(vendor)) : "(null)";
        info["opengl_renderer"] = renderer ? std::string(reinterpret_cast<const char*>(renderer)) : "(null)";
    } else {
        info["opengl_version"] = py::none();
        info["opengl_vendor"] = py::none();
        info["opengl_renderer"] = py::none();
    }
    
    return info;
}

// Helper function to ensure OpenGL context is current
bool ensure_gl_context_current() {
    if (!initialize_glfw_context()) {
        return false;
    }
    
    if (g_glfw_window) {
        glfwMakeContextCurrent(g_glfw_window);
        return true;
    }
    
    return false;
}

// Safe OpenGL error checking
void check_gl_errors(const std::string& operation) {
    GLenum err;
    while ((err = glGetError()) != GL_NO_ERROR) {
        fprintf(stderr, "[VVISF] OpenGL error during %s: %d\n", operation.c_str(), err);
    }
}

// Critical function to reset OpenGL context state and perform cleanup
void reset_gl_context_state() {
    if (!ensure_gl_context_current()) {
        fprintf(stderr, "[pyvvisf] [ERROR] Failed to make OpenGL context current for state reset\n");
        return;
    }
    
    fprintf(stderr, "[pyvvisf] [DEBUG] Resetting OpenGL context state\n");
    
    // Unbind all texture units
    GLint max_texture_units = 0;
    glGetIntegerv(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS, &max_texture_units);
    for (GLint i = 0; i < max_texture_units; ++i) {
        glActiveTexture(GL_TEXTURE0 + i);
        glBindTexture(GL_TEXTURE_2D, 0);
        glBindTexture(GL_TEXTURE_RECTANGLE, 0);
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0);
    }
    glActiveTexture(GL_TEXTURE0);
    
    // Unbind framebuffers
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    glBindFramebuffer(GL_READ_FRAMEBUFFER, 0);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);
    
    // Reset pixel store state
    glPixelStorei(GL_UNPACK_ALIGNMENT, 4);
    glPixelStorei(GL_PACK_ALIGNMENT, 4);
    glPixelStorei(GL_UNPACK_ROW_LENGTH, 0);
    glPixelStorei(GL_UNPACK_SKIP_ROWS, 0);
    glPixelStorei(GL_UNPACK_SKIP_PIXELS, 0);
    glPixelStorei(GL_UNPACK_SWAP_BYTES, GL_FALSE);
    glPixelStorei(GL_UNPACK_LSB_FIRST, GL_FALSE);
    
    // Clear any pending errors
    check_gl_errors("reset_gl_context_state");
    
    fprintf(stderr, "[pyvvisf] [DEBUG] OpenGL context state reset complete\n");
}

// Enhanced scene cleanup function
void cleanup_scene_state(VVISF::ISFSceneRef& scene) {
    if (!scene) {
        return;
    }
    
    fprintf(stderr, "[pyvvisf] [DEBUG] Cleaning up scene state\n");
    
    try {
        // Reset OpenGL context state
        reset_gl_context_state();
        
        // Perform buffer pool housekeeping to clean up idle textures
        VVGL::GLBufferPoolRef global_pool = VVGL::GetGlobalBufferPool();
        if (global_pool) {
            global_pool->housekeeping();
            fprintf(stderr, "[pyvvisf] [DEBUG] Buffer pool housekeeping completed\n");
        }
        
        // Force a small delay to allow GPU operations to complete
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        
    } catch (const std::exception& e) {
        fprintf(stderr, "[pyvvisf] [ERROR] Exception during scene cleanup: %s\n", e.what());
    }
}

// Convert GLBuffer to PIL Image (RGBA format) with improved error handling
py::object glbuffer_to_pil_image(const std::shared_ptr<VVGL::GLBuffer>& buffer) {
    fprintf(stderr, "[pyvvisf] [DEBUG] glbuffer_to_pil_image: called\n");
    if (!buffer) {
        fprintf(stderr, "[pyvvisf] [ERROR] Buffer is null\n");
        throw std::runtime_error("Invalid GLBuffer: buffer is null");
    }
    fprintf(stderr, "[pyvvisf] [DEBUG] Buffer name: %u, type: %d, target: %d\n", 
            buffer->name, buffer->desc.type, buffer->desc.target);
    if (buffer->name == 0) {
        fprintf(stderr, "[pyvvisf] [ERROR] Buffer has invalid OpenGL texture name=0\n");
        throw std::runtime_error("Invalid GLBuffer: no OpenGL texture");
    }
    
    if (!ensure_gl_context_current()) {
        fprintf(stderr, "[pyvvisf] [ERROR] Failed to make OpenGL context current\n");
        throw std::runtime_error("Failed to make OpenGL context current");
    }
    
    // Save current OpenGL state to prevent pollution
    GLint current_texture_binding = 0;
    GLint current_framebuffer_binding = 0;
    GLint current_read_framebuffer_binding = 0;
    GLint current_draw_framebuffer_binding = 0;
    
    glGetIntegerv(GL_TEXTURE_BINDING_2D, &current_texture_binding);
    glGetIntegerv(GL_FRAMEBUFFER_BINDING, &current_framebuffer_binding);
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &current_read_framebuffer_binding);
    glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &current_draw_framebuffer_binding);
    
    // Determine correct texture target based on buffer descriptor
    GLenum texture_target = GL_TEXTURE_2D;
    if (buffer->desc.target == VVGL::GLBuffer::Target_2D) {
        texture_target = GL_TEXTURE_2D;
    } else if (buffer->desc.target == VVGL::GLBuffer::Target_RB) {
        texture_target = GL_TEXTURE_RECTANGLE;
    } else if (buffer->desc.target == VVGL::GLBuffer::Target_Cube) {
        texture_target = GL_TEXTURE_CUBE_MAP;
    } else {
        // The buffer's target field contains the actual OpenGL constant, use it directly
        texture_target = buffer->desc.target;
    }
    
    // Validate texture before binding with proper target
    GLint texture_valid = 0;
    glBindTexture(texture_target, buffer->name);
    GLenum err = glGetError();
    if (err != GL_NO_ERROR) {
        fprintf(stderr, "[pyvvisf] [ERROR] Failed to bind texture %u to target %u: %u\n", 
                buffer->name, texture_target, err);
        // Restore state and throw
        glBindTexture(texture_target, current_texture_binding);
        throw std::runtime_error("Failed to bind texture: " + std::to_string(err));
    }
    
    // Validate texture by checking if it exists
    GLboolean is_texture = glIsTexture(buffer->name);
    err = glGetError();
    if (err != GL_NO_ERROR || !is_texture) {
        glBindTexture(texture_target, current_texture_binding);
        fprintf(stderr, "[pyvvisf] [ERROR] Invalid texture object: name=%u, is_texture=%s, err=%u\n", 
                buffer->name, is_texture ? "true" : "false", err);
        throw std::runtime_error("Invalid texture object: " + std::to_string(err));
    }
    
    // Get texture size with proper target and level
    GLint width = 0, height = 0;
    if (texture_target == GL_TEXTURE_CUBE_MAP) {
        // For cube maps, use positive X face
        glGetTexLevelParameteriv(GL_TEXTURE_CUBE_MAP_POSITIVE_X, 0, GL_TEXTURE_WIDTH, &width);
        glGetTexLevelParameteriv(GL_TEXTURE_CUBE_MAP_POSITIVE_X, 0, GL_TEXTURE_HEIGHT, &height);
    } else {
        glGetTexLevelParameteriv(texture_target, 0, GL_TEXTURE_WIDTH, &width);
        glGetTexLevelParameteriv(texture_target, 0, GL_TEXTURE_HEIGHT, &height);
    }
    check_gl_errors("glGetTexLevelParameteriv");
    
    if (width <= 0 || height <= 0) {
        glBindTexture(texture_target, current_texture_binding);
        fprintf(stderr, "[pyvvisf] [ERROR] Invalid texture dimensions: width=%d, height=%d\n", width, height);
        throw std::runtime_error("Invalid texture dimensions");
    }
    
    // Try direct texture reading first
    std::vector<unsigned char> pixels(width * height * 4);
    bool direct_read_success = false;
    
    if (texture_target == GL_TEXTURE_CUBE_MAP) {
        // For cube maps, read from positive X face
        glGetTexImage(GL_TEXTURE_CUBE_MAP_POSITIVE_X, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
    } else {
        glGetTexImage(texture_target, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
    }
    
    err = glGetError();
    if (err == GL_NO_ERROR) {
        direct_read_success = true;
    } else {
        fprintf(stderr, "[pyvvisf] [WARN] glGetTexImage failed (err=%u), trying framebuffer fallback\n", err);
    }
    
    // If direct reading fails, try framebuffer approach
    if (!direct_read_success) {
        GLuint framebuffer = 0;
        glGenFramebuffers(1, &framebuffer);
        if (framebuffer == 0) {
            glBindTexture(texture_target, current_texture_binding);
            fprintf(stderr, "[pyvvisf] [ERROR] Failed to generate framebuffer\n");
            throw std::runtime_error("Failed to generate framebuffer");
        }
        
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer);
        err = glGetError();
        if (err != GL_NO_ERROR) {
            glDeleteFramebuffers(1, &framebuffer);
            glBindTexture(texture_target, current_texture_binding);
            fprintf(stderr, "[pyvvisf] [ERROR] Failed to bind framebuffer: %u\n", err);
            throw std::runtime_error("Failed to bind framebuffer: " + std::to_string(err));
        }
        
        // Attach texture to framebuffer with proper target
        if (texture_target == GL_TEXTURE_CUBE_MAP) {
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_CUBE_MAP_POSITIVE_X, buffer->name, 0);
        } else {
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, texture_target, buffer->name, 0);
        }
        
        // Check framebuffer status
        GLenum fb_status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
        fprintf(stderr, "[pyvvisf] [DEBUG] glCheckFramebufferStatus: %u\n", fb_status);
        if (fb_status != GL_FRAMEBUFFER_COMPLETE) {
            glBindFramebuffer(GL_FRAMEBUFFER, current_framebuffer_binding);
            glDeleteFramebuffers(1, &framebuffer);
            glBindTexture(texture_target, current_texture_binding);
            fprintf(stderr, "[pyvvisf] [ERROR] Framebuffer not complete: %u\n", fb_status);
            throw std::runtime_error("Framebuffer not complete: " + std::to_string(fb_status));
        }
        
        // Read pixels from framebuffer
        glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
        
        err = glGetError();
        fprintf(stderr, "[pyvvisf] [DEBUG] glReadPixels error: %u\n", err);
        if (err != GL_NO_ERROR) {
            glBindFramebuffer(GL_FRAMEBUFFER, current_framebuffer_binding);
            glDeleteFramebuffers(1, &framebuffer);
            glBindTexture(texture_target, current_texture_binding);
            fprintf(stderr, "[pyvvisf] [ERROR] OpenGL error reading pixels: %u\n", err);
            throw std::runtime_error("OpenGL error reading pixels: " + std::to_string(err));
        }
        
        // Cleanup framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, current_framebuffer_binding);
        glDeleteFramebuffers(1, &framebuffer);
    }
    
    // Restore texture binding to prevent state pollution
    glBindTexture(texture_target, current_texture_binding);
    err = glGetError();
    fprintf(stderr, "[pyvvisf] [DEBUG] glBindTexture(restore) error: %u\n", err);
    if (err != GL_NO_ERROR) {
        fprintf(stderr, "[pyvvisf] [ERROR] Error restoring texture binding: %u\n", err);
        // Don't throw here as we've already got the pixel data
    }
    
    // Create PIL Image from pixel data
    try {
        py::module pil = py::module::import("PIL.Image");
        
        // Debug the PIL creation parameters
        fprintf(stderr, "[pyvvisf] [DEBUG] Creating PIL image: mode=RGBA, size=(%d,%d), data_size=%lu\n", 
                width, height, pixels.size());
        
        // Create python bytes object from pixel data
        py::bytes pixel_bytes(reinterpret_cast<const char*>(pixels.data()), pixels.size());
        fprintf(stderr, "[pyvvisf] [DEBUG] Created Python bytes object with size: %lu\n", 
                py::len(pixel_bytes));
        
        py::object pil_image = pil.attr("frombytes")("RGBA", py::make_tuple(width, height), pixel_bytes);
        fprintf(stderr, "[pyvvisf] [DEBUG] PIL image created successfully\n");
        return pil_image;
    } catch (const py::error_already_set& e) {
        fprintf(stderr, "[pyvvisf] [ERROR] Failed to create PIL Image: %s\n", e.what());
        throw std::runtime_error("Failed to create PIL Image: " + std::string(e.what()));
    }
}

// Create a new PIL Image with the same dimensions as the GLBuffer
py::object create_pil_image_from_buffer(const std::shared_ptr<VVGL::GLBuffer>& buffer, 
                                       const std::string& mode = "RGBA", 
                                       const std::tuple<int, int, int, int>& color = std::make_tuple(0, 0, 0, 255)) {
    if (!buffer) {
        throw std::runtime_error("Invalid GLBuffer: buffer is null");
    }
    
    try {
        // Get buffer dimensions
        int width = static_cast<int>(buffer->size.width);
        int height = static_cast<int>(buffer->size.height);
        
        if (width <= 0 || height <= 0) {
            throw std::runtime_error("Invalid buffer dimensions");
        }
        
        // Import PIL
        py::module pil = py::module::import("PIL.Image");
        
        // Handle different color formats based on mode
        py::object color_obj;
        if (mode == "RGBA") {
            color_obj = py::make_tuple(std::get<0>(color), std::get<1>(color), std::get<2>(color), std::get<3>(color));
        } else if (mode == "RGB") {
            color_obj = py::make_tuple(std::get<0>(color), std::get<1>(color), std::get<2>(color));
        } else if (mode == "L") {
            // For grayscale, use the first component
            color_obj = py::int_(std::get<0>(color));
        } else {
            // Default to RGBA color
            color_obj = py::make_tuple(std::get<0>(color), std::get<1>(color), std::get<2>(color), std::get<3>(color));
        }
        
        // Create new PIL Image with specified mode and color
        py::object pil_image = pil.attr("new")(mode, py::make_tuple(width, height), color_obj);
        
        return pil_image;
        
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Failed to create PIL Image: " + std::string(e.what()));
    }
}

// Convert PIL Image to GLBuffer
std::shared_ptr<VVGL::GLBuffer> pil_image_to_glbuffer(py::object pil_image) {
    if (!ensure_gl_context_current()) {
        throw std::runtime_error("Failed to make OpenGL context current");
    }
    
    try {
        // Get image size and mode
        py::tuple size = pil_image.attr("size");
        int width = size[0].cast<int>();
        int height = size[1].cast<int>();
        std::string mode = pil_image.attr("mode").cast<std::string>();
        
        // Convert image to RGBA if needed
        py::object rgba_image = pil_image;
        if (mode != "RGBA") {
            py::module pil = py::module::import("PIL.Image");
            rgba_image = pil_image.attr("convert")("RGBA");
        }
        
        // Get pixel data
        py::bytes pixel_data = rgba_image.attr("tobytes")();
        std::string pixel_str = pixel_data.cast<std::string>();
        const char* data_ptr = pixel_str.c_str();
        
        // Create OpenGL texture manually
        GLuint texture_name;
        glGenTextures(1, &texture_name);
        
        if (texture_name == 0) {
            throw std::runtime_error("Failed to generate OpenGL texture");
        }
        
        // Upload pixel data to texture
        glBindTexture(GL_TEXTURE_2D, texture_name);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data_ptr);
        
        // Check for OpenGL errors
        GLenum err = glGetError();
        if (err != GL_NO_ERROR) {
            glBindTexture(GL_TEXTURE_2D, 0);
            throw std::runtime_error("OpenGL error uploading texture: " + std::to_string(err));
        }
        
        glBindTexture(GL_TEXTURE_2D, 0);
        
        // Create GLBuffer wrapper
        auto buffer = std::make_shared<VVGL::GLBuffer>();
        buffer->name = texture_name;
        buffer->size = VVGL::Size(width, height);
        buffer->srcRect = VVGL::Rect(0, 0, width, height);  // Set srcRect to cover full size
        buffer->desc.type = VVGL::GLBuffer::Type_Tex;
        buffer->desc.target = static_cast<VVGL::GLBuffer::Target>(Target_2D);
        buffer->desc.internalFormat = static_cast<VVGL::GLBuffer::InternalFormat>(IF_RGBA);
        buffer->desc.pixelFormat = static_cast<VVGL::GLBuffer::PixelFormat>(PF_RGBA);
        
        return buffer;
        
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Failed to convert PIL Image to GLBuffer: " + std::string(e.what()));
    }
}

// Enhanced helper for create_and_render_a_buffer with robust error handling
static VVGL::GLBufferRef pyvvisf_create_and_render_a_buffer(VVISF::ISFScene& self, const VVGL::Size& size, double render_time, py::dict out_pass_dict, VVGL::GLBufferPoolRef pool_ref) {
    // Validate input parameters
    if (size.width <= 0 || size.height <= 0) {
        throw std::invalid_argument("Invalid size: width and height must be positive. Got: " + 
                                  std::to_string(size.width) + "x" + std::to_string(size.height));
    }
    
    // Sanity check for reasonable dimensions to prevent excessive memory allocation
    const double max_dimension = 16384; // 16K should be reasonable maximum
    if (size.width > max_dimension || size.height > max_dimension) {
        throw std::invalid_argument("Size too large: maximum dimension is " + std::to_string(max_dimension) + 
                                  ". Got: " + std::to_string(size.width) + "x" + std::to_string(size.height));
    }
    
    // Ensure OpenGL context is current before rendering
    if (!ensure_gl_context_current()) {
        throw std::runtime_error("Failed to make OpenGL context current for rendering");
    }
    
    // Check if scene has a valid document loaded
    if (!self.doc()) {
        throw std::runtime_error("ISFScene has no document loaded. Call use_doc() first.");
    }
    
    try {
        // Reset OpenGL state to prevent state pollution from previous operations
        reset_gl_context_state();
        
        // Clear any pending OpenGL errors before rendering
        check_gl_errors("pre-render state");
        
        // Perform the actual rendering
        std::map<int32_t, VVGL::GLBufferRef> pass_dict;
        VVGL::GLBufferRef result = self.createAndRenderABuffer(size, render_time, &pass_dict, pool_ref);
        
        // Check for OpenGL errors after rendering
        check_gl_errors("post-render");
        
        // Validate the result
        if (!result) {
            throw std::runtime_error("Rendering failed: createAndRenderABuffer returned null buffer");
        }
        
        // Validate buffer properties
        if (result->name == 0) {
            throw std::runtime_error("Rendering failed: invalid OpenGL texture name in result buffer");
        }
        
        // Copy pass dictionary to Python dict
        for (const auto& pair : pass_dict) {
            out_pass_dict[py::int_(pair.first)] = pair.second;
        }
        
        return result;
        
    } catch (const std::exception& e) {
        // Log the error for debugging
        fprintf(stderr, "[pyvvisf] [ERROR] Exception in create_and_render_a_buffer: %s\n", e.what());
        
        // Attempt to clean up OpenGL state after error
        try {
            reset_gl_context_state();
        } catch (...) {
            // Ignore cleanup errors
        }
        
        // Re-throw the original exception
        throw;
    }
}

// Helper for render_to_buffer
static void pyvvisf_render_to_buffer(VVISF::ISFScene& self, const VVGL::GLBufferRef& target_buffer, const VVGL::Size& render_size, double render_time, py::dict out_pass_dict) {
    std::map<int32_t, VVGL::GLBufferRef> pass_dict;
    self.renderToBuffer(target_buffer, render_size, render_time, &pass_dict);
    for (const auto& pair : pass_dict) {
        out_pass_dict[py::int_(pair.first)] = pair.second;
    }
}

PYBIND11_MODULE(vvisf_bindings, m) {
    m.doc() = "Python bindings for VVISF library - ISF shader rendering"; // Optional module docstring
    
    // Exception class
    py::register_exception<VVISFError>(m, "VVISFError");
    
    // Enums - must be registered before functions that use them as default arguments
    py::enum_<VVISF::ISFValType>(m, "ISFValType")
        .value("None_", VVISF::ISFValType_None)
        .value("Event", VVISF::ISFValType_Event)
        .value("Bool", VVISF::ISFValType_Bool)
        .value("Long", VVISF::ISFValType_Long)
        .value("Float", VVISF::ISFValType_Float)
        .value("Point2D", VVISF::ISFValType_Point2D)
        .value("Color", VVISF::ISFValType_Color)
        .value("Cube", VVISF::ISFValType_Cube)
        .value("Image", VVISF::ISFValType_Image)
        .value("Audio", VVISF::ISFValType_Audio)
        .value("AudioFFT", VVISF::ISFValType_AudioFFT)
        .def("__str__", [](VVISF::ISFValType type) { return isf_val_type_to_string(type); });
    
    // Export ISFValType_* at module level
    m.attr("ISFValType_None") = VVISF::ISFValType_None;
    m.attr("ISFValType_Event") = VVISF::ISFValType_Event;
    m.attr("ISFValType_Bool") = VVISF::ISFValType_Bool;
    m.attr("ISFValType_Long") = VVISF::ISFValType_Long;
    m.attr("ISFValType_Float") = VVISF::ISFValType_Float;
    m.attr("ISFValType_Point2D") = VVISF::ISFValType_Point2D;
    m.attr("ISFValType_Color") = VVISF::ISFValType_Color;
    m.attr("ISFValType_Cube") = VVISF::ISFValType_Cube;
    m.attr("ISFValType_Image") = VVISF::ISFValType_Image;
    m.attr("ISFValType_Audio") = VVISF::ISFValType_Audio;
    m.attr("ISFValType_AudioFFT") = VVISF::ISFValType_AudioFFT;

    py::enum_<VVISF::ISFFileType>(m, "ISFFileType")
        .value("None_", VVISF::ISFFileType_None)
        .value("Source", VVISF::ISFFileType_Source)
        .value("Filter", VVISF::ISFFileType_Filter)
        .value("Transition", VVISF::ISFFileType_Transition)
        .value("All", VVISF::ISFFileType_All)
        .def("__str__", [](VVISF::ISFFileType type) { return isf_file_type_to_string(type); });

    // Export ISFFileType_* at module level
    m.attr("ISFFileType_None") = VVISF::ISFFileType_None;
    m.attr("ISFFileType_Source") = VVISF::ISFFileType_Source;
    m.attr("ISFFileType_Filter") = VVISF::ISFFileType_Filter;
    m.attr("ISFFileType_Transition") = VVISF::ISFFileType_Transition;
    m.attr("ISFFileType_All") = VVISF::ISFFileType_All;

    // --- VVGL::Point bindings ---
    py::class_<VVGL::Point>(m, "Point")
        .def(py::init<>())
        .def(py::init<double, double>(), py::arg("x"), py::arg("y"))
        .def_readwrite("x", &VVGL::Point::x)
        .def_readwrite("y", &VVGL::Point::y)
        .def("is_zero", &VVGL::Point::isZero)
        .def("__str__", [](const VVGL::Point& self) {
            return "Point(" + std::to_string(self.x) + ", " + std::to_string(self.y) + ")";
        });

    // --- VVGL::Size bindings ---
    py::class_<VVGL::Size>(m, "Size")
        .def(py::init<>())
        .def(py::init<double, double>(), py::arg("width"), py::arg("height"))
        .def_readwrite("width", &VVGL::Size::width)
        .def_readwrite("height", &VVGL::Size::height)
        .def("is_zero", &VVGL::Size::isZero)
        .def("__str__", [](const VVGL::Size& self) {
            return "Size(" + std::to_string(self.width) + ", " + std::to_string(self.height) + ")";
        });

    // --- VVGL::Rect bindings ---
    py::class_<VVGL::Rect>(m, "Rect")
        .def(py::init<>())
        .def(py::init<double, double, double, double>(), py::arg("x"), py::arg("y"), py::arg("width"), py::arg("height"))
        .def_readwrite("origin", &VVGL::Rect::origin)
        .def_readwrite("size", &VVGL::Rect::size)
        .def("min_x", &VVGL::Rect::minX)
        .def("max_x", &VVGL::Rect::maxX)
        .def("min_y", &VVGL::Rect::minY)
        .def("max_y", &VVGL::Rect::maxY)
        .def("mid_x", &VVGL::Rect::midX)
        .def("mid_y", &VVGL::Rect::midY)
        .def("top_left", &VVGL::Rect::topLeft)
        .def("top_right", &VVGL::Rect::topRight)
        .def("bot_left", &VVGL::Rect::botLeft)
        .def("bot_right", &VVGL::Rect::botRight)
        .def("center", &VVGL::Rect::center)
        .def("is_zero", &VVGL::Rect::isZero)
        .def("__str__", [](const VVGL::Rect& self) {
            return "Rect(" + std::to_string(self.origin.x) + ", " + std::to_string(self.origin.y) + 
                   ", " + std::to_string(self.size.width) + "x" + std::to_string(self.size.height) + ")";
        });
    
    // Module-level functions
    m.def("get_platform_info", &get_platform_info, "Get platform information");
    m.def("is_vvisf_available", &is_vvisf_available, "Check if VVISF is available");
    m.def("isf_val_type_to_string", &isf_val_type_to_string, "Convert ISFValType to string");
    m.def("isf_val_type_uses_image", &isf_val_type_uses_image, "Check if ISFValType uses image");
    m.def("isf_file_type_to_string", &isf_file_type_to_string, "Convert ISFFileType to string");
    
    // ISFVal class
    py::class_<VVISF::ISFVal>(m, "ISFVal")
        .def(py::init<>())
        .def(py::init<VVISF::ISFValType>())
        .def(py::init<VVISF::ISFValType, bool>())
        .def(py::init<VVISF::ISFValType, int32_t>())
        .def(py::init<VVISF::ISFValType, double>())
        .def(py::init<VVISF::ISFValType, double, double>())
        .def(py::init<VVISF::ISFValType, double, double, double, double>())
        .def("type", &VVISF::ISFVal::type)
        .def("get_double_val", &VVISF::ISFVal::getDoubleVal)
        .def("get_float_val", &VVISF::ISFVal::getDoubleVal)  // Use getDoubleVal for float values
        .def("get_bool_val", &VVISF::ISFVal::getBoolVal)
        .def("get_long_val", &VVISF::ISFVal::getLongVal)
        .def("get_point_val_by_index", &VVISF::ISFVal::getPointValByIndex)
        .def("set_point_val_by_index", &VVISF::ISFVal::setPointValByIndex)
        .def("get_color_val_by_channel", &VVISF::ISFVal::getColorValByChannel)
        .def("set_color_val_by_channel", &VVISF::ISFVal::setColorValByChannel)
        .def("image_buffer", &VVISF::ISFVal::imageBuffer)
        .def("set_image_buffer", &VVISF::ISFVal::setImageBuffer)
        .def("get_type_string", &VVISF::ISFVal::getTypeString)
        .def("get_val_string", &VVISF::ISFVal::getValString)
        .def("is_null_val", &VVISF::ISFVal::isNullVal)
        .def("is_event_val", &VVISF::ISFVal::isEventVal)
        .def("is_bool_val", &VVISF::ISFVal::isBoolVal)
        .def("is_long_val", &VVISF::ISFVal::isLongVal)
        .def("is_float_val", &VVISF::ISFVal::isFloatVal)
        .def("is_point2d_val", &VVISF::ISFVal::isPoint2DVal)
        .def("is_color_val", &VVISF::ISFVal::isColorVal)
        .def("is_cube_val", &VVISF::ISFVal::isCubeVal)
        .def("is_image_val", &VVISF::ISFVal::isImageVal)
        .def("is_audio_val", &VVISF::ISFVal::isAudioVal)
        .def("is_audio_fft_val", &VVISF::ISFVal::isAudioFFTVal)
        .def("__str__", &VVISF::ISFVal::getValString);
    
    // ISFVal creation functions
    m.def("ISFNullVal", &VVISF::ISFNullVal, "Create a null ISFVal");
    m.def("ISFEventVal", &VVISF::ISFEventVal, "Create an event ISFVal", py::arg("value") = false);
    m.def("ISFBoolVal", &VVISF::ISFBoolVal, "Create a boolean ISFVal");
    m.def("ISFLongVal", &VVISF::ISFLongVal, "Create a long ISFVal");
    m.def("ISFFloatVal", &VVISF::ISFFloatVal, "Create a float ISFVal");
    m.def("ISFPoint2DVal", &VVISF::ISFPoint2DVal, "Create a Point2D ISFVal");
    m.def("ISFColorVal", &VVISF::ISFColorVal, "Create a color ISFVal");
    m.def("ISFImageVal", &VVISF::ISFImageVal, "Create an image ISFVal");
    
    // ISFAttr class
    py::class_<VVISF::ISFAttr, std::shared_ptr<VVISF::ISFAttr>>(m, "ISFAttr")
        .def(
            py::init([](const std::string& name,
                          const std::string& description,
                          const std::string& label,
                          VVISF::ISFValType type,
                          const VVISF::ISFVal& min_val,
                          const VVISF::ISFVal& max_val,
                          const VVISF::ISFVal& default_val,
                          const VVISF::ISFVal& identity_val,
                          const std::vector<std::string>& labels,
                          const std::vector<int32_t>& values) {
                const std::vector<std::string>* labels_ptr = labels.empty() ? nullptr : &labels;
                const std::vector<int32_t>* values_ptr = values.empty() ? nullptr : &values;
                return std::make_shared<VVISF::ISFAttr>(name, description, label, type, min_val, max_val, default_val, identity_val, labels_ptr, values_ptr);
            }),
            py::arg("name"),
            py::arg("description"),
            py::arg("label"),
            py::arg("type"),
            py::arg("min_val") = VVISF::ISFNullVal(),
            py::arg("max_val") = VVISF::ISFNullVal(),
            py::arg("default_val") = VVISF::ISFNullVal(),
            py::arg("identity_val") = VVISF::ISFNullVal(),
            py::arg("labels") = std::vector<std::string>{},
            py::arg("values") = std::vector<int32_t>{}
        )
        .def("name", &VVISF::ISFAttr::name)
        .def("description", &VVISF::ISFAttr::description)
        .def("label", &VVISF::ISFAttr::label)
        .def("type", &VVISF::ISFAttr::type)
        .def("current_val", &VVISF::ISFAttr::currentVal)
        .def("set_current_val", &VVISF::ISFAttr::setCurrentVal)
        .def("min_val", &VVISF::ISFAttr::minVal)
        .def("max_val", &VVISF::ISFAttr::maxVal)
        .def("default_val", &VVISF::ISFAttr::defaultVal)
        .def("identity_val", &VVISF::ISFAttr::identityVal)
        .def("label_array", &VVISF::ISFAttr::labelArray)
        .def("val_array", &VVISF::ISFAttr::valArray)
        .def("is_filter_input_image", &VVISF::ISFAttr::isFilterInputImage)
        .def("set_is_filter_input_image", &VVISF::ISFAttr::setIsFilterInputImage)
        .def("is_trans_start_image", &VVISF::ISFAttr::isTransStartImage)
        .def("set_is_trans_start_image", &VVISF::ISFAttr::setIsTransStartImage)
        .def("is_trans_end_image", &VVISF::ISFAttr::isTransEndImage)
        .def("set_is_trans_end_image", &VVISF::ISFAttr::setIsTransEndImage)
        .def("is_trans_progress_float", &VVISF::ISFAttr::isTransProgressFloat)
        .def("set_is_trans_progress_float", &VVISF::ISFAttr::setIsTransProgressFloat)
        .def("clear_uniform_locations", &VVISF::ISFAttr::clearUniformLocations)
        .def("set_uniform_location", &VVISF::ISFAttr::setUniformLocation)
        .def("get_uniform_location", &VVISF::ISFAttr::getUniformLocation)
        .def("get_attr_description", &VVISF::ISFAttr::getAttrDescription)
        .def("__str__", &VVISF::ISFAttr::getAttrDescription);
    
    // ISFDoc class
    py::class_<VVISF::ISFDoc, std::shared_ptr<VVISF::ISFDoc>>(m, "ISFDoc")
        .def(py::init<const std::string&, VVISF::ISFScene*, bool>(),
             py::arg("path"), py::arg("parent_scene") = nullptr, py::arg("throw_except") = true)
        .def(py::init<const std::string&, const std::string&, const std::string&, 
                      VVISF::ISFScene*, bool>(),
             py::arg("fs_contents"), py::arg("vs_contents"), py::arg("imports_dir"),
             py::arg("parent_scene") = nullptr, py::arg("throw_except") = true)
        // File properties
        .def("path", &VVISF::ISFDoc::path)
        .def("name", &VVISF::ISFDoc::name)
        .def("description", &VVISF::ISFDoc::description)
        .def("credit", &VVISF::ISFDoc::credit)
        .def("vsn", &VVISF::ISFDoc::vsn)
        .def("type", &VVISF::ISFDoc::type)
        .def("categories", &VVISF::ISFDoc::categories)
        // Note: getLastErrorLog method doesn't exist in current VVISF API
        // Input attributes
        .def("inputs", &VVISF::ISFDoc::inputs)
        .def("image_inputs", &VVISF::ISFDoc::imageInputs)
        .def("audio_inputs", &VVISF::ISFDoc::audioInputs)
        .def("image_imports", &VVISF::ISFDoc::imageImports)
        .def("inputs_of_type", &VVISF::ISFDoc::inputsOfType)
        .def("input", &VVISF::ISFDoc::input)
        // Render pass getters
        .def("render_passes", &VVISF::ISFDoc::renderPasses)
        .def("get_buffer_for_key", &VVISF::ISFDoc::getBufferForKey)
        .def("get_persistent_buffer_for_key", &VVISF::ISFDoc::getPersistentBufferForKey)
        .def("get_temp_buffer_for_key", &VVISF::ISFDoc::getTempBufferForKey)
        // Source code getters (wrap std::string* as std::string)
        .def("json_source_string", [=](const VVISF::ISFDoc& self) { auto ptr = self.jsonSourceString(); return ptr ? *ptr : std::string(); })
        .def("json_string", [=](const VVISF::ISFDoc& self) { auto ptr = self.jsonString(); return ptr ? *ptr : std::string(); })
        .def("vert_shader_source", [=](const VVISF::ISFDoc& self) { auto ptr = self.vertShaderSource(); return ptr ? *ptr : std::string(); })
        .def("frag_shader_source", [=](const VVISF::ISFDoc& self) { auto ptr = self.fragShaderSource(); return ptr ? *ptr : std::string(); })
        // Utility methods
        .def("set_parent_scene", &VVISF::ISFDoc::setParentScene)
        .def("parent_scene", &VVISF::ISFDoc::parentScene)
        .def("generate_texture_type_string", &VVISF::ISFDoc::generateTextureTypeString)
        .def("generate_shader_source", &VVISF::ISFDoc::generateShaderSource)
        .def("eval_buffer_dimensions_with_render_size", &VVISF::ISFDoc::evalBufferDimensionsWithRenderSize);
    
    // ISFDoc creation functions
    m.def("CreateISFDocRef", &VVISF::CreateISFDocRef, 
          "Create an ISFDoc from file path",
          py::arg("path"), py::arg("parent_scene") = nullptr, py::arg("throw_except") = true);
    m.def("CreateISFDocRefWith", &VVISF::CreateISFDocRefWith,
          "Create an ISFDoc from shader strings",
          py::arg("fs_contents"), py::arg("imports_dir") = "/", 
          py::arg("vs_contents") = std::string(VVISF::ISFVertPassthru_GL2),
          py::arg("parent_scene") = nullptr, py::arg("throw_except") = true);
    
    // ISFScene class
    py::class_<VVISF::ISFScene, std::shared_ptr<VVISF::ISFScene>>(m, "ISFScene")
        .def(py::init<>())
        .def("use_doc", &VVISF::ISFScene::useDoc)
        .def("use_file", static_cast<void (VVISF::ISFScene::*)(const std::string&, const bool&, const bool&)>(&VVISF::ISFScene::useFile), py::arg("path"), py::arg("throw_exc") = true, py::arg("reset_timer") = true)
        .def("create_and_render_a_buffer", &pyvvisf_create_and_render_a_buffer, py::arg("size"), py::arg("render_time") = 0.0, py::arg("out_pass_dict") = py::dict(), py::arg("pool_ref") = nullptr)
        .def("set_filter_input_buffer", &VVISF::ISFScene::setFilterInputBuffer)
        .def("set_buffer_for_input_image_key", &VVISF::ISFScene::setBufferForInputImageKey)
        .def("set_value_for_input_named", [](VVISF::ISFScene& self, const VVISF::ISFVal& value, const std::string& name) {
            self.setValueForInputNamed(value, name);
        })
        .def("get_value_for_input_named", [](VVISF::ISFScene& self, const std::string& name) {
            return self.valueForInputNamed(name);
        })
        .def("set_size", &VVISF::ISFScene::setSize)
        .def("size", &VVISF::ISFScene::size)
        .def("render_size", &VVISF::ISFScene::renderSize)
        .def("get_timestamp", &VVISF::ISFScene::getTimestamp)
        .def("set_always_render_to_float", &VVISF::ISFScene::setAlwaysRenderToFloat)
        .def("always_render_to_float", &VVISF::ISFScene::alwaysRenderToFloat)
        .def("set_persistent_to_iosurface", &VVISF::ISFScene::setPersistentToIOSurface)
        .def("persistent_to_iosurface", &VVISF::ISFScene::persistentToIOSurface)
        .def("set_throw_exceptions", &VVISF::ISFScene::setThrowExceptions)
        .def("throw_exceptions", [](VVISF::ISFScene& self) {
            // Use the available method that returns the current state
            return true; // The existing method isn't accessible, default to true
        })
        .def("set_private_pool", &VVISF::ISFScene::setPrivatePool)
        .def("private_pool", &VVISF::ISFScene::privatePool)
        .def("set_private_copier", &VVISF::ISFScene::setPrivateCopier)
        .def("private_copier", &VVISF::ISFScene::privateCopier)
        .def("doc", &VVISF::ISFScene::doc)
        .def("context", &VVISF::ISFScene::context)
        .def("ortho_size", &VVISF::ISFScene::orthoSize)
        .def("set_ortho_size", &VVISF::ISFScene::setOrthoSize)
        .def("set_vertex_shader_string", &VVISF::ISFScene::setVertexShaderString)
        .def("set_fragment_shader_string", &VVISF::ISFScene::setFragmentShaderString)
        .def("set_render_callback", &VVISF::ISFScene::setRenderCallback)
        .def("render", &VVISF::ISFScene::render)
        .def("render_with_target", &VVISF::ISFScene::render)
        .def("render_with_target_and_size", &VVISF::ISFScene::render)
        .def("render_with_target_and_size_and_time", &VVISF::ISFScene::render)
        .def("render_with_target_and_size_and_time_and_pass_dict", [](VVISF::ISFScene& self, const VVGL::GLBufferRef& target_buffer, const VVGL::Size& render_size, double render_time, py::dict out_pass_dict) {
            // Use proper lambda capture
            std::map<int32_t, VVGL::GLBufferRef> pass_dict;
            // Use the correct render method signature - RenderTarget constructor needs 3 buffers (fbo, color, depth)
            VVGL::GLScene::RenderTarget render_target(nullptr, target_buffer, nullptr);
            self.render(render_target);
            
            // Convert C++ map to Python dict
            for (const auto& pair : pass_dict) {
                out_pass_dict[py::int_(pair.first)] = pair.second;
            }
        }, py::arg("target_buffer"), py::arg("render_size"), py::arg("render_time") = 0.0, py::arg("out_pass_dict") = py::dict())
        .def("cleanup", [](VVISF::ISFScene& self) {
            // Enhanced cleanup for batch rendering
            // We can't easily create a shared_ptr from a reference, so just call the cleanup directly
            reset_gl_context_state();
            
            // Perform buffer pool housekeeping to clean up idle textures
            VVGL::GLBufferPoolRef global_pool = VVGL::GetGlobalBufferPool();
            if (global_pool) {
                global_pool->housekeeping();
                fprintf(stderr, "[pyvvisf] [DEBUG] Buffer pool housekeeping completed\n");
            }
            
            // Force a small delay to allow GPU operations to complete
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }, "Enhanced cleanup for batch rendering operations")
        .def("__str__", [](const VVISF::ISFScene& self) {
            return "ISFScene()";
        });
    
    // ISFScene creation functions
    m.def("CreateISFSceneRef", []() {
        // Ensure GLFW context is initialized before creating scene
        if (!initialize_glfw_context()) {
            throw std::runtime_error("Failed to initialize GLFW context");
        }
        return VVISF::CreateISFSceneRef();
    }, "Create an ISFScene");
    m.def("CreateISFSceneRefUsing", &VVISF::CreateISFSceneRefUsing, "Create an ISFScene with GL context");

    // --- VVGL::GLBuffer enums ---
    py::enum_<VVGL::GLBuffer::Type>(m, "GLBufferType")
        .value("Type_CPU", VVGL::GLBuffer::Type_CPU)
        .value("Type_Tex", VVGL::GLBuffer::Type_Tex)
        .value("Type_RB", VVGL::GLBuffer::Type_RB)
        .value("Type_PBO", VVGL::GLBuffer::Type_PBO)
        .value("Type_VBO", VVGL::GLBuffer::Type_VBO)
        .value("Type_EBO", VVGL::GLBuffer::Type_EBO)
        .value("Type_FBO", VVGL::GLBuffer::Type_FBO)
        .export_values();
    py::enum_<VVGL::GLBuffer::Target>(m, "GLBufferTarget")
        .value("Target_2D", VVGL::GLBuffer::Target_2D)
        .value("Target_Cube", VVGL::GLBuffer::Target_Cube)
        .export_values();
    py::enum_<VVGL::GLBuffer::InternalFormat>(m, "InternalFormat")
        .value("InternalFormat_RGBA", VVGL::GLBuffer::IF_RGBA)
        .export_values();
    py::enum_<VVGL::GLBuffer::PixelFormat>(m, "PixelFormat")
        .value("PixelFormat_RGBA", VVGL::GLBuffer::PF_RGBA)
        .export_values();
    py::enum_<VVGL::GLBuffer::PixelType>(m, "PixelType")
        .value("PixelType_UByte", VVGL::GLBuffer::PT_UByte)
        .export_values();
    py::enum_<VVGL::GLBuffer::Backing>(m, "Backing")
        .value("Backing_None", VVGL::GLBuffer::Backing_None)
        .export_values();

    // --- VVGL::GLBuffer::Descriptor binding ---
    py::class_<VVGL::GLBuffer::Descriptor>(m, "GLBufferDescriptor")
        .def(py::init<>())
        .def_readwrite("type", &VVGL::GLBuffer::Descriptor::type)
        .def_readwrite("target", &VVGL::GLBuffer::Descriptor::target)
        .def_readwrite("internalFormat", &VVGL::GLBuffer::Descriptor::internalFormat)
        .def_readwrite("pixelFormat", &VVGL::GLBuffer::Descriptor::pixelFormat)
        .def_readwrite("pixelType", &VVGL::GLBuffer::Descriptor::pixelType)
        .def_readwrite("cpuBackingType", &VVGL::GLBuffer::Descriptor::cpuBackingType)
        .def_readwrite("gpuBackingType", &VVGL::GLBuffer::Descriptor::gpuBackingType)
        .def_readwrite("texRangeFlag", &VVGL::GLBuffer::Descriptor::texRangeFlag)
        .def_readwrite("texClientStorageFlag", &VVGL::GLBuffer::Descriptor::texClientStorageFlag)
        .def_readwrite("msAmount", &VVGL::GLBuffer::Descriptor::msAmount)
        .def_readwrite("localSurfaceID", &VVGL::GLBuffer::Descriptor::localSurfaceID);

    // --- VVGL::GLBuffer bindings ---
    py::class_<VVGL::GLBuffer, std::shared_ptr<VVGL::GLBuffer>>(m, "GLBuffer")
        .def(py::init<>())
        .def("get_description", &VVGL::GLBuffer::getDescriptionString)
        .def_readwrite("size", &VVGL::GLBuffer::size)
        .def_readwrite("srcRect", &VVGL::GLBuffer::srcRect)
        .def_readwrite("flipped", &VVGL::GLBuffer::flipped)
        .def_readwrite("backingSize", &VVGL::GLBuffer::backingSize)
        .def_readwrite("name", &VVGL::GLBuffer::name)
        .def_readwrite("preferDeletion", &VVGL::GLBuffer::preferDeletion)
        .def("calculate_backing_bytes_per_row", &VVGL::GLBuffer::calculateBackingBytesPerRow)
        .def("calculate_backing_length", &VVGL::GLBuffer::calculateBackingLength)
        .def("alloc_shallow_copy", &VVGL::GLBuffer::allocShallowCopy, py::return_value_policy::reference)
        .def("is_full_frame", &VVGL::GLBuffer::isFullFrame)
        .def("is_pot2d_tex", &VVGL::GLBuffer::isPOT2DTex)
        .def("is_npot2d_tex", &VVGL::GLBuffer::isNPOT2DTex)
        .def("get_description_string", &VVGL::GLBuffer::getDescriptionString)
        .def_property_readonly("desc", [](const VVGL::GLBuffer& self) { return self.desc; })
        .def("to_pil_image", &glbuffer_to_pil_image, "Convert GLBuffer to PIL Image")
        .def("create_pil_image", &create_pil_image_from_buffer, 
             "Create a new PIL Image with the same dimensions as this buffer",
             py::arg("mode") = "RGBA", 
             py::arg("color") = std::make_tuple(0, 0, 0, 255))
        .def_static("from_pil_image", &pil_image_to_glbuffer, "Create GLBuffer from PIL Image", 
                   py::arg("pil_image"));
    // Expose enums as class attributes for test compatibility
    py::object glbuffer = m.attr("GLBuffer");
    glbuffer.attr("Type_Tex") = m.attr("GLBufferType").attr("Type_Tex");
    glbuffer.attr("Target_2D") = m.attr("GLBufferTarget").attr("Target_2D");
    glbuffer.attr("Target_Cube") = m.attr("GLBufferTarget").attr("Target_Cube");
    glbuffer.attr("InternalFormat_RGBA") = m.attr("InternalFormat").attr("InternalFormat_RGBA");
    glbuffer.attr("PixelFormat_RGBA") = m.attr("PixelFormat").attr("PixelFormat_RGBA");
    glbuffer.attr("PixelType_UByte") = m.attr("PixelType").attr("PixelType_UByte");
    glbuffer.attr("Backing_None") = m.attr("Backing").attr("Backing_None");

    // --- VVGL::GLBufferPool bindings ---
    py::class_<VVGL::GLBufferPool, std::shared_ptr<VVGL::GLBufferPool>>(m, "GLBufferPool")
        .def(py::init([]() {
            // Ensure GLFW context is initialized before creating buffer pool
            if (!initialize_glfw_context()) {
                throw std::runtime_error("Failed to initialize GLFW context");
            }
            // Create a GLBufferPool that uses the current GLFW context
            // We pass nullptr to let the pool use the current context instead of creating a new one
            return std::make_shared<VVGL::GLBufferPool>(nullptr);
        }))
        .def("create_buffer", [](std::shared_ptr<VVGL::GLBufferPool>& self, const VVGL::Size& size) {
            using namespace VVGL;
            // Ensure GLFW context is current before creating buffer
            if (!ensure_gl_context_current()) {
                throw std::runtime_error("Failed to make OpenGL context current");
            }
            GLBuffer::Descriptor desc;
            desc.type = GLBuffer::Type_Tex;
            desc.target = static_cast<GLBuffer::Target>(Target_2D);
            desc.internalFormat = static_cast<GLBuffer::InternalFormat>(IF_RGBA);
            desc.pixelFormat = static_cast<GLBuffer::PixelFormat>(PF_RGBA);
            desc.pixelType = static_cast<GLBuffer::PixelType>(PT_UByte);
            // Pass true to createInCurrentContext to use the GLFW context
            return self->createBufferRef(desc, size, nullptr, VVGL::Size(), true);
        }, py::arg("size"))
        .def("cleanup", [](std::shared_ptr<VVGL::GLBufferPool>& self) {
            // Ensure GLFW context is current before cleanup
            if (!ensure_gl_context_current()) {
                throw std::runtime_error("Failed to make OpenGL context current");
            }
            // Call housekeeping to clean up idle buffers
            self->housekeeping();
            // Call purge to remove all free buffers
            self->purge();
        }, "Clean up the buffer pool by removing idle and free buffers")
        .def("housekeeping", [](std::shared_ptr<VVGL::GLBufferPool>& self) {
            if (!ensure_gl_context_current()) {
                throw std::runtime_error("Failed to make OpenGL context current");
            }
            self->housekeeping();
        }, "Perform housekeeping to clean up idle buffers")
        .def("purge", [](std::shared_ptr<VVGL::GLBufferPool>& self) {
            if (!ensure_gl_context_current()) {
                throw std::runtime_error("Failed to make OpenGL context current");
            }
            self->purge();
        }, "Purge all free buffers from the pool");

    // Note: All buffer/image operations require the OpenGL context to be current (GLFW context). Provide helpers in Python for context management.
    
    // Basic module info
    m.attr("__version__") = "0.2.0";
    m.attr("__platform__") = get_platform_info();
    m.attr("__available__") = is_vvisf_available();

    m.def("reinitialize_glfw_context", &reinitialize_glfw_context, "Reinitialize the GLFW/OpenGL context");
    m.def("cleanup_glfw_context", &cleanup_glfw_context, "Clean up the GLFW/OpenGL context");
    m.def("get_gl_info", &get_gl_info, "Get OpenGL/GLFW/VVISF context info");
    m.def("initialize_glfw_context", &initialize_glfw_context, "Initialize the GLFW/OpenGL context");

    // ISFPassTarget binding (public API only)
    py::class_<VVISF::ISFPassTarget, std::shared_ptr<VVISF::ISFPassTarget>>(m, "ISFPassTarget")
        .def(py::init<const std::string&, const VVISF::ISFDoc*>(), py::arg("name"), py::arg("parent_doc"))
        .def_static("Create", &VVISF::ISFPassTarget::Create, py::arg("name"), py::arg("parent_doc"))
        .def("set_target_width_string", &VVISF::ISFPassTarget::setTargetWidthString)
        .def("target_width_string", &VVISF::ISFPassTarget::targetWidthString)
        .def("set_target_height_string", &VVISF::ISFPassTarget::setTargetHeightString)
        .def("target_height_string", &VVISF::ISFPassTarget::targetHeightString)
        .def("set_float_flag", &VVISF::ISFPassTarget::setFloatFlag)
        .def("float_flag", &VVISF::ISFPassTarget::floatFlag)
        .def("set_persistent_flag", &VVISF::ISFPassTarget::setPersistentFlag)
        .def("persistent_flag", &VVISF::ISFPassTarget::persistentFlag)
        .def("clear_buffer", &VVISF::ISFPassTarget::clearBuffer)
        .def("target_size_needs_eval", &VVISF::ISFPassTarget::targetSizeNeedsEval)
        .def("eval_target_size", &VVISF::ISFPassTarget::evalTargetSize)
        .def("name", [](VVISF::ISFPassTarget& self) { return self.name(); })
        .def("buffer", [](VVISF::ISFPassTarget& self) { return self.buffer(); })
        .def("set_buffer", &VVISF::ISFPassTarget::setBuffer)
        .def("target_size", &VVISF::ISFPassTarget::targetSize)
        .def("cache_uniform_locations", &VVISF::ISFPassTarget::cacheUniformLocations)
        .def("get_uniform_location", &VVISF::ISFPassTarget::getUniformLocation)
        .def("clear_uniform_locations", &VVISF::ISFPassTarget::clearUniformLocations)
        .def("__str__", [](VVISF::ISFPassTarget& self) { return self.name(); });

    // Export CreateGLBufferRef
    m.def("CreateGLBufferRef", []() { return std::make_shared<VVGL::GLBuffer>(); }, "Create a new GLBufferRef");

    // Expose cleanup functions
    m.def("reset_gl_context_state", &reset_gl_context_state, "Reset OpenGL context state to prevent texture corruption");
    m.def("cleanup_scene_state", &cleanup_scene_state, "Clean up scene state and perform buffer pool housekeeping");
} 