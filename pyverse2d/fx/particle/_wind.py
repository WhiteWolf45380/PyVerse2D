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
        x: force de base horizontale
        y: force de base verticale
        gust_strength: amplitude des rafales [0, 1]
        gust_frequency: fréquence des rafales en Hz
        turbulence: variation aléatoire par particule
    """
    __slots__ = ("_fx", "_fy", "_gust_strength", "_gust_frequency", "_turbulence", "_time")

    def __init__(
        self,
        x: Real = 10.0,
        y: Real = 0.0,
        gust_strength: Real = 0.4,
        gust_frequency: Real = 0.8,
        turbulence: Real = 2.0,
    ):
        self._fx = float(x)
        self._fy = float(y)
        self._gust_strength = float(gust_strength)
        self._gust_frequency = float(gust_frequency)
        self._turbulence = float(turbulence)
        self._time = 0.0

    def apply(self, dt: float, alive: np.ndarray, positions: np.ndarray, velocities: np.ndarray) -> None:
        self._time += dt

        # Rafale globale
        gust = 1.0 + self._gust_strength * math.sin(self._time * self._gust_frequency * math.tau)

        # Turbulence
        count = int(alive.sum())
        tx = np.random.uniform(-self._turbulence, self._turbulence, count)
        ty = np.random.uniform(-self._turbulence, self._turbulence, count)

        velocities[alive, 0] += (self._fx * gust + tx) * dt
        velocities[alive, 1] += (self._fy * gust + ty) * dt