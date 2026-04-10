# ======================================== IMPORTS ========================================
from __future__ import annotations

from .....shape import Circle, Ellipse, Capsule

from .._registry import Contact
from .._registry import _handlers

from ._vertex import sat, circle_vs_pts, ellipse_vs_pts, capsule_vs_pts

from . import _circle, _ellipse, _capsule     # noqa: F401 (enregistrement des handlers via @register)
from ._prim_transform import _circle_params, _ellipse_params, _capsule_params

# ======================================== CONSTANTS ========================================
_PRIMITIVE_TYPES = (Circle, Ellipse, Capsule)

# ======================================== DISPATCH ========================================
def dispatch(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b) -> Contact | None:
    """Fait correspondre les shapes à leur test de collision"""
    a_is_prim = isinstance(sa, _PRIMITIVE_TYPES)
    b_is_prim = isinstance(sb, _PRIMITIVE_TYPES)

    # Primitive vs Primitive
    if a_is_prim and b_is_prim:
        key = (type(sa), type(sb))
        fn = _handlers.get(key)
        if fn:
            return fn(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b)
        key_flip = (type(sb), type(sa))
        fn = _handlers.get(key_flip)
        if fn:
            c = fn(sb, bx, by, scale_b, rot_b, sa, ax, ay, scale_a, rot_a)
            return _flip(c)
        return None

    # Primitive vs Vertex
    if a_is_prim and not b_is_prim:
        pts_b = sb.world_vertices(bx, by, scale_b, rot_b)
        c = _primitive_vs_pts(sa, ax, ay, scale_a, rot_a, pts_b)
        return _flip(c)  # normale pointe de B vers A

    # Vertex vs Primitive
    if not a_is_prim and b_is_prim:
        pts_a = sa.world_vertices(ax, ay, scale_a, rot_a)
        return _primitive_vs_pts(sb, bx, by, scale_b, rot_b, pts_a)

    # Vertex vs Vertex
    pts_a = sa.world_vertices(ax, ay, scale_a, rot_a)
    pts_b = sb.world_vertices(bx, by, scale_b, rot_b)
    return sat(pts_a, pts_b)

# ======================================== HELPERS ========================================
def _primitive_vs_pts(sp, px, py, scale_p, rot_p, pts):
    """Dispatch une primitive contre un contour polygonal"""
    if isinstance(sp, Circle):
        cx, cy, r = _circle_params(sp, px, py, scale_p)
        return circle_vs_pts(cx, cy, r, pts)

    if isinstance(sp, Ellipse):
        cx, cy, rx, ry, r = _ellipse_params(sp, px, py, scale_p, rot_p)
        return ellipse_vs_pts(cx, cy, rx, ry, r, pts)

    if isinstance(sp, Capsule):
        ax_, ay_, bx_, by_, r = _capsule_params(sp, px, py, scale_p, rot_p)
        return capsule_vs_pts(ax_, ay_, bx_, by_, r, pts)

    return None


def _flip(c: Contact | None) -> Contact | None:
    if c is None:
        return None
    return Contact(c.normal.__class__(-c.normal.x, -c.normal.y), c.depth)