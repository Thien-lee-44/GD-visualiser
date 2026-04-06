"""
OpenGL rendering subsystem.
Handles drawing primitives, surfaces, entities, and framebuffers.
Exposes internal components for clean imports.
"""
from .buffer_objects import BufferObject
from .shader_program import ShaderProgram
from .fbo_picking import FBOPickingManager
from .surface_renderer import SurfaceRenderer
from .entity_renderer import EntityRenderer
from .main_renderer import MainRenderer

__all__ = [
    "BufferObject",
    "ShaderProgram",
    "FBOPickingManager",
    "SurfaceRenderer",
    "EntityRenderer",
    "MainRenderer"
]