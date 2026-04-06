"""
Base definitions for mathematical objective functions.
Ensures uniform structures for scalar evaluation and vectorization.
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import Any, Tuple, Union

class LossFunction(ABC):
    """Abstract base class for all mathematical objective functions."""

    def _get_coords(self, position: Any) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Safely extracts (x, y) coordinates from various data structures (scalar or meshgrid)."""
        # Handle tuple/list of 2D numpy meshgrids (used during surface generation)
        if isinstance(position, (list, tuple)) and len(position) >= 2 and isinstance(position[0], np.ndarray):
            return position[0], position[1]
            
        # Handle objects with strict x, y attributes (e.g., glm.vec2)
        if hasattr(position, 'x') and hasattr(position, 'y'):
            return float(position.x), float(position.y)
            
        # Handle standard arrays or lists
        x, y = position[0], position[1]
        
        # Return dynamically based on scalar or array type
        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
            return x, y
            
        return float(x), float(y)

    @abstractmethod
    def compute_value(self, position: Any) -> Union[float, np.ndarray]:
        """Computes the scalar loss value or a meshgrid of values."""
        pass

    @abstractmethod
    def compute_gradient(self, position: Any) -> np.ndarray:
        """Computes the [dx, dy] gradient vector or a meshgrid of gradients."""
        pass