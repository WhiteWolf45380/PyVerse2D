# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..ecs import System, UpdatePhase, World
from ..component import Transform, RigidBody

# ======================================== SYSTEM ========================================
class PhysicsSystem(System):
    """Système intégrant la physique des corps dynamiques"""
    phase = UpdatePhase.LATE

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Intègre la physique de tous les corps dynamiques actifs

        Args:
            world(World): monde à mettre à jour
            dt(float): delta time
        """
        for entity in world.query(RigidBody, Transform):
            rb: RigidBody = entity.get(RigidBody)
            tr: Transform = entity.get(Transform)

            if rb.is_static() or rb.is_sleeping():
                continue

            # Sauvegarde de la position pour le sweep test anti-tunneling
            rb._save_prev(tr.x, tr.y)

            # Intégration semi-implicite d'Euler
            rb.velocity = rb.velocity + rb.acceleration * dt

            # Intégration de la position
            tr.x += rb.velocity.x * dt
            tr.y += rb.velocity.y * dt

            # Reset accélération et vérification du sleep
            rb.reset_acceleration()
            rb._tick_sleep(dt)