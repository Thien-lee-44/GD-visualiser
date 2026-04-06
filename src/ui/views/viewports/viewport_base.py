"""
Base class for OpenGL viewports.
Provides shared overlay rendering and interaction states.
"""
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget

from src.app import app_context, event_bus, AppEvent

class ViewportBase(QOpenGLWidget):
    """Core OpenGL widget providing common state and overlay capabilities."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.hover_pos: Optional[Any] = None
        self.last_mouse_pos: Optional[Any] = None
        self.mouse_button: Optional[Any] = None
        self.hovered_contour_id: int = 0

    def initializeGL(self) -> None:
        """Override in subclasses to initialize specific engine renderers."""
        pass 

    def _draw_overlay_text(self, render_data: Optional[Dict[str, Any]], is_2d_mode: bool) -> None:
        """Renders context-aware text overlays such as contour values and axis labels."""
        if not render_data: 
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if is_2d_mode and render_data.get("contours") and self.hovered_contour_id > 0 and self.hover_pos:
            text_to_draw = next((text for lid, x, y, text in render_data["contours"] if lid == self.hovered_contour_id), None)
            if text_to_draw:
                hx, hy = self.hover_pos.x(), self.hover_pos.y() - 15 
                painter.setFont(QFont("Consolas", 10, QFont.Bold)) 
                fm = painter.fontMetrics()
                text_rect = fm.boundingRect(text_to_draw)
                text_rect.moveTo(int(hx - text_rect.width() / 2), int(hy - text_rect.height()))
                
                bg_rect = text_rect.adjusted(-4, -2, 4, 2)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(15, 15, 15, 210)) 
                painter.drawRoundedRect(bg_rect, 4, 4)
                
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_rect, Qt.AlignCenter, text_to_draw)
                
        if not is_2d_mode and render_data.get("axis_labels"):
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            for x, y, text in render_data["axis_labels"]:
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(x + 1, y + 1, text)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x, y, text)
                
        painter.end()

    def leaveEvent(self, event: Any) -> None:
        """Clears hover states when the mouse leaves the viewport."""
        self.hover_pos = None
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event: Any) -> None:
        """Handles global viewport key shortcuts."""
        if event.key() == Qt.Key_Escape:
            event_bus.emit(AppEvent.ENTITY_SELECTED, "")
        super().keyPressEvent(event)