# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Component

# ======================================== COMPONENT ========================================
class GroundSensor(Component):
    """
    Composant détectant si l'entité est au sol

    Args:
        threshold(float): composante Y minimale de la normale pour considérer sol (0 à 1)
    """
    __slots__ = ("grounded", "threshold")
    requires = ("Transform", "Collider")

    def __init__(self, threshold: float = 0.65):
        self.grounded: bool = False
        self.threshold: float = float(threshold)

    def __repr__(self) -> str:
        return f"GroundSensor(grounded={self.grounded}, threshold={self.threshold})"

    def __iter__(self):
        return iter((self.grounded, self.threshold))

    def __hash__(self):
        return hash((self.grounded, self.threshold))

    def __eq__(self, other):
        return isinstance(other, GroundSensor) and self.threshold == other.threshold