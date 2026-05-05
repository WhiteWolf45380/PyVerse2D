# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import ParticleModifier

import numpy as np
from numbers import Real
import math

# ======================================== MODIFIER ========================================
class Wind(ParticleModifier):
    """Modificateur de vent: force directionnelle avec rafales et turbulence

    Args:
        strength: intensité de base en unités monde/s²
        direction: direction en degrés (0 = droite, 90 = haut)
        gust_strength: amplitude des rafales [0, 1]
        gust_frequency: fréquence des rafales en Hz
        turbulence: variation aléatoire par particule
    """
    __slots__ = (
        "_strength", "_direction", "_gust_strength", "_gust_frequency", "_turbulence",
        "_fx", "_fy", "_time",
    )

    def __init__(
        self,
        strength: Real = 10.0,
        direction: Real = 0.0,
        gust_strength: Real = 0.4,
        gust_frequency: Real = 0.8,
        turbulence: Real = 2.0,
    ):
        # Transtypage
        strength = float(strength)
        direction = float(direction)
        gust_strength = float(gust_strength)
        gust_frequency = float(gust_frequency)
        turbulence = float(turbulence)

        # Attributs publiques
        self._strength = strength
        self._direction = direction
        self._gust_strength = gust_strength
        self._gust_frequency= gust_frequency
        self._turbulence = turbulence

        # Attributs interne
        self._time = 0.0

        # Calcul du vecteur directionnel
        self._update_components()

    # ======================================== PROPERTIES ========================================
    @property
    def strength(self) -> float:
        """Intensité du vent"""
        return self._strength

    @strength.setter
    def strength(self, value: Real) -> None:
        self._strength = float(value)
        self._update_components()

    @property
    def direction(self) -> float:
        """Direction du vent
        
        La direction est *en degrés* dans le sens trigonométrique *(CCW)*.
        Mettre cette propriété à ``0.0`` pour l'orienter vers ``(1, 0)``.
        """
        return self._direction

    @direction.setter
    def direction(self, value: Real) -> None:
        self._direction = float(value)
        self._update_components()

    # ======================================== INTERFACE ========================================
    def apply(self, dt: float, alive: np.ndarray, positions: np.ndarray, velocities: np.ndarray) -> None:
        self._time += dt

        gust = 1.0 + self._gust_strength * math.sin(self._time * self._gust_frequency * math.tau)
        count = int(alive.sum())
        tx = np.random.uniform(-self._turbulence, self._turbulence, count)
        ty = np.random.uniform(-self._turbulence, self._turbulence, count)

        velocities[alive, 0] += (self._fx * gust + tx) * dt
        velocities[alive, 1] += (self._fy * gust + ty) * dt

    # ======================================== INTERNALS ========================================
    def _update_components(self) -> None:
        """Calcul du vecteur directionnel"""
        rad = math.radians(self._direction)
        self._fx = self._strength * math.cos(rad)
        self._fy = self._strength * math.sin(rad)