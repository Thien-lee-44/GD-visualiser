"""
Defines the virtual camera and its tracking logic for rendering 3D/2D views.
"""
import glm
from typing import Optional, List, Any, Tuple

class Camera:
    """Orbital camera for navigating the 3D viewport and 2D Top-down mapping."""

    def __init__(self, radius: float = 10.0, target: Optional[glm.vec3] = None) -> None:
        self.radius: float = radius
        self.target: glm.vec3 = target if target is not None else glm.vec3(0.0, 0.0, 0.0)
        
        init_pitch = glm.angleAxis(glm.radians(-30.0), glm.vec3(1.0, 0.0, 0.0))
        init_yaw = glm.angleAxis(glm.radians(45.0), glm.vec3(0.0, 1.0, 0.0))
        self.orientation: glm.quat = glm.normalize(init_yaw * init_pitch)
        
        self.fov: float = 45.0
        self.aspect_ratio: float = 16.0 / 9.0
        self.near: float = 0.1
        self.far: float = 1000.0
        
        # 2D Orthographic Configurations
        self.is_ortho: bool = False
        self.ortho_zoom: float = 10.0

    def get_position(self) -> glm.vec3:
        """Calculates the current world-space position of the camera."""
        offset = self.orientation * glm.vec3(0.0, 0.0, self.radius)
        return self.target + offset

    def get_view_matrix(self) -> glm.mat4:
        """Generates the view matrix for OpenGL rendering."""
        position = self.get_position()
        up = self.orientation * glm.vec3(0.0, 1.0, 0.0)
        return glm.lookAt(position, self.target, up)

    def get_projection_matrix(self) -> glm.mat4:
        """Generates the projection matrix based on current mode (3D Perspective / 2D Ortho)."""
        if self.is_ortho:
            half_w = (self.ortho_zoom * self.aspect_ratio) / 2.0
            half_h = self.ortho_zoom / 2.0
            return glm.ortho(-half_w, half_w, -half_h, half_h, -1000.0, 1000.0)
        return glm.perspective(glm.radians(self.fov), self.aspect_ratio, self.near, self.far)


class CameraController:
    """Manages mathematical constraints and entity tracking logic for the Camera."""
    
    def __init__(self, camera: Camera) -> None:
        self.camera = camera

    def get_map_ratio(self, surface: Any, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> float:
        """Calculates the Width/Height ratio of the mathematical surface boundary."""
        sx = getattr(surface, 'scale_x', 1.0)
        sz = getattr(surface, 'scale_z', 1.0)
        map_width = abs(x_range[1] - x_range[0]) * sx
        map_height = abs(y_range[1] - y_range[0]) * sz
        return map_width / max(1.0, map_height)

    def calculate_max_zoom(self, surface: Any, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> float:
        """Determines the maximum allowable orthographic zoom to fit map bounds."""
        aspect = self.camera.aspect_ratio if self.camera.aspect_ratio > 0 else 1.0
        sz = getattr(surface, 'scale_z', 1.0)
        map_height = abs(y_range[1] - y_range[0]) * sz
        map_width = map_height * self.get_map_ratio(surface, x_range, y_range)
        return float(min(map_height, map_width / aspect))

    def clamp_target_2d(self, surface: Any, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> None:
        """Keeps the 2D orthographic camera strictly within the map boundaries."""
        zoom = self.camera.ortho_zoom
        aspect = self.camera.aspect_ratio
        
        sx = getattr(surface, 'scale_x', 1.0)
        sz = getattr(surface, 'scale_z', 1.0)
        
        cx = ((x_range[0] + x_range[1]) / 2.0) * sx
        cz = ((y_range[0] + y_range[1]) / 2.0) * sz
        
        map_half_w = (abs(x_range[1] - x_range[0]) * sx) / 2.0
        map_half_h = (abs(y_range[1] - y_range[0]) * sz) / 2.0
        
        move_w = max(0.0, map_half_w - (zoom * aspect) / 2.0)
        move_h = max(0.0, map_half_h - zoom / 2.0)
        
        self.camera.target.x = max(cx - move_w, min(cx + move_w, self.camera.target.x))
        self.camera.target.z = max(cz - move_h, min(cz + move_h, self.camera.target.z))

    def update_tracking(self, entities: List[Any], tracked_id: Optional[str], is_tracking: bool, 
                        is_dragging_map: bool, is_3d: bool, sphere_radius: float, 
                        surface: Any, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> None:
        """Smoothly updates camera target to follow the selected entity."""
        if not is_tracking or not tracked_id or is_dragging_map: 
            return
            
        for ent in entities:
            if ent.id == tracked_id and getattr(ent, 'last_center_3d', None) is not None:
                self.camera.target.x = ent.last_center_3d.x
                if is_3d: 
                    self.camera.target.y = ent.last_center_3d.y + sphere_radius
                self.camera.target.z = ent.last_center_3d.z
                
                if not is_3d: 
                    self.clamp_target_2d(surface, x_range, y_range)
                break