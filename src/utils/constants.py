"""
Centralized application constants and enumerations.
Replaces magic numbers and loose strings scattered across the UI and Engine architectures.
"""
from enum import Enum
from typing import Tuple

class SurfaceStyle(Enum):
    """Available rendering styles for the 3D mathematical surface."""
    COLORMAP_CONTOUR = "Colormap + Contour"
    COLORMAP = "Colormap"
    CONTOUR = "Contour"

class SphereStyle(Enum):
    """Available rendering styles for the optimizer agent entities."""
    WIREFRAME = "Wireframe"
    TEXTURED = "Textured"

class UIConstants:
    """Standardized UI dimensions and padding values for 2D overlays."""
    MINIMAP_TITLE_HEIGHT: int = 25
    MINIMAP_BOTTOM_MARGIN: int = 20
    MINIMAP_LEFT_MARGIN: int = 5
    MINIMAP_GRIP_SIZE: int = 15
    LEGEND_WIDTH: int = 12
    LEGEND_PADDING: int = 15
    LEGEND_MARGIN: int = 20
    OVERLAY_ALPHA: int = 180

class Colors:
    """Standardized RGB/RGBA color tuples normalized between 0.0 and 1.0 for OpenGL shaders."""
    DEFAULT_TRAIL: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    AXIS_X: Tuple[float, float, float] = (0.9, 0.2, 0.2)
    AXIS_Y: Tuple[float, float, float] = (0.2, 0.9, 0.2)
    AXIS_Z: Tuple[float, float, float] = (0.2, 0.4, 0.9)
    GRID_LINE: Tuple[float, float, float] = (0.35, 0.35, 0.4)
    BOUNDARY_BOX: Tuple[float, float, float] = (1.0, 1.0, 0.0)
    
    # UI-specific unnormalized RGBA colors (0-255)
    UI_TEXT_LIGHT: Tuple[int, int, int, int] = (255, 255, 255, 220)
    UI_BACKGROUND: Tuple[int, int, int, int] = (0, 0, 0, 180)

class MathConstants:
    """Tolerances and structural limits for mathematical operations."""
    EPSILON: float = 1e-7
    GRADIENT_CLIP_MIN: float = 1e-5