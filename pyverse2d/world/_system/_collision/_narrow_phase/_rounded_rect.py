# ======================================== IMPORTS ========================================
from __future__ import annotations

from .....shape import Circle, Ellipse, Capsule, RoundedRect

from .._registry import Contact, register, rounded_rect_contour
from ._vertex import sat, circle_vs_pts, ellipse_vs_pts, capsule_vs_pts, rounded_rect_vs_pts

# ======================================== RoundedRect × RoundedRect ========================================
@register(RoundedRect, RoundedRect)
def rounded_rect_rounded_rect(sa: RoundedRect, ax, ay, scale_a, rot_a, sb: RoundedRect, bx, by, scale_b, rot_b) -> Contact | None:
    """RoundedRect vs RoundedRect"""
    pts_a = rounded_rect_contour(*sa.world_transform(ax, ay, scale_a, rot_a))
    pts_b = rounded_rect_contour(*sb.world_transform(bx, by, scale_b, rot_b))
    return sat(pts_a, pts_b)

# ======================================== RoundedRect × Circle ========================================
@register(RoundedRect, Circle)
def rounded_rect_circle(sa: RoundedRect, ax, ay, scale_a, rot_a, sb: Circle, bx, by, scale_b, rot_b) -> Contact | None:
    """RoundedRect vs Circle)"""
    cx_, cy_, r = sb.world_transform(bx, by, scale_b, rot_b)
    c = circle_vs_pts(cx_, cy_, r, rounded_rect_contour(*sa.world_transform(ax, ay, scale_a, rot_a)))
    if c is None:
        return None
    return Contact(c.normal.__class__(-c.normal.x, -c.normal.y), c.depth)

# ======================================== RoundedRect × Ellipse ========================================
@register(RoundedRect, Ellipse)
def rounded_rect_ellipse(sa: RoundedRect, ax, ay, scale_a, rot_a, sb: Ellipse, bx, by, scale_b, rot_b) -> Contact | None:
    """RoundedRect vs Ellipse"""
    ex, ey, rx, ry, _ = sb.world_transform(bx, by, scale_b, rot_b)
    c = ellipse_vs_pts(ex, ey, rx, ry, rounded_rect_contour(*sa.world_transform(ax, ay, scale_a, rot_a)))
    if c is None:
        return None
    return Contact(c.normal.__class__(-c.normal.x, -c.normal.y), c.depth)

# ======================================== RoundedRect × Capsule ========================================
@register(RoundedRect, Capsule)
def rounded_rect_capsule(sa: RoundedRect, ax, ay, scale_a, rot_a, sb: Capsule, bx, by, scale_b, rot_b) -> Contact | None:
    """RoundedRect vs Capsule"""
    cap_ax, cap_ay, cap_bx, cap_by, cap_r = sb.world_transform(bx, by, scale_b, rot_b)
    c = capsule_vs_pts(cap_ax, cap_ay, cap_bx, cap_by, cap_r, rounded_rect_contour(*sa.world_transform(ax, ay, scale_a, rot_a)))
    if c is None:
        return None
    return Contact(c.normal.__class__(-c.normal.x, -c.normal.y), c.depth)