"""
Base definitions for optimization algorithms.
Ensures uniform structures for position tracking, learning rates, and update steps.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Any
import glm

class Optimizer(ABC):
    """Abstract base class for all optimization algorithms."""

    def __init__(self, learning_rate: float = 0.01, start_pos: List[float] = [0.0, 0.0]) -> None:
        self.lr: float = float(learning_rate)
        self.current_pos: glm.vec2 = glm.vec2(float(start_pos[0]), float(start_pos[1]))
        self.trajectory: List[glm.vec2] = [glm.vec2(self.current_pos)]
        self.epochs: int = 0

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
        self.current_pos = glm.vec2(float(start_pos[0]), float(start_pos[1]))
        self.trajectory = [glm.vec2(self.current_pos)]
        self.epochs = 0