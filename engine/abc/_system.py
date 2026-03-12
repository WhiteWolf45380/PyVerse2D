# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..ecs._update_phase import UpdatePhase

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ecs._world import World

# ======================================== ABSTRACT CLASS ========================================
class System(ABC):
    """Classe abstraite des systèmes"""
    phase: UpdatePhase = UpdatePhase.UPDATE
    exclusive: bool = False
    requires: tuple[type, ...] = ()
    conflicts: tuple[type, ...] = ()

    @abstractmethod
    def update(self, world: World, dt: float): ...