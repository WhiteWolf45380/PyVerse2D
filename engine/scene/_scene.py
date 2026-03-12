# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from ..math import Point
from .._rendering import Camera, Viewport, Renderer
from ..abc import Layer

import bisect

# ======================================== SCENE ========================================
class Scene:
    """
    Orchestre un ensemble de layers ordonnés par z_order
    """
    def __init__(self, camera: Camera = None, viewport: Viewport = None):
        self._layers: list[Layer] = []
        self._z_orders: list[int] = []
        self._camera: Camera = expect(camera, Camera) if camera else Camera(Point(0, 0))
        self._viewport: Viewport = expect(viewport, Viewport) if viewport else Viewport()

    # ======================================== GETTERS ========================================
    @property
    def camera(self) -> Camera:
        """Renvoie la caméra de la scene"""
        return self._camera

    @property
    def viewport(self) -> Viewport:
        """Renvoie le viewport de la scene"""
        return self._viewport

    # ======================================== SETTERS ========================================
    def set_camera(self, camera: Camera):
        """
        Fixe la caméra de la scene

        Args:
            camera (Camera): caméra à utiliser
        """
        self._camera = expect(camera, Camera)

    def set_viewport(self, viewport: Viewport):
        """
        Fixe le viewport de la scene

        Args:
            viewport (Viewport): viewport à utiliser
        """
        self._viewport = expect(viewport, Viewport)

    # ======================================== LAYERS ========================================
    def add_layer(self, layer: Layer, z: int = 0) -> Scene:
        """
        Ajoute un layer à la scene

        Args:
            layer (Layer): layer à ajouter
            z (int): ordre de rendu
        """
        expect(layer, Layer)
        i = bisect.bisect_right(self._z_orders, z)
        self._z_orders.insert(i, z)
        self._layers.insert(i, layer)
        return self

    def remove_layer(self, layer: Layer) -> Scene:
        """
        Supprime un layer de la scene

        Args:
            layer (Layer): layer à supprimer
        """
        i = self._layers.index(expect(layer, Layer))
        self._layers.pop(i)
        self._z_orders.pop(i)
        return self

    # ======================================== CYCLE DE VIE ========================================
    def on_start(self):
        """Démarre tous les layers"""
        for layer in self._layers:
            layer.on_start()

    def on_stop(self):
        """Arrête tous les layers"""
        for layer in self._layers:
            layer.on_stop()

    def suspend(self):
        """Suspend tous les layers"""
        for layer in self._layers:
            layer.on_stop()

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        """
        Met à jour tous les layers

        Args:
            dt (float): delta time
        """
        for layer in self._layers:
            layer.update(dt)

    def draw(self, renderer: Renderer):
        """
        Dessine tous les layers dans l'ordre de z_order

        Args:
            renderer: renderer à utiliser pour le rendu
        """
        renderer.begin(self)
        for layer in self._layers:
            layer.draw(renderer)
        renderer.flush()