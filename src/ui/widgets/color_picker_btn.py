"""
Custom button widget for selecting and displaying RGB colors.
"""
from typing import List, Optional
from PySide6.QtWidgets import QPushButton, QColorDialog, QWidget
from PySide6.QtCore import Signal

class ColorPickerButton(QPushButton):
    """A button that displays a color and opens a dialog to change it when clicked."""
    
    colorChanged = Signal(list)  # Emits [r, g, b] in the 0.0 - 1.0 range

    def __init__(self, initial_color_vec: Optional[List[float]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # Fallback to pure white if no initial color vector is provided
        self._color_vec: List[float] = initial_color_vec if initial_color_vec else [1.0, 1.0, 1.0]
        self.clicked.connect(self._choose_color)
        self._update_ui()

    def set_color(self, color_vec: List[float]) -> None:
        """Sets the color externally (e.g., when loading a new entity profile)."""
        self._color_vec = color_vec
        self._update_ui()

    def get_color(self) -> List[float]:
        """Returns the currently selected color as a list of RGB floats [0.0, 1.0]."""
        return self._color_vec

    def _update_ui(self) -> None:
        """Updates the button's background stylesheet to reflect the current color."""
        r, g, b = [int(c * 255) for c in self._color_vec]
        
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: rgb({r},{g},{b}); "
            f"  border: 1px solid #aaa; "
            f"  height: 24px; "
            f"  border-radius: 4px;"
            f"}}"
        )

    def _choose_color(self) -> None:
        """Opens a QColorDialog and emits the new normalized color if accepted by the user."""
        r, g, b = [int(c * 255) for c in self._color_vec]
        
        # Open the standard system color picker dialog
        color = QColorDialog.getColor(initial=f"#{r:02x}{g:02x}{b:02x}", parent=self, title="Select Optimizer Color")
        
        if color.isValid():
            self._color_vec = [color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0]
            self._update_ui()
            self.colorChanged.emit(self._color_vec)