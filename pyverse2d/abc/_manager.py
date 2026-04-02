# ======================================== IMPORTS ========================================
from __future__ import annotations

from abc import ABC, abstractmethod

# ======================================== ABSTRACT CLASS ========================================
class Manager(ABC):
    """Classe abstraite des managers"""
    __slots__ = ()

    @abstractmethod
    def __init__(self, context_manager): ...

    @abstractmethod
    def update(self, dt: float) -> None: ...