"""
Controller for Environment-related logic.
Handles mathematical surface generation, mesh rebuilds, and view configuration.
"""
import glm
from typing import Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, QCoreApplication

from src.app import event_bus, AppEvent, app_context
from src.core import SimulationConfig

class EnvironmentController(QObject):
    """Controller for environment-related logic, handling mesh and visual updates."""
    
    def __init__(self, redraw_callback: Callable, main_window: Any) -> None:
        super().__init__()
        self.ctx = app_context
        self.window = main_window
        self.request_redraw = redraw_callback
        self.last_config: Optional[SimulationConfig] = None
        self._subscribe()

    def _subscribe(self) -> None:
        """Subscribes to environment-specific application events."""
        event_bus.subscribe(AppEvent.MESH_CONFIG_CHANGED, self._on_mesh_config_changed)
        event_bus.subscribe(AppEvent.VISUAL_TOGGLES_CHANGED, self._on_visual_toggles_changed)
        event_bus.subscribe(AppEvent.BOUNDARY_PREVIEW_CHANGED, self._on_boundary_preview_changed)

    def _get_surface(self, is_2d: bool = False) -> Any:
        """Helper to retrieve the active mathematical surface safely."""
        renderer = self.ctx.engine.renderer_2d if is_2d else self.ctx.engine.renderer_3d
        return getattr(renderer, 'surface', None) if renderer else None

    def _update_viewports(self, config: SimulationConfig) -> None:
        """Safely updates OpenGL viewports enforcing correct thread contexts."""
        vp_3d = getattr(self.window, 'gl_viewport_3d', None)
        vp_2d = getattr(self.window, 'gl_viewport_2d', None)

        if vp_3d:
            vp_3d.makeCurrent()
            try:
                self.ctx.engine.update_surface_mesh_3d(config)
            finally:
                vp_3d.doneCurrent()

        if vp_2d and vp_2d.isVisible():
            vp_2d.makeCurrent()
            try:
                self.ctx.engine.update_surface_mesh_2d(config)
            finally:
                vp_2d.doneCurrent()

    def _on_mesh_config_changed(self, config: SimulationConfig) -> None:
        """Handles mesh regeneration, scaling, and entity repositioning dynamically."""
        is_hard_reset = True
        is_mesh_rebuild = True

        if self.last_config:
            old = self.last_config
            if (old.func_name == config.func_name and
                old.func_params == config.func_params and
                old.x_range == config.x_range and
                old.y_range == config.y_range):
                is_hard_reset = False

            if (not is_hard_reset and
                old.steps == config.steps and
                old.contour_levels == config.contour_levels and
                old.use_log == config.use_log):
                is_mesh_rebuild = False

        self.last_config = config

        if is_hard_reset:
            new_loss_fn = self.ctx.simulation.setup_simulation(
                config, self.ctx.entity_manager.get_all(), self.ctx.simulation.max_epochs
            )
            self.ctx.engine.loss_function = new_loss_fn
            self._update_viewports(config)

            surface_3d = self._get_surface()
            if surface_3d:
                for ent in self.ctx.entity_manager.get_all():
                    ent.initialize_on_surface(new_loss_fn, surface_3d)
                self.ctx.simulation.reset_simulation(surface_3d)
        else:
            if is_mesh_rebuild:
                self._update_viewports(config)
                surface_3d = self._get_surface()
                if surface_3d:
                    for ent in self.ctx.entity_manager.get_all():
                        if hasattr(ent, 'current_pos') and ent.current_pos is not None:
                            _, new_center, _ = surface_3d.get_sphere_transform(ent.current_pos, ent.sphere_radius)
                            ent.last_center_3d = glm.vec3(*new_center)
                            if hasattr(ent, 'path_2d') and ent.path_2d:
                                ent.trail_3d = surface_3d.get_path_3d(ent.path_2d)
            else:
                surface_3d = self._get_surface()
                surface_2d = self._get_surface(is_2d=True)

                if surface_3d:
                    surface_3d.height_scale = config.height_scale
                    for ent in self.ctx.entity_manager.get_all():
                        if hasattr(ent, 'current_pos') and ent.current_pos is not None:
                            _, new_center, _ = surface_3d.get_sphere_transform(ent.current_pos, ent.sphere_radius)
                            ent.last_center_3d = glm.vec3(*new_center)
                if surface_2d:
                    surface_2d.height_scale = config.height_scale

        self.ctx.simulation.broadcast_metrics()
        self.request_redraw()
        QCoreApplication.processEvents()

    def _on_visual_toggles_changed(self, toggles: Dict[str, Any]) -> None:
        """Updates engine visualization states iteratively."""
        for key in ["surface_style", "sphere_style", "show_grid", "show_highlight", "show_arrow", "global_show_trail"]:
            if key in toggles:
                setattr(self.ctx.engine, key, toggles[key])
        self.request_redraw()

    def _on_boundary_preview_changed(self, bounds: Dict[str, Any]) -> None:
        """Updates boundary preview visualization logic."""
        self.ctx.engine.preview_boundary = bounds
        self.request_redraw()