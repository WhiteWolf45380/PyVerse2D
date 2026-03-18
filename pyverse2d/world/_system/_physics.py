# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._flag import UpdatePhase
from ...abc import System
from .._world import World
from .._component import Transform, RigidBody, GroundSensor

from math import exp

# ======================================== SYSTEM ========================================
class PhysicsSystem(System):
    """Système intégrant la physique des corps dynamiques"""
    __slots__ = ("_pixels_per_meter")
    phase = UpdatePhase.LATE
    exclusive = True

    def __init__(self, pixels_per_meter: float = 100.0):
        self._pixels_per_meter: float = float(pixels_per_meter)

    # ======================================== GETTERS ========================================
    @property
    def pixels_per_meter(self) -> float:
        """Renvoie l'échelle px/m"""
        return self._pixels_per_meter

    # ======================================== SETTERS ========================================
    @pixels_per_meter.setter
    def pixels_per_meter(self, value: float):
        """Fixe l'échelle px/m"""
        self._pixels_per_meter = float(value)

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Intègre la physique de tous les corps dynamiques actifs

        Args:
            world(World): monde à mettre à jour
            dt(float): delta time
        """
        ppm = self._pixels_per_meter

        for entity in world.query(RigidBody, Transform):
            rb: RigidBody = entity.get(RigidBody)
            tr: Transform = entity.get(Transform)

            if rb.is_static() or rb.is_sleeping():
                continue

            # Sauvegarde de la position pour l'anti-tunneling
            rb._save_prev(tr.x, tr.y)

            # Intégration semi-implicite d'Euler
            rb.velocity = rb.velocity + rb.acceleration * dt

            # Résistance de l'air sur X et Y
            rb._apply_damping(dt)

            # Amortissement horizontal au sol uniquement
            if entity.has(GroundSensor):
                gs: GroundSensor = entity.get(GroundSensor)
                if gs._grounded and gs._ground_damping > 0.0:
                    factor = exp(-gs._ground_damping * dt)
                    rb.velocity = rb.velocity.__class__(rb.velocity.x * factor, rb.velocity.y)

            # Intégration de la position
            tr.x += rb.velocity.x * dt * ppm
            tr.y += rb.velocity.y * dt * ppm

            # Reset accélération et vérification du sleep
            rb.reset_acceleration()
            rb._tick_sleep(dt)