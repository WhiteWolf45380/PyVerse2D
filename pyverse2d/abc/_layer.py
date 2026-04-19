# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._managers import CoordinatesManager
    from .._rendering import Pipeline
    from ..scene import Camera

# ======================================== ABSTRACT CLASS ========================================
class Layer(ABC):
    """Classe abstraite des layers
    
    Args:
        camera: caméra locale
    """
    __slots__ = ("_camera", "_active", "_visible")

    _IS_FX: bool = False

    def __init__(self, camera: Camera = None):
        from .._rendering import Camera
        self._camera: Camera = expect(camera, (Camera, None))
        self._active: bool = True
        self._visible: bool = True

    # ======================================== PROPERTIES ========================================
    @property
    def camera(self) -> Camera:
        """Caméra clocale

        Si la caméra locale n'est pas définie, celle de la scène est utilisée.
        """
        return self._camera
    
    @camera.setter
    def camera(self, value: Camera) -> None:
        from .._rendering import Camera
        self._camera = expect(value, (Camera, None))

    # ======================================== PREDICATES ========================================
    def is_fx(self) -> bool:
        """Vérifie que le layer soit un layer d'effets  post-process"""
        return self._IS_FX
    
    # ======================================== ACTIVITY ========================================
    def is_active(self) -> bool:
        """Vérifie l'activité"""
        return self._active
    
    def activate(self) -> None:
        """Active le layer"""
        self._active = True

    def deactivate(self) -> None:
        """Désactive le layer"""
        self._active = False
    
    def switch_activity(self) -> None:
        """Bascule l'activité"""
        self._active = not self._active

    # ======================================== VISIBILITY ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._visible
    
    def show(self) -> None:
        """Rend visible le layer"""
        self._visible = True

    def hide(self) -> None:
        """Rend invisible le layer"""
        self._visible = False

    def switch_visibility(self) -> None:
        """Bascule la visibilité"""
        self._visible = not self._visible

    # ======================================== HOOKS ========================================
    @abstractmethod
    def on_start(self): ...

    @abstractmethod
    def on_stop(self): ...

    # ======================================== LIFE CYCLE ========================================
    @abstractmethod
    def _preload(self): ...

    @abstractmethod
    def _update(self, dt: float) -> None: ...

    def update(self, dt: float):
        """Actualisation"""
        if self._camera is not None:
            self._camera.update(dt)
            self._apply_context()
        self._update(dt)

    @abstractmethod
    def _draw(self, pipeline: Pipeline) -> None: ...

    def draw(self, pipeline: Pipeline) -> None:
        """Affichage global"""
        if self._camera is not None:
            self._apply_context()
        self._draw(pipeline)

    # ======================================== INTERNALS ========================================
    def _apply_context(self) -> None:
        """Applique le contexte du layer"""
        from pyverse2d import coordinates
        coordinates.bind_temporary_camera(self._camera)