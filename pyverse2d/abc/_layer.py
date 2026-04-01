# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from .._flag import CameraMode

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._rendering import Renderer

# ======================================== ABSTRACT CLASS ========================================
class Layer(ABC):
    """Classe abstraite des layers"""
    __slots__ = ("_camera_mode", "_active", "_visible")

    def __init__(self, camera_mode: CameraMode = CameraMode.WORLD):
        self._camera_mode: CameraMode = expect(camera_mode, CameraMode)
        self._active: bool = True
        self._visible: bool = True

    # ======================================== PROPERTIES ========================================
    @property
    def camera_mode(self) -> CameraMode:
        """Mode de caméra

        Cette propriété modifie le comportement de la caméra et doit être un ``CameraMode``
        """
        return self._camera_mode
    
    @camera_mode.setter
    def camera_mode(self, value: CameraMode) -> None:
        self._camera_mode = expect
    
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