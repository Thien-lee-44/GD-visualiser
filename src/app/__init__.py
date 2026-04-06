"""
Application core layer.
Exposes central singletons (Context, Settings, EventBus) for clean and easy importing.
"""
from .events import event_bus, AppEvent
from .settings import settings
from .context import app_context

__all__ = [
    "event_bus", 
    "AppEvent",
    "settings",
    "app_context"
]