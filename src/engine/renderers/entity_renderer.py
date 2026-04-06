"""
Renderer for optimizer entities (agents, trails, and markers).
Handles drawing spheres, footballs, historical trajectory lines, and directional arrows.
"""
import numpy as np
import glm
import ctypes
import math
from OpenGL.GL import *
from typing import List, Any, Optional

class EntityRenderer:
    """Encapsulates the OpenGL logic for rendering moving agents and their associated visuals."""
    
    def __init__(self, line_vao: int, line_vbo: int, sphere_mesh: Any, football_mesh: Optional[Any], 
                 cylinder_mesh: Any, cone_mesh: Any) -> None:
        self.line_vao = line_vao 
        self.line_vbo = line_vbo
        self.sphere = sphere_mesh
        self.football = football_mesh
        self.cylinder_mesh = cylinder_mesh
        self.cone_mesh = cone_mesh

    def draw_entities(self, shader: Any, entities: List[Any], world_matrix: glm.mat4, 
                      is_2d_mode: bool, floor_y: float, selected_entity_id: Optional[str], 
                      surface_max_height: float, sphere_style: str, height_scale: float = 1.0) -> None:
        """Draws all active entities, their trails, and highlights the selected one."""
        shader.use()
        shader.set_int("useTexture", 0)
        shader.set_float("alpha", 1.0) 
        
        for ent in entities:
            if np.isnan(ent.current_pos).any() or np.isinf(ent.current_pos).any():
                continue 
                
            is_selected = (selected_entity_id == ent.id)
            shader.set_vec3("objectColor", ent.base_color)
            
            # 1. Render Trajectory Trails
            if ent.show_trail and len(ent.trail_3d) >= 3:
                raw_trail = np.array(ent.trail_3d, dtype=np.float32)
                
                if not is_2d_mode:
                    scaled_world = glm.scale(world_matrix, glm.vec3(1.0, height_scale, 1.0))
                    shader.set_mat4("model", scaled_world)
                else:
                    shader.set_mat4("model", glm.translate(world_matrix, glm.vec3(0.0, floor_y + 0.02, 0.0)))
                    
                glBindVertexArray(self.line_vao) 
                glBindBuffer(GL_ARRAY_BUFFER, self.line_vbo)
                glBufferData(GL_ARRAY_BUFFER, raw_trail.nbytes, raw_trail, GL_DYNAMIC_DRAW)
                glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                glEnableVertexAttribArray(0)
                
                glLineWidth(1.5)
                glDrawArrays(GL_LINE_STRIP, 0, len(ent.trail_3d) // 3)
                
                # Highlight vertices for the selected entity
                if is_selected:
                    glPointSize(5.0 if is_2d_mode else 7.0)
                    shader.set_vec3("objectColor", glm.vec3(1.0, 1.0, 1.0))
                    glDrawArrays(GL_POINTS, 0, len(ent.trail_3d) // 3)
                    glPointSize(1.0)

            # 2. Render Entity Body (Sphere or 3D Football Model)
            if hasattr(ent, 'last_center_3d') and ent.last_center_3d is not None:
                if is_2d_mode:
                    shader.set_mat4("model", glm.translate(world_matrix, glm.vec3(0.0, floor_y + 0.03, 0.0)))
                    glBindVertexArray(self.line_vao)
                    glBindBuffer(GL_ARRAY_BUFFER, self.line_vbo)
                    pt_data = np.array([ent.last_center_3d.x, ent.last_center_3d.y, ent.last_center_3d.z], dtype=np.float32)
                    glBufferData(GL_ARRAY_BUFFER, pt_data.nbytes, pt_data, GL_DYNAMIC_DRAW)
                    
                    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
                    glEnableVertexAttribArray(0)
                    
                    glPointSize(15.0 if is_selected else 7.0)
                    shader.set_vec3("objectColor", ent.base_color)
                    glDrawArrays(GL_POINTS, 0, 1)
                    glPointSize(1.0)
                else:
                    visual_center = glm.vec3(ent.last_center_3d.x, ent.last_center_3d.y, ent.last_center_3d.z)
                    base_model = glm.translate(world_matrix, visual_center) * ent.rotation_matrix 
                    
                    if sphere_style == "Textured" and self.football:
                        shader.set_int("useTexture", 1)
                        shader.set_mat4("model", glm.scale(base_model, glm.vec3(ent.sphere_radius / self.football.original_radius)))
                        shader.set_vec3("objectColor", ent.base_color)
                        self.football.draw(shader)
                        shader.set_int("useTexture", 0)
                    else:
                        shader.set_mat4("model", glm.scale(base_model, glm.vec3(ent.sphere_radius / self.sphere.raw_radius)))
                        shader.set_vec3("objectColor", ent.base_color)
                        self.sphere.draw(shader)

    def draw_gradient_vector(self, shader: Any, entity: Any, surface: Any, world_matrix: glm.mat4, 
                             show_3d: bool, floor_y: float, show_arrow: bool, height_scale: float = 1.0) -> None:
        """Renders the focus laser beam and the directional gradient arrow for the active entity."""
        if not surface or not surface.loss_function: 
            return
            
        if np.isnan(entity.current_pos).any() or np.isinf(entity.current_pos).any(): 
            return
            
        # 1. Draw Laser Beam (Vertical line from the entity to the sky)
        scaled_world_matrix = glm.scale(world_matrix, glm.vec3(1.0, height_scale, 1.0))
        laser_top_y = surface.max_height + (5.0 / height_scale)
        data = np.array([
            entity.current_pos[0], floor_y, entity.current_pos[1], 
            entity.current_pos[0], laser_top_y, entity.current_pos[1]
        ], dtype=np.float32)
        
        glBindVertexArray(self.line_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.line_vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        shader.use()
        shader.set_int("useTexture", 0)
        shader.set_vec3("objectColor", glm.vec3(1.0, 0.0, 0.0)) 
        shader.set_float("alpha", 0.6) 
        shader.set_mat4("model", scaled_world_matrix)
        
        glDisable(GL_DEPTH_TEST) 
        glLineWidth(1.5)
        glDrawArrays(GL_LINES, 0, 2)
        glLineWidth(1.0)
        
        # 2. Draw Directional Arrow
        if not show_arrow: 
            glEnable(GL_DEPTH_TEST)
            return

        try: 
            grad = surface.loss_function.compute_gradient([entity.current_pos[0], entity.current_pos[1]])
        except Exception: 
            grad = surface.loss_function.compute_gradient((entity.current_pos[0], entity.current_pos[1]))
        
        if np.isnan(grad).any() or np.isinf(grad).any():
            glEnable(GL_DEPTH_TEST)
            return

        grad_norm = math.sqrt(grad[0]**2 + grad[1]**2)
        if grad_norm < 1e-5: 
            glEnable(GL_DEPTH_TEST) 
            return
        
        # Calculate rotation matrix for the arrow to point in the gradient direction
        direction = glm.normalize(glm.vec3(-grad[0] / grad_norm, 0.0, -grad[1] / grad_norm))
        z_axis = glm.vec3(0.0, 0.0, 1.0)
        axis = glm.cross(z_axis, direction)
        angle = math.acos(glm.clamp(glm.dot(z_axis, direction), -1.0, 1.0))
        axis = glm.vec3(0.0, 1.0, 0.0) if glm.length(axis) < 1e-5 else glm.normalize(axis)
            
        rot_mat = glm.rotate(glm.mat4(1.0), angle, axis)
        
        y_start = entity.last_center_3d.y if show_3d and entity.last_center_3d else (floor_y + 0.5) * height_scale
        base_model_mat = world_matrix * glm.translate(glm.mat4(1.0), glm.vec3(entity.current_pos[0], y_start, entity.current_pos[1])) * rot_mat
        
        shaft_len = min(max(grad_norm * 0.1, 0.05), 1.0) 
        shader.set_float("alpha", 0.9)
        
        # Enable depth testing and clear buffer to prevent 2D artifact rendering on top
        glEnable(GL_DEPTH_TEST)
        glClear(GL_DEPTH_BUFFER_BIT)
        
        # Draw Arrow Shaft (Cylinder)
        shader.set_mat4("model", base_model_mat * glm.scale(glm.mat4(1.0), glm.vec3(0.01, 0.01, shaft_len)))
        self.cylinder_mesh.draw(shader)
        
        # Draw Arrow Tip (Cone)
        shader.set_mat4("model", base_model_mat * glm.translate(glm.mat4(1.0), glm.vec3(0.0, 0.0, shaft_len)) * glm.scale(glm.mat4(1.0), glm.vec3(0.03, 0.03, 0.1)))
        self.cone_mesh.draw(shader)
        
        glEnable(GL_DEPTH_TEST)