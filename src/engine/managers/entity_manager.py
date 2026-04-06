"""
Manager class for handling the lifecycle of optimizer entities.
Handles creation, updating, and removal of agents in the 3D scene.
"""
import glm
from typing import List, Dict, Any, Optional

from src.core.algorithms.registry import ALGORITHM_REGISTRY
from src.engine.scene.optimizer_entity import OptimizerEntity

class EntityManager:
    """Handles the lifecycle, instantiation, and storage of optimizer entities."""
    
    def __init__(self) -> None:
        self._entities: Dict[str, OptimizerEntity] = {}

    def get_all(self) -> List[OptimizerEntity]:
        """Returns a list of all active entities."""
        return list(self._entities.values())

    def get_entity(self, entity_id: str) -> Optional[OptimizerEntity]:
        """Fetches a specific entity by its unique UUID."""
        return self._entities.get(entity_id)

    def _generate_unique_name(self, base_name: str) -> str:
        """Appends an incremental suffix to ensure unique entity names."""
        existing_names = [e.name for e in self._entities.values()]
        unique_name = base_name
        count = 1
        while unique_name in existing_names:
            unique_name = f"{base_name} ({count})"
            count += 1
        return unique_name

    def create_entity(self, algo_name: str, color_vec: List[float], schema: Dict[str, Any], loss_function: Any, surface: Any) -> OptimizerEntity:
        """Instantiates an optimizer, sets default hyperparameters based on schema, and places it on the map."""
        algo_class = ALGORITHM_REGISTRY[algo_name]
        init_lr = schema.get('lr', {}).get('val', 0.01)
        algo_inst = algo_class(learning_rate=init_lr) 
        
        for k, conf in schema.items():
            if k != 'lr' and hasattr(algo_inst, k): 
                setattr(algo_inst, k, conf['val'])

        unique_name = self._generate_unique_name(algo_name)
        ent = OptimizerEntity(unique_name, algo_inst, color_vec, [0.0, 0.0], sphere_radius=0.15)
        
        if loss_function and surface:
            ent.initialize_on_surface(loss_function, surface)

        self._entities[ent.id] = ent
        return ent

    def remove_entity(self, entity_id: str) -> None:
        """Deletes an entity from the active pool."""
        if entity_id in self._entities:
            del self._entities[entity_id]

    def update_entity_params(self, entity_id: str, params: Dict[str, Any], loss_function: Any, surface: Any) -> Optional[OptimizerEntity]:
        """Dynamically updates an entity's hyperparameters or visual configuration."""
        ent = self.get_entity(entity_id)
        if not ent: 
            return None

        # Update visual color
        ent.base_color = glm.vec3(*params['visuals']['color']) 
        
        if 'show_trail' in params['visuals']:
            ent.show_trail = params['visuals']['show_trail']
            
        # Recalculate safe height if radius changes
        if 'sphere_radius' in params['visuals']:
            ent.sphere_radius = params['visuals']['sphere_radius']
            if loss_function and surface:
                _, safe_center, _ = surface.get_sphere_transform(ent.current_pos, ent.sphere_radius)
                ent.last_center_3d = glm.vec3(*safe_center)

        # Handle start position updates
        new_start = params['visuals']['start_pos']
        if abs(ent.start_pos[0] - new_start[0]) > 1e-4 or abs(ent.start_pos[1] - new_start[1]) > 1e-4:
            ent.start_pos = new_start
            if loss_function and surface:
                ent.initialize_on_surface(loss_function, surface)

        # Update algorithm specific variables
        for k, v in params['algo_params'].items(): 
            if hasattr(ent.algo, k): 
                setattr(ent.algo, k, v)
            elif k == 'lr': 
                ent.algo.lr = v
            
        return ent