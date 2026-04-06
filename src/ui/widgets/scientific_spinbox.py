"""
Composite widget for inputting scientific notation numbers.
"""
import math
from typing import Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QDoubleSpinBox, QSpinBox, QLabel
from PySide6.QtCore import Qt, Signal

class ScientificFloatWidget(QWidget):
    """Allows input of very small or very large floats using a mantissa and an exponent (e.g., 1.5 x 10^-4)."""
    
    valueChanged = Signal(float)
    
    def __init__(self, current_val: float, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.spin_val = QDoubleSpinBox()
        self.spin_val.setRange(1.0, 9.99)
        self.spin_val.setSingleStep(0.1)
        self.spin_val.setDecimals(2)
        
        self.spin_exp = QSpinBox()
        self.spin_exp.setRange(-15, 5)
        
        layout.addWidget(self.spin_val)
        
        lbl = QLabel(" x 10 ^ ")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)
        
        layout.addWidget(self.spin_exp)
        
        self._set_from_float(current_val)
        
        # Connect both spinboxes to trigger the global value change event
        self.spin_val.valueChanged.connect(self._on_internal_value_changed)
        self.spin_exp.valueChanged.connect(self._on_internal_value_changed)

    def _set_from_float(self, val: float) -> None:
        """Calculates the mantissa (base) and exponent from a raw float value and sets the UI."""
        if val == 0:
            self._update_spinboxes_silently(1.0, -4)
            return
            
        exp = math.floor(math.log10(abs(val)))
        base = val / (10 ** exp)
        
        # Normalize boundaries to keep the mantissa between 1.0 and 9.99
        if base >= 10.0: 
            base /= 10.0
            exp += 1
        elif base < 1.0: 
            base *= 10.0
            exp -= 1
            
        self._update_spinboxes_silently(base, exp)

    def _update_spinboxes_silently(self, base: float, exp: int) -> None:
        """Updates the UI elements without triggering recursive signal emissions."""
        self.spin_val.blockSignals(True)
        self.spin_exp.blockSignals(True)
        
        self.spin_val.setValue(base)
        self.spin_exp.setValue(exp)
        
        self.spin_val.blockSignals(False)
        self.spin_exp.blockSignals(False)

    def _on_internal_value_changed(self) -> None: 
        """Emits the combined float value whenever the mantissa or exponent changes."""
        self.valueChanged.emit(self.value())

    def value(self) -> float: 
        """Calculates and returns the combined scientific float value."""
        return self.spin_val.value() * (10 ** self.spin_exp.value())