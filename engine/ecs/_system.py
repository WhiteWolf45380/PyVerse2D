# ======================================== IMPORTS ========================================
from __future__ import annotations

from ._update_phase import UpdatePhase

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._world import World

# ======================================== ABSTRACT CLASS ========================================
class System(ABC):
    """Classe abstraite des systèmes"""
    phase: UpdatePhase = UpdatePhase.UPDATE

    @abstractmethod
    def update(self, world: World, dt: float): ...