# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import clamped
from ...abc import LightEffect
from ...asset import Color

from dataclasses import dataclass
from numbers import Real
from typing import ClassVar

# ======================================== EFFECT ========================================
@dataclass(slots=True, frozen=True)
class Vignette(LightEffect):
    """Effect lumineux: Vision réduite"""
    radius: Real = 0.6
    color: Color = (0, 0, 0)
    strength: Real = 1.0

    _ID: ClassVar[str] = "vignette"

    def __post_init__(self) -> None:
        """Transtypage et vérifications"""
        setattr(self, "radius", float(self.radius))
        setattr(self, "color", Color(self.color))
        setattr(self, "strength", float(self.strength))

        if __debug__:
            clamped(self.radius)
            clamped(self.strength)