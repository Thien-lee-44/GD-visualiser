# 3D Optimizer Visualizer

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![OpenGL](https://img.shields.io/badge/OpenGL-3.3%2B-5586A4?logo=opengl&logoColor=white)
![PySide6](https://img.shields.io/badge/Qt-PySide6-41CD52?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A robust, interactive 3D and 2D mathematical visualizer built entirely in Python. Designed for educational purposes, machine learning research, and optimization algorithm analysis, this engine leverages the power of raw OpenGL for hardware-accelerated rendering and PySide6 (Qt) for a highly interactive, professional-grade authoring interface.

At its core, the application simulates mathematical optimization agents (like Gradient Descent, Adam, etc.) traversing complex, non-convex loss landscapes in real-time, backed by a strictly decoupled Event-Driven Architecture.

---

## Core Architecture & Features

### Software Architecture
* **Event-Driven MVC:** A cleanly decoupled architecture utilizing a centralized `EventBus` that bridges the PySide6 User Interface with the core Simulation Engine.
* **Structural Caching (Data-Oriented Design):** Optimized RAM-based cache management (`MathCacheManager`) for heavy mathematical surface generations, preventing redundant vertex and index calculations during UI scaling or context reloads.
* **Dynamic UI Generation:** The Inspector panel dynamically builds anti-lag sliders and scientific inputs directly from JSON configuration schemas (`optimizer_schema.json`), making adding new algorithms seamless.

### Graphics & Rendering
* **Hardware-Accelerated Pipeline:** Custom GLSL shaders designed to handle high-resolution mathematical surfaces, dynamically mapping gradients to color gradients and contour lines.
* **Dual Synchronized Viewports:** Simultaneously interact with an immersive 3D perspective canvas and a floating, draggable 2D orthographic minimap.
* **FBO-Based Picking:** Framebuffer Object (FBO) pixel-perfect mouse picking allows users to interact with and select precise mathematical contours directly from the 2D UI.
* **Visual Trajectory Interpolation:** Smooth, interpolated rendering of agent paths, directional gradient arrows, and focus laser beams tracking the optimizers.

### Editor & User Interface
* **Context-Aware Inspector:** An anti-lag property editor that provides real-time control over an entity's hyperparameters (Learning Rate, Radius, Start Position).
* **Live Metrics Dashboard:** Real-time data table tracking epoch counts, loss values, gradient norms, and exact spatial coordinates for multiple competing agents simultaneously.
* **Unified Environment Panel:** Comprehensive controls to manipulate mathematical objective functions (e.g., Rastrigin, Ackley), mesh resolutions, map boundaries, and execution speed.
* **Custom Widgets:** Native-styled, professional UI elements including Scientific Spinboxes for deep decimal precision and synchronized Float Sliders.

---

## Installation & Setup

### Prerequisites
* Python 3.9 or higher.
* A dedicated GPU or integrated graphics capable of supporting OpenGL 3.3+.

### Step-by-Step Guide

**1. Clone the repository:**
git clone [https://github.com/Thien-lee-44/GD-visualiser.git](https://github.com/Thien-lee-44/GD-visualiser.git)
```bash
cd GD-visualiser
```
**2. Install required dependencies:**
```bash
pip install -r requirements.txt
```
**3. Launch the Editor:**
```bash
python run.py
```
## User Guide & Controls
### Viewport Navigation
- **Orbit 3D Camera**: Hold `Right Mouse Button` + Drag in the 3D Viewport.
- **Pan 3D Camera**: Hold `Left` or `Middle Mouse Button` + Drag in the 3D Viewport.
- **Zoom**: Use the `Mouse Scroll Wheel`.
- **Pan 2D Minimap**: Click and drag the map area inside the floating 2D widget.
### UI Manipulation & Shortcuts
- **Widget Constraints**: The 2D minimap can be dragged via its title bar or resized via the bottom-right grip. It is strictly constrained to prevent clipping out of the main window.

- **Selection**: Click on an algorithm in the "Active Optimizers" list to expose its parameters.

- **Deselect**: Press `ESC` while focused on a viewport, or click on an empty space inside the Optimizer List to clear the selection and hide the Inspector.
## Project Directory Structure
```text
Optimizer_Visualizer/
│
├── run.py                      # Application entry point & Qt Bootstrap
│
├── assets/                     # Static graphical assets & Resources
│   ├── models/                 # 3D .obj proxies (cone, cylinder, sphere)
│   ├── shaders/                # GLSL vertex and fragment shaders
│   └── textures/               # Image maps (e.g., diffuse maps)
│
├── configs/                    # JSON configuration files
│   ├── app_settings.json       # Window and path configurations
│   └── optimizer_schema.json   # Hyperparameter schema for UI generation
│
└── src/                        # ================= SOURCE CODE =================
    ├── app/                    # Global context, EventBus, and settings manager
    ├── core/                   # Math functions, algorithms, and simulation lifecycle
    │   ├── algorithms/         # Optimizer logic (Gradient Descent, etc.)
    │   └── functions/          # Objective landscapes (Ackley, Rastrigin, etc.)
    │
    ├── engine/                 # Core OpenGL Rendering Engine
    │   ├── core/               # Camera matrices and input controllers
    │   ├── managers/           # Context-safe caching (Shader, Resource, Entity)
    │   ├── renderers/          # Sub-renderers (Main, Surface, Entity, FBO Picking)
    │   └── scene/              # 3D map bounds and physical BufferObjects
    │
    ├── ui/                     # PySide6 Graphical User Interface
    │   ├── controllers/        # Bridge bridging UI interactions with Core/Engine logic
    │   ├── views/              # Layout assembly (Main Window, Viewports, Panels)
    │   └── widgets/            # Custom PySide6 inputs (Color Picker, Float Sliders)
    │
    └── utils/                  # Mathematical RAM caching and UI/OpenGL Constants
```
## Contributing
Contributions, issues, and feature requests are welcome. Feel free to check the issues page to get involved and help improve the visualizer.

## License
This project is open-source and available under the MIT License.
