"""
Input handler utility for the graphics engine.
Separates raw input calculation from the main state management.
"""
import glm
from typing import Optional
from src.engine.core.camera import Camera

class InputHandler:
    """Static utility for processing user interactions and mapping them to camera state."""
    
    @staticmethod
    def process_mouse_orbit(camera: Camera, x_offset: float, y_offset: float, sensitivity: float = 0.005) -> None:
        """Calculates and applies camera orientation rotation around its target."""
        q_yaw = glm.angleAxis(-x_offset * sensitivity, glm.vec3(0.0, 1.0, 0.0))
        q_pitch = glm.angleAxis(-y_offset * sensitivity, glm.vec3(1.0, 0.0, 0.0))
        camera.orientation = glm.normalize(q_yaw * camera.orientation * q_pitch)

    @staticmethod
    def process_mouse_pan(camera: Camera, x_offset: float, y_offset: float, sensitivity: float = 0.05) -> None:
        """Calculates and applies camera target translation based on view-plane axes."""
        right = camera.orientation * glm.vec3(1.0, 0.0, 0.0)
        up = camera.orientation * glm.vec3(0.0, 1.0, 0.0)
        camera.target -= right * x_offset * sensitivity
        camera.target += up * y_offset * sensitivity

    @staticmethod
    def process_mouse_scroll(camera: Camera, y_offset: float, sensitivity: float = 1.5, max_zoom: Optional[float] = None) -> None:
        """Calculates and applies zooming based on the camera's projection mode."""
        if camera.is_ortho:
            camera.ortho_zoom -= y_offset * sensitivity
            camera.ortho_zoom = max(0.5, camera.ortho_zoom)
            if max_zoom is not None:
                camera.ortho_zoom = min(camera.ortho_zoom, max_zoom)
        else:
            camera.radius -= y_offset * sensitivity
            camera.radius = max(1.0, camera.radius)