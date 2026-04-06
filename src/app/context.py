"""
Application Context and Dependency Injection (DI) Container.
Holds global instances of core services, preventing tight coupling.
"""
from src.engine.core.engine import GraphicsEngine
from src.core.simulation import SimulationController
from src.engine.managers.entity_manager import EntityManager

class AppContext:
    """Central registry for application-wide service instances."""
    
    def __init__(self) -> None:
        self.engine: GraphicsEngine = GraphicsEngine()
        self.simulation: SimulationController = SimulationController()
        self.entity_manager: EntityManager = EntityManager()

# Global Pythonic Singleton instance
app_context = AppContext()