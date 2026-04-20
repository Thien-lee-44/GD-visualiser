"""
The central rendering pipeline.
Orchestrates the drawing of surfaces, entities, bounding boxes, and handles pixel-picking.
"""
from pathlib import Path
import glm
import numpy as np
from OpenGL.GL import *
from typing import List, Dict, Any, Tuple, Optional

from src.app.settings import settings
from src.engine.managers import shader_manager, resource_manager 
from src.engine.scene import MathSurface, WireframeSphere, CylinderMesh, ConeMesh, FootballMesh

from .fbo_picking import FBOPickingManager
from .surface_renderer import SurfaceRenderer
from .entity_renderer import EntityRenderer

class MainRenderer:
    """Manages shaders, sub-renderers, and issues GL commands for the entire scene."""
    
    def __init__(self) -> None:
        # Clear context caches first to prevent dead OpenGL handles on hot reloads
        shader_manager.clear_cache()
        resource_manager.clear_cache()
        
        shader_dir = settings.get_path("paths", "shaders", default=Path("assets") / "shaders")
        base_vert = shader_dir / "base.vert"
        
        # Load Shaders via the Cache Manager
        self.surface_shader = shader_manager.get_shader("surface", str(base_vert), str(shader_dir / "surface.frag"))
        self.entity_shader = shader_manager.get_shader("entity", str(base_vert), str(shader_dir / "entity.frag"))
        self.heatmap_shader = shader_manager.get_shader("heatmap", str(base_vert), str(shader_dir / "heatmap.frag"))
        self.picking_shader = shader_manager.get_shader("picking", str(base_vert), str(shader_dir / "picking.frag"))
        
        self.surface: Optional[MathSurface] = None 
        
        # Instantiate primitives in the active context, fetching RAM data via resource_manager internally
        self.sphere = WireframeSphere()
        self.cylinder_mesh = CylinderMesh()
        self.cone_mesh = ConeMesh()
        self.football = FootballMesh()
        
        self.line_vao = int(np.array(glGenVertexArrays(1)).flatten()[0])
        self.line_vbo = int(np.array(glGenBuffers(1)).flatten()[0])

        # Initialize Sub-Renderers
        self.picking_manager = FBOPickingManager()
        self.surface_renderer = SurfaceRenderer()
        self.entity_renderer = EntityRenderer(
            self.line_vao, self.line_vbo, self.sphere, self.football, self.cylinder_mesh, self.cone_mesh
        )

    def _get_2d_viewport(self, width: int, height: int) -> Tuple[int, int, int, int]:
        """Calculates the constrained viewport coordinates for the 2D minimap."""
        if not self.surface: 
            return 0, 0, width, height
        
        top_margin = 25     
        bottom_margin = 20  
        left_margin = 5     
        
        max_val_str = f"{self.surface.max_grad_norm:.2f}"
        right_margin = 12 + 15 + (len(max_val_str) * 7) + 20 
        
        safe_w = max(1, width - left_margin - right_margin)
        safe_h = max(1, height - top_margin - bottom_margin)
        
        x_span = abs(self.surface.x_bounds[1] - self.surface.x_bounds[0])
        z_span = abs(self.surface.z_bounds[1] - self.surface.z_bounds[0])
        map_ratio = (x_span * self.surface.scale_x) / max(1.0, z_span * self.surface.scale_z)
        
        widget_ratio = safe_w / safe_h
        if widget_ratio > map_ratio:
            draw_h = safe_h
            draw_w = int(safe_h * map_ratio)
            x_offset = left_margin + (safe_w - draw_w) // 2
            y_offset = bottom_margin
        else:
            draw_w = safe_w
            draw_h = int(safe_w / map_ratio)
            x_offset = left_margin
            y_offset = bottom_margin + (safe_h - draw_h) // 2
            
        return x_offset, y_offset, draw_w, draw_h

    def resize_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """Adjusts the active OpenGL viewport dimensions."""
        glViewport(x, y, width, height)

    def perform_picking(self, camera: Any, width: int, height: int, mouse_x: int, mouse_y: int) -> int:
        """Renders the scene to an FBO using unique colors to identify clicked elements."""
        x_offset, y_offset, draw_w, draw_h = self._get_2d_viewport(width, height)
        if mouse_x < x_offset or mouse_x >= x_offset + draw_w or mouse_y < y_offset or mouse_y >= y_offset + draw_h: 
            return 0

        current_fbo = glGetIntegerv(GL_FRAMEBUFFER_BINDING)
        fbo = self.picking_manager.setup_fbo(width, height)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        
        glViewport(x_offset, y_offset, draw_w, draw_h)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        camera.aspect_ratio = draw_w / draw_h if draw_h > 0 else 1.0
        self.picking_manager.draw_picking_2d(self.picking_shader, camera, self.surface, draw_w, draw_h)

        pixel_id = 0
        glReadBuffer(GL_COLOR_ATTACHMENT0)
        pixel = glReadPixels(int(mouse_x), int(mouse_y), 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)
        if pixel is not None:
            pixel_data = pixel.tobytes() if hasattr(pixel, 'tobytes') else bytearray(pixel)
            pixel_id = pixel_data[0] | (pixel_data[1] << 8) | (pixel_data[2] << 16)

        glBindFramebuffer(GL_FRAMEBUFFER, current_fbo)
        return pixel_id

    def set_new_surface(self, loss_function: Any, x_range: Tuple[float, float], y_range: Tuple[float, float], 
                        steps: int, height_scale: float, use_log: bool, contour_levels: int = 20) -> None:
        """Instantiates a new math surface model and releases the old one."""
        if self.surface: 
            self.surface.delete_buffers()
        self.surface = MathSurface(loss_function, x_range, y_range, steps, height_scale, use_log, contour_levels)

    def render_frame(self, camera: Any, entities: List[Any], width: int, height: int, 
                     surface_style: str, sphere_style_str: str, sphere_radius: float, 
                     show_grid: bool, show_highlight: bool, show_arrow: bool, 
                     trail_mode: int, selected_entity_id: str, preview_boundary: Dict[str, Any], 
                     is_2d: bool) -> Dict[str, Any]:
        """Main rendering loop. Orchestrates the 3D or 2D drawing processes."""
        if not self.surface: 
            return {"contours": [], "axis_labels": []}

        if is_2d: 
            glClearColor(0.0, 0.0, 0.0, 0.5) 
        else: 
            glClearColor(0.1, 0.1, 0.15, 1.0)
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_PROGRAM_POINT_SIZE) 
        
        if is_2d:
            x_off, y_off, draw_w, draw_h = self._get_2d_viewport(width, height)
            glViewport(x_off, y_off, draw_w, draw_h)
            camera.aspect_ratio = draw_w / draw_h if draw_h > 0 else 1.0
        else:
            glViewport(0, 0, width, height)
            camera.aspect_ratio = width / height if height > 0 else 1.0
        
        active_shaders = [self.surface_shader, self.entity_shader]
        if is_2d: 
            active_shaders.append(self.heatmap_shader)
        
        for shader in active_shaders:
            shader.use()
            shader.set_mat4("view", camera.get_view_matrix())
            shader.set_mat4("projection", camera.get_projection_matrix())
            shader.set_float("flattenY", 1.0) 
        
        self.surface_shader.use()
        self.surface_shader.set_int("use_log", 1 if self.surface.use_log else 0)
        self.surface_shader.set_float("raw_min", self.surface.raw_min)
        self.surface_shader.set_float("raw_max", self.surface.raw_max)
        self.surface_shader.set_float("processed_min", self.surface.processed_min)
        self.surface_shader.set_float("auto_height_scale", self.surface.auto_height_scale)

        floor_y = self.surface.min_height - 0.5
        world_matrix = glm.mat4(1.0)

        # Temporary trail state overriding based on global UI settings
        original_trails = {ent.id: ent.show_trail for ent in entities}
        for ent in entities: 
            if trail_mode == 1: 
                ent.show_trail = True         
            elif trail_mode == 2: 
                ent.show_trail = False      
            
        active_focus_id = selected_entity_id if show_highlight else None

        if is_2d:
            glDisable(GL_DEPTH_TEST)
            self._render_2d_pass(entities, world_matrix, floor_y, active_focus_id, sphere_style_str, show_arrow) 
            glEnable(GL_DEPTH_TEST)
        else:
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LESS) 
            self._render_3d_pass(entities, world_matrix, floor_y, surface_style, show_grid, active_focus_id, sphere_style_str, show_arrow, self.surface.height_scale)
            if preview_boundary: 
                self.surface_renderer.draw_boundary_preview(self.entity_shader, self.surface, preview_boundary, self.line_vao, self.line_vbo, world_matrix, True, floor_y, self.surface.height_scale)

        for ent in entities: 
            ent.show_trail = original_trails[ent.id]
            
        glLineWidth(1.0)
        glPointSize(1.0)
        
        return self._calculate_overlay_text(camera, width, height, surface_style, is_2d, show_grid)

    def _render_2d_pass(self, entities: List[Any], world_matrix: glm.mat4, floor_y: float, active_focus_id: Optional[str], sphere_style_str: str, show_arrow: bool) -> None:
        """Executes drawing commands specifically for the 2D Top-down view."""
        self.surface_renderer.draw_2d_minimap(self.heatmap_shader, self.surface_shader, self.surface, world_matrix, floor_y)
        self.entity_renderer.draw_entities(self.entity_shader, entities, world_matrix, True, floor_y, active_focus_id, self.surface.max_height, sphere_style_str)
        
        if active_focus_id:
            for ent in entities:
                if ent.id == active_focus_id: 
                    self.entity_renderer.draw_gradient_vector(self.entity_shader, ent, self.surface, world_matrix, False, floor_y, show_arrow, 1.0)
                    break

    def _render_3d_pass(self, entities: List[Any], world_matrix: glm.mat4, floor_y: float, surface_style: str, show_grid: bool, active_focus_id: Optional[str], sphere_style_str: str, show_arrow: bool, height_scale: float) -> None:
        """Executes drawing commands specifically for the 3D perspective view."""
        scaled_world = glm.scale(world_matrix, glm.vec3(1.0, height_scale, 1.0))
        self.surface_renderer.draw_3d_environment(self.surface_shader, self.surface, scaled_world, surface_style, show_grid)
        
        self.entity_renderer.draw_entities(self.entity_shader, entities, world_matrix, False, floor_y, active_focus_id, self.surface.max_height, sphere_style_str, height_scale)
        
        if active_focus_id:
            for ent in entities:
                if ent.id == active_focus_id: 
                    self.entity_renderer.draw_gradient_vector(self.entity_shader, ent, self.surface, world_matrix, True, floor_y, show_arrow, height_scale)
                    break

    def _calculate_overlay_text(self, camera: Any, width: int, height: int, surface_style: str, is_2d: bool, show_grid: bool) -> Dict[str, Any]:
        """Calculates screen-space coordinates for overlay labels."""
        contour_data, axis_label_data = [], []
        view, proj = camera.get_view_matrix(), camera.get_projection_matrix()
        
        if is_2d and self.surface:
            x_offset, y_offset, draw_w, draw_h = self._get_2d_viewport(width, height)
            viewport = glm.vec4(x_offset, y_offset, draw_w, draw_h)
        else:
            viewport = glm.vec4(0, 0, width, height)
            
        world_matrix = glm.mat4(1.0)
            
        if is_2d and getattr(self.surface, 'contour_labels', None) and "Contour" in surface_style:
            contour_2d_model = glm.translate(world_matrix, glm.vec3(0.0, self.surface.min_height - 0.49, 0.0))
            for level_id, lx, ly, lz, text in self.surface.contour_labels:
                screen_pos = glm.project(glm.vec3(contour_2d_model * glm.vec4(lx, 0.0, lz, 1.0)), view, proj, viewport)
                if 0.0 <= screen_pos.z <= 1.0: 
                    contour_data.append((level_id, int(screen_pos.x), int(height - screen_pos.y), text))
                    
        elif not is_2d and show_grid and hasattr(self.surface, 'axis_labels'):
            scaled_world = glm.scale(world_matrix, glm.vec3(1.0, self.surface.height_scale, 1.0))
            for lx, ly, lz, text in self.surface.axis_labels:
                screen_pos = glm.project(glm.vec3(scaled_world * glm.vec4(lx, ly, lz, 1.0)), view, proj, viewport)
                if 0.0 <= screen_pos.z <= 1.0: 
                    axis_label_data.append((int(screen_pos.x), int(height - screen_pos.y), text))
                    
        return {"contours": contour_data, "axis_labels": axis_label_data}
