#!/usr/bin/env python3
"""Setup script for pyvvisf - Python bindings for VVISF."""

import os
import sys
import subprocess
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11

# Get the directory containing this setup.py
here = Path(__file__).parent.absolute()


class CMakeExtension(Extension):
    """Custom Extension class for CMake-built extensions."""
    
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    """Custom build command for CMake extensions."""
    
    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        
        # Required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep
            
        cmake_args = [
            f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}',
            f'-DPYTHON_EXECUTABLE={sys.executable}',
            f'-DCMAKE_BUILD_TYPE=Release',
        ]
        
        # Add platform-specific arguments
        if sys.platform.startswith('darwin'):
            cmake_args.extend(['-DCMAKE_OSX_DEPLOYMENT_TARGET=10.15'])
        elif sys.platform.startswith('win'):
            cmake_args.extend(['-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=TRUE'])
            
        # Set CMAKE_PREFIX_PATH to find pybind11
        cmake_args.extend([f'-DCMAKE_PREFIX_PATH={pybind11.get_cmake_dir()}'])
        
        # Ensure we can find the CMakeLists.txt
        cmake_lists_dir = here
        if not os.path.exists(os.path.join(cmake_lists_dir, 'CMakeLists.txt')):
            raise RuntimeError(f"CMakeLists.txt not found in {cmake_lists_dir}")
            
        # Build the extension
        try:
            subprocess.check_call(['cmake', cmake_lists_dir] + cmake_args, cwd=self.build_temp)
            subprocess.check_call(['cmake', '--build', '.', '--config', 'Release'], cwd=self.build_temp)
        except subprocess.CalledProcessError as e:
            print(f"CMake build failed: {e}")
            raise


def main():
    """Main setup function."""
    
    # Check if VVISF-GL is available
    vvisf_gl_path = here / 'external' / 'VVISF-GL'
    if not vvisf_gl_path.exists():
        print("Warning: VVISF-GL not found. Please run:")
        print("  git submodule update --init --recursive")
        print("  ./scripts/setup.sh")
        sys.exit(1)
    
    # Check if VVISF libraries are built
    vvgl_lib = vvisf_gl_path / 'VVGL' / 'bin' / 'libVVGL.a'
    vvisf_lib = vvisf_gl_path / 'VVISF' / 'bin' / 'libVVISF.a'
    
    if not vvgl_lib.exists() or not vvisf_lib.exists():
        print("Warning: VVISF libraries not found. Please run:")
        print("  ./scripts/build_vvisf.sh")
        sys.exit(1)
    
    setup(
        name="pyvvisf",
        version="0.1.0",
        author="Your Name",
        author_email="your.email@example.com",
        description="Python bindings for VVISF (Vidvox Interactive Shader Format)",
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        url="https://github.com/yourusername/pyvvisf",
        packages=["pyvvisf"],
        package_dir={"": "src"},
        ext_modules=[CMakeExtension("pyvvisf")],
        cmdclass={"build_ext": CMakeBuild},
        zip_safe=False,
        python_requires=">=3.8",
        install_requires=[
            "pybind11>=2.6.0",
            "numpy>=1.21.0",
            "pillow>=9.0.0",
        ],
        extras_require={
            "dev": [
                "pytest>=7.0.0",
                "pytest-cov>=4.0.0",
                "black>=22.0.0",
                "isort>=5.0.0",
                "flake8>=5.0.0",
                "mypy>=1.0.0",
                "pre-commit>=2.20.0",
            ],
        },
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Multimedia :: Graphics",
            "Topic :: Scientific/Engineering :: Image Processing",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )


if __name__ == "__main__":
    main() 