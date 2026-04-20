"""
Generates and manages mathematical surface meshes, contours, and gradients.
Integrates with the centralized cache to prevent redundant heavy mathematical computations.
"""
import math
import numpy as np
import glm
from typing import Tuple, List, Any

from src.engine.renderers.buffer_objects import BufferObject
from src.engine.scene.models import LineMesh
from src.utils.caching import surface_cache

class MathSurface:
    """Represents a 3D landscape generated from a mathematical objective function."""
    _SPHERE_RADIAL_SAMPLES = np.linspace(0.0, 1.05, 15, dtype=np.float64)
    _SPHERE_ANGLE_SAMPLES = np.linspace(0.0, 2.0 * math.pi, 36, endpoint=False, dtype=np.float64)
    _SPHERE_COS = np.cos(_SPHERE_ANGLE_SAMPLES)
    _SPHERE_SIN = np.sin(_SPHERE_ANGLE_SAMPLES)
    
    def __init__(self, loss_function: Any, x_range: Tuple[float, float], y_range: Tuple[float, float], 
                 steps: int, height_scale: float = 1.0, use_log: bool = False, contour_levels: int = 20) -> None:
        self.steps = steps
        
        self.surface_mesh: BufferObject = None
        self.slope_mesh: BufferObject = None 
        self.contour_3d_mesh: LineMesh = None
        self.contour_2d_mesh: LineMesh = None
        
        self.grid_mesh: LineMesh = None
        self.axis_x_mesh: LineMesh = None
        self.axis_y_mesh: LineMesh = None
        self.axis_z_mesh: LineMesh = None
        
        self.contour_labels: List[Tuple] = []
        self.axis_labels: List[Tuple] = []
        
        self.x_bounds = x_range
        self.z_bounds = y_range
        
        self.min_height = float('inf')
        self.max_height = float('-inf')
        self.raw_min = 0.0
        self.raw_max = 0.0
        self.processed_min = 0.0
        self.auto_height_scale = 1.0
        
        self.scale_x = 1.0
        self.scale_z = 1.0
        
        self.loss_function = loss_function
        self.use_log = use_log
        self.height_scale = height_scale
        self.contour_levels = contour_levels
        self._vectorized_loss_supported = None
        self._vectorized_grad_supported = None
        
        self.min_grad_norm = 0.0
        self.max_grad_norm = 0.0
        
        self._generate_buffers(x_range, y_range, steps)

    def _compute_value_array(self, x_vals: Any, z_vals: Any) -> np.ndarray:
        """Evaluate loss values on scalar/vector inputs with fast vectorized fallback."""
        x_arr = np.asarray(x_vals, dtype=np.float64)
        z_arr = np.asarray(z_vals, dtype=np.float64)
        if x_arr.shape != z_arr.shape:
            raise ValueError("x and z inputs must share the same shape.")

        if self._vectorized_loss_supported is not False:
            try:
                values = np.asarray(self.loss_function.compute_value((x_arr, z_arr)), dtype=np.float64)
                if values.shape == x_arr.shape:
                    self._vectorized_loss_supported = True
                    return values
            except Exception:
                self._vectorized_loss_supported = False

        flat_vals = np.fromiter(
            (self.loss_function.compute_value([float(px), float(pz)]) for px, pz in zip(x_arr.ravel(), z_arr.ravel())),
            dtype=np.float64,
            count=x_arr.size,
        )
        return flat_vals.reshape(x_arr.shape)

    def _compute_gradient_norm_grid(self, X: np.ndarray, Z: np.ndarray) -> np.ndarray:
        """Compute gradient norm over the mesh grid with vectorized fast-path."""
        if self._vectorized_grad_supported is not False:
            try:
                grad = np.asarray(self.loss_function.compute_gradient((X, Z)), dtype=np.float64)
                if grad.ndim >= 3 and grad.shape[0] == 2 and grad.shape[1:] == X.shape:
                    self._vectorized_grad_supported = True
                    return np.hypot(grad[0], grad[1])
            except Exception:
                self._vectorized_grad_supported = False

        grad_norms = np.zeros(X.shape, dtype=np.float64)
        for i in range(X.shape[0]):
            for j in range(X.shape[1]):
                g = self.loss_function.compute_gradient([X[i, j], Z[i, j]])
                grad_norms[i, j] = math.hypot(float(g[0]), float(g[1]))
        return grad_norms

    def _generate_buffers(self, x_range: Tuple[float, float], y_range: Tuple[float, float], steps: int) -> None:
        """Computes mesh vertices, indices, gradients, and contour lines with caching support."""
        indices = surface_cache.get_indices(steps)
        if indices is None:
            i, j = np.arange(steps - 1), np.arange(steps - 1)
            ii, jj = np.meshgrid(i, j, indexing='ij')
            tl = ii * steps + jj
            indices = np.stack((tl, tl + steps, tl + 1, tl + 1, tl + steps, tl + steps + 1), axis=-1).ravel().tolist()
            surface_cache.set_indices(steps, indices)
            
        func_params = tuple(sorted([(k, v) for k, v in vars(self.loss_function).items() if isinstance(v, (int, float))]))
        
        shape_key = (
            self.loss_function.__class__.__name__, 
            func_params, tuple(x_range), tuple(y_range), steps, 
            self.use_log, self.contour_levels
        )

        cached_data = surface_cache.get_surface_data(shape_key)
        
        if cached_data is not None:
            if len(cached_data) == 14:
                (
                    X,
                    Z,
                    Y_visual,
                    mapped_norms,
                    raw_t_norm,
                    raw_min,
                    raw_max,
                    processed_min,
                    auto_height_scale,
                    base_lines_3d,
                    lines_2d,
                    contour_labels,
                    norm_min,
                    norm_max,
                ) = cached_data
            else:
                (
                    X,
                    Z,
                    Y_visual,
                    mapped_norms,
                    raw_min,
                    raw_max,
                    processed_min,
                    auto_height_scale,
                    base_lines_3d,
                    lines_2d,
                    contour_labels,
                    norm_min,
                    norm_max,
                ) = cached_data
                y_proc = (Y_visual / max(auto_height_scale, 1e-8)) + processed_min
                if self.use_log:
                    raw_est = np.expm1(y_proc) + raw_min
                else:
                    raw_est = y_proc
                raw_span = max(raw_max - raw_min, 1e-8)
                raw_t_norm = np.clip((raw_est - raw_min) / raw_span, 0.0, 1.0).astype(np.float32)
             
            self.raw_min = raw_min
            self.raw_max = raw_max
            self.processed_min = processed_min
            self.auto_height_scale = auto_height_scale
            self.contour_labels = contour_labels
            self.min_grad_norm = norm_min  
            self.max_grad_norm = norm_max  
        else:
            x = np.linspace(x_range[0], x_range[1], steps)
            z = np.linspace(y_range[0], y_range[1], steps)
            X, Z = np.meshgrid(x, z)
            Y_raw = self._compute_value_array(X, Z)
                        
            self.raw_min = float(np.min(Y_raw))
            self.raw_max = float(np.max(Y_raw)) 
            raw_span = max(self.raw_max - self.raw_min, 1e-8)
            raw_t_norm = np.clip((Y_raw - self.raw_min) / raw_span, 0.0, 1.0).astype(np.float32)
             
            Y_processed = np.log1p(np.maximum(0, Y_raw - self.raw_min)) if self.use_log else Y_raw.copy()
            self.processed_min = float(np.min(Y_processed))
            processed_max = float(np.max(Y_processed))
            
            max_span = max(abs(x_range[1] - x_range[0]), abs(y_range[1] - y_range[0])) 
            self.auto_height_scale = float(max_span / (processed_max - self.processed_min)) if processed_max > self.processed_min else 1.0
            Y_visual = (Y_processed - self.processed_min) * self.auto_height_scale

            grad_norms = self._compute_gradient_norm_grid(X, Z)
                    
            norm_min, norm_max = float(np.min(grad_norms)), float(np.max(grad_norms))
            self.min_grad_norm, self.max_grad_norm = norm_min, norm_max
            mapped_norms = (grad_norms - norm_min) / (norm_max - norm_min) if norm_max > norm_min else np.zeros_like(grad_norms)

            if self.use_log:
                log_levels = np.linspace(0.01, processed_max - 0.01, self.contour_levels * 3)
                levels_3d = np.expm1(log_levels) + self.raw_min
            else:
                levels_3d = np.linspace(self.raw_min + 0.01, self.raw_max - 0.01, self.contour_levels * 3)

            if self.raw_min <= 0.0 <= self.raw_max: 
                levels_3d = np.append(levels_3d, 0.0) 
            levels_3d = np.sort(np.unique(np.append(levels_3d, self.raw_min + 1e-4)))
                
            base_lines_3d, _ = self._get_segments(levels_3d, Y_raw, X, Z, is_2d=False)
            
            levels_2d = max(5, self.contour_levels // 2)
            contour_range = np.unique(np.percentile(Y_raw.ravel(), np.linspace(2, 98, levels_2d)))
            if self.raw_min <= 0.0 <= self.raw_max: 
                contour_range = np.append(contour_range, 0.0)
            contour_range = np.sort(np.unique(np.append(contour_range, self.raw_min + 1e-4)))

            lines_2d, self.contour_labels = self._get_segments(contour_range, Y_raw, X, Z, is_2d=True)
            
            surface_cache.set_surface_data(shape_key, (
                X, Z, Y_visual, mapped_norms, raw_t_norm, self.raw_min, self.raw_max, self.processed_min, 
                self.auto_height_scale, base_lines_3d, lines_2d, self.contour_labels, norm_min, norm_max
            ))
            
        self.min_height = float(np.min(Y_visual))
        self.max_height = float(np.max(Y_visual))
        
        vertices = np.zeros((steps * steps, 8), dtype=np.float32)
        vertices[:, 0], vertices[:, 1], vertices[:, 2] = X.ravel(), Y_visual.ravel(), Z.ravel()
        vertices[:, 5] = raw_t_norm.ravel()
        self.surface_mesh = BufferObject(vertices.ravel().tolist(), indices, vertex_size=8)
        
        vertices_slope = np.copy(vertices)
        vertices_slope[:, 1] = mapped_norms.ravel() 
        self.slope_mesh = BufferObject(vertices_slope.ravel().tolist(), indices, vertex_size=8)
        
        if base_lines_3d: 
            self.contour_3d_mesh = LineMesh(base_lines_3d)
        if lines_2d: 
            self.contour_2d_mesh = LineMesh(lines_2d)

        self._generate_grid_and_axes(x_range, y_range)

    def _generate_grid_and_axes(self, x_range: Tuple[float, float], y_range: Tuple[float, float]) -> None:
        """Generates the coordinate axes and background virtual grid dynamically based on the current view."""
        x_min, x_max = x_range
        z_min, z_max = y_range
        y_min, y_max = 0.0, self.max_height
        
        def get_nice_step(vmin: float, vmax: float) -> float:
            rng = vmax - vmin
            if rng <= 0: 
                return 1.0
            raw_step = rng / 10.0
            mag = 10 ** math.floor(math.log10(raw_step))
            rel_step = raw_step / mag
            
            if rel_step < 1.5: return 1.0 * mag
            if rel_step < 3: return 2.0 * mag
            if rel_step < 7: return 5.0 * mag
            return 10.0 * mag

        x_step = get_nice_step(x_min, x_max)
        z_step = get_nice_step(z_min, z_max)
        
        grid_lines = []
        for ix in np.arange(math.ceil(x_min / x_step) * x_step, x_max + x_step * 0.5, x_step):
            grid_lines.extend([
                ix, y_min, z_min, 0, 1, 0, 0, 0, 
                ix, y_min, z_max, 0, 1, 0, 0, 0, 
                ix, y_min, z_min, 0, 1, 0, 0, 0, 
                ix, y_max, z_min, 0, 1, 0, 0, 0
            ])
            
        for iz in np.arange(math.ceil(z_min / z_step) * z_step, z_max + z_step * 0.5, z_step):
            grid_lines.extend([
                x_min, y_min, iz, 0, 1, 0, 0, 0, 
                x_max, y_min, iz, 0, 1, 0, 0, 0, 
                x_min, y_min, iz, 0, 1, 0, 0, 0, 
                x_min, y_max, iz, 0, 1, 0, 0, 0
            ])

        grid_lines.extend([
            x_max, y_min, z_max, 0, 1, 0, 0, 0, x_max, y_max, z_max, 0, 1, 0, 0, 0, 
            x_min, y_max, z_min, 0, 1, 0, 0, 0, x_max, y_max, z_min, 0, 1, 0, 0, 0,
            x_max, y_max, z_min, 0, 1, 0, 0, 0, x_max, y_max, z_max, 0, 1, 0, 0, 0, 
            x_max, y_max, z_max, 0, 1, 0, 0, 0, x_min, y_max, z_max, 0, 1, 0, 0, 0,
            x_min, y_max, z_max, 0, 1, 0, 0, 0, x_min, y_max, z_min, 0, 1, 0, 0, 0
        ])

        c_x, c_y, c_z = x_min, y_min, z_min
        self.axis_x_mesh = LineMesh([c_x, c_y, c_z, 0, 1, 0, 0, 0, x_max, c_y, c_z, 0, 1, 0, 0, 0])
        self.axis_y_mesh = LineMesh([c_x, c_y, c_z, 0, 1, 0, 0, 0, c_x, y_max, c_z, 0, 1, 0, 0, 0])
        self.axis_z_mesh = LineMesh([c_x, c_y, c_z, 0, 1, 0, 0, 0, c_x, c_y, z_max, 0, 1, 0, 0, 0])

        self.axis_labels = []
        rng = self.raw_max - self.raw_min
        step = 1.0
        if rng > 0:
            raw_step = rng / 6
            mag = 10 ** math.floor(math.log10(raw_step))
            rel_step = raw_step / mag
            step = (1.0 if rel_step < 1.5 else 2.0 if rel_step < 3 else 5.0 if rel_step < 7 else 10.0) * mag
            if rng >= 200: 
                step = max(100.0, round(step / 100.0) * 100.0)

        for raw_tick in np.arange(math.ceil(self.raw_min / step) * step, math.floor(self.raw_max / step) * step + step * 0.5, step):
            y_proc = np.log1p(max(0, raw_tick - self.raw_min)) if self.use_log else raw_tick
            visual_y = max(0.0, min((y_proc - self.processed_min) * self.auto_height_scale, y_max))

            if 0.0 < visual_y < y_max:
                grid_lines.extend([
                    x_min, visual_y, z_min, 0, 1, 0, 0, 0, 
                    x_max, visual_y, z_min, 0, 1, 0, 0, 0, 
                    x_min, visual_y, z_min, 0, 1, 0, 0, 0, 
                    x_min, visual_y, z_max, 0, 1, 0, 0, 0
                ])

            lbl = f"{raw_tick/1_000_000:.1f}M".replace('.0M', 'M') if abs(raw_tick) >= 1_000_000 else f"{raw_tick/1_000:.1f}k".replace('.0k', 'k') if abs(raw_tick) >= 1_000 else f"{int(raw_tick)}" if float(raw_tick).is_integer() else f"{raw_tick:.1f}"
            self.axis_labels.append((c_x - (x_max - x_min)*0.04, visual_y, c_z - (z_max - z_min)*0.04, lbl))

        self.grid_mesh = LineMesh(grid_lines)

    def _get_segments(self, levels: Any, target_Y: Any, X: Any, Z: Any, is_2d: bool = False) -> Tuple[List[float], List[Tuple]]:
        """Extracts contour lines robustly using vectorized Marching Squares algorithm."""
        lines, labels = [], []
        v00, v01, v10, v11 = target_Y[:-1, :-1], target_Y[:-1, 1:], target_Y[1:, :-1], target_Y[1:, 1:]
        
        for idx, L in enumerate(levels):
            r, g, b = ((idx + 1) & 0xFF) / 255.0, (((idx + 1) >> 8) & 0xFF) / 255.0, (((idx + 1) >> 16) & 0xFF) / 255.0
            state = (v00 >= L).astype(np.int8) + (v01 >= L).astype(np.int8) + (v10 >= L).astype(np.int8) + (v11 >= L).astype(np.int8)
            active_indices = np.argwhere((state > 0) & (state < 4))
            
            y_proc = math.log1p(max(0, L - self.raw_min)) if self.use_log else L
            visual_y = float((y_proc - self.processed_min) * self.auto_height_scale)
            level_pts = []

            for i, j in active_indices:
                y00, y01, y10, y11 = target_Y[i, j], target_Y[i, j+1], target_Y[i+1, j], target_Y[i+1, j+1]
                pts = []
                
                if (y00 >= L) != (y01 >= L): 
                    pts.append([X[i, j] + (L - y00) / (y01 - y00) * (X[i, j+1] - X[i, j]), visual_y, Z[i, j]])
                if (y10 >= L) != (y11 >= L): 
                    pts.append([X[i+1, j] + (L - y10) / (y11 - y10) * (X[i+1, j+1] - X[i+1, j]), visual_y, Z[i+1, j]])
                if (y00 >= L) != (y10 >= L): 
                    pts.append([X[i, j], visual_y, Z[i, j] + (L - y00) / (y10 - y00) * (Z[i+1, j] - Z[i, j])])
                if (y01 >= L) != (y11 >= L): 
                    pts.append([X[i, j+1], visual_y, Z[i, j+1] + (L - y01) / (y11 - y01) * (Z[i+1, j+1] - Z[i, j+1])])

                if len(pts) >= 2: 
                    lines.extend([
                        float(pts[0][0]), visual_y, float(pts[0][2]), float(r), float(g), float(b), 0.0, 0.0, 
                        float(pts[1][0]), visual_y, float(pts[1][2]), float(r), float(g), float(b), 0.0, 0.0
                    ])
                    level_pts.append(pts[0])
                if len(pts) == 4: 
                    lines.extend([
                        float(pts[2][0]), visual_y, float(pts[2][2]), float(r), float(g), float(b), 0.0, 0.0, 
                        float(pts[3][0]), visual_y, float(pts[3][2]), float(r), float(g), float(b), 0.0, 0.0
                    ])

            if is_2d and level_pts:
                m_pt = level_pts[len(level_pts) // 3]
                labels.append((idx + 1, float(m_pt[0]), 0.0, float(m_pt[2]), f"{L:.2f}"))
                
        return lines, labels

    def get_sphere_transform(self, pos_2d: Any, sphere_radius: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]:
        """Calculates collision constraints for spheres rolling on the surface to prevent clipping."""
        x, z = float(pos_2d.x if hasattr(pos_2d, 'x') else pos_2d[0]), float(pos_2d.y if hasattr(pos_2d, 'y') else pos_2d[1])
        raw_y = float(self.loss_function.compute_value([x, z]))
            
        y_proc = math.log1p(max(0.0, raw_y - self.raw_min)) if self.use_log else raw_y
        log_drv = 1.0 / (1.0 + max(0, raw_y - self.raw_min)) if self.use_log else 1.0
        
        y_base_unscaled = (y_proc - self.processed_min) * self.auto_height_scale
        y_base_scaled = y_base_unscaled * self.height_scale
        
        grad = self.loss_function.compute_gradient([x, z])
        math_gx, math_gz = float(grad[0]), float(grad[1])
        normal = glm.normalize(glm.vec3(-math_gx * log_drv * self.auto_height_scale * self.height_scale, 1.0, -math_gz * log_drv * self.auto_height_scale * self.height_scale))
        
        radial_offsets = sphere_radius * self._SPHERE_RADIAL_SAMPLES
        y_sphere_offsets = np.sqrt(np.maximum(0.0, sphere_radius**2 - radial_offsets**2))
        sample_x = x + np.outer(radial_offsets, self._SPHERE_COS)
        sample_z = z + np.outer(radial_offsets, self._SPHERE_SIN)
        sample_raw = self._compute_value_array(sample_x, sample_z)

        if self.use_log:
            sample_proc = np.log1p(np.maximum(0.0, sample_raw - self.raw_min))
        else:
            sample_proc = sample_raw
        sample_scaled = (sample_proc - self.processed_min) * self.auto_height_scale * self.height_scale
        required_center_y = sample_scaled + y_sphere_offsets[:, None]
        max_safe_y = max(y_base_scaled + sphere_radius, float(np.max(required_center_y)))

        return (x, float(y_base_unscaled), z), (x, float(max_safe_y), z), (normal.x, normal.y, normal.z)

    def get_path_3d(self, path_list: List[Any]) -> List[float]:
        """Fast vectorized calculation of 3D trail coordinates from raw 2D optimization paths."""
        if not path_list: 
            return []
            
        path = np.array(path_list, dtype=np.float32)
        X, Z = path[:, 0], path[:, 1]
        raw_y = self._compute_value_array(X, Z)

        y_proc = np.log1p(np.maximum(0, raw_y - self.raw_min)) if self.use_log else raw_y
        y_base = (y_proc - self.processed_min) * self.auto_height_scale

        trail_3d = np.zeros((len(X), 3), dtype=np.float32)
        trail_3d[:, 0], trail_3d[:, 1], trail_3d[:, 2] = X, y_base, Z
        return trail_3d.ravel().tolist()

    def draw(self) -> None:
        """Issues draw command for the main surface."""
        if self.surface_mesh: 
            self.surface_mesh.draw()
            
    def draw_contours_3d(self) -> None:
        """Issues draw command for the 3D contour lines."""
        if self.contour_3d_mesh: 
            self.contour_3d_mesh.draw()
            
    def draw_contours_2d(self) -> None:
        """Issues draw command for the 2D contour lines on the minimap."""
        if self.contour_2d_mesh: 
            self.contour_2d_mesh.draw()
            
    def delete_buffers(self) -> None:
        """Releases OpenGL resources when the surface is destroyed to prevent VRAM leaks."""
        for mesh in [self.surface_mesh, self.slope_mesh, self.contour_3d_mesh, self.contour_2d_mesh, 
                     self.grid_mesh, self.axis_x_mesh, self.axis_y_mesh, self.axis_z_mesh]:
            if mesh: 
                mesh.delete_buffers()
