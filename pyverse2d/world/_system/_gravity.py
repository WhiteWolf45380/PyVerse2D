# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._flag import UpdatePhase
from ...abc import System
from ...math import Vector

from .._world import World
from .._component import Transform, RigidBody

from numbers import Real

# ======================================== SYSTEM ========================================
class GravitySystem(System):
    """
    Système appliquant la force gravitationnelle sur les corps dynamiques

    Args:
        gravity(Real): force gravitationnelle en N/kg
    """
    __slots__ = ("_gravity")
    phase = UpdatePhase.EARLY
    exclusive = False
    requires = ("PhysicsSystem")

    def __init__(self, gravity: Real = 9.8):
        self._gravity: float = float(gravity)

    # ======================================== GETTERS ========================================
    @property
    def gravity(self) -> float:
        """Renvoie la force gravitationnelle en N/kg"""
        return self._gravity

    # ======================================== SETTERS ========================================
    @gravity.setter
    def gravity(self, value: Real):
        """Fixe la force gravitationnelle en N/kg"""
        self._gravity = float(value)

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Applique la force gravitationnelle sur tous les corps dynamiques

        Args:
            world(World): monde à mettre à jour
            dt(float): delta time
        """
        for entity in world.query(RigidBody, Transform):
            rb: RigidBody = entity.get(RigidBody)
            if rb.is_static() or not rb.is_gravitational():
                continue
            rb.apply_acceleration(Vector(0.0, -self._gravity * rb.gravity_scale))