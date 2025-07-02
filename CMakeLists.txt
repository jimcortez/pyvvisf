cmake_minimum_required(VERSION 3.15)
project(pyvvisf)

# Check if VVISF-GL submodule exists
if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/external/VVISF-GL/README.md")
    message(FATAL_ERROR 
        "VVISF-GL submodule not found!\n"
        "Please run: git submodule update --init --recursive\n"
        "Or run: ./scripts/setup.sh"
    )
endif()

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Platform detection
if(APPLE)
    set(PLATFORM "macOS")
    set(VVGL_SDK "VVGL_SDK_GLFW")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D${VVGL_SDK} -DGL_SILENCE_DEPRECATION")
elseif(UNIX AND NOT APPLE)
    set(PLATFORM "Linux")
    set(VVGL_SDK "VVGL_SDK_GLFW")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D${VVGL_SDK}")
elseif(WIN32)
    set(PLATFORM "Windows")
    set(VVGL_SDK "VVGL_SDK_GLFW")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D${VVGL_SDK}")
else()
    set(PLATFORM "Unknown")
    message(WARNING "Unknown platform detected. VVISF may not work correctly.")
endif()

message(STATUS "Platform: ${PLATFORM}")
message(STATUS "VVGL SDK: ${VVGL_SDK}")

# Set include directories
include_directories(
    ${GLEW_INCLUDE_DIRS}
    ${GLFW_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVGL/include
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVISF/include
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVGL/include/stb
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVISF/include/exprtk
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVISF/include/nlohmann_json
)

# Add definitions
add_definitions(-D${VVGL_SDK})

# Pre-built VVISF libraries
set(VVGL_LIBRARY ${CMAKE_CURRENT_SOURCE_DIR}/external/VVISF-GL/VVGL/bin/libVVGL.a)
set(VVISF_LIBRARY ${CMAKE_CURRENT_SOURCE_DIR}/external/VVISF-GL/VVISF/bin/libVVISF.a)

# Check if libraries exist
if(NOT EXISTS ${VVGL_LIBRARY})
    message(FATAL_ERROR "VVGL library not found: ${VVGL_LIBRARY}")
endif()

if(NOT EXISTS ${VVISF_LIBRARY})
    message(FATAL_ERROR "VVISF library not found: ${VVISF_LIBRARY}")
endif()

message(STATUS "Using VVGL library: ${VVGL_LIBRARY}")
message(STATUS "Using VVISF library: ${VVISF_LIBRARY}")

# Create imported libraries
add_library(VVGL STATIC IMPORTED)
set_target_properties(VVGL PROPERTIES IMPORTED_LOCATION ${VVGL_LIBRARY})

add_library(VVISF STATIC IMPORTED)
set_target_properties(VVISF PROPERTIES IMPORTED_LOCATION ${VVISF_LIBRARY})

# Platform-specific linking - now using GLFW for all platforms
if(APPLE)
    find_package(OpenGL REQUIRED)
    find_package(glfw3 REQUIRED)
    find_package(GLEW REQUIRED)
    set(PLATFORM_LIBS
        "-framework Foundation"
        "-framework ImageIO"
        "-framework OpenGL"
        "-framework IOSurface"
        "-framework CoreGraphics"
        "-framework CoreVideo"
        "-framework CoreMedia"
        "-framework AppKit"
        glfw
        GLEW::GLEW
    )
elseif(UNIX AND NOT APPLE)
    find_package(OpenGL REQUIRED)
    find_package(glfw3 REQUIRED)
    find_package(GLEW REQUIRED)
    set(PLATFORM_LIBS OpenGL::GL glfw GLEW::GLEW)
elseif(WIN32)
    find_package(OpenGL REQUIRED)
    find_package(glfw3 REQUIRED)
    find_package(GLEW REQUIRED)
    set(PLATFORM_LIBS OpenGL::GL glfw GLEW::GLEW)
endif()

# After finding GLEW and GLFW, add their include directories explicitly
include_directories(
    ${GLEW_INCLUDE_DIRS}
    ${GLFW_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVGL/include
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVISF/include
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVGL/include/stb
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVISF/include/exprtk
    ${CMAKE_SOURCE_DIR}/external/VVISF-GL/VVISF/include/nlohmann_json
)

# Print include directories for debugging
get_property(dirs DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
message(STATUS "Include dirs: ${dirs}")

# Test executable to verify VVISF works
add_executable(vvisf_test src/vvisf_test.cpp)
target_compile_definitions(vvisf_test PRIVATE ${VVGL_SDK})
target_link_libraries(vvisf_test VVISF VVGL ${PLATFORM_LIBS})

# Python bindings (required for pyvvisf)
find_package(pybind11 REQUIRED)
if(pybind11_FOUND)
    message(STATUS "pybind11 found, building Python bindings")
    
    pybind11_add_module(vvisf_bindings src/pyvvisf/vvisf_bindings.cpp)
    target_compile_definitions(vvisf_bindings PRIVATE ${VVGL_SDK})
    target_link_libraries(vvisf_bindings PRIVATE VVISF VVGL ${PLATFORM_LIBS})
    
    # Set output directory to src/pyvvisf for development
    set_target_properties(vvisf_bindings PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/src/pyvvisf
    )
else()
    message(FATAL_ERROR "pybind11 not found, but is required for pyvvisf")
endif() 