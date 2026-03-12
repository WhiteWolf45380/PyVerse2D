# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..ecs import System, UpdatePhase, World
from ..component import Transform, RigidBody

# ======================================== SYSTEM ========================================
class PhysicsSystem(System):
    """Système appliquant la physique des corps dynamiques"""
    phase = UpdatePhase.LATE

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Intègre la physique de tous les corps dynamiques

        Args:
            world(World): monde à mettre à jour
            dt(float): delta time
        """
        for entity in world.query(RigidBody, Transform):
            rb: RigidBody = entity.get(RigidBody)
            tr: Transform = entity.get(Transform)

            if rb.is_static():
                continue

            # Intégration semi-implicite d'Euler
            rb.velocity = rb.velocity + rb.acceleration * dt

            # Position = position + vélocité * dt
            tr.x += rb.velocity.x * dt
            tr.y += rb.velocity.y * dt

            # Reset accélération pour la prochaine frame
            rb.reset_acceleration()