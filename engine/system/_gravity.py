# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._flag import UpdatePhase
from ..abc import System
from ..ecs import World
from ..component import Transform, RigidBody
from ..math import Vector

from numbers import Real
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._physics import PhysicsSystem

# ======================================== SYSTEM ========================================
class GravitySystem(System):
    """
    Système appliquant la force gravitationnelle sur les corps dynamiques

    Args:
        gravity(Real): force gravitationnelle en N/kg
    """
    phase = UpdatePhase.EARLY
    exclusive = False
    requires = (PhysicsSystem,)

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

            rb.apply_force(Vector(0.0, -self._gravity * rb.gravity_scale * rb.mass))