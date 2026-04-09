# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.gl as gl
from pyglet.graphics import Batch, Group
from pyglet.math import Mat4
from pyglet.window import Window as PygletWindow

from typing import TYPE_CHECKING
from dataclasses import dataclass
from contextlib import contextmanager
from ctypes import c_int
from math import radians

if TYPE_CHECKING:
    from ..abc import Layer
    from ..scene import Scene, Viewport, Camera
    from ._window import Window
    from ._screen import Screen

# ======================================== DATA ========================================
@dataclass(slots=True, frozen=True)
class SceneRenderData:
    batch: Batch
    layers: dict[Layer, LayerGroups]

@dataclass(slots=True, frozen=True)
class LayerGroups:
    group: CameraGroup
    z_groups: dict[int, Group]

# ======================================== CAMERA GROUP ========================================
class CameraGroup(Group):
    def __init__(self, window: PygletWindow, order: int= 0, parent: Group = None):
        super().__init__(order=order, parent=parent)
        self._window = window
        self.projection: Mat4 = None
        self.view: Mat4 = None
    
    def set_state(self):
        """Applique les matrices du groupe"""
        self._window.projection = self.projection
        self._window.view = self.view
    
    def unset_state(self):
        """Retire les matrices du groupe"""
        pass

# ======================================== PIPELINE ========================================
class Pipeline:
    """
    Pipeline de rendu exploitant OpenGL

    Args:
        window(Window): fenêtre associée
    """
    __slots__ = (
        "_window", "_scene", "_layer",
        "_data", "_projection_cache", "_view_cache", '_view_buffer', "_default_view",
        "_context",
        "_batch", "_group", "_z_groups",
    )

    def __init__(self, window: Window):
        # Binding
        self._window: Window = window
        self._scene: Scene | None = None
        self._layer: Layer | None = None

        # Cache
        self._data: dict[Scene, SceneRenderData] = {}
        self._projection_cache: dict[tuple[float, float, float], Mat4] = {}
        self._view_cache: dict[tuple[float, float, float], Mat4] = {}

        # Pipeline de vue
        self._view_buffer: dict[tuple[float, float, float], Mat4] = {}
        self._default_view: Mat4 = Mat4()

        # Contexte
        self._context: _PipelineContext = _PipelineContext()

        # Gpu configuration
        self._batch: Batch = None
        self._group: Group = None
        self._z_groups: dict[int, Group] = None

    # ======================================== GETTERS ========================================
    @property
    def window(self) -> Window:
        """Fenêtre OS assignée"""
        return self._window
    
    @property
    def gl_viewport(self) -> tuple[int, int, int, int]:
        """Viewport OpenGl"""
        return self._context.gl_viewport
    
    @property
    def screen(self) -> Screen:
        """Espace logique de référence assigné"""
        return self._window.screen
    
    @property
    def scene(self) -> Scene:
        """Scene en cours de rendu"""
        return self._scene
    
    @property
    def viewport(self) -> Viewport:
        """Viewport de la scène en cours de rendu"""
        return self._scene.viewport
    
    @property
    def viewport_resolve(self) -> tuple[float, float, float, float]:
        """Résolution du viewport dans l'espace logique"""
        return self._context.viewport_resolve
    
    @property
    def layer(self) -> Layer:
        """Layer en couche de rendu"""
        return self._layer
    
    @property
    def camera(self) -> Camera:
        """Caméra du layer en cours de rendu"""
        return self._layer.camera or self._scene.camera
    
    @property
    def camera_resolve(self) -> tuple[float, float, float, float, float, float]:
        """Résolution de la caméra"""
        return self._context.camera_resolve
    
    @property
    def ppu(self) -> tuple[float, float]:
        """Ratio pixels par unité moyen"""
        return (self._context.ppu_x + self._context.ppu_y) / 2
    
    @property
    def ppu_x(self) -> float:
        """Ratio pixels par unité horizontal"""
        return self._context.ppu_x
    
    @property
    def ppu_y(self) -> float:
        """Ratio pixels par unité vertical"""
        return self._context.ppu_y

    @property
    def batch(self) -> Batch:
        """Batch courant"""
        return self._batch
    
    @property
    def group(self) -> Group:
        """Groupe du ``Layer`` courant"""
        return self._group
    
    @property
    def z_groups(self) -> dict[int, Group]:
        """Groupes du ``Layer`` courant selon leur ``z-order``"""
        return self._z_groups
    
    def get_group(self, z: int = 0) -> Group:
        """Renvoie le ``Group`` associé au z-order donné dans le ``Layer``courant

        Args:
            z (int): z-order du groupe
        """
        if z not in self._z_groups:
            self._z_groups[z] = Group(order=z, parent=self.group)
        return self._z_groups[z]

    # ======================================== PIPELINE ========================================
    def bind_scene(self, scene: Scene) -> None:
        """Configure le contexte de rendu pour une scene

        Args:
            scene: scene courante
        """
        # Etablissement de la connexion à la scene
        self._scene = scene
        if scene not in self._data:
            self._data[scene] = SceneRenderData(Batch(), {})
        self._batch = self._data[scene].batch

        # Espace logique
        screen = self._window.screen
        self._context.viewport_resolve = scene.viewport.resolve(screen.width, screen.height)
        lx, ly, lw, lh, _, _ = self._context.viewport_resolve

        # FrameBuffer
        window_viewport = self._window.viewport
        sx = self._window.framebuffer_scale_x
        sy = self._window.framebuffer_scale_y

        # Viewport OpenGl
        px = int(window_viewport.x + lx * sx)
        py = int(window_viewport.y + ly * sy)
        pw = int(lw * sx)
        ph = int(lh * sy)
        self._context.gl_viewport = (px, py, pw, ph)

        # Activation du FrameBuffer Viewport
        gl.glViewport(px, py, pw, ph)

    def bind_layer(self, layer: Layer, z: int=0) -> None:
        """Configure le contexte de rendu pour un layer de la scene courante
        
        Args:
            layer: Layer courant
        """
        # Etablissement de la connexion au layer
        self._layer = layer
        layer_groups = self._data[self._scene].layers
        if layer not in layer_groups:
            layer_groups[layer] = LayerGroups(CameraGroup(window=self._window.native, order=z), {})
        self._group = layer_groups[layer].group
        self._z_groups = layer_groups[layer].z_groups

        # Espace viewport
        _, _, lw, lh, (ox , oy), (dx, dy) = self._context.viewport_resolve

        # Frustum
        self._context.camera_resolve = self.camera.resolve(lw, lh)
        cx, cy, vw, vh, zoom, rotation = self._context.camera_resolve

        # Ratios pixels per unit
        self._context.ppu_x,  self._context.ppu_y = self.compute_ppu(lw, lh, vw, vh, zoom)

        # Matrice de projection
        projection = self.compute_projection(vw, vh, zoom)
        self._group.projection = projection
        self._context.projection_matrix = projection

        # Matrice de vue
        view = self.compute_view(cx, cy, rotation, ox, oy, dx, dy)
        self._window.native.view = view
        self._group.view = view

    def flush(self) -> None:
        """Envoie tout le batch au GPU"""
        self._batch.draw()

    def end(self) -> None:
        """Met fin à la connexion avec une scene"""
        self._scene = None
        self._context.clear()
        self._view_cache, self._view_buffer = self._view_buffer, self._view_cache
        self._view_buffer.clear()

    # ======================================== COMPUTING ========================================
    def compute_ppu(self, lw: float, lh: float, vw: float, vh: float, zoom: float) -> tuple[float, float]:
        """Calcul des ratios pixels per unit
        
        Args:
            lw: largeur du viewport (logical space)
            lh: hauteur du viewport (logical space)
            vw: largeur de la vision (view space)
            vh: hauteur de la vision (view space)
            zoom: facteur de zoom
        """
        ppu_x = (lw / vw) * zoom
        ppu_y = (lh / vh) * zoom
        return (ppu_x, ppu_y)

    def compute_projection(self, vw: float, vh: float, zoom: float) -> Mat4:
        """Calcul la matrice de projection

        Args:
            vw: largeur de la vision (view space)
            vh: hauteur de la vision (view space)
            zoom: facteur de zoom
        """
        projection_key = (vw, vh, zoom)
        if projection_key not in self._projection_cache:
            half_w = (vw / zoom) / 2
            half_h = (vh / zoom) / 2
            self._projection_cache[projection_key] = Mat4.orthogonal_projection(
                left=-half_w,
                right=half_w,
                bottom=-half_h,
                top=half_h,
                z_near=-8192.0,
                z_far=8192.0,
            )
        return self._projection_cache[projection_key]
    
    def compute_view(self, cx: float, cy: float, rotation: float, ox: float, oy: float, dx: float, dy: float) -> Mat4:
        """Calcul la matrice de vue
        
        Args
            cx: centre horizontal de la vision (world space)
            cy: centre vertical de la vision (world space)
            rotation: angle de rotation en degrés (CCW)
            ox: origine horizontale du viewport (absolute viewport space)
            oy: origine verticale du viewport (absolute viewport space)
            scale_x: facteur de redimensionnement horizontal
            scale_y: facteur de redimensionnement vertical
        """
        view_key = (cx, cy, rotation, ox, oy, dx, dy)
        if view_key in self._view_buffer:
            return self._view_buffer[view_key]
        if view_key in self._view_cache:
            view = self._view_cache[view_key]
            self._view_buffer[view_key] = view
            return view
        view = self._default_view
        view = self.compute_camera(view, cx, cy, rotation)
        view = self.compute_viewport(view, ox, oy, dx, dy)
        self._view_buffer[view_key] = view
        return view
    
    def compute_camera(self, view: Mat4, cx: float, cy: float, rotation: float) -> Mat4:
        """Transforme une matrice selon l'espace camera
        
        Args:
            matrix: matrice de vue
            cx: centre horizontal de la camera (world space)
            cy: centre vertical de la camera (world space)
            rotation: angle de rotation en degrés (CCW)
        """
        view = view.translate((-cx, -cy, 0))
        if rotation != 0.0:
            view = view.rotate(radians(rotation), (0, 0, 1))
        return view
    
    def compute_viewport(self, view: Mat4, ox: float, oy: float, dx: float, dy: float) -> Mat4:
        """Transforme une matrice selon l'espace viewport

        Args:
            ox: origine horizontale du viewport (absolute viewport space)
            oy: origine verticale du viewport (absolute viewport space)
            dx: direction horizontale du viewport (logical space)
            dy: direction verticale du viewport (logical space)
        """
        view = view.translate((-ox / self.ppu_x, -oy / self.ppu_y, 0))
        if dx != 1.0 or dy != 1.0:
            view = view.scale((dx, dy, 1.0))
        return view

    # ======================================== UTILITAIRES ========================================
    def scale_to_screen(self, width: float = None, height: float = None) -> float | tuple[float, float]:
        """Convertit une taille monde en taille espace logique
        
        Args:
            width: largeur monde
            height: hauteur monde
        """
        if width is None:
            return height * self._context.ppu_y
        if height is None:
            return width * self._context.ppu_x
        return (width * self._context.ppu_x, height * self._context.ppu_y)

    def world_to_framebuffer(self, x: float, y: float) -> tuple[int, int]:
        """Convertit une coordonnée monde en pixels framebuffer

        Args:
            x: coordonnée horizontale monde
            y: coordonnée verticale monde
        """
        lx, ly, lw, lh = self._context.viewport_resolve
        cx, cy, vw, vh, zoom, _ = self._context.camera_resolve

        half_w = (vw / zoom) / 2
        half_h = (vh / zoom) / 2

        # World to NDC
        ndc_x = (x - cx) / half_w
        ndc_y = (y - cy) / half_h

        # NDC to viewport logique
        px_logic = (ndc_x + 1) / 2 * lw
        py_logic = (ndc_y + 1) / 2 * lh

        # Viewport logique to framebuffer
        px_fb = int(self._window.viewport.x + (lx + px_logic) * self._window.framebuffer_scale_x)
        py_fb = int(self._window.viewport.y + (ly + py_logic) * self._window.framebuffer_scale_y)

        return px_fb, py_fb

    @contextmanager
    def scissor(self, wx: float, wy: float, ww: float, wh: float):
        """Context manager appliquant un scissor test en coordonnées monde

        Args:
            wx: x monde du coin bas-gauche
            wy: y monde du coin bas-gauche
            ww: largeur monde
            wh: hauteur monde
        """
        _, _, vw, vh, zoom, _ = self._context.camera_resolve
        half_w = (vw / zoom) / 2
        half_h = (vh / zoom) / 2

        x0, y0 = self.world_to_framebuffer(wx, wy)
        w = int(ww / half_w * self._context.gl_viewport[2] / 2)
        h = int(wh / half_h * self._context.gl_viewport[3] / 2)

        was_enabled = (gl.GLboolean * 1)()
        prev_box = (c_int * 4)()
        gl.glGetBooleanv(gl.GL_SCISSOR_TEST, was_enabled)
        gl.glGetIntegerv(gl.GL_SCISSOR_BOX, prev_box)

        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(x0, y0, w, h)
        try:
            yield
        finally:
            gl.glScissor(*prev_box)
            if not was_enabled[0]:
                gl.glDisable(gl.GL_SCISSOR_TEST)

# ======================================== CONTEXTE ========================================
@dataclass(slots=True)
class _PipelineContext:
    viewport_resolve: tuple[float, float, float, float, tuple[float, float], tuple[float, float]] = None
    camera_resolve: tuple[float, float, float, float, float, float] = None
    gl_viewport: tuple[int, int, int, int] = None
    projection_matrix: Mat4 = None
    view_matrix: Mat4 = None
    ppu_x: float = None
    ppu_y: float = None

    def clear(self) -> None:
        """Nettoie le contexte"""
        self.viewport_resolve = None
        self.camera_resolve = None
        self.gl_viewport = None
        self.projection_matrix = None
        self.view_matrix = None
        self.ppu_x = None
        self.ppu_y = None