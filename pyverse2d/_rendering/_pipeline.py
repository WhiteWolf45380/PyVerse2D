# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.gl as gl
from pyglet.graphics import Batch, Group
from pyglet.math import Mat4

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..scene import Scene, Viewport, Camera
    from ._window import Window
    from ._screen import Screen

# ======================================== RENDERER ========================================
class Pipeline:
    """
    Pipeline de rendu exploitant OpenGL

    Args:
        window(Window): fenêtre associée
    """
    __slots__ = ("_window", "_scene", "_batch", "_groups")

    def __init__(self, window: Window):
        self._window: Window = window
        self._scene: Scene | None = None
        self._batch: Batch = Batch()
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
        self._scene = scene
        screen = self._window.screen

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

    def flush(self) -> None:
        """Envoie tout le batch au GPU"""
        self._batch.draw()

    def end(self) -> None:
        """Met fin à la connexion avec une scene"""
        self._scene = None