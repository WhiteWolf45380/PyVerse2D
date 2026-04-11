from __future__ import annotations

from math import exp
from ...abc import System
from ...math import Vector
from .._world import World
from .._component import Transform, RigidBody, Follow

class SteeringSystem(System):
    """Système gérant le pilotage positionnel"""
    __slots__ = ()
    order = 10
    exclusive = True

    def update(self, world: World, dt: float):
        for entity in world.query(Follow, Transform):
            follow: Follow = entity.follow
            tr: Transform = entity.transform

            target_tr: Transform = follow.entity.transform
            target_x = target_tr.x + follow.offset.x
            target_y = target_tr.y + follow.offset.y

            dx = target_x - tr.x
            dy = target_y - tr.y
            dist_sq = dx * dx + dy * dy
            radius = follow.radius

            # Cible atteinte
            if dist_sq <= radius * radius:
                continue

            # Cas dynamique
            rb = entity.rigid_body
            if rb is not None:
                if rb.is_static():
                    continue
                if rb.is_sleeping():
                    rb.wake()

                dist = dist_sq ** 0.5
                nx, ny = dx / dist, dy / dist

                # Force d'attraction directe
                steer_x = nx * follow.force
                steer_y = ny * follow.force

                # Lissage
                if follow.smoothing > 0.0:
                    s = 1.0 - follow.smoothing
                    steer_x *= s
                    steer_y *= s

                rb.apply_force(Vector._make(steer_x, steer_y))

            # Cas cinématique
            else:
                s = follow.smoothing
                if s == 0.0:
                    tr.x = target_x
                    tr.y = target_y
                else:
                    alpha = 1.0 - exp(-(1.0 - s) * dt * 10.0)
                    tr.x += dx * alpha
                    tr.y += dy * alpha