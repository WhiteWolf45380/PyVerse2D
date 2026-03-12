# ======================================== IMPORTS ========================================
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._rendering import Renderer

# ======================================== ABSTRACT CLASS ========================================
class Layer(ABC):
    """Classe abstraite des layers"""
    @abstractmethod
    def on_start(self): ...

    @abstractmethod
    def on_stop(self): ...

    @abstractmethod
    def update(self, dt: float): ...

    @abstractmethod
    def draw(self, renderer: Renderer): ...