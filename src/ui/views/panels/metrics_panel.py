"""
Panel for displaying real-time numerical metrics of active optimizers.
"""
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.core import MetricData

class MetricsPanel(QWidget):
    """Data table view for live algorithm tracking."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.items_dict: Dict[str, Dict[str, QTableWidgetItem]] = {} 
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initializes the table layout and structural properties."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self._setup_table_headers()
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def _setup_table_headers(self) -> None:
        """Configures the specific columns for the metrics table."""
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Color", "Algorithm ID", "Epoch", "Loss", "Grad Norm", "Pos X", "Pos Y", "Learning Rate"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def update_metrics(self, metrics_list: List[MetricData]) -> None:
        """Updates numerical values in the table rapidly without recreating rows."""
        self.table.setSortingEnabled(False)
        for data in metrics_list:
            ent_id = data.entity_id
            if ent_id in self.items_dict:
                row_items = self.items_dict[ent_id]
                row_items['epoch'].setData(Qt.DisplayRole, data.epoch)
                row_items['loss'].setData(Qt.DisplayRole, float(f"{data.loss:.6f}"))
                row_items['grad'].setData(Qt.DisplayRole, float(f"{data.grad_norm:.6f}"))
                row_items['x'].setData(Qt.DisplayRole, float(f"{data.pos_x:.5f}"))
                row_items['y'].setData(Qt.DisplayRole, float(f"{data.pos_y:.5f}"))
                row_items['lr'].setData(Qt.DisplayRole, float(f"{data.learning_rate:.6f}"))
        self.table.setSortingEnabled(True)

    def rebuild_table(self, entities_list: List[Any]) -> None:
        """Reconstructs the entire table when optimizers are added or removed."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.items_dict.clear()
        self.table.setRowCount(len(entities_list))

        for row, ent in enumerate(entities_list):
            i_color = QTableWidgetItem()
            i_color.setBackground(QColor(
                int(ent.base_color.x * 255), 
                int(ent.base_color.y * 255), 
                int(ent.base_color.z * 255)
            ))
            i_name = QTableWidgetItem(ent.name)
            
            i_epoch = QTableWidgetItem()
            i_loss = QTableWidgetItem()
            i_grad = QTableWidgetItem()
            i_x = QTableWidgetItem()
            i_y = QTableWidgetItem()
            i_lr = QTableWidgetItem()

            for item in (i_name, i_epoch, i_loss, i_grad, i_x, i_y, i_lr): 
                item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, i_color)
            self.table.setItem(row, 1, i_name)
            self.table.setItem(row, 2, i_epoch)
            self.table.setItem(row, 3, i_loss)
            self.table.setItem(row, 4, i_grad)
            self.table.setItem(row, 5, i_x)
            self.table.setItem(row, 6, i_y)
            self.table.setItem(row, 7, i_lr)

            self.items_dict[ent.id] = {
                'epoch': i_epoch, 'loss': i_loss, 'grad': i_grad, 
                'x': i_x, 'y': i_y, 'lr': i_lr
            }
            
        self.table.setSortingEnabled(True)