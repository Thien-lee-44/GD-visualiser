"""
Renderer for the mathematical landscape.
Handles drawing the 3D map, 2D heatmap, grid lines, and boundary previews.
"""
import numpy as np
import glm
import ctypes
from OpenGL.GL import *
from typing import Any, Dict

from src.utils.constants import Colors, SurfaceStyle

class SurfaceRenderer:
    """Encapsulates the OpenGL logic for rendering the environment map."""
    
    def draw_2d_minimap(self, heatmap_shader: Any, surface_shader: Any, surface: Any, world_matrix: glm.mat4, floor_y: float) -> None:
        """Draws the top-down 2D heatmap and contour lines."""
        heatmap_shader.use()
        heatmap_shader.set_float("flattenY", 0.0)
        heatmap_shader.set_mat4("model", glm.translate(world_matrix, glm.vec3(0.0, floor_y, 0.0)))
        heatmap_shader.set_float("alpha", 1.0) 
        
        glDepthMask(GL_FALSE) 
        if hasattr(surface, 'slope_mesh') and surface.slope_mesh: 
            surface.slope_mesh.draw()
        glDepthMask(GL_TRUE)

        surface_shader.use()
        surface_shader.set_float("flattenY", 0.0)
        surface_shader.set_int("is_contour", 1) 
        surface_shader.set_float("line_brightness", 1.5) 
        surface_shader.set_mat4("model", glm.translate(world_matrix, glm.vec3(0.0, floor_y + 0.01, 0.0)))
        
        glLineWidth(1.5) 
        surface.draw_contours_2d()
        glLineWidth(1.0)
        surface_shader.set_int("is_contour", 0) 

    def draw_3d_environment(self, shader: Any, surface: Any, scaled_world_matrix: glm.mat4, surface_style: str, show_grid: bool) -> None:
        """Draws the 3D surface mesh and coordinate grids using central color constants."""
        shader.use()
        shader.set_float("flattenY", 1.0)
        shader.set_mat4("model", scaled_world_matrix)
        shader.set_float("alpha", 0.3) 

        if show_grid and surface.grid_mesh:
            shader.set_int("is_grid", 1) 
            shader.set_vec3("objectColor", glm.vec3(*Colors.GRID_LINE)) 
            glLineWidth(1.0)
            surface.grid_mesh.draw()

            glLineWidth(3.0)
            shader.set_vec3("objectColor", glm.vec3(*Colors.AXIS_X))
            surface.axis_x_mesh.draw()
            
            shader.set_vec3("objectColor", glm.vec3(*Colors.AXIS_Y))
            surface.axis_y_mesh.draw()
            
            shader.set_vec3("objectColor", glm.vec3(*Colors.AXIS_Z))
            surface.axis_z_mesh.draw()
            
            glLineWidth(1.0)
            shader.set_int("is_grid", 0)

        if SurfaceStyle.COLORMAP.value in str(surface_style):
            if SurfaceStyle.CONTOUR.value in str(surface_style):
                shader.set_int("is_contour", 1) 
                shader.set_float("line_brightness", 1.2) 
                glLineWidth(1.5) 
                surface.draw_contours_3d() 
                shader.set_int("is_contour", 0)

            glEnable(GL_POLYGON_OFFSET_FILL)
            glPolygonOffset(2.0, 2.0) 
            
            glEnable(GL_CULL_FACE)
            glDepthMask(GL_FALSE) 
            
            glCullFace(GL_FRONT)
            surface.draw()
            
            glCullFace(GL_BACK)
            surface.draw()
            
            glDepthMask(GL_TRUE)
            glDisable(GL_CULL_FACE)
            glDisable(GL_POLYGON_OFFSET_FILL)
        else:
            if SurfaceStyle.CONTOUR.value in str(surface_style):
                shader.set_int("is_contour", 1) 
                shader.set_float("line_brightness", 1.2) 
                glLineWidth(1.5) 
                surface.draw_contours_3d()
                shader.set_int("is_contour", 0)

    def draw_boundary_preview(self, shader: Any, surface: Any, preview_boundary: Dict[str, Any], 
                              line_vao: int, line_vbo: int, world_matrix: glm.mat4, 
                              show_3d: bool, floor_y: float, height_scale: float = 1.0) -> None:
        """Draws the bounding box preview when adjusting map sizes."""
        if not preview_boundary or not surface: 
            return
            
        x_min, x_max = preview_boundary['x_range']
        z_min, z_max = preview_boundary['y_range']
        
        y_min = floor_y if show_3d else floor_y + 0.01
        y_max = (surface.max_height * height_scale) + 0.5 if show_3d else floor_y + 0.01
        
        shader.use()
        shader.set_float("flattenY", 1.0 if show_3d else 0.0)
        shader.set_mat4("model", world_matrix)

        lines = [
            x_min, y_min, z_min,  x_max, y_min, z_min,  x_max, y_min, z_min,  x_max, y_min, z_max,
            x_max, y_min, z_max,  x_min, y_min, z_max,  x_min, y_min, z_max,  x_min, y_min, z_min,
            x_min, y_max, z_min,  x_max, y_max, z_min,  x_max, y_max, z_min,  x_max, y_max, z_max,
            x_max, y_max, z_max,  x_min, y_max, z_max,  x_min, y_max, z_max,  x_min, y_max, z_min,
            x_min, y_min, z_min,  x_min, y_max, z_min,  x_max, y_min, z_min,  x_max, y_max, z_min,
            x_max, y_min, z_max,  x_max, y_max, z_max,  x_min, y_min, z_max,  x_min, y_max, z_max,
        ]
        
        data = np.array(lines, dtype=np.float32)
        glBindVertexArray(line_vao)
        glBindBuffer(GL_ARRAY_BUFFER, line_vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        shader.set_int("useTexture", 0)
        shader.set_vec3("objectColor", glm.vec3(*Colors.BOUNDARY_BOX)) 
        glEnable(GL_DEPTH_TEST) 
        glLineWidth(2.5)
        glDrawArrays(GL_LINES, 0, 24)
        glLineWidth(1.0)