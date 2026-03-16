# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....math import Vector
from ....abc import VertexShape

from ._narrowphase import sat_vertex_vertex, dispatch_vertex_primitive

from typing import Callable, NamedTuple
from math import cos, sin, atan2

# ======================================== CONTACT ========================================
class Contact(NamedTuple):
    """
    Résultat d'une détection de collision

    Convention : normal pointe de B vers A (pousse A hors de B)
    """
    normal: Vector
    depth: float

# ======================================== REGISTRY ========================================
_handlers: dict[tuple[type, type], Callable] = {}

def register(type_a: type, type_b: type):
    """Décore une fonction de narrowphase pour la paire (type_a, type_b)"""
    def decorator(fn: Callable) -> Callable:
        _handlers[(type_a, type_b)] = fn
        return fn
    return decorator

def dispatch(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b) -> Contact | None:
    """Dispatche vers le bon handler de narrowphase"""
    a_is_vertex = isinstance(sa, VertexShape)
    b_is_vertex = isinstance(sb, VertexShape)

    if a_is_vertex and b_is_vertex:
        return sat_vertex_vertex(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b)

    if a_is_vertex:
        c = dispatch_vertex_primitive(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b)
        return Contact(Vector(-c.normal.x, -c.normal.y), c.depth) if c is not None else None

    if b_is_vertex:
        return dispatch_vertex_primitive(sb, bx, by, scale_b, rot_b, sa, ax, ay, scale_a, rot_a)

    key = (type(sa), type(sb))
    fn = _handlers.get(key)
    if fn is not None:
        return fn(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b)

    key_flip = (type(sb), type(sa))
    fn = _handlers.get(key_flip)
    if fn is not None:
        c = fn(sb, bx, by, scale_b, rot_b, sa, ax, ay, scale_a, rot_a)
        return Contact(Vector(-c.normal.x, -c.normal.y), c.depth) if c is not None else None

    return None

def world_center(shape, tr, offset=(0.0, 0.0)) -> tuple[float, float]:
    """Calcule le centre géométrique monde depuis transform, bounding_box et offset"""
    x_min, y_min, x_max, y_max = shape.bounding_box
    anchor_x = x_min + tr.anchor.x * (x_max - x_min)
    anchor_y = y_min + tr.anchor.y * (y_max - y_min)
    cx = tr.x - anchor_x * tr.scale + offset[0] * tr.scale
    cy = tr.y - anchor_y * tr.scale + offset[1] * tr.scale
    return cx, cy

# ======================================== HELPERS GÉOMÉTRIQUES ========================================
def closest_pt_on_seg(sx, sy, sdx, sdy, px, py) -> tuple[float, float]:
    """Point le plus proche de (px,py) sur le segment (sx,sy)→(sx+sdx,sy+sdy)"""
    len_sq = sdx * sdx + sdy * sdy
    if len_sq < 1e-10:
        return sx, sy
    t = max(0.0, min(1.0, ((px - sx) * sdx + (py - sy) * sdy) / len_sq))
    return sx + t * sdx, sy + t * sdy

def closest_pt_seg_to_seg(ax, ay, adx, ady, bx, by, bdx, bdy) -> tuple[float, float]:
    """Point le plus proche sur le segment A du segment B"""
    a_len_sq = adx * adx + ady * ady
    b_len_sq = bdx * bdx + bdy * bdy
    rx, ry = ax - bx, ay - by
    e = rx * bdx + ry * bdy
    f = adx * bdx + ady * bdy

    if a_len_sq < 1e-10 and b_len_sq < 1e-10:
        return ax, ay
    if a_len_sq < 1e-10:
        s = max(0.0, min(1.0, e / b_len_sq))
        return bx + s * bdx, by + s * bdy
    c = rx * adx + ry * ady
    if b_len_sq < 1e-10:
        t = max(0.0, min(1.0, -c / a_len_sq))
        return ax + t * adx, ay + t * ady
    denom = a_len_sq * b_len_sq - f * f
    t = max(0.0, min(1.0, (f * e - c * b_len_sq) / denom)) if abs(denom) > 1e-10 else 0.0
    s = max(0.0, min(1.0, (f * t + e) / b_len_sq))
    t = max(0.0, min(1.0, (f * s - c) / a_len_sq))
    return ax + t * adx, ay + t * ady

def closest_pt_on_ellipse(cx, cy, rx, ry, px, py) -> tuple[float, float]:
    """Point le plus proche sur l'ellipse (cx,cy,rx,ry) du point (px,py)"""
    lx = px - cx
    ly = py - cy
    if abs(lx) < 1e-12 and abs(ly) < 1e-12:
        return cx + rx, cy
    t = atan2(ly * rx, lx * ry)
    for _ in range(25):
        ct, st = cos(t), sin(t)
        ex2 = rx * ct
        ey2 = ry * st
        f = -rx * st * (ex2 - lx) + ry * ct * (ey2 - ly)
        fp = (-rx * ct * (ex2 - lx) + rx * rx * st * st
              - ry * st * (ey2 - ly) + ry * ry * ct * ct)
        if abs(fp) < 1e-12:
            break
        delta = f / fp
        t -= delta
        if abs(delta) < 1e-9:
            break
    ct, st = cos(t), sin(t)
    return cx + rx * ct, cy + ry * st

def point_in_convex_poly(px: float, py: float, pts: list) -> bool:
    """Vérifie si (px,py) est à l'intérieur d'un polygone convexe"""
    n = len(pts)
    sign = None
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
        if abs(cross) < 1e-10:
            continue
        s = cross > 0
        if sign is None:
            sign = s
        elif sign != s:
            return False
    return sign is not None