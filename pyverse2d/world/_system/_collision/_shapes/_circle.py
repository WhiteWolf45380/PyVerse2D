# ======================================== IMPORTS ========================================
from __future__ import annotations

from .....math import Vector
from .....shape import Circle, Ellipse, Capsule

from .._registry import (
    Contact, register,
    closest_pt_on_seg, closest_pt_on_ellipse,
)

from math import sqrt

# ======================================== Circle × Circle ========================================
@register(Circle, Circle)
def circle_circle(sa: Circle, ax, ay, scale_a, rot_a, sb: Circle, bx, by, scale_b, rot_b) -> Contact | None:
    """Cercle vs Cercle"""
    _, _, ra = sa.world_transform(ax, ay, scale_a, rot_a)
    _, _, rb = sb.world_transform(bx, by, scale_b, rot_b)
    dx = ax - bx
    dy = ay - by
    dist_sq = dx * dx + dy * dy
    radii = ra + rb
    if dist_sq >= radii * radii:
        return None
    dist = sqrt(dist_sq) or 1e-8
    return Contact(Vector(dx / dist, dy / dist), radii - dist)

# ======================================== Circle × Ellipse ========================================
@register(Circle, Ellipse)
def circle_ellipse(sa: Circle, ax, ay, scale_a, rot_a, sb: Ellipse, bx, by, scale_b, rot_b) -> Contact | None:
    """Cercle vs Ellipse"""
    _, _, r = sa.world_transform(ax, ay, scale_a, rot_a)
    ex, ey, rx, ry, _ = sb.world_transform(bx, by, scale_b, rot_b)
    lx = (ax - ex) / rx
    ly = (ay - ey) / ry
    inside = lx * lx + ly * ly <= 1.0
    qx, qy = closest_pt_on_ellipse(ex, ey, rx, ry, ax, ay)
    dx = ax - qx
    dy = ay - qy
    dist = sqrt(dx * dx + dy * dy) or 1e-8
    if inside:
        return Contact(Vector(dx / dist, dy / dist), r + dist)
    if dist >= r:
        return None
    return Contact(Vector(dx / dist, dy / dist), r - dist)

# ======================================== Circle × Capsule ========================================
@register(Circle, Capsule)
def circle_capsule(sa: Circle, ax, ay, scale_a, rot_a, sb: Capsule, bx, by, scale_b, rot_b) -> Contact | None:
    """Cercle vs Capsule"""
    _, _, r = sa.world_transform(ax, ay, scale_a, rot_a)
    cap_ax, cap_ay, cap_bx, cap_by, cap_r = sb.world_transform(bx, by, scale_b, rot_b)
    spine_dx = cap_bx - cap_ax
    spine_dy = cap_by - cap_ay
    qx, qy = closest_pt_on_seg(cap_ax, cap_ay, spine_dx, spine_dy, ax, ay)
    dx = ax - qx
    dy = ay - qy
    dist_sq = dx * dx + dy * dy
    radii = r + cap_r
    if dist_sq >= radii * radii:
        return None
    dist = sqrt(dist_sq) or 1e-8
    return Contact(Vector(dx / dist, dy / dist), radii - dist)