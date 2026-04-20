"""
Application settings management.
Provides a robust, type-safe way to load and access JSON configurations.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

PathLike = Union[str, Path]

class AppSettings:
    """Configuration manager handling application settings and schemas."""

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self._schema: Dict[str, Any] = {}
        self._project_root = Path(__file__).resolve().parents[2]

    def load_configs(self, app_settings_path: Optional[PathLike] = None) -> None:
        """Loads core application settings and the optimizer schema from JSON files."""
        config_path = self._resolve_path(app_settings_path or Path("configs") / "app_settings.json")
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                self._config = json.load(f)
        else:
            raise FileNotFoundError(f"Missing core configuration file: {config_path}")

        schema_path = self.get_path("paths", "schema", default=Path("configs") / "optimizer_schema.json")
        if schema_path.exists():
            with schema_path.open("r", encoding="utf-8") as f:
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

    def get_path(self, *keys: str, default: PathLike) -> Path:
        """Resolves a configured path relative to the project root when needed."""
        raw_path = self.get(*keys, default=default)
        return self._resolve_path(raw_path)

    def _resolve_path(self, path_value: PathLike) -> Path:
        """Converts a path value into an absolute normalized path."""
        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = self._project_root / candidate
        return candidate.resolve()

    @property
    def schema(self) -> Dict[str, Any]:
        """Returns the loaded optimizer parameter schema."""
        return self._schema

# Global Pythonic Singleton instance
settings = AppSettings()
