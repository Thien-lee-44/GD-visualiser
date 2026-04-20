"""
Base definitions for optimization algorithms.
Ensures uniform structures for position tracking, learning rates, and update steps.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Any
import numpy as np

class Optimizer(ABC):
    """Abstract base class for all optimization algorithms."""

    def __init__(self, learning_rate: float = 0.01, start_pos: List[float] = [0.0, 0.0]) -> None:
        self.lr: float = float(learning_rate)
        self.current_pos: np.ndarray = self._vec2(start_pos)
        self.trajectory: List[np.ndarray] = [self.current_pos.copy()]
        self.epochs: int = 0

    @staticmethod
    def _vec2(values: Any) -> np.ndarray:
        return np.array([float(values[0]), float(values[1])], dtype=np.float64)

    @abstractmethod
    def step(self, loss_function: Any) -> Tuple[float, float]:
        """
        Executes a single optimization step.
        Returns:
            Tuple[float, float]: The current loss value and the gradient norm.
        """
        pass

    def reset(self, start_pos: List[float]) -> None:
        """Resets the optimizer's state and trajectory back to the starting position."""
        self.current_pos = self._vec2(start_pos)
        self.trajectory = [self.current_pos.copy()]
        self.epochs = 0
