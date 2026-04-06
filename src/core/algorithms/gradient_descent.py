"""
Standard Gradient Descent algorithms including Momentum and Nesterov variations.
"""
from typing import Tuple, List, Any
import glm

from src.core.algorithms.base import Optimizer
from src.core.algorithms.registry import register_algorithm

@register_algorithm("GradientDescent")
class GradientDescent(Optimizer):
    """Vanilla Gradient Descent algorithm."""
    
    def step(self, loss_function: Any) -> Tuple[float, float]:
        # Cast gradient to glm.vec2 for safe math operations
        raw_grad = loss_function.compute_gradient(self.current_pos)
        grad = glm.vec2(float(raw_grad[0]), float(raw_grad[1]))
        loss = float(loss_function.compute_value(self.current_pos))
        
        self.current_pos = self.current_pos - (grad * self.lr)
        self.trajectory.append(glm.vec2(self.current_pos))
        self.epochs += 1
        
        return loss, glm.length(grad)

@register_algorithm("MomentumGD")
class MomentumGD(Optimizer):
    """Gradient Descent with Momentum to accelerate gradients in the right directions."""
    
    def __init__(self, learning_rate: float = 0.01, start_pos: List[float] = [0.0, 0.0], momentum: float = 0.9) -> None:
        super().__init__(learning_rate, start_pos)
        self.momentum: float = float(momentum)
        self.velocity: glm.vec2 = glm.vec2(0.0, 0.0)

    def step(self, loss_function: Any) -> Tuple[float, float]:
        raw_grad = loss_function.compute_gradient(self.current_pos)
        grad = glm.vec2(float(raw_grad[0]), float(raw_grad[1]))
        loss = float(loss_function.compute_value(self.current_pos))
        
        self.velocity = (self.velocity * self.momentum) - (grad * self.lr)
        self.current_pos = self.current_pos + self.velocity
        
        self.trajectory.append(glm.vec2(self.current_pos))
        self.epochs += 1
        
        return loss, glm.length(grad)

    def reset(self, start_pos: List[float]) -> None:
        super().reset(start_pos)
        self.velocity = glm.vec2(0.0, 0.0)

@register_algorithm("Nesterov")
class Nesterov(Optimizer):
    """Nesterov Accelerated Gradient (NAG) calculates the gradient at the 'lookahead' position."""
    
    def __init__(self, learning_rate: float = 0.01, start_pos: List[float] = [0.0, 0.0], momentum: float = 0.9) -> None:
        super().__init__(learning_rate, start_pos)
        self.momentum: float = float(momentum)
        self.velocity: glm.vec2 = glm.vec2(0.0, 0.0)

    def step(self, loss_function: Any) -> Tuple[float, float]:
        # Compute gradient at the lookahead position
        lookahead_pos = self.current_pos + (self.velocity * self.momentum)
        raw_grad = loss_function.compute_gradient(lookahead_pos)
        grad = glm.vec2(float(raw_grad[0]), float(raw_grad[1]))
        loss = float(loss_function.compute_value(self.current_pos))
        
        self.velocity = (self.velocity * self.momentum) - (grad * self.lr)
        self.current_pos = self.current_pos + self.velocity
        
        self.trajectory.append(glm.vec2(self.current_pos))
        self.epochs += 1
        
        return loss, glm.length(grad)

    def reset(self, start_pos: List[float]) -> None:
        super().reset(start_pos)
        self.velocity = glm.vec2(0.0, 0.0)