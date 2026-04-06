"""
Global Cache Manager for OpenGL Shader Programs.
Prevents redundant compilation of GLSL files.
"""
from typing import Dict
from src.engine.renderers.shader_program import ShaderProgram

class ShaderManager:
    """Manager ensuring shaders are compiled and stored in GPU memory exactly once."""
    
    def __init__(self) -> None:
        self._shaders: Dict[str, ShaderProgram] = {}

    def get_shader(self, name: str, vert_path: str, frag_path: str) -> ShaderProgram:
        """Retrieves a cached shader or compiles a new one if not found."""
        if name not in self._shaders:
            self._shaders[name] = ShaderProgram(vert_path, frag_path)
        return self._shaders[name]

    def clear_cache(self) -> None:
        """Clears all cached shaders (Useful when hot-reloading shaders)."""
        self._shaders.clear()

# Global Pythonic Singleton instance
shader_manager = ShaderManager()