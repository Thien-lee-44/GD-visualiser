"""
Represents a single optimizer agent in the 3D environment.
Handles interpolation logic, positional tracking, and visual states.
"""
import uuid
import numpy as np
import glm
from typing import Any, List, Optional

class OptimizerEntity:
    """An active agent navigating the mathematical surface using an optimization algorithm."""
    
    def __init__(self, name: str, optimizer_algo: Any, color: List[float], start_pos: List[float], sphere_radius: float) -> None:
        self.id = str(uuid.uuid4())
        self.name = name
        self.algo = optimizer_algo
        
        self.start_pos = list(start_pos) 
        self.current_pos = np.array(start_pos, dtype=np.float64)
        
        self.step_start_pos = self.current_pos.copy()
        self.target_pos = self.current_pos.copy()
        
        self.interpolation_t = 1.0 
        self.is_converged = False
        
        self.path_2d = [list(start_pos)]
        self.trail_3d: List[float] = [] 
        
        self.base_color = glm.vec3(*color)
        self.sphere_radius = sphere_radius
        self.show_trail = True
        self.transparency = 0.8 
        self.rotation_matrix = glm.mat4(1.0)
        self.last_center_3d: Optional[glm.vec3] = None

    def update_visual_height(self, surface: Any) -> None:
        """Updates the 3D elevation of the entity based on its 2D coordinates."""
        if surface is not None:
            _, safe_center, _ = surface.get_sphere_transform(self.current_pos, self.sphere_radius)
            self.last_center_3d = glm.vec3(*safe_center)

    def initialize_on_surface(self, loss_function: Any, surface: Any) -> None:
        """Resets the entity to its starting position and clears its memory."""
        self.algo.reset(self.start_pos)
        self.current_pos = np.array(self.start_pos, dtype=np.float64)
        self.step_start_pos = self.current_pos.copy()
        self.target_pos = self.current_pos.copy()
        
        self.interpolation_t = 1.0
        self.is_converged = False
        
        self.path_2d = [list(self.start_pos)]
        self.trail_3d = []
        self.rotation_matrix = glm.mat4(1.0)
        
        if loss_function and surface:
            self.update_visual_height(surface)
            surface_pt, _, _ = surface.get_sphere_transform(self.current_pos, self.sphere_radius)
            self.trail_3d.extend(surface_pt)

    def update_step(self, loss_function: Any, surface: Any, sim_speed: float = 1.0) -> None:
        """Advances the agent along its path, interpolating smoothly between optimization steps."""
        if self.is_converged: 
            return

        budget_t = sim_speed 
        while budget_t > 0:
            if self.interpolation_t >= 1.0:
                self.current_pos = self.target_pos.copy()
                self.step_start_pos = self.target_pos.copy()
                
                try:
                    self.algo.step(loss_function)
                    if hasattr(surface, 'x_bounds') and hasattr(surface, 'z_bounds'):
                        cx = np.clip(self.algo.current_pos[0], surface.x_bounds[0], surface.x_bounds[1])
                        cz = np.clip(self.algo.current_pos[1], surface.z_bounds[0], surface.z_bounds[1])
                        self.algo.current_pos = np.array([cx, cz], dtype=np.float64)
                        
                    next_target = self.algo.current_pos.copy()
                    if np.linalg.norm(next_target - self.target_pos) < 1e-7:
                        self.is_converged = True
                        break 
                        
                    self.target_pos = next_target
                    self.interpolation_t = 0.0 
                    
                    self.path_2d.append([float(self.target_pos[0]), float(self.target_pos[1])])
                    
                    surface_pt, _, _ = surface.get_sphere_transform(self.target_pos, self.sphere_radius)
                    self.trail_3d.extend(surface_pt)
                except OverflowError:
                    self.is_converged = True
                    break

            step_t = min(1.0 - self.interpolation_t, budget_t)
            self.interpolation_t += step_t
            budget_t -= step_t
            self.current_pos = self.step_start_pos + (self.target_pos - self.step_start_pos) * self.interpolation_t
            
        _, safe_center, normal_tuple = surface.get_sphere_transform(self.current_pos, self.sphere_radius)
        curr_center_3d = glm.vec3(*safe_center)
        surface_normal = glm.vec3(*normal_tuple)
        
        if self.last_center_3d is not None:
            move_vec = curr_center_3d - self.last_center_3d
            dist_3d = glm.length(move_vec)
            if dist_3d > 1e-4:
                move_dir = glm.normalize(move_vec)
                axis = glm.normalize(glm.cross(surface_normal, move_dir))
                angle = float(dist_3d / self.sphere_radius)
                self.rotation_matrix = glm.rotate(glm.mat4(1.0), angle, axis) * self.rotation_matrix
                
        self.last_center_3d = curr_center_3d