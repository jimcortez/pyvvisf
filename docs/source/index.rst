pyvvisf Documentation
=====================

Welcome to the documentation for **pyvvisf**!

About
-----

pyvvisf is a Python library for working with ISF shaders and rendering.

Getting Started
---------------

Instructions for installation and usage.

API Reference
-------------

ISFRenderer
~~~~~~~~~~~

The ``ISFRenderer`` class is the main entry point for rendering ISF shaders. It manages the OpenGL context, shader compilation, and rendering workflow.

Basic Usage
^^^^^^^^^^^

.. code-block:: python

    from pyvvisf import ISFRenderer

    shader_content = """
    /*{
        "DESCRIPTION": "Simple color shader",
        "INPUTS": [
            {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]}
        ]
    }*/

    void main() {
        gl_FragColor = color;
    }
    """

    with ISFRenderer(shader_content) as renderer:
        # Render a 1920x1080 image with the default color
        result = renderer.render(1920, 1080)
        image = result.to_pil_image()
        image.save("output.png")

Setting Shader Inputs
^^^^^^^^^^^^^^^^^^^^^

You can set shader inputs using plain Python primitives:

- ``int``, ``float``, ``bool``
- ``list`` or ``tuple`` (for colors and points)

Examples:

.. code-block:: python

    renderer.set_input("scale", 1.0)  # float
    renderer.set_input("color", [1.0, 0.0, 0.0, 1.0])  # RGBA color as list
    renderer.set_input("point", (0.5, 0.5))  # point2D as tuple
    renderer.set_input("flag", False)  # boolean

You do not need to use ISFColor, ISFPoint2D, or other ISF value classes directly.

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