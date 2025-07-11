"""OpenGL framebuffer management utilities."""

from typing import List, Tuple, Optional, Iterable, Any
import logging

from OpenGL.GL import glBindFramebuffer, glDeleteFramebuffers, glDeleteTextures, glGenFramebuffers, glGenTextures, glBindTexture, glTexImage2D, glTexParameteri, glFramebufferTexture2D, glCheckFramebufferStatus, glViewport, glDisable, glClear, glReadPixels, glActiveTexture, GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, GL_RGBA, GL_UNSIGNED_BYTE, GL_LINEAR, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_FRAMEBUFFER_COMPLETE, GL_DEPTH_TEST, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_TEXTURE0

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
        try:
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo_id)
        except NameError:
            pass
    
    def cleanup(self):
        """Delete the framebuffer and texture."""
        try:
            if self.fbo_id:
                glDeleteFramebuffers(1, [self.fbo_id])
            if self.texture_id:
                glDeleteTextures(1, [self.texture_id])
        except NameError:
            pass
        self.fbo_id = 0
        self.texture_id = 0


class FramebufferManager:
    """Manages creation and cleanup of OpenGL framebuffers."""
    
    def __init__(self):
        self.framebuffers: List[Framebuffer] = []
    
    def create_framebuffer(self, width: int, height: int) -> Framebuffer:
        """Create a new framebuffer with attached texture."""
        try:
            # Create framebuffer
            fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            
            # Create texture
            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            
            # Attach texture to framebuffer
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)
            
            # Check framebuffer completeness
            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                glBindFramebuffer(GL_FRAMEBUFFER, 0)
                glDeleteFramebuffers(1, [fbo])
                glDeleteTextures(1, [tex])
                raise RenderingError(f"Framebuffer is not complete: status={status}")
            
            framebuffer = Framebuffer(fbo, tex, width, height)
            self.framebuffers.append(framebuffer)
            return framebuffer
            
        except NameError:
            # OpenGL not available - for testing purposes
            return Framebuffer(1, 1, width, height)
    
    def bind_default_framebuffer(self):
        """Bind the default framebuffer."""
        try:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
        except NameError:
            pass
    
    def setup_viewport_and_clear(self, width: int, height: int):
        """Set viewport and clear the framebuffer."""
        try:
            glViewport(0, 0, width, height)
            glDisable(GL_DEPTH_TEST)
            glClear(int(GL_COLOR_BUFFER_BIT) | int(GL_DEPTH_BUFFER_BIT))
        except NameError:
            pass
    
    def read_pixels(self, width: int, height: int) -> bytes:
        """Read pixels from the current framebuffer."""
        try:
            data = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
            if not isinstance(data, bytes):
                data = bytes(data)
            return data
        except NameError:
            # OpenGL not available - for testing purposes
            return b'\x00' * (width * height * 4)
    
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
    
    def create_pass_framebuffers(self, passes: List[Any], width: int, height: int) -> List[Optional[Framebuffer]]:
        """Create framebuffers for each pass that has a target."""
        pass_framebuffers = []
        
        for pass_def in passes:
            target_name = self._get_pass_target(pass_def)
            
            if target_name and target_name != 'default':
                # Create framebuffer for this pass
                framebuffer = self.create_framebuffer(width, height)
                self.pass_targets[target_name] = framebuffer
                pass_framebuffers.append(framebuffer)
            else:
                # No target or default target - will render to final framebuffer
                pass_framebuffers.append(None)
        
        return pass_framebuffers
    
    def get_target_texture_id(self, target_name: str) -> Optional[int]:
        """Get the texture ID for a named target."""
        framebuffer = self.pass_targets.get(target_name)
        return framebuffer.texture_id if framebuffer else None
    
    def bind_target_textures(self, targets: List[str], texture_unit_start: int = 1):
        """Bind target textures to texture units for shader access."""
        try:
            tex_unit = texture_unit_start
            for target_name in targets:
                if target_name in self.pass_targets:
                    glActiveTexture(int(GL_TEXTURE0) + tex_unit)
                    glBindTexture(GL_TEXTURE_2D, self.pass_targets[target_name].texture_id)
                    tex_unit += 1
        except NameError:
            pass
    
    def _get_pass_target(self, pass_def) -> Optional[str]:
        """Extract target name from pass definition."""
        if hasattr(pass_def, 'target'):
            return getattr(pass_def, 'target', None)
        elif isinstance(pass_def, dict):
            return pass_def.get('target')
        return None
    
    def cleanup_all(self):
        """Clean up all framebuffers and targets."""
        super().cleanup_all()
        self.pass_targets.clear()