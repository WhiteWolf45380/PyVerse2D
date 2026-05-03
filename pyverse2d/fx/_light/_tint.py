# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import clamped
from ...abc import LightEffect
from ...asset import Color

from dataclasses import dataclass
from numbers import Real

# ======================================== EFFECT ========================================
@dataclass(slots=True, frozen=True)
class Tint(LightEffect):
    """Effect lumineux: Teinte
    
    Args:
        color: couleur d'accentuation
        strength: force d'accentuation
    """
    color: Color
    strength: Real = 1.0

    def __pos_init__(self) -> None:
        """Transtypage et vérifications"""
        setattr(self, "color", Color(self.color))
        setattr(self, "strength", float(self.strength))

        if __debug__:
            clamped(self.strength)