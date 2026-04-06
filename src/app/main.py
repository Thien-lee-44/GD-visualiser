"""
Bootstrap process for the application.
Initializes configuration, OpenGL context sharing, and assembles the MVC architecture.
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtCore import QCoreApplication, Qt

# Notice how clean this import is now, thanks to __init__.py
from src.app import settings 

from src.ui.views.main_window import MainWindow
from src.ui.controllers.main_controller import MainController

def bootstrap() -> None:
    """Configures and launches the application loop."""
    # 1. Load application configurations
    settings.load_configs()

    # 2. Enforce OpenGL Context sharing across multiple Viewports
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    # 3. Setup Anti-Aliasing (MSAA)
    fmt = QSurfaceFormat()
    samples = settings.get("window", "msaa_samples", default=8)
    fmt.setSamples(samples)
    QSurfaceFormat.setDefaultFormat(fmt)

    # 4. Initialize Qt Application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 5. Assemble MVC Architecture
    main_window = MainWindow()
    
    # Inject window to the Controller
    main_controller = MainController(main_window)
    
    main_window.show()
    sys.exit(app.exec())