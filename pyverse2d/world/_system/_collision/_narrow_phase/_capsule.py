# ======================================== IMPORTS ========================================
from __future__ import annotations

from .....math import Vector
from .....shape import Capsule

from .._registry import Contact, register

from ._prim_transform import _capsule_params
from ._helper import closest_pt_on_seg, closest_pt_seg_to_seg

from math import sqrt

# ======================================== Capsule × Capsule ========================================
@register(Capsule, Capsule)
def capsule_capsule(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b):
    """Vérifie la collision entre ``Capsule`` et ``Capsule``"""
    a_ax, a_ay, a_bx, a_by, ra = _capsule_params(sa, ax, ay, scale_a, rot_a)
    b_ax, b_ay, b_bx, b_by, rb = _capsule_params(sb, bx, by, scale_b, rot_b)
    a_dx, a_dy = a_bx - a_ax, a_by - a_ay
    b_dx, b_dy = b_bx - b_ax, b_by - b_ay
    px, py = closest_pt_seg_to_seg(a_ax, a_ay, a_dx, a_dy, b_ax, b_ay, b_dx, b_dy)
    qx, qy = closest_pt_on_seg(b_ax, b_ay, b_dx, b_dy, px, py)
    dx = px - qx
    dy = py - qy
    dist_sq = dx * dx + dy * dy
    radii = ra + rb
    if dist_sq >= radii * radii:
        return None
    dist = sqrt(dist_sq) or 1e-8
    return Contact(Vector._make(dx / dist, dy / dist), radii - dist)

# ======================================== EXPORTS ========================================
__all__ = [
    "capsule_capsule",
]