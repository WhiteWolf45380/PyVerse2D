# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet
import pyglet.gl as gl
from pyglet.graphics import Batch, Group

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..scene._scene import Scene

# ======================================== RENDERER ========================================
class Renderer:
    """
    Pipeline de rendu exploitant OpenGL

    Args:
        virtual_width (int): largeur de l'espace virtuel
        virtual_height (int): hauteur de l'espace virtuel
    """

    def __init__(self, virtual_width: int, virtual_height: int):
        self._virtual_width: int = int(virtual_width)
        self._virtual_height: int = int(virtual_height)
        self._batch: Batch = Batch()
        self._groups: dict[int, Group] = {}

    # ======================================== GETTERS ========================================
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

    # ======================================== PIPELINE ========================================
    def begin(self, scene: Scene):
        """
        Configure le contexte de rendu depuis la scene active.
        Applique la caméra et le viewport.

        Args:
            scene (Scene): scene à rendre
        """
        x, y, w, h = scene.viewport.resolve(self._virtual_width, self._virtual_height)
        gl.glViewport(int(x), int(y), int(w), int(h))
        pyglet.get_default_window().view = scene.camera.view_matrix(self._virtual_width, self._virtual_height)

    def flush(self):
        """Envoie tout le batch au GPU"""
        self._batch.draw()