"""
Manages Framebuffer Objects (FBO) for color-based mouse picking.
Renders the scene off-screen with unique colors to identify clickable elements.
"""
import numpy as np
import glm
from OpenGL.GL import *
from typing import Any, Optional

class FBOPickingManager:
    """Handles the creation and binding of FBOs used for pixel-perfect object selection."""
    
    def __init__(self) -> None:
        self.fbo: Optional[int] = None
        self.tex: Optional[int] = None
        self.depth: Optional[int] = None
        self.w: int = 0
        self.h: int = 0

    def setup_fbo(self, width: int, height: int) -> int:
        """Initializes or resizes the framebuffer to match the viewport dimensions."""
        if self.fbo and self.w == width and self.h == height: 
            return self.fbo
            
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])
            glDeleteTextures(1, [self.tex])
            glDeleteRenderbuffers(1, [self.depth])

        self.fbo = int(np.array(glGenFramebuffers(1)).flatten()[0])
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        
        self.tex = int(np.array(glGenTextures(1)).flatten()[0])
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.tex, 0)

        self.depth = int(np.array(glGenRenderbuffers(1)).flatten()[0])
        glBindRenderbuffer(GL_RENDERBUFFER, self.depth)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth)
        
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.w = width
        self.h = height
        
        return self.fbo

    def draw_picking_2d(self, shader: Any, camera: Any, surface: Any, width: int, height: int) -> None:
        """Renders the 2D contours into the FBO for picking."""
        if not surface: 
            return
            
        shader.use()
        shader.set_mat4("view", camera.get_view_matrix())
        shader.set_mat4("projection", camera.get_projection_matrix())
        shader.set_float("flattenY", 0.0)
        shader.set_int("useUniformPickingColor", 0) 
        shader.set_mat4("model", glm.translate(glm.mat4(1.0), glm.vec3(0.0, surface.min_height - 0.49, 0.0)))
        
        glDisable(GL_MULTISAMPLE)
        glLineWidth(8.0) 
        
        surface.draw_contours_2d()
        
        glLineWidth(1.0)
        glEnable(GL_MULTISAMPLE)