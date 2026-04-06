"""
Event Bus for decoupled communication between application layers.
Implements the Publish-Subscribe pattern to eliminate tight GUI coupling.
"""
from typing import Callable, Dict, List, Any

class AppEvent:
    """Standardized event string constants to prevent typo-related bugs."""
    SIMULATION_STARTED = "SIMULATION_STARTED"
    SIMULATION_PAUSED = "SIMULATION_PAUSED"
    SIMULATION_RESET = "SIMULATION_RESET"
    SIMULATION_SPEED_CHANGED = "SIMULATION_SPEED_CHANGED"
    SIMULATION_FINISHED = "SIMULATION_FINISHED"
    
    MESH_CONFIG_CHANGED = "MESH_CONFIG_CHANGED"
    VISUAL_TOGGLES_CHANGED = "VISUAL_TOGGLES_CHANGED"
    BOUNDARY_PREVIEW_CHANGED = "BOUNDARY_PREVIEW_CHANGED"
    
    ENTITY_ADDED = "ENTITY_ADDED"
    ENTITY_REMOVED = "ENTITY_REMOVED"
    ENTITY_SELECTED = "ENTITY_SELECTED"
    ENTITY_PARAMS_UPDATED = "ENTITY_PARAMS_UPDATED"
    
    METRICS_UPDATED = "METRICS_UPDATED"

class EventBus:
    """Event dispatcher for global application messaging."""
    
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Registers a callback function to a specific event."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """Removes a callback function from a specific event."""
        if event_name in self._subscribers and callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def emit(self, event_name: str, data: Any = None) -> None:
        """Dispatches an event with an optional payload to all registered callbacks."""
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                if data is not None:
                    callback(data)
                else:
                    callback()

# Global Pythonic Singleton instance
event_bus = EventBus()