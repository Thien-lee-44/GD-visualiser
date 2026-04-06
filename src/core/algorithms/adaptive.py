"""
Adaptive learning rate optimization algorithms.
"""
from typing import Tuple, List, Any
import glm

from src.core.algorithms.base import Optimizer
from src.core.algorithms.registry import register_algorithm

@register_algorithm("AdaGrad")
class AdaGrad(Optimizer):
    """Adapts the learning rate to the parameters, performing smaller updates for frequent features."""
    
    def __init__(self, learning_rate: float = 0.1, start_pos: List[float] = [0.0, 0.0], eps: float = 1e-8) -> None:
        super().__init__(learning_rate, start_pos)
        self.eps: float = float(eps)
        self.G: glm.vec2 = glm.vec2(0.0, 0.0)

    def step(self, loss_function: Any) -> Tuple[float, float]:
        raw_grad = loss_function.compute_gradient(self.current_pos)
        grad = glm.vec2(float(raw_grad[0]), float(raw_grad[1]))
        loss = float(loss_function.compute_value(self.current_pos))
        
        self.G = self.G + (grad * grad)
        adjusted_lr = self.lr / (glm.sqrt(self.G) + self.eps)
        self.current_pos = self.current_pos - (grad * adjusted_lr)
        
        self.trajectory.append(glm.vec2(self.current_pos))
        self.epochs += 1
        
        return loss, glm.length(grad)

    def reset(self, start_pos: List[float]) -> None:
        super().reset(start_pos)
        self.G = glm.vec2(0.0, 0.0)

@register_algorithm("RMSprop")
class RMSprop(Optimizer):
    """Maintains a moving average of squared gradients to resolve AdaGrad's diminishing learning rates."""
    
    def __init__(self, learning_rate: float = 0.01, start_pos: List[float] = [0.0, 0.0], decay_rate: float = 0.9, eps: float = 1e-8) -> None:
        super().__init__(learning_rate, start_pos)
        self.decay_rate: float = float(decay_rate)
        self.eps: float = float(eps)
        self.E_g2: glm.vec2 = glm.vec2(0.0, 0.0)

    def step(self, loss_function: Any) -> Tuple[float, float]:
        raw_grad = loss_function.compute_gradient(self.current_pos)
        grad = glm.vec2(float(raw_grad[0]), float(raw_grad[1]))
        loss = float(loss_function.compute_value(self.current_pos))
        
        self.E_g2 = (self.E_g2 * self.decay_rate) + ((grad * grad) * (1.0 - self.decay_rate))
        adjusted_lr = self.lr / (glm.sqrt(self.E_g2) + self.eps)
        self.current_pos = self.current_pos - (grad * adjusted_lr)
        
        self.trajectory.append(glm.vec2(self.current_pos))
        self.epochs += 1
        
        return loss, glm.length(grad)

    def reset(self, start_pos: List[float]) -> None:
        super().reset(start_pos)
        self.E_g2 = glm.vec2(0.0, 0.0)

@register_algorithm("Adam")
class Adam(Optimizer):
    """Adaptive Moment Estimation computes adaptive learning rates using first and second moments."""
    
    def __init__(self, learning_rate: float = 0.05, start_pos: List[float] = [0.0, 0.0], beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8) -> None:
        super().__init__(learning_rate, start_pos)
        self.beta1: float = float(beta1)
        self.beta2: float = float(beta2)
        self.eps: float = float(eps)
        self.m: glm.vec2 = glm.vec2(0.0, 0.0)
        self.v: glm.vec2 = glm.vec2(0.0, 0.0)

    def step(self, loss_function: Any) -> Tuple[float, float]:
        raw_grad = loss_function.compute_gradient(self.current_pos)
        grad = glm.vec2(float(raw_grad[0]), float(raw_grad[1]))
        loss = float(loss_function.compute_value(self.current_pos))
        
        self.epochs += 1
        
        self.m = (self.m * self.beta1) + (grad * (1.0 - self.beta1))
        self.v = (self.v * self.beta2) + ((grad * grad) * (1.0 - self.beta2))
        
        m_hat = self.m / (1.0 - (self.beta1 ** self.epochs))
        v_hat = self.v / (1.0 - (self.beta2 ** self.epochs))
        
        self.current_pos = self.current_pos - (m_hat * (self.lr / (glm.sqrt(v_hat) + self.eps)))
        self.trajectory.append(glm.vec2(self.current_pos))
        
        return loss, glm.length(grad)

    def reset(self, start_pos: List[float]) -> None:
        super().reset(start_pos)
        self.m = glm.vec2(0.0, 0.0)
        self.v = glm.vec2(0.0, 0.0)