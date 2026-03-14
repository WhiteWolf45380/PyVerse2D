# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....math import Vector
from ....shape import Rect, Capsule, Polygon, Segment

from ._registry import (
    Contact, register,
    _sat, _rect_corners, _seg_corners
)

# ======================================== Rect × Rect ========================================
@register(Rect, Rect)
def rect_rect(sa: Rect, ax, ay, sb: Rect, bx, by) -> Contact | None:
    """Rect vs Rect"""
    a_cx = ax + sa.width * 0.5
    a_cy = ay + sa.height * 0.5
    b_cx = bx + sb.width * 0.5
    b_cy = by + sb.height * 0.5
    dx = a_cx - b_cx
    dy = a_cy - b_cy
    ox = (sa.width + sb.width) * 0.5 - abs(dx)
    oy = (sa.height + sb.height) * 0.5 - abs(dy)
    if ox <= 0 or oy <= 0:
        return None
    if ox < oy:
        return Contact(Vector(1.0 if dx > 0 else -1.0, 0.0), ox)
    return Contact(Vector(0.0, 1.0 if dy > 0 else -1.0), oy)


# ======================================== Rect × Capsule ========================================
@register(Rect, Capsule)
def rect_capsule(sa: Rect, ax, ay, sb: Capsule, bx, by) -> Contact | None:
    """Rect vs Capsule"""
    from ._capsule import _capsule_convex
    pts = _rect_corners(ax, ay, sa.width, sa.height)
    return _capsule_convex(bx, by, sb.spine, sb.radius, pts)


# ======================================== Rect × Polygon ========================================
@register(Rect, Polygon)
def rect_polygon(sa: Rect, ax, ay, sb: Polygon, bx, by) -> Contact | None:
    """Rect vs Polygone"""
    return _sat(
        _rect_corners(ax, ay, sa.width, sa.height),
        [(bx + p.x, by + p.y) for p in sb.points],
    )


# ======================================== Rect × Segment ========================================
@register(Rect, Segment)
def rect_segment(sa: Rect, ax, ay, sb: Segment, bx, by) -> Contact | None:
    """Rect vs Segment"""
    return _sat(
        _rect_corners(ax, ay, sa.width, sa.height),
        _seg_corners(bx, by, sb),
    )