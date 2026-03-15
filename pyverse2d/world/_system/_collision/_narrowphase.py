# _narrowphase.py
from __future__ import annotations

from math import sqrt

from ....math import Vector
from ....abc import VertexShape
from ....shape import Circle, Ellipse, Capsule

from ._registry import (
    Contact,
    closest_pt_on_seg, closest_pt_seg_to_seg,
    closest_pt_on_ellipse, point_in_convex_poly,
)

# ======================================== VERTEX HELPERS ========================================
def vertex_world_pts(sv: VertexShape, x, y, scale, rotation) -> list[tuple[float, float]]:
    """Renvoie les vertices monde d'une VertexShape"""
    return [tuple(v) for v in sv.world_vertices(x, y, scale, rotation)]

def dispatch_vertex_primitive(sv, vx, vy, scale_v, rot_v, sp, px, py, scale_p, rot_p) -> Contact | None:
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

# ======================================== SAT ========================================
def sat_vertex_vertex(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b) -> Contact | None:
    """SAT pour deux VertexShapes"""
    pts_a = vertex_world_pts(sa, ax, ay, scale_a, rot_a)
    pts_b = vertex_world_pts(sb, bx, by, scale_b, rot_b)
    return sat(pts_a, pts_b)

def sat(pts_a: list, pts_b: list) -> Contact | None:
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

    ca_x = sum(p[0] for p in pts_a) / len(pts_a)
    ca_y = sum(p[1] for p in pts_a) / len(pts_a)
    cb_x = sum(p[0] for p in pts_b) / len(pts_b)
    cb_y = sum(p[1] for p in pts_b) / len(pts_b)
    if (ca_x - cb_x) * best_nx + (ca_y - cb_y) * best_ny < 0:
        best_nx, best_ny = -best_nx, -best_ny

    return Contact(Vector(best_nx, best_ny), min_depth)

# ======================================== CIRCLE VS POLYGONE ========================================
def circle_vs_pts(cx: float, cy: float, cr: float, pts: list) -> Contact | None:
    """Cercle vs polygone convexe"""
    n = len(pts)
    min_depth = float("inf")
    best_nx, best_ny = 0.0, 1.0

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
            best_nx, best_ny = (nx, ny) if pc > (min_p + max_p) * 0.5 else (-nx, -ny)

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

# ======================================== ELLIPSE VS POLYGONE ========================================
def ellipse_vs_pts(ex: float, ey: float, rx: float, ry: float, pts: list) -> Contact | None:
    """Ellipse vs polygone convexe"""
    n = len(pts)
    min_ov = float("inf")
    best_nx, best_ny = 0.0, 1.0
    pg_cx = sum(p[0] for p in pts) / n
    pg_cy = sum(p[1] for p in pts) / n

    def _test_axis(nx: float, ny: float) -> bool:
        nonlocal min_ov, best_nx, best_ny
        le = sqrt(nx * nx + ny * ny)
        if le < 1e-10:
            return True
        nx /= le
        ny /= le
        h = sqrt(rx * rx * nx * nx + ry * ry * ny * ny)
        ec = ex * nx + ey * ny
        projs = [px * nx + py * ny for px, py in pts]
        min_p, max_p = min(projs), max(projs)
        ov = min(ec + h, max_p) - max(ec - h, min_p)
        if ov <= 0:
            return False
        if ov < min_ov:
            min_ov = ov
            mid = (min_p + max_p) * 0.5
            if abs(ec - mid) > 1e-6:
                best_nx, best_ny = (nx, ny) if ec > mid else (-nx, -ny)
            else:
                dx = ex - pg_cx
                dy = ey - pg_cy
                best_nx, best_ny = (nx, ny) if dx * nx + dy * ny > 0 else (-nx, -ny)
        return True

    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if not _test_axis(-(y2 - y1), x2 - x1):
            return None

    min_d2 = float("inf")
    cpx, cpy = pts[0]
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        px_, py_ = closest_pt_on_seg(x1, y1, x2 - x1, y2 - y1, ex, ey)
        d2 = (px_ - ex) ** 2 + (py_ - ey) ** 2
        if d2 < min_d2:
            min_d2 = d2
            cpx, cpy = px_, py_
    if not _test_axis(cpx - ex, cpy - ey):
        return None

    return Contact(Vector(best_nx, best_ny), min_ov)

# ======================================== CAPSULE VS POLYGONE ========================================
def capsule_vs_pts(ax: float, ay: float, bx: float, by: float, r: float, pts: list) -> Contact | None:
    """Capsule vs polygone convexe"""
    n = len(pts)
    spine_dx = bx - ax
    spine_dy = by - ay
    mid_x = ax + spine_dx * 0.5
    mid_y = ay + spine_dy * 0.5
    min_dist = float("inf")
    best_nx, best_ny = 0.0, 1.0
    best_sx, best_sy = mid_x, mid_y

    for i in range(n):
        px1, py1 = pts[i]
        px2, py2 = pts[(i + 1) % n]
        edx = px2 - px1
        edy = py2 - py1
        le = sqrt(edx * edx + edy * edy)
        if le < 1e-10:
            continue
        enx, eny = -edy / le, edx / le

        sp_x, sp_y = closest_pt_seg_to_seg(ax, ay, spine_dx, spine_dy, px1, py1, edx, edy)
        ep_x, ep_y = closest_pt_on_seg(px1, py1, edx, edy, sp_x, sp_y)
        ddx = sp_x - ep_x
        ddy = sp_y - ep_y
        dist = sqrt(ddx * ddx + ddy * ddy)

        if dist < min_dist:
            min_dist = dist
            best_sx, best_sy = sp_x, sp_y
            if dist > 1e-8:
                best_nx, best_ny = ddx / dist, ddy / dist
            else:
                best_nx, best_ny = enx, eny

    if min_dist > 1e-6 and point_in_convex_poly(mid_x, mid_y, pts):
        near_dist = float("inf")
        near_nx, near_ny = 0.0, 1.0
        for i in range(n):
            px1, py1 = pts[i]
            px2, py2 = pts[(i + 1) % n]
            edx = px2 - px1
            edy = py2 - py1
            le = sqrt(edx * edx + edy * edy)
            if le < 1e-10:
                continue
            ep_x, ep_y = closest_pt_on_seg(px1, py1, edx, edy, mid_x, mid_y)
            ddx = mid_x - ep_x
            ddy = mid_y - ep_y
            d = sqrt(ddx * ddx + ddy * ddy)
            if d < near_dist:
                near_dist = d
                if d > 1e-8:
                    near_nx, near_ny = ddx / d, ddy / d
                else:
                    near_nx, near_ny = -edy / le, edx / le
        return Contact(Vector(near_nx, near_ny), r + near_dist)

    if min_dist >= r:
        return None

    to_mid_x = mid_x - best_sx
    to_mid_y = mid_y - best_sy
    if best_nx * to_mid_x + best_ny * to_mid_y < 0:
        best_nx, best_ny = -best_nx, -best_ny

    return Contact(Vector(best_nx, best_ny), r - min_dist)