"""
Caching mechanisms to optimize heavy mathematical surface generations.
Prevents redundant vertex and index calculations across frame renders.
"""
from typing import Dict, Any, Tuple, Optional

class MathCacheManager:
    """Manager for caching computations of 3D surfaces, indices, and grid data."""
    
    def __init__(self) -> None:
        self._math_cache: Dict[Tuple, Any] = {}
        self._index_cache: Dict[int, Any] = {}

    def get_indices(self, steps: int) -> Optional[Any]:
        """Retrieves cached mesh indices for a given grid resolution."""
        return self._index_cache.get(steps)

    def set_indices(self, steps: int, indices: Any) -> None:
        """Caches mesh indices to prevent recalculation."""
        self._index_cache[steps] = indices

    def get_surface_data(self, shape_key: Tuple) -> Optional[Any]:
        """Retrieves mathematical surface evaluation data based on the parameter signature."""
        return self._math_cache.get(shape_key)

    def set_surface_data(self, shape_key: Tuple, data: Any) -> None:
        """Caches mathematical surface evaluation data."""
        self._math_cache[shape_key] = data

    def clear(self) -> None:
        """Flushes all cached data to free up memory (useful during context reloads)."""
        self._math_cache.clear()
        self._index_cache.clear()

# Global accessible module-level Singleton instance
surface_cache = MathCacheManager()