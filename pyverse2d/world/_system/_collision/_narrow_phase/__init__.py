# ======================================== IMPORTS ========================================
from __future__ import annotations

from .....abc import Shape
from .....shape import Circle, Ellipse, Capsule

from .._registry import _handlers, Contact

from ._vertex import sat, circle_vs_pts, ellipse_vs_pts, capsule_vs_pts

from . import _circle, _ellipse, _capsule, _rounded_rect     # noqa: F401 (enregistrement des handlers via @register)
from ._prim_transform import circle_params, ellipse_params, capsule_params

import numpy as np
from numpy.typing import NDArray

# ======================================== CONSTANTS ========================================
_PRIMITIVE_TYPES = (Circle, Ellipse, Capsule)

# ======================================== DISPATCH ========================================
def dispatch(sa: Shape, ax: float, ay: float, scale_a: float, rot_a: float, sb: Shape, bx: float, by: float, scale_b: float, rot_b: float) -> Contact | None:
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
        return c

    # Vertex vs Primitive
    if not a_is_prim and b_is_prim:
        pts_a = sa.world_vertices(ax, ay, scale_a, rot_a)
        c = _primitive_vs_pts(sb, bx, by, scale_b, rot_b, pts_a)
        return c

    # Vertex vs Vertex
    pts_a = sa.world_vertices(ax, ay, scale_a, rot_a)
    pts_b = sb.world_vertices(bx, by, scale_b, rot_b)
    return sat(pts_a, pts_b)

# ======================================== HELPERS ========================================
def _primitive_vs_pts(sp: Shape, px: float, py: float, scale_p: float, rot_p: float, pts: NDArray[np.float32]):
    """Dispatch une primitive contre un contour polygonal"""
    if isinstance(sp, Circle):
        cx, cy, r = circle_params(sp, px, py, scale_p)
        return circle_vs_pts(cx, cy, r, pts)

    if isinstance(sp, Ellipse):
        cx, cy, rx, ry, r = ellipse_params(sp, px, py, scale_p, rot_p)
        return ellipse_vs_pts(cx, cy, rx, ry, r, pts)

    if isinstance(sp, Capsule):
        ax_, ay_, bx_, by_, r = capsule_params(sp, px, py, scale_p, rot_p)
        return capsule_vs_pts(ax_, ay_, bx_, by_, r, pts)

    return None


def _flip(c: Contact | None) -> Contact | None:
    """Inverse l'ordre d'une contacte"""
    if c is None:
        return None
    return Contact(c.normal.__class__(-c.normal.x, -c.normal.y), c.depth)

# ======================================== EXPORTS ========================================
__all__ = [
    "dispatch",
]