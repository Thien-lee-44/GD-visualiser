"""
2D Minimap Viewport.
Handles top-down orthographic rendering, gradient legend overlay, 
and bounded widget interactions (dragging, resizing).
"""
from typing import Optional, Any
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QLinearGradient, QPolygonF, QFontMetrics
from PySide6.QtWidgets import QWidget

from src.app import app_context
from src.utils import UIConstants
from .viewport_base import ViewportBase

class Viewport2D(ViewportBase):
    """Floating 2D Minimap widget with interactive bounded overlays."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True) 
        
        self.is_dragging_widget: bool = False
        self.is_resizing_widget: bool = False
        self.drag_start_global: Optional[QPointF] = None
        self.start_geometry: Any = None

    def initializeGL(self) -> None:
        """Initializes the engine 2D renderer."""
        super().initializeGL()
        app_context.engine.init_renderer_2d()

    def paintGL(self) -> None:
        """Renders the 2D mathematical map and custom UI overlays."""
        is_dragging_map = self.mouse_button in (Qt.LeftButton, Qt.RightButton, Qt.MiddleButton) \
                          and not self.is_dragging_widget \
                          and not self.is_resizing_widget
                          
        app_context.engine.update_camera_tracking(is_dragging_map, is_2d=True)
        render_data = app_context.engine.render_frame(self.width(), self.height(), is_2d=True)
        self._draw_overlay_text(render_data, is_2d_mode=True)

        renderer = app_context.engine.renderer_2d
        surface = renderer.surface if renderer else None
        if not surface: 
            return
        
        min_grad = getattr(surface, 'min_grad_norm', 0.0)
        max_grad = getattr(surface, 'max_grad_norm', 0.0)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        font = QFont("Consolas", 8, QFont.Bold)
        fm = QFontMetrics(font)
        max_val_text = f"{max_grad:.2f}"
        text_width = fm.horizontalAdvance(max_val_text)
        
        dyn_right_margin = UIConstants.LEGEND_WIDTH + UIConstants.LEGEND_PADDING + text_width + UIConstants.LEGEND_MARGIN
        
        # Background overlays
        painter.setBrush(QColor(0, 0, 0, UIConstants.OVERLAY_ALPHA)) 
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, self.width(), UIConstants.MINIMAP_TITLE_HEIGHT) 
        painter.drawRect(self.width() - dyn_right_margin, UIConstants.MINIMAP_TITLE_HEIGHT, dyn_right_margin, self.height() - UIConstants.MINIMAP_TITLE_HEIGHT) 
        painter.drawRect(0, self.height() - UIConstants.MINIMAP_BOTTOM_MARGIN, self.width() - dyn_right_margin, UIConstants.MINIMAP_BOTTOM_MARGIN) 
        painter.drawRect(0, UIConstants.MINIMAP_TITLE_HEIGHT, UIConstants.MINIMAP_LEFT_MARGIN, self.height() - 45) 
        
        painter.setPen(QColor(255, 255, 255, 80))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        painter.setPen(QColor(255, 255, 255, 220))
        painter.setFont(font)
        painter.drawText(10, 16, "2D Minimap (Drag to move)")

        grip_size = UIConstants.MINIMAP_GRIP_SIZE
        poly = QPolygonF([
            QPointF(self.width(), self.height() - grip_size),
            QPointF(self.width(), self.height()),
            QPointF(self.width() - grip_size, self.height())
        ])
        painter.setBrush(QColor(255, 255, 255, 120))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(poly)
        
        legend_w = UIConstants.LEGEND_WIDTH                     
        legend_h = min(200, self.height() - 80)  
        rect_x = self.width() - dyn_right_margin + 10    
        rect_y = max(35, (self.height() - legend_h) // 2)
        
        gradient = QLinearGradient(0, rect_y, 0, rect_y + legend_h)
        gradient.setColorAt(0.0, QColor(255, 0, 0))     
        gradient.setColorAt(0.25, QColor(255, 255, 0))  
        gradient.setColorAt(0.5, QColor(0, 255, 255))   
        gradient.setColorAt(0.75, QColor(0, 0, 255))    
        gradient.setColorAt(1.0, QColor(0, 0, 128))     
        
        painter.setBrush(gradient)
        painter.setPen(QColor(255, 255, 255, 100))
        painter.drawRect(rect_x, rect_y, legend_w, legend_h)
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(font)
        painter.drawText(rect_x - 10, rect_y - 8, "GRADIENT")
        
        segments = 10
        for i in range(segments + 1):
            t_visual = i / segments  
            tick_y = rect_y + int(t_visual * legend_h)
            
            painter.setPen(QColor(255, 255, 255, 200))
            painter.drawLine(rect_x + legend_w, tick_y, rect_x + legend_w + 5, tick_y)
            
            t_invert = 1.0 - t_visual
            t_raw = (pow(51.0, t_invert) - 1.0) / 50.0
            val = min_grad + t_raw * (max_grad - min_grad)
            
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect_x + legend_w + 10, tick_y + fm.ascent() // 2 - 1, f"{val:.2f}")
                
        painter.end()

    def mousePressEvent(self, event: Any) -> None:
        """Handles initiating window drag or resize operations."""
        pos = event.position()
        if pos.x() > self.width() - 20 and pos.y() > self.height() - 20:
            self.is_resizing_widget = True
            self.drag_start_global = event.globalPosition()
            self.start_geometry = self.geometry()
            event.accept()
            return
            
        elif pos.y() <= UIConstants.MINIMAP_TITLE_HEIGHT:
            self.is_dragging_widget = True
            self.drag_start_global = event.globalPosition()
            self.start_geometry = self.geometry()
            event.accept()
            return
            
        self.last_mouse_pos = pos
        self.mouse_button = event.button()
        self.setFocus()
        event.accept()

    def mouseReleaseEvent(self, event: Any) -> None:
        """Finalizes dragging/resizing and resets cursor."""
        self.is_dragging_widget = False
        self.is_resizing_widget = False
        self.mouse_button = None
        self.setCursor(Qt.ArrowCursor)
        event.accept()

    def mouseMoveEvent(self, event: Any) -> None:
        """Handles map interactions with strict boundary clamping."""
        pos = event.position()
        
        if self.is_resizing_widget or (pos.x() > self.width() - 20 and pos.y() > self.height() - 20): 
            self.setCursor(Qt.SizeFDiagCursor) 
        elif self.is_dragging_widget or pos.y() <= UIConstants.MINIMAP_TITLE_HEIGHT: 
            self.setCursor(Qt.ClosedHandCursor if self.is_dragging_widget else Qt.OpenHandCursor)
        else: 
            self.setCursor(Qt.ArrowCursor)

        if self.is_resizing_widget:
            delta = event.globalPosition() - self.drag_start_global
            new_w = max(250, int(self.start_geometry.width() + delta.x()))
            new_h = max(250, int(self.start_geometry.height() + delta.y()))
            
            # Clamp resize to prevent extending past parent view
            parent_size = self.parentWidget().size() if self.parentWidget() else None
            if parent_size:
                max_w = parent_size.width() - self.x()
                max_h = parent_size.height() - self.y()
                new_w = min(new_w, max_w)
                new_h = min(new_h, max_h)
                
            self.resize(new_w, new_h)
            return

        if self.is_dragging_widget:
            delta = event.globalPosition() - self.drag_start_global
            new_x = int(self.start_geometry.x() + delta.x())
            new_y = int(self.start_geometry.y() + delta.y())
            
            # Clamp drag to strictly remain within parent view bounds
            parent_size = self.parentWidget().size() if self.parentWidget() else None
            if parent_size:
                new_x = max(0, min(new_x, parent_size.width() - self.width()))
                new_y = max(0, min(new_y, parent_size.height() - self.height()))
            self.move(new_x, new_y)
            return

        self.hover_pos = pos
        
        if self.last_mouse_pos is not None and self.mouse_button in (Qt.LeftButton, Qt.RightButton, Qt.MiddleButton):
            delta = pos - self.last_mouse_pos
            app_context.engine.process_mouse_pan(delta.x() * 0.05, delta.y() * 0.05, is_2d=True)
            app_context.engine.clamp_camera_target(is_2d=True)
            self.last_mouse_pos = pos
            
        if self.mouse_button is None:
            self.makeCurrent()
            renderer = app_context.engine.renderer_2d
            camera = app_context.engine.camera_2d
            if renderer:
                self.hovered_contour_id = renderer.perform_picking(
                    camera, self.width(), self.height(), 
                    int(self.hover_pos.x()), int(self.height() - self.hover_pos.y())
                )
            self.doneCurrent()
            
        self.update()

    def wheelEvent(self, event: Any) -> None:
        """Handles map zoom, preventing zoom triggers over UI borders."""
        pos = event.position()
        if (pos.y() <= UIConstants.MINIMAP_TITLE_HEIGHT or 
            pos.x() > self.width() - 85 or 
            (pos.x() > self.width() - 20 and pos.y() > self.height() - 20)): 
            return
            
        app_context.engine.process_mouse_scroll(event.angleDelta().y() / 120.0, is_2d=True)
        self.update()