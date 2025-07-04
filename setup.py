#!/usr/bin/env python3
"""Setup script for pyvvisf - Python bindings for VVISF."""

import os
import sys
import subprocess
import platform
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
    """Custom build command for CMake extensions with wheel support."""
    
    def run(self):
        """Run the build process."""
        # Check if we're building a wheel
        is_wheel_build = os.environ.get('VVISF_BUILD_TYPE') == 'wheel'
        
        # Also check if we're in a pip build environment
        is_pip_build = (
            os.environ.get('PIP_BUILD_WHEEL') == '1' or
            'pip' in os.environ.get('PIP_BUILD_ENV', '') or
            any('pip' in arg for arg in sys.argv if isinstance(arg, str)) or
            'bdist_wheel' in sys.argv or
            'build' in sys.argv
        )
        
        if is_wheel_build or is_pip_build:
            print("Building for wheel distribution...")
            # Set the environment variable for CMake
            os.environ['VVISF_BUILD_TYPE'] = 'wheel'
            self._build_for_wheel()
        else:
            print("Building for development...")
            self._build_for_development()
    
    def _build_for_wheel(self):
        """Build process optimized for wheel creation."""
        print("Starting wheel build process...")
        
        # Ensure VVISF-GL is available
        print("Ensuring VVISF-GL is available...")
        self._ensure_vvisf_gl()
        
        # Build VVISF libraries
        print("Building VVISF libraries...")
        self._build_vvisf_libraries()
        
        # Build the extension
        print("Building Python extension...")
        for ext in self.extensions:
            self.build_extension(ext)
    
    def _build_for_development(self):
        """Build process for development environment."""
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
        
        # Build the extension
        for ext in self.extensions:
            self.build_extension(ext)
    
    def _ensure_vvisf_gl(self):
        """Ensure VVISF-GL submodule is available."""
        vvisf_gl_path = here / 'external' / 'VVISF-GL'
        print(f"Checking for VVISF-GL at: {vvisf_gl_path}")
        
        if not vvisf_gl_path.exists():
            print("Cloning VVISF-GL repository...")
            subprocess.check_call([
                'git', 'clone', 'https://github.com/mrRay/VVISF-GL.git', 
                str(vvisf_gl_path)
            ])
        else:
            print("VVISF-GL repository already exists")
        
        # Apply patches
        patches = [
            'vvisf-architecture-support.patch',
            'vvisf-glfw-support.patch'
        ]
        
        for patch_name in patches:
            patch_file = here / 'patches' / patch_name
            if patch_file.exists():
                print(f"Applying {patch_name}...")
                try:
                    subprocess.check_call([
                        'git', 'apply', str(patch_file)
                    ], cwd=vvisf_gl_path)
                except subprocess.CalledProcessError:
                    print(f"Warning: {patch_name} may already be applied")
            else:
                print(f"Warning: {patch_name} not found")
    
    def _build_vvisf_libraries(self):
        """Build VVISF libraries for the current platform."""
        vvisf_gl_path = here / 'external' / 'VVISF-GL'
        
        # Enhanced architecture detection
        arch = self._detect_architecture()
        print(f"Building VVISF libraries for {arch}...")
        
        # Set up build environment
        build_env = os.environ.copy()
        build_env['ARCH'] = arch
        
        # Add platform-specific environment variables
        if sys.platform.startswith('darwin'):
            # macOS specific settings
            build_env['MACOSX_DEPLOYMENT_TARGET'] = '10.15'
            if arch == 'universal2':
                build_env['CMAKE_OSX_ARCHITECTURES'] = 'x86_64;arm64'
            else:
                build_env['CMAKE_OSX_ARCHITECTURES'] = arch
        elif sys.platform.startswith('linux'):
            # Linux specific settings
            build_env['CFLAGS'] = f'-march=native -mtune=native'
            build_env['CXXFLAGS'] = f'-march=native -mtune=native'
        elif sys.platform.startswith('win'):
            # Windows specific settings
            build_env['PLATFORM'] = 'x64'
        
        # Build VVGL
        vvgl_dir = vvisf_gl_path / 'VVGL'
        print(f"Building VVGL for {arch}...")
        subprocess.check_call(['make', 'clean'], cwd=vvgl_dir, env=build_env)
        subprocess.check_call(['make'], cwd=vvgl_dir, env=build_env)
        
        # Build VVISF
        vvisf_dir = vvisf_gl_path / 'VVISF'
        print(f"Building VVISF for {arch}...")
        subprocess.check_call(['make', 'clean'], cwd=vvisf_dir, env=build_env)
        subprocess.check_call(['make'], cwd=vvisf_dir, env=build_env)
    
    def _detect_architecture(self):
        """Enhanced architecture detection for wheel builds."""
        # Check if we're in a CI environment with specific architecture
        ci_arch = os.environ.get('CIBW_ARCHS')
        if ci_arch:
            if ci_arch == 'x86_64':
                return 'x86_64'
            elif ci_arch in ['aarch64', 'arm64']:
                return 'arm64'
            elif ci_arch == 'universal2':
                return 'universal2'
        
        # Check if we're building for a specific target
        target_arch = os.environ.get('TARGET_ARCH')
        if target_arch:
            return target_arch
        
        # Detect current architecture
        arch = platform.machine().lower()
        
        if sys.platform.startswith('darwin'):
            # macOS architecture detection
            if arch in ['arm64', 'aarch64']:
                return 'arm64'
            elif arch == 'x86_64':
                # Check if we should build universal2
                if os.environ.get('BUILD_UNIVERSAL2', 'false').lower() == 'true':
                    return 'universal2'
                return 'x86_64'
            else:
                return 'x86_64'  # Default fallback
        elif sys.platform.startswith('linux'):
            # Linux architecture detection
            if arch in ['aarch64', 'arm64']:
                return 'aarch64'
            elif arch in ['x86_64', 'amd64']:
                return 'x86_64'
            else:
                return 'x86_64'  # Default fallback
        elif sys.platform.startswith('win'):
            # Windows architecture detection
            if arch in ['amd64', 'x86_64']:
                return 'x64'
            elif arch in ['arm64', 'aarch64']:
                return 'arm64'
            else:
                return 'x64'  # Default fallback
        else:
            # Unknown platform, use generic detection
            if arch in ['aarch64', 'arm64']:
                return 'arm64'
            else:
                return 'x86_64'
    
    def build_extension(self, ext):
        """Build a single extension."""
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        
        # Required for auto-detection of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep
        
        # Ensure build directory exists
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
            
        cmake_args = [
            f'-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}',
            f'-DPYTHON_EXECUTABLE={sys.executable}',
            f'-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_VERBOSE_MAKEFILE=ON',
        ]
        
        # Add platform-specific arguments
        if sys.platform.startswith('darwin'):
            arch = self._detect_architecture()
            cmake_args.append('-DCMAKE_OSX_DEPLOYMENT_TARGET=10.15')
            if arch == 'universal2':
                cmake_args.append('-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64')
            else:
                cmake_args.append(f'-DCMAKE_OSX_ARCHITECTURES={arch}')
        elif sys.platform.startswith('win'):
            cmake_args.extend(['-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=TRUE'])
            
        # Set CMAKE_PREFIX_PATH to find pybind11
        cmake_args.extend([f'-DCMAKE_PREFIX_PATH={pybind11.get_cmake_dir()}'])
        
        # Ensure we can find the CMakeLists.txt
        cmake_lists_dir = here
        if not os.path.exists(os.path.join(cmake_lists_dir, 'CMakeLists.txt')):
            raise RuntimeError(f"CMakeLists.txt not found in {cmake_lists_dir}")
            
        # Build the extension
        print(f"Building extension in: {self.build_temp}")
        print(f"CMake arguments: {cmake_args}")
        
        try:
            print("Running cmake configure...")
            subprocess.check_call(['cmake', cmake_lists_dir] + cmake_args, cwd=self.build_temp)
            print("Running cmake build...")
            subprocess.check_call(['cmake', '--build', '.', '--config', 'Release'], cwd=self.build_temp)
        except subprocess.CalledProcessError as e:
            print(f"CMake build failed: {e}")
            raise


def main():
    """Main setup function."""
    
    # Import version from the generated file
    try:
        from src.pyvvisf._version import __version__
    except ImportError:
        # Fallback for when version file doesn't exist yet
        __version__ = "0.0.0"
    
    setup(
        name="pyvvisf",
        version=__version__,
        ext_modules=[CMakeExtension("pyvvisf")],
        cmdclass={"build_ext": CMakeBuild},
        zip_safe=False,
        python_requires=">=3.8",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Multimedia :: Graphics",
            "Topic :: Scientific/Engineering :: Image Processing",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Operating System :: OS Independent",
        ],
    )


if __name__ == "__main__":
    main() 