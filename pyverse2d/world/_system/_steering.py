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
            if entity.has(RigidBody):
                rb: RigidBody = entity.get(RigidBody)
                if rb.is_static():
                    continue

                if rb.is_sleeping():
                    rb.wake()

                dist = dist_sq ** 0.5

                speed = follow.max_speed if follow.max_speed is not None else (
                    (rb.velocity.x ** 2 + rb.velocity.y ** 2) ** 0.5
                )
                desired_vx = (dx / dist) * speed
                desired_vy = (dy / dist) * speed

                # Force de steering vers la vélocité désirée
                steer_x = (desired_vx - rb.velocity.x) * rb.mass
                steer_y = (desired_vy - rb.velocity.y) * rb.mass

                # Lissage sur la force
                if follow.smoothing > 0.0:
                    s = 1.0 - follow.smoothing
                    steer_x *= s
                    steer_y *= s

                rb.apply_force(Vector(steer_x, steer_y))

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