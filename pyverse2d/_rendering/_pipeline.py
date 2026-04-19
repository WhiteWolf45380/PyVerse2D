# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._flag import CoordSpace
from ..abc import Layer

from ._quad import ScreenQuad
from ._fbo import Framebuffer
from ._spaces import Window, LogicalScreen, Viewport, Camera

import pyglet.gl as gl
from pyglet.graphics import Batch, Group
from pyglet.math import Mat4
from pyglet.graphics.shader import ShaderProgram

from typing import TYPE_CHECKING
from dataclasses import dataclass
from contextlib import contextmanager
from ctypes import c_int
import math

if TYPE_CHECKING: 
    from .._managers import CoordinatesManager
    from ..scene import Scene

# ======================================== DATA ========================================
@dataclass(slots=True, frozen=True)
class SceneData:
    fbo: Framebuffer
    layers: dict[Layer, LayerData]

@dataclass(slots=True, frozen=True)
class LayerData:
    batch: Batch
    z_groups: dict[int, Group]

# ======================================== PIPELINE ========================================
class Pipeline:
    """Pipeline de rendu OpenGl

    Args:
        window(Window): fenêtre associée
    """
    __slots__ = (
        "_window", "_quad", "_temp_fbo",
        "_data", "_projection_cache", "_view_cache",
        "_view_buffer", "_default_view",
        "_context",
    )

    _COORD: CoordinatesManager = None

    @classmethod
    def get_coord(cls) -> CoordinatesManager:
        """Renvoie l'instance du gestionnaire de coordonnées"""
        if cls._COORD is None:
            from .._managers import CoordinatesManager
            cls._COORD = CoordinatesManager.get_instance()
        return cls._COORD

    def __init__(self, window: Window):
        # Binding
        self._window: Window = window

        # Objets OpenGl
        self._quad: ScreenQuad = ScreenQuad()
        self._temp_fbo: Framebuffer = None

        # Cache
        self._data: dict[Scene, SceneData] = {}
        self._projection_cache: dict[tuple, Mat4] = {}
        self._view_cache: dict[tuple, Mat4] = {}

        # Buffering de la view matrix
        self._view_buffer: dict[tuple, Mat4] = {}
        self._default_view: Mat4 = Mat4()

        # Contexte
        self._context: _PipelineContext = _PipelineContext()

    # ======================================== GETTERS ========================================
    # OpenGl
    @property
    def quad(self) -> ScreenQuad:
        """Rectangle d'écran complet"""
        return self._quad
    
    @property
    def temp_fbo(self) -> Framebuffer:
        """Renvoie le FrameBuffer éphémère"""
        return self._temp_fbo
    
    @property
    def gl_viewport(self) -> tuple[int, int, int, int]:
        """Viewport OpenGl"""
        return self._context.gl_viewport
    
    # Pipeline interne
    @property
    def window(self) -> Window:
        """Fenêtre OS assignée"""
        return self._window
    
    @property
    def screen(self) -> LogicalScreen:
        """Espace logique de référence assigné"""
        return self._window.screen
    
    @property
    def viewport(self) -> Viewport:
        """Viewport de la scène en cours de rendu"""
        return self._context.viewport

    @property
    def camera(self) -> Camera:
        """Caméra du layer en cours de rendu"""
        return self._context.camera
    
    # Assgination courante
    @property
    def scene(self) -> Scene:
        """Scene en cours de rendu"""
        return self._context.scene
    
    @property
    def layer(self) -> Layer:
        """Layer en couche de rendu"""
        return self._context.layer
    
    # Etat courant
    @property
    def batch(self) -> Batch:
        """Batch courant"""
        return self._context.batch
    
    @property
    def fbo(self) -> Framebuffer:
        """Framebuffer courant"""
        return self._context.fbo
    
    @property
    def z_groups(self) -> dict[int, Group]:
        """Groupes du ``Layer`` courant selon leur ``z-order``"""
        return self._context.z_groups
    
    # Résolutions
    @property
    def viewport_resolve(self) -> tuple[float, float, float, float]:
        """Résolution du viewport dans l'espace logique"""
        return self._context.viewport_resolve
    
    @property
    def camera_resolve(self) -> tuple[float, float, float, float, float, float, tuple[float, float]]:
        """Résolution de la caméra"""
        return self._context.camera_resolve
    
    # Ratios
    @property
    def ppu(self) -> tuple[float, float]:
        """Ratio pixels par unité moyen"""
        return self._context.ppu
    
    @property
    def ppu_x(self) -> float:
        """Ratio pixels par unité horizontal"""
        return self._context.ppu_x
    
    @property
    def ppu_y(self) -> float:
        """Ratio pixels par unité vertical"""
        return self._context.ppu_y
    
    # Matrices
    @property
    def projection_matrix(self) -> Mat4:
        """Matrice de projection"""
        return self._context.projection_matrix
    
    @property
    def view_matrix(self) -> Mat4:
        """Matrice de vue"""
        return self._context.view_matrix
    
    # ======================================== INTERFACE ========================================
    def get_group(self, z: int = 0) -> Group:
        """Renvoie le ``Group`` associé au z-order donné dans le ``Layer``courant

        Args:
            z (int): z-order du groupe
        """
        if z not in self._context.z_groups:
            self._context.z_groups[z] = Group(order=z)
        return self._context.z_groups[z]
    
    def apply_shader(self, program: ShaderProgram, **uniforms) -> None:
        """Applique un shader post-process sur le FBO courant (ping-pong)

        Args:
            program: shader program à appliquer
            **uniforms: uniforms à passer au shader (u_texture réservé)
        """
        scene_fbo = self._context.fbo
        temp_fbo = self._get_temp_fbo(scene_fbo)

        gl.glViewport(0, 0, scene_fbo.width, scene_fbo.height)

        temp_fbo.bind()
        temp_fbo.clear()
        program.use()
        for name, value in uniforms.items():
            program[name] = value
        program['u_texture'] = 0
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, scene_fbo.texture_id)
        self.quad.draw_raw()

        scene_fbo.bind()
        scene_fbo.clear()
        self.quad.blit(temp_fbo.texture_id)
        scene_fbo.bind()

        gl.glViewport(*self._context.gl_viewport)

    # ======================================== PIPELINE ========================================
    def bind_scene(self, scene: Scene) -> None:
        """Configure le contexte de rendu pour une scene

        Args:
            scene: scene courante
        """
        screen = self._window.screen

        # Assignation de la scene
        self._context.scene = scene
        self._context.viewport = scene.viewport

        # Création des données si non exisantes
        if scene not in self._data:
            fbo = Framebuffer(screen.width, screen.height)
            self._data[scene] = SceneData(fbo, {})

        # Enregistrement de l'état courant
        self._context.fbo = self._data[scene].fbo

        # Résolution du viewport
        self._context.viewport_resolve = scene.viewport.resolve(screen.width, screen.height)
        lx, ly, lw, lh, _, _ = self._context.viewport_resolve

        # Calcul du viewport OpenGl
        gl_x = int(lx)
        gl_y = int(ly)
        gl_w = int(lw)
        gl_h = int(lh)
        self._context.gl_viewport = (gl_x, gl_y, gl_w, gl_h)
        gl.glViewport(gl_x, gl_y, gl_w, gl_h)

        # Assignation du FrameBuffer
        self._context.fbo.bind()
        self._context.fbo.clear()

    def bind_layer(self, layer: Layer) -> None:
        """Configure le contexte de rendu pour un layer de la scene courante
        
        Args:
            layer: Layer courant
        """
        # Etablissement de la connexion au layer
        self._context.layer = layer
        self._context.camera = layer.camera or self._context.scene.camera

        # Création des données si non existantes
        layers_data = self._data[self._context.scene].layers
        if layer not in layers_data:
            layers_data[layer] = LayerData(Batch(), {})

        # Enregistrement de l'état courant
        self._context.batch = layers_data[layer].batch
        self._context.z_groups = layers_data[layer].z_groups

        # Résolution de la caméra
        _, _, lw, lh, (ox , oy), (dx, dy) = self._context.viewport_resolve
        self._context.camera_resolve = self._context.camera.resolve(lw, lh)
        cx, cy, vw, vh, zoom, rotation = self._context.camera_resolve

        # Calcul des ratios
        self._context.ppu_x, self._context.ppu_y = self.compute_ppu(lw, lh, vw, vh, zoom)
        self._context.ppu = (self._context.ppu_x + self._context.ppu_y) / 2

        # Matrice de projection
        projection = self.compute_projection(vw, vh, dx, dy, zoom)
        self._context.projection_matrix = projection
        self._window.native.projection = projection

        # Matrice de vue
        view = self.compute_view(cx, cy, rotation, ox, oy)
        self._context.view_matrix = view
        self._window.native.view = view

    def flush(self) -> None:
        """Envoie tout le batch au GPU"""
        self._context.batch.draw()

    def end(self) -> None:
        """Met fin à la connexion avec une scene"""
        canvas = self._window.canvas

        # Blit FBO sur window
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glViewport(
            canvas.x,
            canvas.y,
            canvas.width,
            canvas.height,
        )
        self._quad.blit(self._context.fbo.texture_id)

        # Nettoyage de l'état courant
        self._context.clear()

        # Nettoyage des caches
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

    def compute_projection(self, vw: float, vh: float, dx: float, dy: float, zoom: float) -> Mat4:
        """Calcul la matrice de projection

        Args:
            vw: largeur de la vision (view space)
            vh: hauteur de la vision (view space)
            zoom: facteur de zoom
        """
        projection_key = (vw, vh, dx, dy, zoom)
        if projection_key not in self._projection_cache:
            half_w = vw / (dx * zoom * 2)
            half_h = vh / (dy * zoom * 2)
            self._projection_cache[projection_key] = Mat4.orthogonal_projection(
                left=-half_w,
                right=half_w,
                bottom=-half_h,
                top=half_h,
                z_near=-8192.0,
                z_far=8192.0,
            )
        return self._projection_cache[projection_key]
    
    def compute_view(self, cx: float, cy: float, rotation: float, ox: float, oy: float) -> Mat4:
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
        view_key = (cx, cy, rotation, ox, oy)
        if view_key in self._view_buffer:
            return self._view_buffer[view_key]
        if view_key in self._view_cache:
            view = self._view_cache[view_key]
            self._view_buffer[view_key] = view
            return view
        view = self._default_view
        view = self.compute_camera(view, cx, cy, rotation)
        view = self.compute_viewport(view, ox, oy)
        self._view_buffer[view_key] = view
        return view
    
    def compute_camera(self, view: Mat4, cx: float, cy: float, rotation: float) -> Mat4:
        """Transforme une matrice selon l'espace caméra
        
        Args:
            matrix: matrice de vue
            cx: centre horizontal de la camera (world space)
            cy: centre vertical de la camera (world space)
            rotation: angle de rotation en degrés (CCW)
        """
        view = view.translate((-cx, -cy, 0))
        if rotation != 0.0:
            view = view.rotate(math.radians(rotation), (0, 0, 1))
        return view
    
    def compute_viewport(self, view: Mat4, ox: float, oy: float) -> Mat4:
        """Transforme une matrice selon l'espace viewport

        Args:
            ox: origine horizontale du viewport (absolute viewport space)
            oy: origine verticale du viewport (absolute viewport space)
        """
        view = view.translate((ox / self.ppu_x, oy / self.ppu_y, 0))
        return view
        
    # ======================================== SPACE CONVERSIONS ========================================
    def convert(self, x: float, y: float, from_space: CoordSpace, to_space: CoordSpace, viewport: Viewport = None, camera: Camera = None) -> tuple[float, float]:
        """Convertit une position d'un espace à un autre

        x: position horizontale
        y: position verticale
        from_space: espace source
        to_space: espace cible
        viewport: viewport à utiliser (par défaut le viewport courant)
        camera: camera à utiliser (par défaut la camera courante)
        """
        return self.get_coord().convert(x, y, from_space, to_space, viewport=viewport, camera=camera)

    def world_to_framebuffer(self, x: float, y: float, viewport: Viewport = None, camera: Camera = None) -> tuple[int, int]:
        """Convertit un point monde en pixel framebuffer

        Args:
            x: coordonnée horizontale monde
            y: coordonnée verticale monde
            viewport: Viewport à utiliser (par défaut le viewport courant)
            camera: Camera à utiliser (par défaut la caméra courante)
        """
        return self.get_coord().world_to_logical(x, y, viewport=viewport, camera=camera)

    def framebuffer_to_world(self, x: int, y: int, viewport: Viewport =  None, camera: Camera = None) -> tuple[float, float]:
        """Convertit un pixel framebuffer en point monde

        Args:
            x: coordonnée horizontale framebuffer
            y: coordonnée verticale framebuffer
            viewport: Viewport à utiliser (par défaut le viewport courant)
            camera: Camera à utiliser (par défaut la caméra courante)
        """
        return self.get_coord().logical_to_world(x, y, viewport=viewport, camera=camera)
    
    def world_to_framebuffer_dir(self, dx: float, dy: float) -> tuple[float, float]:
        """Convertit un vecteur directionnel monde en vecteur framebuffer

        Args:
            dx: composante horizontale monde
            dy: composante verticale monde
        """
        _, _, vw, vh, zoom, rotation = self._context.camera_resolve
        _, _, lw, lh, _, (fdx, fdy) = self._context.viewport_resolve

        # Rotation caméra uniquement (pas de translation)
        if rotation != 0.0:
            rad = math.radians(rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            dx, dy = dx * cos_r + dy * sin_r, -dx * sin_r + dy * cos_r

        # Scale frustum -> NVC -> Framebuffer
        half_w, half_h = vw / (zoom * fdx * 2), vh / (zoom * fdy * 2)
        fx = (dx / half_w / 2) * lw
        fy = (dy / half_h / 2) * lh

        return fx, fy

    def world_to_framebuffer_dir_normalized(self, dx: float, dy: float) -> tuple[float, float]:
        """Convertit un vecteur directionnel monde en vecteur framebuffer normalisé

        Args:
            dx: composante horizontale monde
            dy: composante verticale monde
        """
        fx, fy = self.world_to_framebuffer_dir(dx, dy)
        length = math.sqrt(fx * fx + fy * fy)
        if length == 0.0:
            return (0.0, 0.0)
        return (fx / length, fy / length)

    # ======================================== UTILITAIRES ========================================
    def visible_world_rect(self) -> tuple[float, float, float, float]:
        """Renvoie ``(x, y, width, height)`` du frustum visible en coordonnées monde"""
        cx, cy, vw, vh, zoom, _ = self._context.camera_resolve
        _, _, _, _, _, (dx, dy) = self._context.viewport_resolve
        half_w = vw / (zoom * 2 * abs(dx))
        half_h = vh / (zoom * 2 * abs(dy))
        return (cx - half_w, cy - half_h, half_w * 2, half_h * 2)

    def scale_to_framebuffer(self, width: float = None, height: float = None) -> float | tuple[float, float]:
        """Convertit une taille monde en taille framebuffer
        
        Args:
            width: largeur monde
            height: hauteur monde
        """
        if width is None:
            return height * self._context.ppu_y
        if height is None:
            return width * self._context.ppu_x
        return (width * self._context.ppu_x, height * self._context.ppu_y)
    
    @contextmanager
    def scissor_world(self, wx: float, wy: float, ww: float, wh: float, viewport: Viewport = None, camera: Camera = None):
        """Context manager appliquant un scissor test en coordonnées monde

        Args:
            wx: x monde du coin bas-gauche
            wy: y monde du coin bas-gauche
            ww: largeur monde
            wh: hauteur monde
        """
        x0, y0 = self.world_to_framebuffer(wx, wy, viewport=viewport, camera=camera)
        x1, y1 = self.world_to_framebuffer(wx + ww, wy + wh, viewport=viewport, camera=camera)

        left = min(x0, x1)
        top = min(y0, y1)
        width = abs(x0 - x1)
        height = abs(y0 - y1)

        was_enabled = (gl.GLboolean * 1)()
        prev_box = (c_int * 4)()
        gl.glGetBooleanv(gl.GL_SCISSOR_TEST, was_enabled)
        gl.glGetIntegerv(gl.GL_SCISSOR_BOX, prev_box)

        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(left, top, width, height)
        try:
            yield
        finally:
            gl.glScissor(*prev_box)
            if not was_enabled[0]:
                gl.glDisable(gl.GL_SCISSOR_TEST)

    @contextmanager
    def scissor_framebuffer(self, x: float, y: float, w: float, h: float):
        """Context manager appliquant un scissor test en coordonnées écran

        Args:
            x: coordonnée horizontale coin bas-gauche
            y: coordonnée verticale du coin bas-gauche
            w: largeur
            h: hauteur
        """
        was_enabled = (gl.GLboolean * 1)()
        prev_box = (c_int * 4)()
        gl.glGetBooleanv(gl.GL_SCISSOR_TEST, was_enabled)
        gl.glGetIntegerv(gl.GL_SCISSOR_BOX, prev_box)

        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(x, y, w, h)
        try:
            yield
        finally:
            gl.glScissor(*prev_box)
            if not was_enabled[0]:
                gl.glDisable(gl.GL_SCISSOR_TEST)
        
    # ======================================== INTERNALS ========================================
    def _get_temp_fbo(self, fbo: Framebuffer) -> Framebuffer:
        """Renvoie le FrameBuffer temporaire"""
        if self._temp_fbo is None:
            self._temp_fbo = Framebuffer(fbo.width, fbo.height)
        elif self._temp_fbo.width != fbo.width or self._temp_fbo.height != fbo.height:
            self._temp_fbo.resize(fbo.width, fbo.height)
        return self._temp_fbo

# ======================================== CONTEXT ========================================
@dataclass(slots=True)
class _PipelineContext:
    # Binding
    scene: Scene = None
    layer: Layer = None

    # Configuration OpenGl
    gl_viewport: tuple = None
    fbo: Framebuffer = None
    batch: Batch = None
    z_groups: dict[int, Group] = None

    # Espaces internes
    viewport: Viewport = None
    viewport_resolve: tuple = None
    camera: Camera = None
    camera_resolve: tuple = None

    # Ratios
    ppu_x: float = None
    ppu_y: float = None
    ppu: float = None
    
    # Matrices
    projection_matrix: Mat4 = None
    view_matrix: Mat4 = None

    def clear(self) -> None:
        """Nettoie le contexte"""
        for attr in self.__slots__:
            setattr(self, attr, None)