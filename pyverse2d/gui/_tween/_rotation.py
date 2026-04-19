# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Tween
from ...math import Point
from ...math.easing import EasingFunc

from numbers import Real

# ======================================== TWEEN ========================================
class RotationTween(Tween):
    """Interpolation rotationnelle"""
    __slots__ = ()

    def __init__(self, target_value: Real, duration: Real, easing: EasingFunc):
        target_value = float(target_value)
        
        super().__init__("rotation", target_value, duration, easing)