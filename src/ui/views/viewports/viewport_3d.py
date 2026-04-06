"""
Main 3D Viewport.
Handles 3D perspective rendering and bounds management for child viewports.
"""
from typing import Any
from PySide6.QtCore import Qt

from src.app import app_context
from .viewport_base import ViewportBase
from .viewport_2d import Viewport2D

class Viewport3D(ViewportBase):
    """Main immersive 3D view handling camera tracking and child constraints."""
    
    def initializeGL(self) -> None:
        """Initializes the 3D rendering context."""
        super().initializeGL()
        app_context.engine.init_renderer_3d() 
        
    def paintGL(self) -> None:
        """Renders the 3D environment, entities, and overlay text."""
        is_dragging = self.mouse_button in (Qt.LeftButton, Qt.MiddleButton)
        app_context.engine.update_camera_tracking(is_dragging, is_2d=False)
        render_data = app_context.engine.render_frame(self.width(), self.height(), is_2d=False)
        self._draw_overlay_text(render_data, is_2d_mode=False)

    def resizeEvent(self, event: Any) -> None:
        """Ensures floating child viewports (like the 2D map) remain within boundaries on resize."""
        super().resizeEvent(event)
        new_w, new_h = event.size().width(), event.size().height()
        
        # Clamp and shrink the child 2D minimap if the parent window shrinks
        for child in self.children():
            if isinstance(child, Viewport2D):
                geom = child.geometry()
                cx, cy, cw, ch = geom.x(), geom.y(), geom.width(), geom.height()
                
                # Push the widget inwards if it falls outside the right/bottom edge
                cx = max(0, min(cx, new_w - cw))
                cy = max(0, min(cy, new_h - ch))
                
                # Shrink the widget size if the parent is now smaller than the widget
                cw = min(cw, new_w - cx)
                ch = min(ch, new_h - cy)
                
                child.setGeometry(cx, cy, cw, ch)

    def mousePressEvent(self, event: Any) -> None:
        """Records initial click for map panning/rotating."""
        self.last_mouse_pos = event.position()
        self.mouse_button = event.button()
        self.setFocus()

    def mouseReleaseEvent(self, event: Any) -> None:
        """Clears drag states."""
        self.mouse_button = None

    def mouseMoveEvent(self, event: Any) -> None:
        """Handles 3D camera rotation and panning based on drag state."""
        self.hover_pos = event.position()
        if self.last_mouse_pos is not None:
            delta = event.position() - self.last_mouse_pos
            if self.mouse_button == Qt.RightButton: 
                app_context.engine.process_mouse_movement(delta.x(), delta.y(), is_2d=False)
            elif self.mouse_button in (Qt.LeftButton, Qt.MiddleButton): 
                app_context.engine.process_mouse_pan(delta.x() * 0.1, delta.y() * 0.1, is_2d=False)
            self.last_mouse_pos = event.position()
        self.update()

    def wheelEvent(self, event: Any) -> None:
        """Handles 3D camera zooming."""
        app_context.engine.process_mouse_scroll(event.angleDelta().y() / 120.0, is_2d=False)
        self.update()