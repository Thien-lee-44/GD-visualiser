"""
Controller for Simulation execution logic.
Handles play/pause states, simulation resets, and speed adjustments.
"""
from typing import Any, Callable
from PySide6.QtCore import QObject

from src.app import event_bus, AppEvent, app_context

class SimulationControllerUI(QObject):
    """Manages the lifecycle and execution speed of the mathematical simulation loop."""
    
    def __init__(self, main_window: Any, render_timer: Any, redraw_callback: Callable) -> None:
        super().__init__()
        self.ctx = app_context
        self.window = main_window
        self.render_timer = render_timer
        self.request_redraw = redraw_callback
        self._subscribe()

    def _subscribe(self) -> None:
        """Subscribes to simulation playback events."""
        event_bus.subscribe(AppEvent.SIMULATION_STARTED, self._on_sim_started)
        event_bus.subscribe(AppEvent.SIMULATION_PAUSED, self._on_sim_paused)
        event_bus.subscribe(AppEvent.SIMULATION_RESET, self._on_sim_reset)
        event_bus.subscribe(AppEvent.SIMULATION_SPEED_CHANGED, self._on_speed_changed)

    def _on_sim_started(self) -> None:
        """Starts the simulation loop and updates UI state."""
        self.ctx.simulation.is_running = True
        self.window.sim_panel.set_status(running=True, finished=False)
        self.render_timer.start()

    def _on_sim_paused(self) -> None:
        """Pauses the simulation loop and updates UI state."""
        self.ctx.simulation.is_running = False
        self.window.sim_panel.set_status(running=False, finished=False)
        self.render_timer.stop()

    def _on_sim_reset(self) -> None:
        """Resets all entities to their starting states and pauses the simulation."""
        renderer = self.ctx.engine.renderer_3d
        surface = getattr(renderer, 'surface', None) if renderer else None
        
        self.ctx.simulation.reset_simulation(surface)
        self._on_sim_paused()
        self.request_redraw()

    def _on_speed_changed(self, speed: float) -> None:
        """Updates the multi-step execution budget per tick."""
        self.ctx.simulation.set_speed(speed)