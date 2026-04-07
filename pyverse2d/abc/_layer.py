# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._rendering import Renderer
    from ..scene import Camera

# ======================================== ABSTRACT CLASS ========================================
class Layer(ABC):
    """Classe abstraite des layers
    
    Args:
        camera: caméra locale
    """
    __slots__ = ("_camera", "_active", "_visible")

    def __init__(self, camera: Camera = None):
        from ..scene import Camera
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
        from ..scene import Camera
        self._camera = expect(value, (Camera, None))
    
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
    def update(self, dt: float): ...

    @abstractmethod
    def draw(self, renderer: Renderer): ...