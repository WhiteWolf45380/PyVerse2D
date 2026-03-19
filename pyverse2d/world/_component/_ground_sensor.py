# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, clamped
from ...abc import Component
from ...math import Vector

from math import cos, radians
from numbers import Real
from typing import Iterator

# ======================================== COMPONENT ========================================
class GroundSensor(Component):
    """
    Composant détectant si l'entité est au sol

    Args:
        threshold(float): composante Y minimale de la normale pour considérer sol (0 à 1)
        stability_angle(float): angle maximal en degrés auquel l'entité peut ne pas glisser (0 à 75)
        ground_damping(float): amortissement horizontal appliqué uniquement au sol
        coyote_time(float): durée de grâce en secondes après perte du sol
    """
    __slots__ = ("_threshold", "_stability_angle", "_ground_damping", "_coyote_time", "_grounded", "_coyote_elapsed", "_climb_ny_min", "_ground_normal")
    requires = ("Transform", "Collider")

    def __init__(self, threshold: Real = 0.65, stability_angle: Real = 90.0, ground_damping: Real = 0.0, coyote_time: Real = 0.08):
        self._threshold: float = float(clamped(expect(threshold, Real)))
        self._stability_angle: float = abs(float(expect(stability_angle, Real)))
        self._ground_damping: float = float(max(0.0, expect(ground_damping, Real)))
        self._coyote_time: float = float(max(0.0, expect(coyote_time, Real)))
        self._grounded: bool = False
        self._coyote_elapsed: float = 0.0
        self._compute()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"GroundSensor(grounded={self._grounded}, threshold={self._threshold}, stability_angle={self._stability_angle}, ground_damping={self._ground_damping}, coyote_time={self._coyote_time})"

    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter((self._grounded, self._threshold, self._stability_angle, self._ground_damping, self._coyote_time))

    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash((self._threshold, self._stability_angle, self._ground_damping, self._coyote_time))

    def __eq__(self, other: GroundSensor) -> bool:
        """Vérifie la correspondance des deux composants"""
        if isinstance(other, GroundSensor):
            return (
                self._threshold == other._threshold
                and self._stability_angle == other._stability_angle
                and self._ground_damping == other._ground_damping
                and self._coyote_time == other._coyote_time
            )
        return False
    
    # ======================================== GETTERS ========================================
    @property
    def threshold(self) -> float:
        """Renvoie le seuil de support"""
        return self._threshold
    
    @property
    def stability_angle(self) -> float:
        """Renvoie l'angle maximale grimpable"""
        return self._stability_angle
    
    @property
    def ground_damping(self) -> float:
        """Renvoie l'amortissement horizontal au sol"""
        return self._ground_damping

    @property
    def coyote_time(self) -> float:
        """Renvoie la durée de grâce après perte du sol"""
        return self._coyote_time
    
    @property
    def ground_normal(self) -> Vector | None:
        """Renvoie la normal de collision au sol"""
        return self._ground_normal

    # ======================================== SETTERS ========================================
    @threshold.setter
    def threshold(self, value: Real):
        """Fixe le seuil de support"""
        self._threshold = float(clamped(expect(value, Real)))

    @stability_angle.setter
    def stability_angle(self, value: Real):
        """Fixe l'angle maximal grimpable"""
        self._stability_angle = abs(float(expect(value, Real)))
        self._compute()

    @ground_damping.setter
    def ground_damping(self, value: Real):
        """Fixe l'amortissement horizontal au sol"""
        self._ground_damping = float(max(0.0, expect(value, Real)))

    @coyote_time.setter
    def coyote_time(self, value: Real):
        """Fixe la durée de grâce après perte du sol"""
        self._coyote_time = float(max(0.0, expect(value, Real)))

    # ======================================== PREDICATES ========================================
    def is_grounded(self) -> bool:
        """Vérifie que l'entité soit au sol"""
        return self._grounded

    # ======================================== INTERNALS ========================================
    def _compute(self) -> None:
        """Précalcul"""
        self._stability_ny_min: float = cos(radians(self._stability_angle))
        self._ground_normal: Vector | None = None