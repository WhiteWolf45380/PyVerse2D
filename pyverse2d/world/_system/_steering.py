# ======================================== IMPORTS ========================================
from __future__ import annotations

from math import exp, sin, pi
from ...abc import System
from ...math import Vector
from .._world import World
from .._component import Transform, Follow


# ======================================== HELPERS ========================================
def _smooth_noise(t: float) -> float:
    """Bruit pseudo-aléatoire lisse basé sur des sinusoïdes déphasées

    Args:
        t: temps normalisé
    """
    return (
        sin(t * 1.0) * 0.5 +
        sin(t * 2.3 + 1.7) * 0.25 +
        sin(t * 5.1 + 3.2) * 0.125 +
        sin(t * 11.7 + 5.8) * 0.0625
    ) / 0.9375


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

            # Avancement du temps de bruit
            follow._noise_t += dt * follow._noise_frequency * 2 * pi

            target_tr: Transform = follow.entity.transform

            # Offset de base + bruit organique
            noise_x = noise_y = 0.0
            if follow.noise_amplitude > 0.0:
                noise_x = _smooth_noise(follow._noise_t) * follow.noise_amplitude
                noise_y = _smooth_noise(follow._noise_t + 100.0) * follow.noise_amplitude

            target_x = target_tr.x + (follow.offset.x if follow.axis_x else 0.0) + noise_x
            target_y = target_tr.y + (follow.offset.y if follow.axis_y else 0.0) + noise_y

            dx = (target_x - tr.x) if follow.axis_x else 0.0
            dy = (target_y - tr.y) if follow.axis_y else 0.0
            dist_sq = dx * dx + dy * dy
            dist = dist_sq ** 0.5

            if dist < 1e-8:
                continue

            nx, ny = dx / dist, dy / dist

            # Vérification de la zone directionnelle acceptable
            in_direction = True
            ref_len = (follow.offset.x ** 2 + follow.offset.y ** 2) ** 0.5
            if ref_len > 1e-8:
                rx, ry = follow.offset.x / ref_len, follow.offset.y / ref_len
                ex, ey = -nx, -ny
                dot = ex * rx + ey * ry
                cross = ex * ry - ey * rx
                in_direction = dot >= follow.dot_min and follow.cross_min <= cross <= follow.cross_max

            # Calcul de la force selon la distance
            if dist < follow.radius_min:
                # Force répulsive
                fx, fy = -nx, -ny
                t = 1.0 - dist / follow.radius_min if follow.radius_min > 0.0 else 1.0
            elif dist <= follow.radius_max:
                # Pas de force distance
                if in_direction:
                    continue
                fx, fy = nx, ny
                t = 0.0
            else:
                # Force attractive
                fx, fy = nx, ny
                span = follow.radius_max
                t = min(1.0, (dist - follow.radius_max) / span) if span > 0.0 else 1.0

            if t < 1e-6:
                continue

            # Cas dynamique
            rb = entity.rigid_body
            if rb is not None:
                if rb.is_static():
                    continue
                if rb.is_sleeping():
                    rb.wake()

                steer_x = fx * follow.force * t
                steer_y = fy * follow.force * t

                # Freinage à l'approche
                vel = rb.velocity
                steer_x -= vel.x * follow.smoothing
                steer_y -= vel.y * follow.smoothing

                rb.apply_force(Vector._make(steer_x, steer_y))

            # Cas cinématique
            else:
                s = follow.smoothing
                if s == 0.0:
                    tr.x = target_x if follow.axis_x else tr.x
                    tr.y = target_y if follow.axis_y else tr.y
                else:
                    alpha = 1.0 - exp(-(1.0 - s) * dt * 10.0)
                    tr.x += dx * alpha * t
                    tr.y += dy * alpha * t