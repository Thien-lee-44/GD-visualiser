"""
Registry for mathematical objective functions.
Provides decorators to dynamically register new mathematical functions without hardcoding them.
"""
from typing import Dict, Type, List, Optional, Any

# Global registry storing string names to function class mappings
FUNCTION_REGISTRY: Dict[str, Type[Any]] = {}

def register_function(name: str):
    """Decorator to automatically register a loss function into the system."""
    def decorator(cls: Type[Any]) -> Type[Any]:
        FUNCTION_REGISTRY[name] = cls
        return cls
    return decorator

def get_function_names() -> List[str]:
    """Returns a list of all registered function names."""
    return list(FUNCTION_REGISTRY.keys())

def get_function_class(name: str) -> Optional[Type[Any]]:
    """Retrieves the class definition for a given function name."""
    return FUNCTION_REGISTRY.get(name)