"""
Defines mathematical and geometric entities for the 3D scene.
All models strictly inherit from the core BufferObject and fetch raw data via ResourceManager.
"""
import math
from pathlib import Path
import numpy as np
from OpenGL.GL import *
from typing import List, Any, Optional

from src.engine.renderers.buffer_objects import BufferObject
from src.engine.managers.resource_manager import resource_manager
from src.app.settings import settings

class LineMesh(BufferObject):
    """A generic dynamic mesh for drawing lines (e.g., axes, grid, contour lines)."""
    
    def __init__(self, vertices: List[float]) -> None:
        super().__init__(vertices, None, vertex_size=8)
        
    def draw(self, shader: Optional[Any] = None) -> None:
        """Issues the OpenGL draw call for rendering the lines."""
        if len(self.vertices) > 0:
            glBindVertexArray(self.vao)
            glDrawArrays(GL_LINES, 0, len(self.vertices) // self.vertex_size)
            glBindVertexArray(0)

class TexturedMeshObj(BufferObject):
    """Loads and renders a 3D model, utilizing the ResourceManager for RAM-cached raw data."""
    
    def __init__(self, obj_path: str, texture_path: Optional[str] = None, original_radius: float = 0.5) -> None:
        self.original_radius = original_radius
        
        # 1. Retrieve raw texture pixel data from RAM cache and generate Texture ID in the active context
        tex_data = resource_manager.get_texture_data(texture_path) if texture_path else None
        if tex_data:
            img_data, width, height = tex_data
            self.texture_id = int(np.array(glGenTextures(1)).flatten()[0])
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)
        else:
            self.texture_id = 0

        # 2. Retrieve raw vertex data from RAM cache
        vertex_data = resource_manager.get_obj_data(obj_path)
        
        # 3. Initialize VAO/VBO via BufferObject parent in the current active context
        super().__init__(vertex_data.tolist(), None, vertex_size=8)
        self.vertex_count = len(vertex_data) // 8

    def draw(self, shader: Optional[Any] = None) -> None:
        """Binds textures and issues the OpenGL draw call for rendering the triangles."""
        if self.texture_id and shader:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            shader.set_int("uTexture", 0)
            shader.set_int("useTexture", 1) 
        elif shader:
            shader.set_int("useTexture", 0)

        super().draw()

class FootballMesh(TexturedMeshObj):
    """High-poly textured football model for 3D optimizer representation."""
    
    def __init__(self) -> None:
        models_dir = settings.get_path("paths", "models", default=Path("assets") / "models")
        textures_dir = settings.get_path("paths", "textures", default=Path("assets") / "textures")
        obj_path = models_dir / "sphere_latlong.obj"
        tex_path = textures_dir / "football-diffuse.png"
        super().__init__(str(obj_path), str(tex_path), original_radius=0.5)

class CylinderMesh(TexturedMeshObj):
    """High-poly cylinder model for arrows, loaded via OBJ data cache."""
    
    def __init__(self) -> None:
        models_dir = settings.get_path("paths", "models", default=Path("assets") / "models")
        super().__init__(str(models_dir / "cylinder.obj"))

class ConeMesh(TexturedMeshObj):
    """High-poly cone model for arrows, loaded via OBJ data cache."""
    
    def __init__(self) -> None:
        models_dir = settings.get_path("paths", "models", default=Path("assets") / "models")
        super().__init__(str(models_dir / "cone.obj"))

class WireframeSphere(BufferObject):
    """A minimal wireframe sphere calculated via trigonometry for a cleaner visual."""
    
    def __init__(self, radius: float = 1.0, num_meridians: int = 6, segments_per_circle: int = 36) -> None:
        self.raw_radius = radius
        vertices = []
        
        for i in range(num_meridians):
            lon = i * (math.pi / num_meridians) 
            for j in range(segments_per_circle):
                lat1 = j * (2 * math.pi / segments_per_circle)
                lat2 = (j + 1) * (2 * math.pi / segments_per_circle)
                
                x1 = radius * math.cos(lat1) * math.cos(lon)
                y1 = radius * math.sin(lat1)
                z1 = radius * math.cos(lat1) * math.sin(lon)
                
                x2 = radius * math.cos(lat2) * math.cos(lon)
                y2 = radius * math.sin(lat2)
                z2 = radius * math.cos(lat2) * math.sin(lon)
                
                vertices.extend([x1, y1, z1, 0, 1, 0, 0, 0, x2, y2, z2, 0, 1, 0, 0, 0])
                
        super().__init__(vertices, None, vertex_size=8)
        
    def draw(self, shader: Optional[Any] = None) -> None:
        """Issues the OpenGL draw call for rendering the wireframe lines."""
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINES, 0, len(self.vertices) // self.vertex_size)
        glBindVertexArray(0)
