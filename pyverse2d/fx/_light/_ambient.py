# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import clamped
from ...abc import LightEffect
from ...asset import Color

from dataclasses import dataclass
from numbers import Real

# ======================================== EFFECT ========================================
@dataclass(slots=True, frozen=True)
class Ambient(LightEffect):
    """Effect lumineux: Ambiance
    
    Args:
        level: niveau de luminosité *[0, 1]*
        color: couleur d'assombrissement
    """
    level: Real = 1.0
    color: Color = (0, 0, 0)

    def __pos_init__(self) -> None:
        """Transtypage et vérifications"""
        setattr(self, "level", float(self.level))
        setattr(self, "color", Color(self.color))

        if __debug__:
            clamped(self.level)