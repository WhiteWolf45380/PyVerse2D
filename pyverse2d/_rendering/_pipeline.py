# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.gl as gl
from pyglet.graphics import Batch, Group
from pyglet.math import Mat4

from typing import TYPE_CHECKING
from contextlib import contextmanager
from ctypes import c_int

if TYPE_CHECKING:
    from ..scene import Scene, Layer, Viewport, Camera
    from ._window import Window
    from ._screen import Screen

# ======================================== RENDERER ========================================
class Pipeline:
    """
    Pipeline de rendu exploitant OpenGL

    Args:
        window(Window): fenêtre associée
    """
    __slots__ = ("_window", "_scene", "_all_batches", "_batch", "_groups")

    def __init__(self, window: Window):
        self._window: Window = window
        self._scene: Scene | None = None
        self._all_batches: dict[Scene, dict[Layer, Batch]] = {}
        self._batch: Batch = None
        self._groups: dict[int, Group] = {}

    # ======================================== GETTERS ========================================
    @property
    def window(self) -> Window:
        """Renvoie la fenêtre OS assignée"""
        return self._window
    
    @property
    def screen(self) -> Screen:
        """Renvoie l'espace logique de référence"""
        return self._window.screen
    
    @property
    def scene(self) -> Scene:
        """Renvoie la scene en cours de rendu"""
        return self._scene
    
    @property
    def viewport(self) -> Viewport:
        """Renvoie le viewport de la scene en cours de rendu"""
        return self._scene.viewport
    
    @property
    def camera(self) -> Camera:
        """Renvoie la caméra de la scene en cours de rendu"""
        return self._scene.camera
    
    @property
    def scene_batches(self) -> dict[str, Batch]:
        """Renvoie les batches de la scene courante"""
        if not self._scene:
            return {}
        return self._all_batches.get(self._scene)

    @property
    def batch(self) -> Batch:
        """Renvoie le batch global"""
        return self._batch
    
    def get_group(self, z: int = 0) -> Group:
        """
        Renvoie le Group associé au z_order, le crée si inexistant

        Args:
            z (int): z_order du group
        """
        if z not in self._groups:
            self._groups[z] = Group(order=z)
        return self._groups[z]
    
    # ======================================== SETTERS ========================================
    def set_view(self, matrix: Mat4 = None) -> None:
        """
        Applique une matrice de vue — identité si None (layers fixed)

        Args:
            matrix(Mat4): matrice de vue, ou None pour annuler la caméra
        """
        self._window.native.view = matrix if matrix is not None else Mat4()

    # ======================================== PIPELINE ========================================
    def begin(self, scene: Scene) -> None:
        """
        Configure le contexte de rendu depuis une scene

        Args:
            scene(Scene): scène active à rendre
        """
        screen = self._window.screen

        # Etablissement de la connexion à la scene
        self._scene = scene
        if scene not in self._all_batches:
            self._all_batches[scene] = {}

        # NDC
        lx, ly, lw, lh = scene.viewport.resolve(screen.width, screen.height)

        # FrameBuffer
        win_vx, win_vy, win_vw, win_vh = self._window.viewport
        sx = win_vw / screen.width
        sy = win_vh / screen.height

        px = int(win_vx + lx * sx)
        py = int(win_vy + ly * sy)
        pw = int(lw * sx)
        ph = int(lh * sy)

        gl.glViewport(px, py, pw, ph)

    def layer(self, current: Layer) -> None:
        """Fixe la layer courant"""
        if current not in self.scene_batches:
            self.scene_batches[current] = Batch()
        self._batch = self.scene_batches[current]

    def flush(self) -> None:
        """Envoie tout le batch au GPU"""
        self._batch.draw()

    def end(self) -> None:
        """Met fin à la connexion avec une scene"""
        self._scene = None

    # ======================================== UTILITAIRES ========================================
    def world_to_framebuffer(self, x: float, y: float) -> tuple[int, int]:
        """
        Convertit une coordonnée monde en pixels framebuffer

        Args:
            x(float): coordonnée horizontale monde
            y(float): coordonnée verticale monde
        """
        cam = self._scene.camera
        screen = self._window.screen
        win_vx, win_vy, win_vw, win_vh = self._window.viewport

        sx = win_vw / screen.width
        sy = win_vh / screen.height

        lx = (x - cam.x) * cam.zoom + screen.half_width
        ly = (y - cam.y) * cam.zoom + screen.half_height

        return int(win_vx + lx * sx), int(win_vy + ly * sy)
    
    @contextmanager
    def scissor(self, wx: float, wy: float, ww: float, wh: float):
        """
        Context manager appliquant un scissor test en coordonnées monde

        Args:
            wx(float): x monde du coin bas-gauche
            wy(float): y monde du coin bas-gauche
            ww(float): largeur monde
            wh(float): hauteur monde
        """
        x0, y0 = self.world_to_framebuffer(wx, wy)
        sx, sy = self.window.framebuffer_scale
        cam = self._scene.camera
        w = int(ww * cam.zoom * sx)
        h = int(wh * cam.zoom * sy)

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