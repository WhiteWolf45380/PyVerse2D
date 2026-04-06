# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import System
from ...math import Vector

from .._world import World
from .._component import Transform, RigidBody

# ======================================== SYSTEM ========================================
class GravitySystem(System):
    """Système appliquant une force gravitationnelle sur les corps dynamiques

    Args:
        gravity(Real): force gravitationnelle en N/kg
    """
    __slots__ = ("_gravity")
    order = 0
    exclusive = False
    requires = ("PhysicsSystem",)

    def __init__(self, gravity: Vector = (0.0, -9.8)):
        self._gravity: Vector = Vector(gravity)

    # ======================================== GETTERS ========================================
    @property
    def gravity(self) -> Vector:
        """Renvoie le vecteur gravitationnel en N/kg"""
        return self._gravity

    # ======================================== SETTERS ========================================
    @gravity.setter
    def gravity(self, value: Vector):
        """Fixe le vecteur gravitationnel en N/kg"""
        self._gravity = Vector(value)

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
            rb.apply_acceleration(self._gravity * rb.gravity_scale)