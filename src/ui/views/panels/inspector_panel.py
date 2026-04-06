"""
Panel for inspecting and modifying hyperparameters of a selected optimizer entity.
Builds dynamic UI sliders based on the algorithm's JSON schema.
"""
from typing import Optional, Dict, Any, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QCheckBox

from src.app import event_bus, AppEvent, settings
from src.ui.widgets import FloatSliderWidget, ScientificFloatWidget, ColorPickerButton

class DynamicInspectorPanel(QWidget):
    """Dynamic UI panel that adapts to the currently selected optimizer's parameters."""
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.schema: Dict[str, Any] = settings.schema 
        
        self.current_entity_id: Optional[str] = None
        self.current_x_range: Tuple[float, float] = (-5.0, 5.0)
        self.current_y_range: Tuple[float, float] = (-5.0, 5.0)
        self.slider_widgets: Dict[str, Any] = {}

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.group_box = QGroupBox("Inspector: No Selection")
        self.form_layout = QFormLayout(self.group_box)
        self.layout.addWidget(self.group_box)

    def clear_ui(self) -> None:
        """Removes all dynamically generated widgets from the panel."""
        self.current_entity_id = None
        self.group_box.setTitle("Inspector: No Selection")
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget: 
                widget.deleteLater()
        self.slider_widgets.clear()

    def load_entity(self, entity: Any) -> None:
        """Generates sliders and inputs based on the given entity's configuration schema."""
        self.clear_ui()
        self.current_entity_id = entity.id
        self.group_box.setTitle(f"Inspector: {entity.name}")

        self.btn_color = ColorPickerButton(initial_color_vec=entity.base_color)
        self.btn_color.colorChanged.connect(self._on_value_changed)
        self.form_layout.addRow("Agent Color:", self.btn_color)

        self.chk_show_trail = QCheckBox("Show Trail")
        self.chk_show_trail.setChecked(getattr(entity, 'show_trail', True))
        self.chk_show_trail.stateChanged.connect(self._on_value_changed)
        self.form_layout.addRow("", self.chk_show_trail)

        self.spin_radius = FloatSliderWidget(0.01, 1.0, 0.01, entity.sphere_radius, 2)
        self.spin_radius.valueChanged.connect(self._on_value_changed)
        self.form_layout.addRow("Sphere Radius:", self.spin_radius)

        self.start_x_widget = FloatSliderWidget(self.current_x_range[0], self.current_x_range[1], 0.1, entity.start_pos[0], 2)
        self.start_y_widget = FloatSliderWidget(self.current_y_range[0], self.current_y_range[1], 0.1, entity.start_pos[1], 2)
        self.form_layout.addRow("Start Pos X:", self.start_x_widget)
        self.form_layout.addRow("Start Pos Y:", self.start_y_widget)
        
        self.start_x_widget.valueChanged.connect(self._on_value_changed)
        self.start_y_widget.valueChanged.connect(self._on_value_changed)

        algo_name = entity.algo.__class__.__name__
        algo_schema = self.schema.get(algo_name, {})
        
        for param_key, conf in algo_schema.items():
            current_val = getattr(entity.algo, param_key, conf['val'])
            if param_key == 'lr': 
                slider_grp = ScientificFloatWidget(current_val) 
            else: 
                slider_grp = FloatSliderWidget(conf['min'], conf['max'], conf['step'], current_val, conf['decimals'])
            
            slider_grp.valueChanged.connect(self._on_value_changed)
            self.slider_widgets[param_key] = slider_grp
            self.form_layout.addRow(conf['name'] + ":", slider_grp)

    def _on_value_changed(self) -> None:
        """Packages all current input values and broadcasts them to update the entity."""
        if not self.current_entity_id: 
            return
            
        new_params = {
            'visuals': {
                'color': self.btn_color.get_color(),
                'show_trail': self.chk_show_trail.isChecked(),
                'sphere_radius': self.spin_radius.value(),
                'start_pos': [self.start_x_widget.value(), self.start_y_widget.value()]
            },
            'algo_params': {key: widget.value() for key, widget in self.slider_widgets.items()}
        }
        
        event_bus.emit(AppEvent.ENTITY_PARAMS_UPDATED, {
            "entity_id": self.current_entity_id,
            "params": new_params
        })