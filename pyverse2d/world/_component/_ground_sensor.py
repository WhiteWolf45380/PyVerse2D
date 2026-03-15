# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Component

from math import cos, radians

# ======================================== COMPONENT ========================================
class GroundSensor(Component):
    """
    Composant détectant si l'entité est au sol

    Args:
        threshold(float): composante Y minimale de la normale pour considérer sol (0 à 1)
        max_climb_angle(float): angle maximal en degrés que l'entité peut gravir (0 à 90)
    """
    __slots__ = ("grounded", "threshold", "max_climb_angle", "_climb_ny_min")
    requires = ("Transform", "Collider")

    def __init__(self, threshold: float = 0.65, max_climb_angle: float = 90.0):
        self.grounded: bool = False
        self.threshold: float = float(threshold)
        self.max_climb_angle: float = float(max_climb_angle)
        self._climb_ny_min: float = cos(radians(max_climb_angle))

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return f"GroundSensor(grounded={self.grounded}, threshold={self.threshold}, max_climb_angle={self.max_climb_angle})"

    def __iter__(self):
        return iter((self.grounded, self.threshold, self.max_climb_angle))

    def __hash__(self):
        return hash((self.threshold, self.max_climb_angle))

    def __eq__(self, other):
        return isinstance(other, GroundSensor) and self.threshold == other.threshold and self.max_climb_angle == other.max_climb_angle