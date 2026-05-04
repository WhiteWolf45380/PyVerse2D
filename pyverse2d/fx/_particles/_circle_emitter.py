# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import ParticleEmitter
from ...math import Point

from ._particle import Particle

import numpy as np
import math
from numbers import Real

# ======================================== EMITTER ========================================
class CircleEmitter(ParticleEmitter):
    """Emetteur circulaire: émission depuis le périmètre ou l'intérieur d'un cercle

    Args:
        position: position du centre
        radius: rayon du cercle en unités monde
        fill: True pour émettre depuis l'intérieur, False pour le périmètre uniquement
        particle: pattern de particule
        max_particles: nombre maximum de particules simultanées
        rate: taux d'émission en particules/seconde
        outward: True pour émettre vers l'extérieur, False pour direction aléatoire
    """
    __slots__ = ("_radius", "_fill", "_outward")

    def __init__(
        self,
        position: Point = (0.0, 0.0),
        *,
        radius: Real = 1.0,
        fill: bool = False,
        outward: bool = True,
        particle: Particle = None,
        max_particles: int = 500,
        rate: Real = 0.0,
    ):
        # Transtypage
        radius = float(radius)
        fill = bool(fill)
        outward = bool(outward)

        # Initialisation de l'émetteur
        super().__init__(position, particle=particle, max_particles=max_particles, rate=rate)

        # Attributs publiques
        self._radius = radius
        self._fill = fill
        self._outward = outward

    # ======================================== PROPERTIES ========================================

    # ======================================== INTERNALS ========================================
    def _emit(self, count: int) -> tuple[np.ndarray, np.ndarray]:
        p = self._particle
        angles = np.random.uniform(0.0, 2.0 * math.pi, count)

        if self._fill:
            r = self._radius * np.sqrt(np.random.uniform(0.0, 1.0, count))
        else:
            r = np.full(count, self._radius)

        ox = r * np.cos(angles)
        oy = r * np.sin(angles)

        positions = np.stack([self._position.x + ox, self._position.y + oy], axis=1).astype(np.float32)

        speeds = np.random.uniform(p.speed[0], p.speed[1], count)
        if self._outward:
            norms = np.maximum(np.sqrt(ox**2 + oy**2), 1e-6)
            vx, vy = (ox / norms) * speeds, (oy / norms) * speeds
        else:
            va = np.random.uniform(0.0, 2.0 * math.pi, count)
            vx, vy = speeds * np.cos(va), speeds * np.sin(va)

        velocities = np.stack([vx, vy], axis=1).astype(np.float32)
        return positions, velocities