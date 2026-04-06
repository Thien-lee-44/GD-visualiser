"""
Registry for optimization algorithms.
Provides a decorator to dynamically register new optimizers into the system.
"""
from typing import Dict, Type, List, Any

# Global registry storing string names to optimizer class mappings
ALGORITHM_REGISTRY: Dict[str, Type[Any]] = {}

def register_algorithm(name: str):
    """Decorator to automatically register an optimizer algorithm."""
    def decorator(cls: Type[Any]) -> Type[Any]:
        ALGORITHM_REGISTRY[name] = cls
        return cls
    return decorator

def get_algorithm_names() -> List[str]:
    """Returns a list of all registered algorithm names."""
    return list(ALGORITHM_REGISTRY.keys())