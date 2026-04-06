"""
Controller for Optimizer Entities.
Manages adding, removing, selecting, and updating hyperparameters of optimizers.
"""
from typing import Dict, Any, Optional, Callable
from PySide6.QtCore import QObject

from src.app import event_bus, AppEvent, app_context, settings

class InspectorController(QObject):
    """Bridges the gap between the UI Inspector Panel and the EntityManager."""
    
    def __init__(self, main_window: Any, redraw_callback: Callable) -> None:
        super().__init__()
        self.ctx = app_context
        self.window = main_window
        self.request_redraw = redraw_callback
        self._subscribe()

    def _subscribe(self) -> None:
        """Subscribes to entity-specific application events."""
        event_bus.subscribe(AppEvent.ENTITY_ADDED, self._on_entity_added)
        event_bus.subscribe(AppEvent.ENTITY_REMOVED, self._on_entity_removed)
        event_bus.subscribe(AppEvent.ENTITY_SELECTED, self._on_entity_selected)
        event_bus.subscribe(AppEvent.ENTITY_PARAMS_UPDATED, self._on_entity_params_updated)

    def _get_current_surface(self) -> Optional[Any]:
        """Safely retrieves the 3D mathematical surface if it exists."""
        renderer = self.ctx.engine.renderer_3d
        return getattr(renderer, 'surface', None) if renderer else None

    def _on_entity_added(self, data: Dict[str, Any]) -> None:
        """Handles the instantiation and registration of a new optimizer entity."""
        algo_name = data.get("algo_name")
        color_vec = data.get("color")
        schema = settings.schema.get(algo_name, {})
        
        surface = self._get_current_surface()
        ent = self.ctx.entity_manager.create_entity(
            algo_name, color_vec, schema, self.ctx.simulation.loss_function, surface
        )

        self.window.active_optimizers_panel.add_item_to_ui(ent.id, ent.name, color_vec)
        self._sync_entities()

    def _on_entity_removed(self, entity_id: str) -> None:
        """Handles the removal of an optimizer entity."""
        self.ctx.entity_manager.remove_entity(entity_id)
        
        if getattr(self.window.inspector, 'current_entity_id', None) == entity_id:
            self.window.active_optimizers_panel.list_widget.clearSelection()
            self.window.inspector.clear_ui()
            self.ctx.engine.tracked_entity_id = None
            
        self._sync_entities()

    def _on_entity_selected(self, entity_id: str) -> None:
        """Handles entity selection in the UI to update the inspector properties panel."""
        if not entity_id:
            self.window.active_optimizers_panel.list_widget.clearSelection()
            self.window.inspector.clear_ui()
            self.ctx.engine.tracked_entity_id = None
        else:
            ent = self.ctx.entity_manager.get_entity(entity_id)
            if ent:
                self.window.inspector.load_entity(ent)
                self.ctx.engine.tracked_entity_id = entity_id
        self.request_redraw()

    def _on_entity_params_updated(self, payload: Dict[str, Any]) -> None:
        """Updates hyperparameters or visual settings for an entity based on user input."""
        entity_id = payload.get("entity_id")
        params = payload.get("params")
        
        surface = self._get_current_surface()
        ent = self.ctx.entity_manager.update_entity_params(
            entity_id, params, self.ctx.simulation.loss_function, surface
        )
        
        if ent:
            self.window.active_optimizers_panel.update_item_color(entity_id, params['visuals']['color'])
            self.ctx.simulation.broadcast_metrics() 
            self.request_redraw()

    def _sync_entities(self) -> None:
        """Synchronizes the engine and UI state globally with the current entity list."""
        entities = self.ctx.entity_manager.get_all()
        self.ctx.simulation.update_entities_list(entities)
        self.ctx.engine.entities = entities
        self.window.metrics.rebuild_table(entities)
        self.request_redraw()