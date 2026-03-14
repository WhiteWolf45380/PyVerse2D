# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....math import Vector
from ....shape import Ellipse, Rect, Capsule, Polygon, Segment

from ._registry import (
    Contact, register,
    _ellipse_vs_convex_pts,
    _closest_pt_on_ellipse, _closest_pt_on_seg,
    _rect_corners, _seg_corners,
)

from math import sqrt, cos, sin, atan2, pi as _PI

# ======================================== Ellipse × Ellipse ========================================
@register(Ellipse, Ellipse)
def ellipse_ellipse(sa: Ellipse, ax, ay, sb: Ellipse, bx, by) -> Contact | None:
    """Ellipse vs Ellipse"""
    cdx = bx - ax
    cdy = by - ay
    rx_a, ry_a = sa.rx, sa.ry
    rx_b, ry_b = sb.rx, sb.ry

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

    # Raffinement Newton-Raphson
    theta = best_theta
    for _ in range(10):
        ct, st = cos(theta), sin(theta)
        h_a = sqrt(rx_a * rx_a * ct * ct + ry_a * ry_a * st * st) or 1e-10
        h_b = sqrt(rx_b * rx_b * ct * ct + ry_b * ry_b * st * st) or 1e-10
        c_proj = cdx * ct + cdy * st
        c_proj_abs = abs(c_proj)
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
        ov_pp = h_a_pp + h_b_pp + c_proj_abs

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
    return Contact(Vector(ct * sign_c, st * sign_c), overlap)


# ======================================== Ellipse × Rect ========================================
@register(Ellipse, Rect)
def ellipse_rect(sa: Ellipse, ax, ay, sb: Rect, bx, by) -> Contact | None:
    """Ellipse vs Rect"""
    return _ellipse_vs_convex_pts(ax, ay, sa.rx, sa.ry, _rect_corners(bx, by, sb.width, sb.height))


# ======================================== Ellipse × Capsule ========================================
@register(Ellipse, Capsule)
def ellipse_capsule(sa: Ellipse, ax, ay, sb: Capsule, bx, by) -> Contact | None:
    """Ellipse vs Capsule"""
    cpx, cpy = _closest_pt_on_seg(bx, by, 0.0, sb.spine, ax, ay)

    lx = (cpx - ax) / sa.rx
    ly = (cpy - ay) / sa.ry
    spine_inside = lx * lx + ly * ly <= 1.0

    qx, qy = _closest_pt_on_ellipse(ax, ay, sa.rx, sa.ry, cpx, cpy)
    dx = cpx - qx
    dy = cpy - qy
    dist = sqrt(dx * dx + dy * dy) or 1e-8
    nx, ny = -dx / dist, -dy / dist

    if spine_inside:
        return Contact(Vector(nx, ny), sb.radius + dist)
    if dist >= sb.radius:
        return None
    return Contact(Vector(nx, ny), sb.radius - dist)


# ======================================== Ellipse × Polygon ========================================
@register(Ellipse, Polygon)
def ellipse_polygon(sa: Ellipse, ax, ay, sb: Polygon, bx, by) -> Contact | None:
    """Ellipse vs Polygone convexe"""
    return _ellipse_vs_convex_pts(
        ax, ay, sa.rx, sa.ry,
        [(bx + p.x, by + p.y) for p in sb.points],
    )

# ======================================== Ellipse × Segment ========================================
@register(Ellipse, Segment)
def ellipse_segment(sa: Ellipse, ax, ay, sb: Segment, bx, by) -> Contact | None:
    """Ellipse vs Segment"""
    obb = _seg_corners(bx, by, sb)
    c = _ellipse_vs_convex_pts(ax, ay, sa.rx, sa.ry, obb)
    if c is not None:
        return c

    seg_ax = bx + sb.A.x
    seg_ay = by + sb.A.y
    seg_bx = bx + sb.B.x
    seg_by = by + sb.B.y
    cpx, cpy = _closest_pt_on_seg(seg_ax, seg_ay, seg_bx - seg_ax, seg_by - seg_ay, ax, ay)
    lx, ly = (cpx - ax) / sa.rx, (cpy - ay) / sa.ry
    if lx * lx + ly * ly >= 1.0:
        return None
    qx, qy = _closest_pt_on_ellipse(ax, ay, sa.rx, sa.ry, cpx, cpy)
    ddx, ddy = qx - cpx, qy - cpy
    dist = sqrt(ddx * ddx + ddy * ddy) or 1e-8
    return Contact(Vector(ddx / dist, ddy / dist), dist)