# ======================================== IMPORTS ========================================
from __future__ import annotations

from . import _circle, _ellipse, _capsule  # noqa: F401 — enregistrement des handlers via @register

from .....abc import VertexShape
from .....shape import Circle, Ellipse, Capsule

from .._registry import Contact, _handlers
from ._vertex import (
    vertex_world_pts, sat,
    circle_vs_pts, ellipse_vs_pts, capsule_vs_pts,
)

# ======================================== DISPATCH ========================================
def dispatch(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b) -> Contact | None:
    """Dispatche vers le bon handler de narrowphase"""
    a_is_vertex = isinstance(sa, VertexShape)
    b_is_vertex = isinstance(sb, VertexShape)

    if a_is_vertex and b_is_vertex:
        pts_a = vertex_world_pts(sa, ax, ay, scale_a, rot_a)
        pts_b = vertex_world_pts(sb, bx, by, scale_b, rot_b)
        return sat(pts_a, pts_b)

    if a_is_vertex:
        # pts=A, primitive=B — normale pointe de A vers B, on flippe pour avoir B vers A
        c = _dispatch_vertex_primitive(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b)
        if c is None:
            return None
        return Contact(c.normal.__class__(-c.normal.x, -c.normal.y), c.depth)

    if b_is_vertex:
        # pts=B, primitive=A — normale pointe de B vers A, correct
        return _dispatch_vertex_primitive(sb, bx, by, scale_b, rot_b, sa, ax, ay, scale_a, rot_a)

    # Primitives vs primitives
    key = (type(sa), type(sb))
    fn = _handlers.get(key)
    if fn is not None:
        return fn(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b)

    key_flip = (type(sb), type(sa))
    fn = _handlers.get(key_flip)
    if fn is not None:
        c = fn(sb, bx, by, scale_b, rot_b, sa, ax, ay, scale_a, rot_a)
        if c is None:
            return None
        return Contact(c.normal.__class__(-c.normal.x, -c.normal.y), c.depth)

    return None

def _dispatch_vertex_primitive(sv, vx, vy, scale_v, rot_v, sp, px, py, scale_p, rot_p) -> Contact | None:
    """Dispatch VertexShape vs primitive"""
    pts = vertex_world_pts(sv, vx, vy, scale_v, rot_v)

    if isinstance(sp, Circle):
        cx_, cy_, r = sp.world_transform(px, py, scale_p, rot_p)
        return circle_vs_pts(cx_, cy_, r, pts)

    if isinstance(sp, Ellipse):
        cx_, cy_, rx, ry, angle = sp.world_transform(px, py, scale_p, rot_p)
        return ellipse_vs_pts(cx_, cy_, rx, ry, pts)

    if isinstance(sp, Capsule):
        ax_, ay_, bx_, by_, r = sp.world_transform(px, py, scale_p, rot_p)
        return capsule_vs_pts(ax_, ay_, bx_, by_, r, pts)

    return None