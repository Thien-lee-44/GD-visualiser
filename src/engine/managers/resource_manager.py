"""
Global Cache Manager for 3D Models and Textures.
Caches raw parsed data (RAM) instead of OpenGL buffers (VRAM) to survive context reloads safely.
"""
import os
import numpy as np
from PIL import Image
from typing import Dict, Tuple, Optional

class ResourceManager:
    """Manager ensuring heavy assets are read from disk exactly once and stored in RAM."""
    
    def __init__(self) -> None:
        self._obj_cache: Dict[str, np.ndarray] = {}
        self._texture_cache: Dict[str, Tuple[np.ndarray, int, int]] = {}

    def get_obj_data(self, path: str) -> np.ndarray:
        """Parses an .obj file once and caches its raw vertex data array."""
        if path not in self._obj_cache:
            if not os.path.exists(path):
                return np.array([], dtype=np.float32)
            self._obj_cache[path] = self._parse_obj(path)
        return self._obj_cache[path]

    def get_texture_data(self, path: str) -> Optional[Tuple[np.ndarray, int, int]]:
        """Loads an image once and caches its raw pixel data."""
        if not path or not os.path.exists(path):
            return None
        if path not in self._texture_cache:
            img = Image.open(path).transpose(Image.FLIP_TOP_BOTTOM).convert("RGBA")
            img_data = np.array(img, dtype=np.uint8)
            self._texture_cache[path] = (img_data, img.width, img.height)
        return self._texture_cache[path]

    def _parse_obj(self, path: str) -> np.ndarray:
        """Internal method to process standard Wavefront OBJ files into vertex arrays."""
        vertices, uvs, normals, vertex_data = [], [], [], []
        with open(path, 'r') as f:
            for line in f:
                if line.startswith('v '): 
                    vertices.append(list(map(float, line.strip().split()[1:])))
                elif line.startswith('vt '): 
                    uvs.append(list(map(float, line.strip().split()[1:])))
                elif line.startswith('vn '): 
                    normals.append(list(map(float, line.strip().split()[1:])))
                elif line.startswith('f '):
                    for face in line.strip().split()[1:]:
                        parts = face.split('/')
                        v = int(parts[0]) - 1
                        t = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else -1
                        n = int(parts[2]) - 1 if len(parts) > 2 and parts[2] else -1
                        
                        pos = vertices[v]
                        norm = normals[n] if n >= 0 else [0.0, 1.0, 0.0]
                        uv = uvs[t] if t >= 0 else [0.0, 0.0]
                        vertex_data.extend(pos + norm + uv)
        return np.array(vertex_data, dtype=np.float32)

    def clear_cache(self) -> None:
        """Clears all cached raw data from memory."""
        self._obj_cache.clear()
        self._texture_cache.clear()

# Global Pythonic Singleton instance
resource_manager = ResourceManager()