# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import over
from ...abc import Tween
from ...math import Point
from ...math.easing import EasingFunc

from numbers import Real

# ======================================== TWEEN ========================================
class ScaleTween(Tween):
    """Interpolation de la taille"""
    __slots__ = ()

    def __init__(self, target_value: Real, duration: Real, easing: EasingFunc):
        target_value = float(target_value)
        if __debug__:
            over(target_value, 0.0, include=False)

        super().__init__("scale", target_value, duration, easing)