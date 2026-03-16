# ======================================== IMPORTS ========================================
from __future__ import annotations

from math import sqrt, cos, sin, atan2, pi as _PI

from .....math import Vector
from .....shape import Ellipse, Capsule

from .._registry import (
    Contact, register,
    closest_pt_on_seg, closest_pt_on_ellipse,
)

# ======================================== Ellipse × Ellipse ========================================
@register(Ellipse, Ellipse)
def ellipse_ellipse(sa: Ellipse, ax, ay, scale_a, rot_a, sb: Ellipse, bx, by, scale_b, rot_b) -> Contact | None:
    """Ellipse vs Ellipse"""
    ex_a, ey_a, rx_a, ry_a, _ = sa.world_transform(ax, ay, scale_a, rot_a)
    ex_b, ey_b, rx_b, ry_b, _ = sb.world_transform(bx, by, scale_b, rot_b)
    cdx = ex_b - ex_a
    cdy = ey_b - ey_a

    if cdx == 0.0 and cdy == 0.0:
        return Contact(Vector(1.0, 0.0), rx_a + rx_b)

    _STEP = _PI / 24
    best_ov = float("inf")
    best_theta = atan2(cdy, cdx) % _PI

    for i in range(24):
        theta = i * _STEP
        ct, st = cos(theta), sin(theta)
        h_a = sqrt(rx_a * rx_a * ct * ct + ry_a * ry_a * st * st)
        h_b = sqrt(rx_b * rx_b * ct * ct + ry_b * ry_b * st * st)
        ov = h_a + h_b - abs(cdx * ct + cdy * st)
        if ov < best_ov:
            best_ov = ov
            best_theta = theta

    if best_ov <= 0:
        return None

    theta = best_theta
    for _ in range(10):
        ct, st = cos(theta), sin(theta)
        h_a = sqrt(rx_a * rx_a * ct * ct + ry_a * ry_a * st * st) or 1e-10
        h_b = sqrt(rx_b * rx_b * ct * ct + ry_b * ry_b * st * st) or 1e-10
        c_proj = cdx * ct + cdy * st
        sign_c = 1.0 if c_proj >= 0.0 else -1.0
        g_a = ry_a * ry_a - rx_a * rx_a
        g_b = ry_b * ry_b - rx_b * rx_b
        sc = st * ct
        h_a_p = g_a * sc / h_a
        h_b_p = g_b * sc / h_b
        c_p = -cdx * st + cdy * ct
        ov_p = h_a_p + h_b_p - sign_c * c_p
        cos2t = ct * ct - st * st
        h_a_pp = g_a * cos2t / h_a - h_a_p * h_a_p / h_a
        h_b_pp = g_b * cos2t / h_b - h_b_p * h_b_p / h_b
        ov_pp = h_a_pp + h_b_pp + abs(c_proj)
        if abs(ov_pp) < 1e-12:
            break
        delta = ov_p / ov_pp
        theta -= delta
        if abs(delta) < 1e-8:
            break

    ct, st = cos(theta), sin(theta)
    h_a = sqrt(rx_a * rx_a * ct * ct + ry_a * ry_a * st * st)
    h_b = sqrt(rx_b * rx_b * ct * ct + ry_b * ry_b * st * st)
    c_proj = cdx * ct + cdy * st
    overlap = h_a + h_b - abs(c_proj)

    if overlap <= 0:
        return None

    sign_c = 1.0 if c_proj >= 0.0 else -1.0
    return Contact(Vector(-ct * sign_c, -st * sign_c), overlap)

# ======================================== Ellipse × Capsule ========================================
@register(Ellipse, Capsule)
def ellipse_capsule(sa: Ellipse, ax, ay, scale_a, rot_a, sb: Capsule, bx, by, scale_b, rot_b) -> Contact | None:
    """Ellipse vs Capsule"""
    ex, ey, rx, ry, _ = sa.world_transform(ax, ay, scale_a, rot_a)
    cap_ax, cap_ay, cap_bx, cap_by, cap_r = sb.world_transform(bx, by, scale_b, rot_b)
    spine_dx = cap_bx - cap_ax
    spine_dy = cap_by - cap_ay
    qx, qy = closest_pt_on_seg(cap_ax, cap_ay, spine_dx, spine_dy, ex, ey)
    lx = (qx - ex) / rx
    ly = (qy - ey) / ry
    spine_inside = lx * lx + ly * ly <= 1.0
    cpx, cpy = closest_pt_on_ellipse(ex, ey, rx, ry, qx, qy)
    dx = qx - cpx
    dy = qy - cpy
    dist = sqrt(dx * dx + dy * dy) or 1e-8
    nx, ny = -dx / dist, -dy / dist
    if spine_inside:
        return Contact(Vector(nx, ny), cap_r + dist)
    if dist >= cap_r:
        return None
    return Contact(Vector(nx, ny), cap_r - dist)