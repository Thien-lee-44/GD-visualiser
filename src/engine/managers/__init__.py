"""
Engine Lifecycle and Resource Managers.
Handles centralized instantiation of entities, shaders, and heavy GPU asset data.
"""
from .entity_manager import EntityManager
from .shader_manager import ShaderManager, shader_manager
from .resource_manager import ResourceManager, resource_manager

__all__ = [
    "EntityManager",
    "ShaderManager",
    "shader_manager",
    "ResourceManager",
    "resource_manager"
]