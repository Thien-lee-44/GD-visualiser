"""
Data Transfer Objects (DTOs) representing the core domain entities.
These structures enforce type safety and replace loose dictionaries across the application.
"""
from dataclasses import dataclass, field
from typing import Dict, Tuple

@dataclass
class MetricData:
    """Represents a single snapshot of an optimizer's performance metric."""
    entity_id: str
    name: str
    epoch: int
    loss: float
    grad_norm: float
    pos_x: float
    pos_y: float
    learning_rate: float

@dataclass
class SimulationConfig:
    """Encapsulates all parameters required to generate a mathematical environment."""
    func_name: str
    func_params: Dict[str, float] = field(default_factory=dict)
    x_range: Tuple[float, float] = (-5.0, 5.0)
    y_range: Tuple[float, float] = (-5.0, 5.0)
    steps: int = 300
    contour_levels: int = 20
    height_scale: float = 1.0
    use_log: bool = False

@dataclass
class VisualParams:
    """Visual properties of an optimizer entity."""
    color: Tuple[float, float, float]
    show_trail: bool = True
    sphere_radius: float = 0.15
    start_pos: Tuple[float, float] = (0.0, 0.0)