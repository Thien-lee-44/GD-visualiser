"""
Implementations of classical optimization test functions.
These functions evaluate the performance and behavior of optimization algorithms.
"""
import numpy as np
from typing import Any, Union, Dict

from src.core.functions.base import LossFunction
from src.core.functions.registry import register_function

@register_function("Quadratic")
class Quadratic(LossFunction):
    """A simple convex bowl-shaped function."""
    
    def compute_value(self, position: Any) -> Union[float, np.ndarray]:
        x, y = self._get_coords(position)
        return x**2 + y**2

    def compute_gradient(self, position: Any) -> np.ndarray:
        x, y = self._get_coords(position)
        return np.array([2 * x, 2 * y], dtype=np.float64)

@register_function("Himmelblau")
class Himmelblau(LossFunction):
    """A multi-modal function with four identical local minima."""
    
    def compute_value(self, position: Any) -> Union[float, np.ndarray]:
        x, y = self._get_coords(position)
        return (x**2 + y - 11)**2 + (x + y**2 - 7)**2

    def compute_gradient(self, position: Any) -> np.ndarray:
        x, y = self._get_coords(position)
        df_dx = 4 * x * (x**2 + y - 11) + 2 * (x + y**2 - 7)
        df_dy = 2 * (x**2 + y - 11) + 4 * y * (x + y**2 - 7)
        return np.array([df_dx, df_dy], dtype=np.float64)

@register_function("Rosenbrock")
class Rosenbrock(LossFunction):
    """A non-convex function with a narrow, curved valley (the 'banana' function)."""
    
    # UI Schema for dynamically rendering parameter sliders
    params_schema: Dict[str, Dict[str, Any]] = {
        'a': {'min': -10.0, 'max': 10.0, 'default': 1.0, 'label': 'Rosen a:', 'step': 0.1},
        'b': {'min': 1.0, 'max': 1000.0, 'default': 100.0, 'label': 'Rosen b:', 'step': 1.0}
    }
    
    def __init__(self, a: float = 1.0, b: float = 100.0) -> None:
        self.a = float(a)
        self.b = float(b)

    def compute_value(self, position: Any) -> Union[float, np.ndarray]:
        x, y = self._get_coords(position)
        return (self.a - x)**2 + self.b * (y - x**2)**2

    def compute_gradient(self, position: Any) -> np.ndarray:
        x, y = self._get_coords(position)
        df_dx = -2 * (self.a - x) - 4 * self.b * x * (y - x**2)
        df_dy = 2 * self.b * (y - x**2)
        return np.array([df_dx, df_dy], dtype=np.float64)

@register_function("Booth")
class Booth(LossFunction):
    """A plate-shaped function with a long, narrow valley."""
    
    def compute_value(self, position: Any) -> Union[float, np.ndarray]:
        x, y = self._get_coords(position)
        return (x + 2 * y - 7)**2 + (2 * x + y - 5)**2

    def compute_gradient(self, position: Any) -> np.ndarray:
        x, y = self._get_coords(position)
        return np.array([10 * x + 8 * y - 34, 8 * x + 10 * y - 38], dtype=np.float64)