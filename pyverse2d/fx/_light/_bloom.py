# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import not_null, clamped, positive
from ...abc import LightEffect

from dataclasses import dataclass
from numbers import Real

# ======================================== EFFECT ========================================
@dataclass(slots=True, frozen=True)
class Bloom(LightEffect):
    """Effect lumineux: Saignement
    
    Args:   
        radius: rayon du saignement
        treshold: seuil minimum d'intesité lumineuse pour saignement
        intensity: intensité du saignement
    """
    radius: Real = 0.0
    treshold: Real = 0.7
    intensity: Real = 1.0

    def __pos_init__(self) -> None:
        """Transtypage et vérifications"""
        setattr(self, "radius", abs(float(self.radius)))
        setattr(self, "treshold", float(self.treshold))
        setattr(self, "intensity", float(self.intensity))

        if __debug__:
            not_null(self.radius)
            clamped(self.treshold)
            positive(self.intensity)