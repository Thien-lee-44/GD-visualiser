"""
Main application window.
Acts strictly as a View component, responsible only for layout assembly.
"""
from typing import Optional
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QDockWidget, QGroupBox, QSplitter
from PySide6.QtCore import Qt

from src.app import settings, app_context

# Utilize centralized exports to keep imports minimal and clean
from src.ui.views.viewports import Viewport2D, Viewport3D
from src.ui.views.panels import (
    EnvironmentPanel, 
    OptimizerLeftPanel, 
    DynamicInspectorPanel, 
    MetricsPanel
)

class MainWindow(QMainWindow):
    """Assembles the primary layout using splitters and dockable widgets."""
    
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(settings.get("window", "title", default="Optimizer Visualizer"))
        self.resize(
            settings.get("window", "width", default=1800), 
            settings.get("window", "height", default=1000)
        )
        self.viewports = [] 
        self._setup_ui()

    def _create_dock(self, title: str, widget: QWidget, default_area: Qt.DockWidgetArea) -> QDockWidget:
        """Helper to create floating dock widgets globally."""
        dock = QDockWidget(title, self)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        
        for group_box in widget.findChildren(QGroupBox):
            if group_box.title().strip().lower() == title.strip().lower() or title in group_box.title():
                group_box.setTitle("")
                
        dock.setWidget(widget)
        self.addDockWidget(default_area, dock)
        return dock

    def _setup_ui(self) -> None:
        """Initializes panels, splitters, and core UI layout."""
        self.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AnimatedDocks)
        
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.main_splitter)

        # Picture-in-Picture Viewports
        self.gl_viewport_3d = Viewport3D(parent=self)
        self.gl_viewport_2d = Viewport2D(parent=self.gl_viewport_3d)
        self.gl_viewport_2d.setGeometry(20, 20, 350, 350) 
        
        self.main_splitter.addWidget(self.gl_viewport_3d)
        self.viewports = [self.gl_viewport_3d, self.gl_viewport_2d]
        
        # Right Side Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)

        self.active_optimizers_panel = OptimizerLeftPanel(self)
        self.inspector = DynamicInspectorPanel(self)
        
        self.control_panel_splitter = QSplitter(Qt.Vertical)
        
        active_optimizers_widget = QWidget()
        active_optimizers_layout = QVBoxLayout(active_optimizers_widget)
        active_optimizers_layout.setContentsMargins(0, 0, 0, 0)
        active_optimizers_layout.addWidget(self.active_optimizers_panel)
        self.control_panel_splitter.addWidget(active_optimizers_widget)
        
        inspector_widget = QWidget()
        inspector_layout = QVBoxLayout(inspector_widget)
        inspector_layout.setContentsMargins(0, 0, 0, 0)
        inspector_layout.addWidget(self.inspector)
        self.control_panel_splitter.addWidget(inspector_widget)
        
        right_layout.addWidget(self.control_panel_splitter)
        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setSizes([1000, 450]) 
        
        # Merged Environment & Execution Controls Dock
        self.env_panel = EnvironmentPanel(self)
        self.sim_panel = self.env_panel 
        
        env_container = QWidget()
        env_layout = QVBoxLayout(env_container)
        env_layout.addWidget(self.env_panel)
        
        self.env_panel.minimap_toggled.connect(self.gl_viewport_2d.setVisible)
        self.env_panel.tracking_toggled.connect(self._toggle_camera_tracking)

        self.dock_env = self._create_dock("Environment and Controls", env_container, Qt.LeftDockWidgetArea)
        
        # Metrics Dock
        self.metrics = MetricsPanel(self)
        self.dock_metrics = self._create_dock("Live Metrics", self.metrics, Qt.BottomDockWidgetArea)

    def _toggle_camera_tracking(self, is_checked: bool) -> None:
        """Directly toggles tracking state in the engine context."""
        app_context.engine.is_tracking = is_checked
        for vp in self.viewports: 
            vp.update()