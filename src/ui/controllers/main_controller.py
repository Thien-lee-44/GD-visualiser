"""
Main application controller.
Initializes sub-controllers and manages the primary rendering loop.
"""
from typing import Any
from PySide6.QtCore import QObject, QTimer

from src.app import app_context, event_bus, AppEvent

from .env_controller import EnvironmentController
from .sim_controller import SimulationControllerUI
from .inspector_controller import InspectorController

class MainController(QObject):
    """The central brain orchestrating UI updates and simulation loops."""
    
    def __init__(self, main_window: Any) -> None:
        super().__init__()
        self.window = main_window
        self.ctx = app_context
        
        # Setup main render timer (runs continuously when simulation is playing)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._tick_simulation)
        self.render_timer.setInterval(0)  # 0 means "run as fast as the Qt event loop allows"
        
        # Initialize Sub-Controllers
        self.env_ctrl = EnvironmentController(self.force_redraw_viewports, self.window)
        self.sim_ctrl = SimulationControllerUI(self.window, self.render_timer, self.force_redraw_viewports)
        self.inspector_ctrl = InspectorController(self.window, self.force_redraw_viewports)

        # Handle globally reaching events
        event_bus.subscribe(AppEvent.METRICS_UPDATED, self.window.metrics.update_metrics)
        event_bus.subscribe(AppEvent.SIMULATION_FINISHED, self._on_simulation_finished)

        # Delay the first render until the window and OpenGL contexts are fully initialized by Qt
        QTimer.singleShot(100, self._initialize_first_map)

    def _initialize_first_map(self) -> None:
        """Forces the Environment Panel to apply default settings and generate the initial surface."""
        if hasattr(self.window, 'env_panel') and hasattr(self.window.env_panel, 'btn_apply'):
            self.window.env_panel.btn_apply.click()

    def _on_simulation_finished(self) -> None:
        """Callback triggered when all entities have converged or max epochs are reached."""
        self.window.sim_panel.set_status(running=False, finished=True)

    def _tick_simulation(self) -> None:
        """Advances simulation one tick and updates viewports if changes occurred."""
        renderer = self.ctx.engine.renderer_3d
        surface = getattr(renderer, 'surface', None) if renderer else None
        
        needs_redraw = self.ctx.simulation.tick(surface)
        if needs_redraw:
            self.force_redraw_viewports()

    def force_redraw_viewports(self) -> None:
        """Triggers a redraw for all registered viewports in the main window."""
        for vp in getattr(self.window, 'viewports', []):
            vp.update()