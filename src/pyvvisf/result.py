"""Wrapper for rendered image output."""


class RenderResult:
    """Wrapper for a rendered image result."""

    def __init__(self, array):
        self.array = array

    def to_pil_image(self):
        """Convert the result to a PIL Image."""
        from PIL import Image

        return Image.fromarray(self.array).convert("RGBA")

    def __array__(self):
        return self.array
