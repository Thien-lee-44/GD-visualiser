"""
Merged panel for Environment Configuration, Visual Toggles, and Simulation Execution.
Provides a clean, native-styled interface for controlling the mathematical landscape.
"""
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QComboBox, QPushButton, QDoubleSpinBox,
                               QCheckBox, QFormLayout, QSpinBox, QSlider)
from PySide6.QtCore import Qt, QTimer, Signal

from src.core.functions.registry import get_function_names, get_function_class
from src.app import event_bus, AppEvent, app_context
from src.core  import SimulationConfig
from src.utils import SurfaceStyle, SphereStyle

class EnvironmentPanel(QWidget):
    """Unified UI Panel controlling map parameters, visual toggles, and execution."""
    
    minimap_toggled = Signal(bool)
    tracking_toggled = Signal(bool)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group_box = QGroupBox()
        self.form = QFormLayout(group_box)
        
        self.dynamic_param_widgets: Dict[str, QDoubleSpinBox] = {} 
        
        self._setup_function_section()
        self._setup_boundary_section()
        self._setup_visuals_section()
        self._setup_toggles_section()
        self._setup_execution_section()

        layout.addWidget(group_box)
        self._rebuild_dynamic_params(self.cb_function.currentText())

    def _setup_function_section(self) -> None:
        """Sets up the function selection dropdown and dynamic parameter layout."""
        self.cb_function = QComboBox()
        self.cb_function.addItems(get_function_names())
        self.form.addRow("Function:", self.cb_function)
        
        self.dynamic_params_layout = QFormLayout()
        self.form.addRow(self.dynamic_params_layout)
        self.cb_function.currentTextChanged.connect(self._rebuild_dynamic_params)

    def _setup_boundary_section(self) -> None:
        """Sets up boundary inputs and map resolution spinners."""
        self.spin_x_min, self.spin_x_max = self._create_boundary_pair()
        self.form.addRow("X Axis Bounds:", self._create_h_layout(self.spin_x_min, self.spin_x_max))
        
        self.spin_y_min, self.spin_y_max = self._create_boundary_pair()
        self.form.addRow("Z Axis Bounds:", self._create_h_layout(self.spin_y_min, self.spin_y_max))
        
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(1500) 
        self.preview_timer.timeout.connect(self._emit_clear_preview)

        for spin in [self.spin_x_min, self.spin_x_max, self.spin_y_min, self.spin_y_max]:
            spin.valueChanged.connect(self._emit_boundary_preview)

        self.spin_x_min.valueChanged.connect(self._enforce_x_range)
        self.spin_x_max.valueChanged.connect(self._enforce_x_range)
        self.spin_y_min.valueChanged.connect(self._enforce_y_range)
        self.spin_y_max.valueChanged.connect(self._enforce_y_range)

        self.spin_res = QSpinBox()
        self.spin_res.setRange(10, 1000)
        self.spin_res.setValue(300)
        self.form.addRow("Mesh Resolution:", self.spin_res)
        
        self.spin_contour = QSpinBox()
        self.spin_contour.setRange(5, 100)
        self.spin_contour.setValue(20)
        self.form.addRow("Contour Lines:", self.spin_contour)

        self.btn_apply = QPushButton("Apply Configuration")
        # Kept the primary action button visually distinct
        self.btn_apply.setStyleSheet("background-color: #005A9E; color: white; font-weight: bold; padding: 6px; border-radius: 4px; margin-top: 5px; margin-bottom: 5px;")
        self.btn_apply.clicked.connect(self._emit_mesh_changed)
        self.form.addRow("", self.btn_apply)

    def _setup_visuals_section(self) -> None:
        """Sets up combo boxes for 3D visual styles."""
        self.cb_style = QComboBox()
        self.cb_style.addItems([style.value for style in SurfaceStyle])
        self.cb_style.currentTextChanged.connect(self._emit_visual_toggles)
        self.form.addRow("Surface Style:", self.cb_style)

        self.cb_sphere_style = QComboBox()
        self.cb_sphere_style.addItems([style.value for style in SphereStyle])
        self.cb_sphere_style.setCurrentText(SphereStyle.TEXTURED.value)
        self.cb_sphere_style.currentTextChanged.connect(self._emit_visual_toggles)
        self.form.addRow("Agent Style:", self.cb_sphere_style)

        self.spin_height_scale = QDoubleSpinBox()
        self.spin_height_scale.setRange(0.01, 10.0)
        self.spin_height_scale.setSingleStep(0.1)
        self.spin_height_scale.setValue(1.0)
        self.spin_height_scale.valueChanged.connect(self._emit_mesh_changed)
        self.form.addRow("Vertical Scale:", self.spin_height_scale)
        
        self.cb_trail_mode = QComboBox()
        self.cb_trail_mode.addItems(["Agent Defaults", "Force Enable All", "Force Disable All"])
        self.cb_trail_mode.currentIndexChanged.connect(self._emit_visual_toggles)
        self.form.addRow("Global Trails:", self.cb_trail_mode)

    def _setup_toggles_section(self) -> None:
        """Sets up boolean checkboxes for rendering toggles."""
        v_box = QVBoxLayout()
        v_box.setContentsMargins(0, 0, 0, 0)
        v_box.setSpacing(4)
        
        self.chk_log = QCheckBox("Logarithmic Scaling")
        self.chk_log.setChecked(True)
        self.chk_log.stateChanged.connect(self._emit_mesh_changed)
        
        self.chk_show_minimap = QCheckBox("Enable Minimap Overlay")
        self.chk_show_minimap.setChecked(True)
        self.chk_show_minimap.stateChanged.connect(lambda: self.minimap_toggled.emit(self.chk_show_minimap.isChecked()))
        
        self.chk_tracking = QCheckBox("Follow Selected Agent")
        self.chk_tracking.stateChanged.connect(lambda: self.tracking_toggled.emit(self.chk_tracking.isChecked()))
        
        self.chk_grid = QCheckBox("Render Virtual Grid")
        self.chk_grid.setChecked(True)
        self.chk_grid.stateChanged.connect(self._emit_visual_toggles)
        
        self.chk_highlight = QCheckBox("Render Focus Beam")
        self.chk_highlight.setChecked(True)
        self.chk_highlight.stateChanged.connect(self._emit_visual_toggles)
        
        self.chk_arrow = QCheckBox("Render Gradient Arrow")
        self.chk_arrow.setChecked(True)
        self.chk_arrow.stateChanged.connect(self._emit_visual_toggles)
        
        self.chk_highlight.toggled.connect(self.chk_arrow.setEnabled)

        for chk in [self.chk_log, self.chk_show_minimap, self.chk_tracking, self.chk_grid, self.chk_highlight, self.chk_arrow]:
            v_box.addWidget(chk)

        toggle_widget = QWidget()
        toggle_widget.setLayout(v_box)
        self.form.addRow("View Options:", toggle_widget)

    def _setup_execution_section(self) -> None:
        """Sets up playback buttons and execution speed sliders."""
        self.chk_limit_epochs = QCheckBox("Max Epochs")
        self.chk_limit_epochs.setChecked(True)
        
        self.spin_max_epochs = QSpinBox()
        self.spin_max_epochs.setRange(1, 1000000)
        self.spin_max_epochs.setValue(1000)
        self.form.addRow("Constraints:", self._create_h_layout(self.chk_limit_epochs, self.spin_max_epochs))
        
        self.chk_limit_epochs.toggled.connect(self.spin_max_epochs.setEnabled)
        self.chk_limit_epochs.toggled.connect(self._update_max_epochs)
        self.spin_max_epochs.valueChanged.connect(self._update_max_epochs)

        self.btn_play = QPushButton("▶ Start")
        self.btn_play.setStyleSheet("font-weight: bold; color: white; background-color: #1976D2; padding: 6px; border-radius: 4px;")
        self.btn_play.clicked.connect(
            lambda: event_bus.emit(AppEvent.SIMULATION_PAUSED if "Pause" in self.btn_play.text() else AppEvent.SIMULATION_STARTED)
        )
        
        self.btn_reset = QPushButton("↺ Reset")
        # Removed the heavy background color to make it look like a standard secondary action button
        self.btn_reset.setStyleSheet("font-weight: bold; color: white; background-color: #1976D2; padding: 6px; border-radius: 4px;")
        self.btn_reset.clicked.connect(lambda: event_bus.emit(AppEvent.SIMULATION_RESET))
        
        self.form.addRow("Execution:", self._create_h_layout(self.btn_play, self.btn_reset))

        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setRange(1, 100)
        self.slider_speed.setValue(80) 
        self.slider_speed.valueChanged.connect(lambda v: event_bus.emit(AppEvent.SIMULATION_SPEED_CHANGED, v))
        self.form.addRow("Speed:", self.slider_speed)

    def set_status(self, running: bool, finished: bool = False) -> None:
        """Updates the styling and text of the Play button based on simulation state."""
        if finished:
            self.btn_play.setText("✓ Complete")
            self.btn_play.setStyleSheet("font-weight: bold; color: white; background-color: #388E3C; padding: 6px; border-radius: 4px;")
            self.btn_play.setEnabled(False)
        elif running:
            self.btn_play.setText("⏸ Pause")
            self.btn_play.setStyleSheet("font-weight: bold; color: white; background-color: #F57C00; padding: 6px; border-radius: 4px;")
            self.btn_play.setEnabled(True)
        else:
            self.btn_play.setText("▶ Start")
            self.btn_play.setStyleSheet("font-weight: bold; color: white; background-color: #1976D2; padding: 6px; border-radius: 4px;")
            self.btn_play.setEnabled(True)

    def _create_boundary_pair(self) -> tuple:
        """Helper to create synchronized spin boxes for map boundaries."""
        min_spin = QDoubleSpinBox()
        min_spin.setRange(-50, 50)
        min_spin.setValue(-5.0)
        
        max_spin = QDoubleSpinBox()
        max_spin.setRange(-50, 50)
        max_spin.setValue(5.0)
        return min_spin, max_spin

    def _create_h_layout(self, w1: QWidget, w2: QWidget) -> QWidget:
        """Helper to create a unified horizontal widget container."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(w1)
        layout.addWidget(w2)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def _update_max_epochs(self) -> None:
        """Propagates the max epoch limit down to the simulation context."""
        val = self.spin_max_epochs.value() if self.chk_limit_epochs.isChecked() else 0
        app_context.simulation.max_epochs = val

    def _rebuild_dynamic_params(self, func_name: str) -> None:
        """Dynamically regenerates mathematical parameter inputs when the objective function changes."""
        while self.dynamic_params_layout.count():
            child = self.dynamic_params_layout.takeAt(0)
            if child.widget(): 
                child.widget().deleteLater()
        
        self.dynamic_param_widgets.clear()
        func_class = get_function_class(func_name)
        if not func_class: 
            return
        
        for p_name, p_config in getattr(func_class, 'params_schema', {}).items():
            spin = QDoubleSpinBox()
            spin.setRange(p_config.get('min', -100), p_config.get('max', 100))
            spin.setValue(p_config.get('default', 1.0))
            spin.setSingleStep(p_config.get('step', 0.1))
            self.dynamic_params_layout.addRow(p_config.get('label', p_name).capitalize() + ":", spin)
            self.dynamic_param_widgets[p_name] = spin

    def _enforce_x_range(self) -> None:
        """Prevents minimum X boundary from exceeding maximum X boundary."""
        self.spin_x_min.blockSignals(True)
        self.spin_x_max.blockSignals(True)
        if self.spin_x_min.value() >= self.spin_x_max.value():
            if self.sender() == self.spin_x_min: 
                self.spin_x_max.setValue(self.spin_x_min.value() + 0.5)
            else: 
                self.spin_x_min.setValue(self.spin_x_max.value() - 0.5)
        self.spin_x_min.blockSignals(False)
        self.spin_x_max.blockSignals(False)

    def _enforce_y_range(self) -> None:
        """Prevents minimum Y boundary from exceeding maximum Y boundary."""
        self.spin_y_min.blockSignals(True)
        self.spin_y_max.blockSignals(True)
        if self.spin_y_min.value() >= self.spin_y_max.value():
            if self.sender() == self.spin_y_min: 
                self.spin_y_max.setValue(self.spin_y_min.value() + 0.5)
            else: 
                self.spin_y_min.setValue(self.spin_y_max.value() - 0.5)
        self.spin_y_min.blockSignals(False)
        self.spin_y_max.blockSignals(False)

    def _emit_mesh_changed(self) -> None:
        """Compiles configuration and requests a full 3D surface mesh rebuild via EventBus."""
        self._emit_clear_preview()
        self._update_max_epochs()
        func_params = {name: widget.value() for name, widget in self.dynamic_param_widgets.items()}
        config = SimulationConfig(
            func_name=self.cb_function.currentText(),
            func_params=func_params,
            x_range=(self.spin_x_min.value(), self.spin_x_max.value()),
            y_range=(self.spin_y_min.value(), self.spin_y_max.value()),
            steps=self.spin_res.value(),
            contour_levels=self.spin_contour.value(),
            height_scale=self.spin_height_scale.value(),
            use_log=self.chk_log.isChecked()
        )
        event_bus.emit(AppEvent.MESH_CONFIG_CHANGED, config)

    def _emit_visual_toggles(self) -> None:
        """Broadcasts current visual toggle states to the rendering engine."""
        event_bus.emit(AppEvent.VISUAL_TOGGLES_CHANGED, {
            "surface_style": self.cb_style.currentText(),
            "sphere_style": self.cb_sphere_style.currentText(), 
            "show_grid": self.chk_grid.isChecked(),
            "show_highlight": self.chk_highlight.isChecked(),
            "show_arrow": self.chk_arrow.isChecked(),
            "global_show_trail": self.cb_trail_mode.currentIndex()
        })

    def _emit_boundary_preview(self) -> None:
        """Broadcasts transient boundary changes to render a 3D box preview."""
        event_bus.emit(AppEvent.BOUNDARY_PREVIEW_CHANGED, {
            'x_range': (self.spin_x_min.value(), self.spin_x_max.value()),
            'y_range': (self.spin_y_min.value(), self.spin_y_max.value())
        })
        self.preview_timer.start()

    def _emit_clear_preview(self) -> None:
        """Removes the transient boundary preview box."""
        event_bus.emit(AppEvent.BOUNDARY_PREVIEW_CHANGED, {})