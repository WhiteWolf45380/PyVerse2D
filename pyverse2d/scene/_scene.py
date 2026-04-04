# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from .._rendering._pipeline import Pipeline
from .._flag import StackMode, SceneState, CameraMode
from ..math import Point
from ..abc import Layer

from ._camera import Camera
from ._viewport import Viewport

from typing import Callable
import bisect

# ======================================== SCENE ========================================
class Scene:
    """
    Orchestre un ensemble de layers ordonnés par z_order

    Args:
        camera(Camera): caméra de la scene
        viewport(Viewport): viewport de la scene
        stack_mode(StackMode): mode d'empilement par rapport aux autres scenes
    """
    def __init__(self, camera: Camera = None, viewport: Viewport = None, stack_mode: StackMode = StackMode.OVERLAY):
        self._layers: list[Layer] = []
        self._z_orders: list[int] = []
        self._camera: Camera = expect(camera, Camera) if camera else Camera(Point(0, 0))
        self._viewport: Viewport = expect(viewport, Viewport) if viewport else Viewport()
        self._stack_mode: StackMode = expect(stack_mode, StackMode)
        self._state: SceneState = SceneState.SLEEPING
        self._update_callbacks: list[Callable[[float], None]] = []
        self._draw_callbacks: list[Callable[[Pipeline], None]] = []

    # ======================================== GETTERS ========================================
    @property
    def camera(self) -> Camera:
        """Renvoie la caméra de la scene"""
        return self._camera

    @property
    def viewport(self) -> Viewport:
        """Renvoie le viewport de la scene"""
        return self._viewport

    @property
    def stack_mode(self) -> StackMode:
        """Renvoie le mode d'empilement"""
        return self._stack_mode

    @property
    def state(self) -> SceneState:
        """Renvoie l'état de la scène"""
        return self._state

    # ======================================== SETTERS ========================================
    def set_camera(self, camera: Camera):
        """
        Fixe la caméra de la scene

        Args:
            camera(Camera): caméra à utiliser
        """
        self._camera = expect(camera, Camera)

    def set_viewport(self, viewport: Viewport):
        """
        Fixe le viewport de la scene

        Args:
            viewport(Viewport): viewport à utiliser
        """
        self._viewport = expect(viewport, Viewport)

    def set_stack_mode(self, stack_mode: StackMode):
        """
        Fixe le mode d'empilement

        Args:
            stackmode(StackMode): mode d'empilement de la scène
        """
        self._stack_mode = expect(stack_mode, StackMode)

    def set_state(self, state: SceneState):
        """
        Fixe l'état de la scène

        Args:
            state(SceneState): état de la scène
        """
        self._state = expect(state, SceneState)

    # ======================================== LAYERS ========================================
    def add_layer(self, layer: Layer, z: int = 0) -> Scene:
        """
        Ajoute un layer à la scene

        Args:
            layer(Layer): layer à ajouter
            z(int): ordre de rendu
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
            layer(Layer): layer à supprimer
        """
        i = self._layers.index(expect(layer, Layer))
        self._layers.pop(i)
        self._z_orders.pop(i)
        return self

    # ======================================== CALLBACKS ========================================
    def on_update(self, fn: Callable[[float], None]) -> Callable[[float], None]:
        """
        Enregistre un callback appelé à chaque update

        Args:
            fn(Callable[[float], None]): fonction prenant dt en paramètre
        """
        self._update_callbacks.append(fn)
        return fn

    def on_draw(self, fn: Callable[[Pipeline], None]) -> Callable[[Pipeline], None]:
        """
        Enregistre un callback appelé à chaque draw, après les layers

        Args:
            fn(Callable[[Pipeline], None]): fonction prenant pipeline en paramètre
        """
        self._draw_callbacks.append(fn)
        return fn

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

    def preload(self):
        """Force le build de tous les layers qui l'implémentent, avant la boucle principale"""
        for layer in self._layers:
            if hasattr(layer, "preload"):
                layer.preload()

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        """
        Met à jour tous les layers puis appelle les callbacks utilisateur

        Args:
            dt(float): delta time
        """
        self.camera.update(dt)
        for layer in reversed(self._layers):
            if not layer.is_active():
                continue
            layer.update(dt)
        for fn in self._update_callbacks:
            fn(dt)

    def draw(self, pipeline: Pipeline):
        """
        Dessine tous les layers dans l'ordre de z_order, puis appelle les callbacks utilisateur

        Args:
            pipeline(Pipeline): pipeline à utiliser pour le rendu
        """
        pipeline.begin(self)
        camera_view = self.camera.view_matrix()
        camera_zoom = self.camera.zoom_matrix()
        for layer in self._layers:
            if not layer.is_visible():
                continue
            pipeline.layer(layer)

            if layer.camera_mode is CameraMode.WORLD:
                pipeline.set_view(camera_view)
            elif layer.camera_mode is CameraMode.ZOOM:
                pipeline.set_view(camera_zoom)
            else:
                pipeline.set_view(None)

            layer.draw(pipeline)
            pipeline.flush()

        for fn in self._draw_callbacks:
            fn(pipeline)

        pipeline.end()