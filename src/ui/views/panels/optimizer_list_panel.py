"""
Panel for managing active optimizer entities.
Broadcasts selection, creation, and deletion requests via the EventBus.
"""
import random
from typing import Optional, List, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QListWidget, QListWidgetItem, QComboBox, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap, QIcon

from src.core.algorithms import get_algorithm_names
from src.app import event_bus, AppEvent

class OptimizerListWidget(QListWidget):
    """Custom ListWidget that emits an event when clicking on an empty area to deselect."""
    clicked_empty = Signal()
    
    def mousePressEvent(self, event: Any) -> None:
        """Overrides mouse press to detect clicks outside of populated rows."""
        super().mousePressEvent(event)
        if not self.itemAt(event.pos()):
            self.clearSelection()
            self.clicked_empty.emit()

class OptimizerLeftPanel(QWidget):
    """UI Panel containing the list of active optimizer algorithms."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("Active Optimizers")
        main_layout = QVBoxLayout(group)
        
        self.list_widget = OptimizerListWidget()
        self.list_widget.itemClicked.connect(
            lambda item: event_bus.emit(AppEvent.ENTITY_SELECTED, item.data(Qt.UserRole))
        )
        self.list_widget.clicked_empty.connect(
            lambda: event_bus.emit(AppEvent.ENTITY_SELECTED, "")
        )
        main_layout.addWidget(self.list_widget)
        
        add_layout = QHBoxLayout()
        self.cb_algo = QComboBox()
        self.cb_algo.addItems(get_algorithm_names())
        
        self.btn_add = QPushButton("Add Algorithm")
        self.btn_add.clicked.connect(self._on_add_clicked)
        add_layout.addWidget(self.cb_algo)
        add_layout.addWidget(self.btn_add)
        main_layout.addLayout(add_layout)
        
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        main_layout.addWidget(self.btn_remove)
        
        layout.addWidget(group)

    def _on_add_clicked(self) -> None:
        """Broadcasts a request to instantiate a new algorithm with a random color."""
        color = [random.uniform(0.3, 1.0), random.uniform(0.3, 1.0), random.uniform(0.3, 1.0)]
        event_bus.emit(AppEvent.ENTITY_ADDED, {
            "algo_name": self.cb_algo.currentText(), 
            "color": color
        })

    def _on_remove_clicked(self) -> None:
        """Broadcasts a request to delete the currently selected algorithm."""
        item = self.list_widget.currentItem()
        if item:
            event_bus.emit(AppEvent.ENTITY_REMOVED, item.data(Qt.UserRole))
            self.list_widget.takeItem(self.list_widget.row(item))

    def _create_color_icon(self, color_vec: List[float]) -> QIcon:
        """Generates a solid color icon to visually identify the optimizer."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(int(color_vec[0]*255), int(color_vec[1]*255), int(color_vec[2]*255)))
        return QIcon(pixmap)

    def add_item_to_ui(self, entity_id: str, display_name: str, color_vec: List[float]) -> None:
        """Appends a new optimizer to the visual list."""
        item = QListWidgetItem(display_name)
        item.setIcon(self._create_color_icon(color_vec))
        item.setData(Qt.UserRole, entity_id)
        self.list_widget.addItem(item)
        self.list_widget.setCurrentItem(item)
        event_bus.emit(AppEvent.ENTITY_SELECTED, entity_id)

    def update_item_color(self, entity_id: str, color_vec: List[float]) -> None:
        """Updates the list icon when an optimizer's color is modified in the inspector."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == entity_id:
                item.setIcon(self._create_color_icon(color_vec))
                break