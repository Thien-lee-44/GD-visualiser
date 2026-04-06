"""
Core simulation engine responsible for advancing optimizers across mathematical surfaces.
Completely decoupled from the UI layer; broadcasts state changes via EventBus.
"""
import numpy as np
from typing import List, Any, Optional

from src.core.functions.registry import FUNCTION_REGISTRY
from src.core.models import SimulationConfig, MetricData
from src.app.events import event_bus, AppEvent

class SimulationController:
    """Manages the execution loop and state of all optimizer entities."""
    
    def __init__(self) -> None:
        self.sim_speed: float = 1.0
        self.loss_function: Optional[Any] = None
        self.entities: List[Any] = []
        self.is_running: bool = False
        self.max_epochs: int = 1000

    def setup_simulation(self, config: SimulationConfig, entities: List[Any], max_epochs: int = 1000) -> Any:
        """Initializes the objective function and binds entities to the simulation context."""
        func_class = FUNCTION_REGISTRY.get(config.func_name)
        
        if not func_class:
            raise ValueError(f"Function '{config.func_name}' is not registered in FUNCTION_REGISTRY.")

        # Dynamically unpack function parameters (e.g., Rosenbrock's 'a' and 'b')
        new_loss_fn = func_class(**config.func_params)
        
        self.loss_function = new_loss_fn
        self.entities = entities
        self.max_epochs = max_epochs 
        self.broadcast_metrics()
        
        return new_loss_fn

    def update_entities_list(self, new_entities: List[Any]) -> None:
        """Refreshes the active entities pool."""
        self.entities = new_entities
        self.broadcast_metrics()

    def toggle_play_pause(self) -> bool:
        """Toggles the running state and broadcasts the change."""
        if not self.entities or not self.loss_function: 
            return False
            
        self.is_running = not self.is_running
        
        if self.is_running:
            event_bus.emit(AppEvent.SIMULATION_STARTED)
        else:
            event_bus.emit(AppEvent.SIMULATION_PAUSED)
            
        return self.is_running

    def reset_simulation(self, surface: Any) -> None:
        """Resets all entities to their starting positions."""
        self.is_running = False
        
        if surface and self.loss_function:
            for ent in self.entities:
                ent.initialize_on_surface(self.loss_function, surface)
                
        event_bus.emit(AppEvent.SIMULATION_PAUSED)
        self.broadcast_metrics()

    def set_speed(self, slider_value: int) -> None:
        """Scales UI slider value (1-100) to the actual simulation step budget."""
        if slider_value <= 50:
            self.sim_speed = max(0.01, (slider_value / 50.0) ** 2)
        else:
            self.sim_speed = 1.0 + ((slider_value - 50) / 50.0) * 19.0

    def tick(self, surface: Any) -> bool:
        """Advances the simulation by one frame budget. Returns True if a redraw is needed."""
        if not self.is_running or not self.entities: 
            return False
            
        all_finished = True
        
        for ent in self.entities:
            if self.max_epochs > 0 and ent.algo.epochs >= self.max_epochs:
                continue
                
            ent.update_step(self.loss_function, surface, sim_speed=self.sim_speed)
            all_finished = False
        
        if all_finished and self.max_epochs > 0 and self.is_running:
            self.is_running = False
            event_bus.emit(AppEvent.SIMULATION_FINISHED)
                
        self.broadcast_metrics()
        return True 

    def broadcast_metrics(self) -> None:
        """Calculates current metrics and broadcasts them as strongly-typed MetricData objects."""
        if not self.loss_function: 
            return 
            
        metrics_data: List[MetricData] = []
        for ent in self.entities:
            loss = float(self.loss_function.compute_value(ent.current_pos))
            grad_norm = float(np.linalg.norm(self.loss_function.compute_gradient(ent.current_pos)))
            
            metrics_data.append(MetricData(
                entity_id=ent.id,
                name=ent.name,
                epoch=ent.algo.epochs,
                loss=loss,
                grad_norm=grad_norm,
                pos_x=float(ent.current_pos[0]),
                pos_y=float(ent.current_pos[1]),
                learning_rate=float(getattr(ent.algo, 'lr', 0.0))
            ))
            
        event_bus.emit(AppEvent.METRICS_UPDATED, metrics_data)