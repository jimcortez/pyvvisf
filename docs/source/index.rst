pyvvisf Documentation
=====================

Welcome to the documentation for **pyvvisf**!

About
-----

pyvvisf is a Python library for working with ISF shaders and rendering.

Getting Started
---------------

Install pyvvisf with pip:

.. code-block:: bash

    pip install pyvvisf

For development installation:

.. code-block:: bash

    git clone https://github.com/jimcortez/pyvvisf.git
    cd pyvvisf
    pip install -e .

Quick Start
~~~~~~~~~~~

Here's a minimal example using a well-formed ISF shader:

.. code-block:: python

    from pyvvisf import ISFRenderer

    # A simple ISF shader (every pixel is the selected color)
    test_shader = """
    /*{
        \"DESCRIPTION\": \"Every pixel is the selected color.\",
        \"CREDIT\": \"pyvvisf example\",
        \"ISFVSN\": \"2.0\",
        \"CATEGORIES\": [\"Generator\"],
        \"INPUTS\": [
            {\"NAME\": \"color\", \"TYPE\": \"color\", \"DEFAULT\": [1.0, 0.0, 0.0, 1.0]}
        ]
    }*/
    void main() {
        gl_FragColor = color;
    }
    """

    with ISFRenderer(test_shader) as renderer:
        # Render with the default color (red)
        buffer = renderer.render(512, 512)
        image = buffer.to_pil_image()
        image.save("output_red.png")

        # Render with a custom color (green)
        renderer.set_input("color", (0.0, 1.0, 0.0, 1.0))
        buffer = renderer.render(512, 512)
        image = buffer.to_pil_image()
        image.save("output_green.png")

GLSL Version Support
~~~~~~~~~~~~~~~~~~~

pyvvisf supports multiple GLSL versions and can automatically detect which versions are supported on your system:

.. code-block:: python

    from pyvvisf import get_supported_glsl_versions, ISFRenderer

    # Check which GLSL versions are supported
    supported_versions = get_supported_glsl_versions()
    print(f"Supported GLSL versions: {supported_versions}")

    # Create renderer with specific GLSL version
    renderer = ISFRenderer(shader_content, glsl_version='330')

The default GLSL version is '330', but you can specify any supported version. The library will automatically test shader compilation to ensure compatibility.

Examples
~~~~~~~~

See the ``examples/`` directory for complete examples:

- ``isf_renderer_demo.py``: Render ISF shaders to images, set inputs, and save output.
- ``isf_window_demo.py``: Render ISF shaders in a window (interactive display).
- ``time_offset_demo.py``: Render shaders at different time offsets (for animation or frame capture).

Shader examples are in ``examples/shaders/``:

- ``simple_color_change.fs``: Single color input, fills the screen with the selected color.
- ``simple_color_animation.fs``: Fades between two user-selected colors over time.
- ``shapes.fs``: Animated shapes (moving circle, rotating rectangle, pulsating ring).
- ``simple.fs``: Minimal shader, fills the screen with blue.

Setting Shader Inputs
^^^^^^^^^^^^^^^^^^^^^

You can set shader inputs using plain Python primitives:

- ``int``, ``float``, ``bool``
- ``list`` or ``tuple`` (for colors and points)

You can set a single input with :meth:`set_input`, or set multiple inputs at once with :meth:`set_inputs`:

Examples:

.. code-block:: python

    renderer.set_input("scale", 1.0)  # float
    renderer.set_input("color", [1.0, 0.0, 0.0, 1.0])  # RGBA color as list
    renderer.set_input("point", (0.5, 0.5))  # point2D as tuple
    renderer.set_input("flag", False)  # boolean

    # Set multiple inputs at once
    renderer.set_inputs({
        "color": [0.0, 1.0, 0.0, 1.0],
        "scale": 0.5,
        "flag": True
    })

The :meth:`set_inputs` method is a convenience function that takes a dictionary of input names and values, and calls :meth:`set_input` for each one. This is useful for updating several shader parameters in a single call.

You do not need to use ISFColor, ISFPoint2D, or other ISF value classes directly.

ISF Features
-----------

pyvvisf supports the full ISF 2.0 specification including:

- **Multi-pass rendering**: Shaders with multiple render passes
- **ISF imports**: Support for imported textures and shaders
- **ISF special functions**: IMG_THIS_PIXEL, IMG_PIXEL, IMG_SIZE, etc.
- **ISF sampling functions**: VVSAMPLER_2DBYPIXEL, VVSAMPLER_2DBYNORM
- **Modern GLSL**: Support for GLSL 330+ with proper ISF 2.0 compatibility

Value Types
-----------

These types help you specify shader inputs in a structured way (optional, primitives are preferred):

- **ISFColor**: RGBA color value
- **ISFPoint2D**: 2D point value
- **ISFFloat**: Floating-point value
- **ISFInt**: Integer value
- **ISFBool**: Boolean value

Error Handling
--------------

All rendering errors raise exceptions derived from ``pyvvisf.errors.ISFError``. For example:

.. code-block:: python

    from pyvvisf import ISFRenderer, errors

    try:
        with ISFRenderer("") as renderer:  # Empty shader will fail
            renderer.render()
    except errors.ISFError as e:
        print(f"Rendering failed: {e}")

Development
-----------

To install development dependencies and run tests:

.. code-block:: bash

    pip install -e ".[dev]"
    pytest


API Details
===========

.. autoclass:: pyvvisf.ISFRenderer
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ISFParser
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ISFMetadata
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ISFColor
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ISFPoint2D
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ISFValue
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ISFError
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ISFParseError
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.ShaderCompilationError
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: pyvvisf.RenderingError
    :members:
    :undoc-members:
    :show-inheritance:

Utility Functions
================

.. autofunction:: pyvvisf.get_supported_glsl_versions 