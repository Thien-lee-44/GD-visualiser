"""
Main Graphics Engine.
Orchestrates OpenGL renderers, cameras, and global scene state.
"""
from typing import Optional, List, Dict, Any
import glm

from src.engine.core.camera import Camera, CameraController
from src.engine.core.input import InputHandler
from src.engine.renderers.main_renderer import MainRenderer
from src.core.models import SimulationConfig
from src.utils.constants import SurfaceStyle, SphereStyle

class GraphicsEngine:
    """Manages the lifecycle and state of OpenGL renderers and scene cameras."""
    
    def __init__(self) -> None:
        self.current_is_2d: bool = False
        
        # Initialize Cameras
        self.camera_3d = Camera()
        self.camera_2d = Camera(radius=10.0)
        self.camera_2d.is_ortho = True
        
        # Setup Top-Down orientation for 2D mode
        pitch = glm.angleAxis(glm.radians(-90.0), glm.vec3(1.0, 0.0, 0.0))
        yaw = glm.angleAxis(glm.radians(0.0), glm.vec3(0.0, 1.0, 0.0))
        self.camera_2d.orientation = glm.normalize(yaw * pitch)
        self.camera_2d.target = glm.vec3(0.0, 0.0, 0.0)
        
        self.cam_ctrl_3d = CameraController(self.camera_3d)
        self.cam_ctrl_2d = CameraController(self.camera_2d)
        
        self.renderer_3d: Optional[MainRenderer] = None
        self.renderer_2d: Optional[MainRenderer] = None
        
        self.loss_function: Optional[Any] = None
        self.entities: List[Any] = []
        self.config: Optional[SimulationConfig] = None
        
        # Default Visual States
        self.surface_style: str = SurfaceStyle.COLORMAP_CONTOUR.value
        self.sphere_style: str = SphereStyle.TEXTURED.value
        self.show_grid: bool = True
        self.sphere_radius: float = 0.15
        self.show_highlight: bool = True
        self.show_arrow: bool = True
        self.global_show_trail: int = 0
        
        self.tracked_entity_id: Optional[str] = None
        self.is_tracking: bool = False
        self.preview_boundary: Optional[Dict[str, Any]] = None

    def get_camera(self, is_2d: bool) -> Camera:
        """Retrieves the active camera for the specified mode."""
        return self.camera_2d if is_2d else self.camera_3d

    def get_controller(self, is_2d: bool) -> CameraController:
        """Retrieves the active camera controller for the specified mode."""
        return self.cam_ctrl_2d if is_2d else self.cam_ctrl_3d

    def init_renderer_3d(self) -> None:
        """Lazy initialization of the 3D renderer context."""
        if self.renderer_3d is None:
            self.renderer_3d = MainRenderer()

    def init_renderer_2d(self) -> None:
        """Lazy initialization of the 2D renderer context."""
        if self.renderer_2d is None:
            self.renderer_2d = MainRenderer()

    def update_surface_mesh_3d(self, config: SimulationConfig) -> None:
        """Updates the internal 3D surface geometry."""
        self.config = config
        if self.renderer_3d and self.loss_function:
            self.renderer_3d.set_new_surface(
                self.loss_function, config.x_range, config.y_range, 
                config.steps, config.height_scale, config.use_log, config.contour_levels
            )

    def update_surface_mesh_2d(self, config: SimulationConfig) -> None:
        """Updates the internal 2D orthographic surface geometry."""
        self.config = config
        if self.renderer_2d and self.loss_function:
            self.renderer_2d.set_new_surface(
                self.loss_function, config.x_range, config.y_range, 
                config.steps, config.height_scale, config.use_log, config.contour_levels
            )

    def process_mouse_movement(self, dx: float, dy: float, is_2d: bool) -> None:
        """Delegates orbit/rotation logic to the input handler."""
        InputHandler.process_mouse_orbit(self.get_camera(is_2d), dx, dy)

    def process_mouse_pan(self, dx: float, dy: float, is_2d: bool) -> None:
        """Delegates panning logic to the input handler."""
        InputHandler.process_mouse_pan(self.get_camera(is_2d), dx, dy)

    def process_mouse_scroll(self, dy: float, max_zoom: Optional[float] = None, is_2d: bool = False) -> None:
        """Calculates dynamic zoom constraints and processes camera scaling."""
        surface = self.renderer_2d.surface if is_2d and self.renderer_2d else (self.renderer_3d.surface if self.renderer_3d else None)
        ctrl = self.get_controller(is_2d)
        cam = self.get_camera(is_2d)
        
        final_max_zoom = max_zoom
        if is_2d and max_zoom is None and self.config:
            final_max_zoom = ctrl.calculate_max_zoom(surface, self.config.x_range, self.config.y_range)
            
        InputHandler.process_mouse_scroll(cam, dy, max_zoom=final_max_zoom)
            
        if is_2d and self.config:
            ctrl.clamp_target_2d(surface, self.config.x_range, self.config.y_range)

    def clamp_camera_target(self, is_2d: bool) -> None:
        """Manually triggers boundary clamping for the 2D view."""
        if is_2d and self.config:
            surface = self.renderer_2d.surface if self.renderer_2d else None
            self.get_controller(is_2d).clamp_target_2d(surface, self.config.x_range, self.config.y_range)

    def update_camera_tracking(self, is_dragging_map: bool, is_2d: bool) -> None:
        """Executes smooth camera tracking updates if enabled."""
        if not self.config: 
            return
        surface = self.renderer_2d.surface if is_2d and self.renderer_2d else (self.renderer_3d.surface if self.renderer_3d else None)
        self.get_controller(is_2d).update_tracking(
            self.entities, self.tracked_entity_id, self.is_tracking, 
            is_dragging_map, not is_2d, self.sphere_radius, 
            surface, self.config.x_range, self.config.y_range
        )

    def render_frame(self, width: int, height: int, is_2d: bool) -> Optional[Dict[str, Any]]:
        """Main entry point for a single frame render pass."""
        self.current_is_2d = is_2d
        renderer = self.renderer_2d if is_2d else self.renderer_3d
        camera = self.get_camera(is_2d)
        
        if not renderer or not self.loss_function: 
            return None
            
        return renderer.render_frame(
            camera, self.entities, width, height, 
            self.surface_style, self.sphere_style, self.sphere_radius, 
            self.show_grid, self.show_highlight, self.show_arrow, 
            self.global_show_trail, self.tracked_entity_id, 
            self.preview_boundary, is_2d
        )