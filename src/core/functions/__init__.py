"""
Mathematical objective functions module.
Exposes the base class, registry, and auto-registers the classical functions.
"""
# 1. Import registry elements first to establish the decorators
from .registry import register_function, get_function_names, get_function_class, FUNCTION_REGISTRY

# 2. Import abstract base class
from .base import LossFunction

# 3. Import classical functions (Triggers the @register_function decorators)
from .classical_functions import Quadratic, Himmelblau, Rosenbrock, Booth

__all__ = [
    "LossFunction",
    "register_function",
    "get_function_names",
    "get_function_class",
    "FUNCTION_REGISTRY",
    "Quadratic",
    "Himmelblau",
    "Rosenbrock",
    "Booth"
]