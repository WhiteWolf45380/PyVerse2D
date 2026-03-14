# ======================================== IMPORTS ========================================
from __future__ import annotations

from math import sqrt, cos, sin, atan2
from typing import NamedTuple, Callable

from ....math import Vector
from ....shape import Capsule, Ellipse, Segment
from ....abc import Shape

# ======================================== CONTACT ========================================
class Contact(NamedTuple):
    """Résultat d'une détection de collision"""
    normal: Vector
    depth: float

# ======================================== REGISTRY ========================================
_handlers: dict[tuple[type, type], Callable] = {}

def register(type_a: type, type_b: type):
    """
    Décore une fonction de narrowphase pour la paire (type_a, type_b)
    """
    def decorator(fn: Callable) -> Callable:
        _handlers[(type_a, type_b)] = fn
        return fn
    return decorator

def dispatch(sa, ax: float, ay: float, sb, bx: float, by: float) -> Contact | None:
    """
    Dispatche vers le bon handler de narrowphase
    """
    key = (type(sa), type(sb))
    fn = _handlers.get(key)
    if fn is not None:
        return fn(sa, ax, ay, sb, bx, by)

    key_flip = (type(sb), type(sa))
    fn = _handlers.get(key_flip)
    if fn is not None:
        c = fn(sb, bx, by, sa, ax, ay)
        return Contact(-c.normal, c.depth) if c is not None else None

    return _aabb_fallback(sa, ax, ay, sb, bx, by)

# ======================================== NARROWPHASE PARTAGÉE ========================================
def _circle_pts(cx: float, cy: float, cr: float, pts: list) -> Contact | None:
    """Cercle vs polygone convexe (SAT)"""
    n = len(pts)
    min_depth = float("inf")
    best_nx, best_ny = 0.0, 1.0

    # Axes des arêtes
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        ex, ey = x2 - x1, y2 - y1
        le = sqrt(ex * ex + ey * ey)
        if le < 1e-10:
            continue
        nx, ny = -ey / le, ex / le

        min_p = min(qx * nx + qy * ny for qx, qy in pts)
        max_p = max(qx * nx + qy * ny for qx, qy in pts)
        pc = cx * nx + cy * ny

        ov = min(pc + cr, max_p) - max(pc - cr, min_p)
        if ov <= 0:
            return None
        if ov < min_depth:
            min_depth = ov
            if pc < (min_p + max_p) * 0.5:
                best_nx, best_ny = -nx, -ny
            else:
                best_nx, best_ny = nx, ny

    # Axe du sommet le plus proche
    near_x, near_y = min(pts, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
    ddx, ddy = cx - near_x, cy - near_y
    le = sqrt(ddx * ddx + ddy * ddy) or 1e-8
    nx, ny = ddx / le, ddy / le

    min_p = min(qx * nx + qy * ny for qx, qy in pts)
    max_p = max(qx * nx + qy * ny for qx, qy in pts)
    pc = cx * nx + cy * ny

    ov = min(pc + cr, max_p) - max(pc - cr, min_p)
    if ov <= 0:
        return None
    if ov < min_depth:
        min_depth = ov
        best_nx, best_ny = nx, ny

    return Contact(Vector(best_nx, best_ny), min_depth)


def _sat(pts_a: list, pts_b: list) -> Contact | None:
    """SAT pour deux polygones convexes"""
    min_depth = float("inf")
    best_nx, best_ny = 0.0, 1.0

    for pts, other in ((pts_a, pts_b), (pts_b, pts_a)):
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            ex, ey = x2 - x1, y2 - y1
            le = sqrt(ex * ex + ey * ey)
            if le < 1e-10:
                continue
            nx, ny = -ey / le, ex / le

            min_a = min(px * nx + py * ny for px, py in pts)
            max_a = max(px * nx + py * ny for px, py in pts)
            min_b = min(px * nx + py * ny for px, py in other)
            max_b = max(px * nx + py * ny for px, py in other)

            ov = min(max_a, max_b) - max(min_a, min_b)
            if ov <= 0:
                return None
            if ov < min_depth:
                min_depth = ov
                best_nx, best_ny = nx, ny

    # Orienter de B vers A via centroïdes
    ca_x = sum(p[0] for p in pts_a) / len(pts_a)
    ca_y = sum(p[1] for p in pts_a) / len(pts_a)
    cb_x = sum(p[0] for p in pts_b) / len(pts_b)
    cb_y = sum(p[1] for p in pts_b) / len(pts_b)
    if (ca_x - cb_x) * best_nx + (ca_y - cb_y) * best_ny < 0:
        best_nx, best_ny = -best_nx, -best_ny

    return Contact(Vector(best_nx, best_ny), min_depth)


def _ellipse_vs_convex_pts(ex: float, ey: float, rx: float, ry: float, pts: list) -> Contact | None:
    """Ellipse vs polygone convexe"""
    n = len(pts)

    # Point du polygone le plus proche du centre de l'ellipse
    min_d2 = float("inf")
    best_px, best_py = pts[0]
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        px, py = _closest_pt_on_seg(x1, y1, x2 - x1, y2 - y1, ex, ey)
        d2 = (px - ex) ** 2 + (py - ey) ** 2
        if d2 < min_d2:
            min_d2 = d2
            best_px, best_py = px, py

    lx, ly = (best_px - ex) / rx, (best_py - ey) / ry
    poly_pt_inside = lx * lx + ly * ly < 1.0
    center_in_poly = _point_in_convex_poly(ex, ey, pts)

    if not poly_pt_inside and not center_in_poly:
        return None

    if center_in_poly:
        # SAT avec fonction support de l'ellipse
        min_ov = float("inf")
        best_nx, best_ny = 0.0, 1.0
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            edx, edy = x2 - x1, y2 - y1
            le = sqrt(edx * edx + edy * edy) or 1e-10
            nx, ny = -edy / le, edx / le
            # Projection de l'ellipse via sa fonction support
            h = sqrt(rx * rx * nx * nx + ry * ry * ny * ny)
            ec_proj = ex * nx + ey * ny
            projs = [qx * nx + qy * ny for qx, qy in pts]
            min_p, max_p = min(projs), max(projs)
            ov = min(ec_proj + h, max_p) - max(ec_proj - h, min_p)
            if ov <= 0:
                return None
            if ov < min_ov:
                min_ov = ov
                if ec_proj < (min_p + max_p) * 0.5:
                    best_nx, best_ny = -nx, -ny
                else:
                    best_nx, best_ny = nx, ny
        return Contact(Vector(best_nx, best_ny), min_ov)

    # Point du polygone à l'intérieur de l'ellipse
    qx, qy = _closest_pt_on_ellipse(ex, ey, rx, ry, best_px, best_py)
    ddx, ddy = qx - best_px, qy - best_py
    dist = sqrt(ddx * ddx + ddy * ddy) or 1e-8
    return Contact(Vector(ddx / dist, ddy / dist), dist)


# ======================================== HELPERS GÉOMÉTRIQUES ========================================
def _rect_corners(x: float, y: float, w: float, h: float) -> list:
    """Renvoie les 4 sommets d'un Rect en coordonnées monde"""
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

def _seg_corners(x: float, y: float, seg: Segment) -> list:
    """Renvoie les 4 sommets OBB d'un Segment en coordonnées monde"""
    wx_a = x + seg.A.x
    wy_a = y + seg.A.y
    wx_b = x + seg.B.x
    wy_b = y + seg.B.y
    dx = wx_b - wx_a
    dy = wy_b - wy_a
    le = sqrt(dx * dx + dy * dy)
    if le < 1e-10:
        hw = seg.width * 0.5
        return [
            (wx_a - hw, wy_a - hw), (wx_a + hw, wy_a - hw),
            (wx_a + hw, wy_a + hw), (wx_a - hw, wy_a + hw),
        ]
    ux, uy = dx / le, dy / le
    nx, ny = -uy, ux
    hw = seg.width * 0.5
    return [
        (wx_a + nx * hw, wy_a + ny * hw),
        (wx_b + nx * hw, wy_b + ny * hw),
        (wx_b - nx * hw, wy_b - ny * hw),
        (wx_a - nx * hw, wy_a - ny * hw),
    ]


def _closest_pt_on_seg(sx: float, sy: float, sdx: float, sdy: float,px: float, py: float) -> tuple[float, float]:
    """Point le plus proche de (px,py) sur le segment (sx,sy)→(sx+sdx,sy+sdy)"""
    len_sq = sdx * sdx + sdy * sdy
    if len_sq < 1e-10:
        return sx, sy
    t = max(0.0, min(1.0, ((px - sx) * sdx + (py - sy) * sdy) / len_sq))
    return sx + t * sdx, sy + t * sdy


def _closest_pt_seg_to_seg(ax: float, ay: float, adx: float, ady: float,bx: float, by: float, bdx: float, bdy: float,) -> tuple[float, float]:
    """Point sur le segment A le plus proche du segment B"""
    a_len_sq = adx * adx + ady * ady
    b_len_sq = bdx * bdx + bdy * bdy
    rx, ry = ax - bx, ay - by
    e = rx * bdx + ry * bdy
    f = adx * bdx + ady * bdy

    if a_len_sq < 1e-10 and b_len_sq < 1e-10:
        return ax, ay
    if a_len_sq < 1e-10:
        s = max(0.0, min(1.0, e / b_len_sq))
    else:
        c = rx * adx + ry * ady
        if b_len_sq < 1e-10:
            s = 0.0
            t = max(0.0, min(1.0, -c / a_len_sq))
            return ax + t * adx, ay + t * ady
        else:
            denom = a_len_sq * b_len_sq - f * f
            t = max(0.0, min(1.0, (f * e - c * b_len_sq) / denom)) if abs(denom) > 1e-10 else 0.0
            s = max(0.0, min(1.0, (f * t + e) / b_len_sq))
            t = max(0.0, min(1.0, (f * s - c) / a_len_sq))
            return ax + t * adx, ay + t * ady

    return bx + s * bdx, by + s * bdy


def _closest_pt_on_ellipse(cx: float, cy: float, rx: float, ry: float,px: float, py: float,) -> tuple[float, float]:
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


def _point_in_convex_poly(px: float, py: float, pts: list) -> bool:
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


def _half_extents(shape: Shape) -> tuple[float, float]:
    """Demi-dimensions AABB d'une shape"""
    _, _, w, h = shape.bounding_box()
    return 0.5 * w, 0.5 * h

def _aabb_fallback(sa, ax: float, ay: float, sb, bx: float, by: float) -> Contact | None:
    """Fallback AABB pour les paires sans narrowphase dédiée"""
    def _bounds(shape, x, y):
        if isinstance(shape, Ellipse):
            return x - shape.rx, y - shape.ry, shape.rx * 2, shape.ry * 2
        if isinstance(shape, Segment):
            dx = abs(shape.B.x - shape.A.x)
            dy = abs(shape.B.y - shape.A.y)
            return x, y, dx + shape.width * 2, dy + shape.width * 2
        if isinstance(shape, Capsule):
            hw, hh = _half_extents(shape)
            return x - hw, y - hh, hw * 2, hh * 2
        return x, y, 1.0, 1.0

    ax2, ay2, aw, ah = _bounds(sa, ax, ay)
    bx2, by2, bw, bh = _bounds(sb, bx, by)

    a_cx, a_cy = ax2 + aw * 0.5, ay2 + ah * 0.5
    b_cx, b_cy = bx2 + bw * 0.5, by2 + bh * 0.5
    dx, dy = a_cx - b_cx, a_cy - b_cy
    ox = (aw + bw) * 0.5 - abs(dx)
    oy = (ah + bh) * 0.5 - abs(dy)
    if ox <= 0 or oy <= 0:
        return None
    if ox < oy:
        return Contact(Vector(1.0 if dx > 0 else -1.0, 0.0), ox)
    return Contact(Vector(0.0, 1.0 if dy > 0 else -1.0), oy)