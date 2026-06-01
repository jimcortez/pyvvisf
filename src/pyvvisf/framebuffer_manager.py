"""OpenGL framebuffer management utilities."""

import logging
from typing import Any

from OpenGL import GL

from .errors import RenderingError

logger = logging.getLogger(__name__)


class Framebuffer:
    """Represents an OpenGL framebuffer with associated texture."""

    def __init__(self, fbo_id: int, texture_id: int, width: int, height: int):
        self.fbo_id = fbo_id
        self.texture_id = texture_id
        self.width = width
        self.height = height

    def bind(self):
        """Bind this framebuffer for rendering."""
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.fbo_id)

    def cleanup(self):
        """Delete the framebuffer and texture."""
        if self.fbo_id:
            GL.glDeleteFramebuffers(1, [self.fbo_id])
        if self.texture_id:
            GL.glDeleteTextures(1, [self.texture_id])
        self.fbo_id = 0
        self.texture_id = 0


class FramebufferManager:
    """Manages creation and cleanup of OpenGL framebuffers."""

    def __init__(self):
        self.framebuffers: list[Framebuffer] = []

    def create_framebuffer(self, width: int, height: int) -> Framebuffer:
        """Create a new framebuffer with attached texture."""
        fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)

        tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA,
            width,
            height,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            None,
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)

        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D,
            tex,
            0,
        )

        status = GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
        if status != GL.GL_FRAMEBUFFER_COMPLETE:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            GL.glDeleteFramebuffers(1, [fbo])
            GL.glDeleteTextures(1, [tex])
            raise RenderingError(f"Framebuffer is not complete: status={status}")

        framebuffer = Framebuffer(fbo, tex, width, height)
        self.framebuffers.append(framebuffer)
        return framebuffer

    def bind_default_framebuffer(self):
        """Bind the default framebuffer."""
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def setup_viewport_and_clear(self, width: int, height: int):
        """Set viewport and clear the framebuffer."""
        GL.glViewport(0, 0, width, height)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glClear(int(GL.GL_COLOR_BUFFER_BIT) | int(GL.GL_DEPTH_BUFFER_BIT))

    def read_pixels(self, width: int, height: int) -> bytes:
        """Read pixels from the current framebuffer."""
        data = GL.glReadPixels(0, 0, width, height, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
        if not isinstance(data, bytes):
            data = bytes(data)
        return data

    def cleanup_all(self):
        """Clean up all managed framebuffers."""
        for fb in self.framebuffers:
            fb.cleanup()
        self.framebuffers.clear()

    def cleanup_framebuffer(self, framebuffer: Framebuffer):
        """Clean up a specific framebuffer."""
        if framebuffer in self.framebuffers:
            framebuffer.cleanup()
            self.framebuffers.remove(framebuffer)


class MultiPassFramebufferManager(FramebufferManager):
    """Specialized framebuffer manager for multi-pass rendering."""

    def __init__(self):
        super().__init__()
        self.pass_targets: dict[str, Framebuffer] = {}

    def create_pass_framebuffers(
        self, passes: list[Any], width: int, height: int
    ) -> list[Framebuffer | None]:
        """Create framebuffers for each pass that has a target."""
        pass_framebuffers: list[Framebuffer | None] = []

        for pass_def in passes:
            target_name = self._get_pass_target(pass_def)

            if target_name and target_name != "default":
                framebuffer = self.create_framebuffer(width, height)
                self.pass_targets[target_name] = framebuffer
                pass_framebuffers.append(framebuffer)
            else:
                pass_framebuffers.append(None)

        return pass_framebuffers

    def get_target_texture_id(self, target_name: str) -> int | None:
        """Get the texture ID for a named target."""
        framebuffer = self.pass_targets.get(target_name)
        return framebuffer.texture_id if framebuffer else None

    def bind_target_textures(self, targets: list[str], texture_unit_start: int = 1):
        """Bind target textures to texture units for shader access."""
        tex_unit = texture_unit_start
        for target_name in targets:
            if target_name in self.pass_targets:
                GL.glActiveTexture(int(GL.GL_TEXTURE0) + tex_unit)
                GL.glBindTexture(GL.GL_TEXTURE_2D, self.pass_targets[target_name].texture_id)
                tex_unit += 1

    def _get_pass_target(self, pass_def) -> str | None:
        """Extract target name from pass definition."""
        if hasattr(pass_def, "target"):
            return getattr(pass_def, "target", None)
        elif isinstance(pass_def, dict):
            return pass_def.get("target")
        return None

    def cleanup_all(self):
        """Clean up all framebuffers and targets."""
        super().cleanup_all()
        self.pass_targets.clear()
