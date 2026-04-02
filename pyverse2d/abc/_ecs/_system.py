# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._flag import UpdatePhase

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...world import World

# ======================================== ABSTRACT CLASS ========================================
class System(ABC):
    """Classe abstraite des systèmes"""
    __slots__ = ()
    phase: UpdatePhase = UpdatePhase.UPDATE
    exclusive: bool = False
    requires: tuple[type, ...] = ()
    conflicts: tuple[type, ...] = ()

    @abstractmethod
    def update(self, world: World, dt: float): ...