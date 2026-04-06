"""
Application settings management.
Provides a robust, type-safe way to load and access JSON configurations.
"""
import json
import os
from typing import Any, Dict

class AppSettings:
    """Configuration manager handling application settings and schemas."""

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._schema: Dict[str, Any] = {}

    def load_configs(self, app_settings_path: str = "configs/app_settings.json") -> None:
        """Loads core application settings and the optimizer schema from JSON files."""
        if os.path.exists(app_settings_path):
            with open(app_settings_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            raise FileNotFoundError(f"Missing core configuration file: {app_settings_path}")

        schema_path = self.get("paths", "schema", default="configs/optimizer_schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                self._schema = json.load(f)
        else:
            self._schema = {}

    def get(self, *keys: str, default: Any = None) -> Any:
        """Retrieves a nested configuration value safely using variable string keys."""
        val = self._config
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                return default
        return val

    @property
    def schema(self) -> Dict[str, Any]:
        """Returns the loaded optimizer parameter schema."""
        return self._schema

# Global Pythonic Singleton instance
settings = AppSettings()