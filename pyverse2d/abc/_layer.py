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
    def __init__(self, camera_mode: CameraMode = CameraMode.WORLD):
        self._camera_mode: CameraMode = camera_mode

    @abstractmethod
    def on_start(self): ...

    @abstractmethod
    def on_stop(self): ...

    @abstractmethod
    def update(self, dt: float): ...

    @abstractmethod
    def draw(self, renderer: Renderer): ...