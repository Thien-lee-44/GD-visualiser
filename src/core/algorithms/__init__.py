"""
Optimization algorithms module.
Exposes the base class, registry, and automatically registers all solver classes.
"""
# 1. Initialize the registry first
from .registry import register_algorithm, get_algorithm_names, ALGORITHM_REGISTRY

# 2. Import the Base class
from .base import Optimizer

# 3. Import algorithm implementations (This executes the decorators)
from .gradient_descent import GradientDescent, MomentumGD, Nesterov
from .adaptive import AdaGrad, RMSprop, Adam
from .stochastic import SimulatedSGD, MiniBatchSGD

__all__ = [
    "register_algorithm",
    "get_algorithm_names",
    "ALGORITHM_REGISTRY",
    "Optimizer",
    "GradientDescent",
    "MomentumGD",
    "Nesterov",
    "AdaGrad",
    "RMSprop",
    "Adam",
    "SimulatedSGD",
    "MiniBatchSGD"
]