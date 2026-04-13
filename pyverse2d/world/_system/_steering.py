# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import System
from ...math import Vector
from .._world import World
from .._component import Transform, Follow

import math

# ======================================== SYSTEM ========================================
class SteeringSystem(System):
    """Système gérant le pilotage positionnel"""
    __slots__ = ()
    order = 10
    exclusive = True

    def update(self, world: World, dt: float):
        """Actualisation du pilotage

        Args:
            world: monde courant
            dt: delta temps
        """
        for entity in world.query(Follow, Transform):
            follow: Follow = entity.follow
            tr: Transform = entity.transform

            target_tr: Transform = follow.entity.transform
            target_x = target_tr.x + (follow.offset.x if follow.axis_x else 0.0)
            target_y = target_tr.y + (follow.offset.y if follow.axis_y else 0.0)

            dx = (target_x - tr.x) if follow.axis_x else 0.0
            dy = (target_y - tr.y) if follow.axis_y else 0.0
            dist = (dx * dx + dy * dy) ** 0.5

            in_zone = follow.radius_min <= dist <= follow.radius_max

            # Vérification du cône angulaire
            in_direction = True
            if follow.cone < 180.0 and dist > 1e-8:
                entity_angle = math.degrees(math.atan2(-dy, -dx))
                diff = abs((entity_angle - follow.angle + 180.0) % 360.0 - 180.0)
                in_direction = follow.cone_gap <= diff <= follow.cone

            follow._arrived = in_zone and in_direction

            # Cas cinématique
            rb = entity.rigid_body
            if rb is None:
                if follow._arrived:
                    continue
                t = 1.0 - follow.smoothing ** dt
                tr.x += dx * t
                tr.y += dy * t

            # Cas dynamique
            else:
                if rb.is_static():
                    continue
                if rb.is_sleeping():
                    rb.wake()

                vel = rb.velocity
                fx = fy = 0.0

                if not in_zone:
                    if dist < 1e-8:
                        continue

                    nx, ny = dx / dist, dy / dist

                    if dist < follow.radius_min:
                        # Force répulsive
                        t = 1.0 - dist / follow.radius_min if follow.radius_min > 0.0 else 1.0
                        fx = -nx * follow.force * t
                        fy = -ny * follow.force * t
                    else:
                        # Force attractive
                        if not in_direction:
                            t = 0.0
                        else:
                            span = follow.radius_max if follow.radius_max > 0.0 else 1.0
                            t = min(1.0, (dist - follow.radius_max) / span)

                        if t < 1e-6 and in_direction:
                            continue

                        fx = nx * follow.force * t
                        fy = ny * follow.force * t

                # Damping
                if follow.damping > 0.0:
                    fx -= vel.x * follow.damping
                    fy -= vel.y * follow.damping

                if fx == 0.0 and fy == 0.0:
                    continue

                rb.apply_force(Vector._make(fx, fy))