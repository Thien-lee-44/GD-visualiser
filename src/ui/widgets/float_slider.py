"""
Composite widget combining a horizontal slider and a double spinbox.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSlider, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal

class FloatSliderWidget(QWidget):
    """A slider that supports smooth floating-point values by syncing with a QDoubleSpinBox."""
    
    valueChanged = Signal(float)
    
    def __init__(self, min_val: float, max_val: float, step: float, current_val: float, decimals: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.resolution = 10000 
        self._updating = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self.resolution)
        layout.addWidget(self.slider)
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(self.min_val, self.max_val)
        self.spinbox.setSingleStep(step)
        self.spinbox.setDecimals(decimals)
        self.spinbox.setMinimumWidth(80)
        layout.addWidget(self.spinbox)
        
        # Connect signals to cross-sync the widgets
        self.slider.valueChanged.connect(self._on_slider_moved)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        
        self.spinbox.setValue(current_val)
        self._sync_slider_to_spinbox(current_val)
        
    def setRange(self, min_val: float, max_val: float) -> None:
        """Dynamically updates the allowed numerical range of both the slider and spinbox."""
        self.min_val = min_val
        self.max_val = max_val
        self.spinbox.setRange(self.min_val, self.max_val)
        
        current = self.spinbox.value()
        if current < self.min_val: 
            self.spinbox.setValue(self.min_val)
        elif current > self.max_val: 
            self.spinbox.setValue(self.max_val)
            
        self._sync_slider_to_spinbox(self.spinbox.value())

    def _on_slider_moved(self, slider_raw_val: int) -> None:
        """Translates the integer slider position into a float and updates the spinbox."""
        if self._updating: 
            return
            
        self._updating = True
        normalized_val = self.min_val + (slider_raw_val / self.resolution) * (self.max_val - self.min_val)
        self.spinbox.setValue(normalized_val)
        self.valueChanged.emit(normalized_val)
        self._updating = False

    def _on_spinbox_changed(self, spinbox_val: float) -> None:
        """Translates the float spinbox value into an integer and updates the slider."""
        if self._updating: 
            return
            
        self._updating = True
        self._sync_slider_to_spinbox(spinbox_val)
        self.valueChanged.emit(spinbox_val)
        self._updating = False

    def _sync_slider_to_spinbox(self, float_val: float) -> None:
        """Helper to safely calculate and set the slider's integer position without emitting events."""
        if self.max_val > self.min_val:
            slider_pos = int(((float_val - self.min_val) / (self.max_val - self.min_val)) * self.resolution)
        else:
            slider_pos = 0
        self.slider.setValue(slider_pos)

    def value(self) -> float: 
        """Returns the current synchronized float value."""
        return self.spinbox.value()