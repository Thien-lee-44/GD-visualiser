"""
Stochastic algorithms that simulate noisy environment gradients and batching.
"""
import math
import random
from typing import Tuple, List, Any
import numpy as np

from src.core.algorithms.base import Optimizer
from src.core.algorithms.registry import register_algorithm

@register_algorithm("SimulatedSGD")
class SimulatedSGD(Optimizer):
    """Simulates Stochastic Gradient Descent by adding Gaussian noise to the true gradient."""
    
    def __init__(self, learning_rate: float = 0.01, start_pos: List[float] = [0.0, 0.0], noise_std: float = 0.5) -> None:
        super().__init__(learning_rate, start_pos)
        self.noise_std: float = float(noise_std)

    def step(self, loss_function: Any) -> Tuple[float, float]:
        exact_grad = self._vec2(loss_function.compute_gradient(self.current_pos))
        loss = float(loss_function.compute_value(self.current_pos))
        
        noise = np.array([random.gauss(0.0, self.noise_std), random.gauss(0.0, self.noise_std)], dtype=np.float64)
        noisy_grad = exact_grad + noise
        
        self.current_pos = self.current_pos - (noisy_grad * self.lr)
        self.trajectory.append(self.current_pos.copy())
        self.epochs += 1
        
        return loss, float(np.linalg.norm(exact_grad))

@register_algorithm("MiniBatchSGD")
class MiniBatchSGD(SimulatedSGD):
    """Simulates Mini-Batch SGD by scaling noise variance inversely with the square root of the batch size."""
    
    def __init__(self, learning_rate: float = 0.01, start_pos: List[float] = [0.0, 0.0], base_noise: float = 0.5, batch_size: int = 32) -> None:
        actual_noise = base_noise / math.sqrt(float(batch_size))
        super().__init__(learning_rate, start_pos, noise_std=actual_noise)
        self.batch_size: int = batch_size
