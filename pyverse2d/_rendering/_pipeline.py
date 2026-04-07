# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.gl as gl
from pyglet.graphics import Batch, Group
from pyglet.math import Mat4

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
    group: Group
    z_groups: dict[int, Group]    

# ======================================== PIPELINE ========================================
class Pipeline:
    """
    Pipeline de rendu exploitant OpenGL

    Args:
        window(Window): fenêtre associée
    """
    __slots__ = (
        "_window", "_scene", "_layer",
        "_data",
        "_batch", "_group", "_z_groups",
    )

    def __init__(self, window: Window):
        # Binding
        self._window: Window = window
        self._scene: Scene | None = None
        self._layer: Layer | None = None

        # Cache
        self._data: dict[Scene, SceneRenderData] = {}

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
    def layer(self) -> Layer:
        """Layer en couche de rendu"""
        return self._layer
    
    @property
    def camera(self) -> Camera:
        """Caméra du layer en cours de rendu"""
        return self._layer.camera or self._scene.camera

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
            self._z_groups[z] = Group(order=z)
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
        lx, ly, lw, lh = scene.viewport.resolve(screen.width, screen.height)

        # FrameBuffer
        win_vx, win_vy, win_vw, win_vh = self._window.viewport
        sx = win_vw / screen.width
        sy = win_vh / screen.height

        # Viewport sur le FrameBuffer
        px = int(win_vx + lx * sx)
        py = int(win_vy + ly * sy)
        pw = int(lw * sx)
        ph = int(lh * sy)

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
            layer_groups[layer] = LayerGroups(Group(order=z), {})
        self._group = layer_groups[layer].group
        self._z_groups = layer_groups[layer].z_groups

        # Frustum
        cx, cy, vw, vh, zoom, rotation = self.camera.resolve(self.viewport.width, self.viewport.height)

        # Matrice de projection
        half_w = vw / 2
        half_h = vh / 2
        self._window.native.projection = Mat4.orthogonal_projection(
            left=-half_w,
            right=half_w,
            bottom=-half_h,
            top=half_h,
            z_near=-1.0,
            z_far=1.0,
        )

        # Matrice de vue
        view = Mat4()
        view = view.translate((-cx, -cy, 0))
        if rotation != 0.0:
            view = view.rotate(radians(rotation), (0, 0, 1))
        view = view.rotate(radians(rotation), (0, 0, 1))
        self._window.native.view = view

    def flush(self) -> None:
        """Envoie tout le batch au GPU"""
        self._batch.draw()

    def end(self) -> None:
        """Met fin à la connexion avec une scene"""
        self._scene = None

    # ======================================== UTILITAIRES ========================================
    def world_to_framebuffer(self, x: float, y: float) -> tuple[int, int]:
        """Convertit une coordonnée monde en pixels framebuffer

        Args:
            x (float): coordonnée horizontale monde
            y (float): coordonnée verticale monde
        """
        cam = self.camera  # caméra active (layer ou scene)
        
        # Taille logique de la scène
        lx, ly, lw, lh = self.viewport.resolve(self.screen.width, self.screen.height)

        # Déplacement relatif au centre caméra
        px_logic = (x - cam.x) * cam.zoom + lw / 2
        py_logic = (y - cam.y) * cam.zoom + lh / 2

        # Projection viewport → framebuffer
        win_vx, win_vy, win_vw, win_vh = self._window.viewport
        sx = win_vw / self.screen.width
        sy = win_vh / self.screen.height

        px_fb = int(win_vx + lx * sx + px_logic * sx)
        py_fb = int(win_vy + ly * sy + py_logic * sy)

        return px_fb, py_fb


    @contextmanager
    def scissor(self, wx: float, wy: float, ww: float, wh: float):
        """Context manager appliquant un scissor test en coordonnées monde

        Args:
            wx (float): x monde du coin bas-gauche
            wy (float): y monde du coin bas-gauche
            ww (float): largeur monde
            wh (float): hauteur monde
        """
        cam = self.camera

        # Coin bas-gauche en pixels framebuffer
        x0, y0 = self.world_to_framebuffer(wx, wy)

        # Taille en pixels framebuffer
        lx, ly, lw, lh = self.viewport.resolve(self.screen.width, self.screen.height)
        win_vx, win_vy, win_vw, win_vh = self._window.viewport
        sx = win_vw / self.screen.width
        sy = win_vh / self.screen.height

        w = int(ww * cam.zoom * sx)
        h = int(wh * cam.zoom * sy)

        # Sauvegarde état précédent
        was_enabled = (gl.GLboolean * 1)()
        prev_box = (c_int * 4)()
        gl.glGetBooleanv(gl.GL_SCISSOR_TEST, was_enabled)
        gl.glGetIntegerv(gl.GL_SCISSOR_BOX, prev_box)

        # Activation scissor
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(x0, y0, w, h)
        try:
            yield
        finally:
            # Restauration
            gl.glScissor(*prev_box)
            if not was_enabled[0]:
                gl.glDisable(gl.GL_SCISSOR_TEST)