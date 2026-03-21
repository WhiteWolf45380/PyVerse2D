# ======================================== IMPORTS ========================================
from __future__ import annotations

from math import sqrt

import numpy as np
from numpy.typing import NDArray

from .....math import Vector
from .....abc import VertexShape
from .._registry import (
    Contact,
    closest_pt_on_seg, closest_pt_seg_to_seg,
    closest_pt_on_ellipse, point_in_convex_poly,
)

# ======================================== HELPERS ========================================
def vertex_world_pts(sv: VertexShape, x: float, y: float, scale: float, rotation: float) -> NDArray[np.float32]:
    """Renvoie les vertices monde d'une VertexShape sous forme de ndarray (N, 2)"""
    return sv.world_vertices(x, y, scale, rotation)

# ======================================== SAT ========================================
def sat(pts_a: NDArray[np.float32], pts_b: NDArray[np.float32]) -> Contact | None:
    """SAT vectorisé pour deux polygones convexes"""
    min_depth = float("inf")
    best_nx, best_ny = 0.0, 1.0

    for pts, other in ((pts_a, pts_b), (pts_b, pts_a)):
        # Calcul des arêtes et normales vectorisé
        edges = np.roll(pts, -1, axis=0) - pts               # (N, 2)
        lengths = np.linalg.norm(edges, axis=1, keepdims=True)
        mask = lengths[:, 0] > 1e-10
        normals = np.where(
            np.repeat(mask[:, np.newaxis], 2, axis=1),
            np.stack([-edges[:, 1], edges[:, 0]], axis=1) / np.where(lengths > 1e-10, lengths, 1.0),
            0.0
        )

        for i in range(len(pts)):
            if not mask[i]:
                continue
            nx, ny = float(normals[i, 0]), float(normals[i, 1])

            # Projections vectorisées
            proj_a = pts @ np.array([nx, ny], dtype=np.float32)
            proj_b = other @ np.array([nx, ny], dtype=np.float32)
            min_a, max_a = float(proj_a.min()), float(proj_a.max())
            min_b, max_b = float(proj_b.min()), float(proj_b.max())

            ov = min(max_a, max_b) - max(min_a, min_b)
            if ov <= 0:
                return None
            if ov < min_depth:
                min_depth = ov
                best_nx, best_ny = nx, ny

    # Orientation de la normale : pointe de B vers A
    ca = pts_a.mean(axis=0)
    cb = pts_b.mean(axis=0)
    if float((ca[0] - cb[0]) * best_nx + (ca[1] - cb[1]) * best_ny) < 0:
        best_nx, best_ny = -best_nx, -best_ny

    return Contact(Vector._make(best_nx, best_ny), min_depth)

# ======================================== CIRCLE VS POLYGONE ========================================
def circle_vs_pts(cx: float, cy: float, cr: float, pts: NDArray[np.float32]) -> Contact | None:
    """Cercle vs polygone convexe"""
    n = len(pts)
    min_depth = float("inf")
    best_nx, best_ny = 0.0, 1.0

    pg_cx = float(pts.mean(axis=0)[0])
    pg_cy = float(pts.mean(axis=0)[1])

    # Test des axes des arêtes vectorisé
    edges = np.roll(pts, -1, axis=0) - pts
    lengths = np.linalg.norm(edges, axis=1)

    for i in range(n):
        le = float(lengths[i])
        if le < 1e-10:
            continue
        nx = float(-edges[i, 1]) / le
        ny = float(edges[i, 0]) / le

        nv = np.array([nx, ny], dtype=np.float32)
        proj = pts @ nv
        min_p, max_p = float(proj.min()), float(proj.max())
        pc = cx * nx + cy * ny
        ov = min(pc + cr, max_p) - max(pc - cr, min_p)
        if ov <= 0:
            return None
        if ov < min_depth:
            min_depth = ov
            best_nx, best_ny = nx, ny

    # Axe vers le vertex le plus proche
    diffs = pts - np.array([cx, cy], dtype=np.float32)
    dists_sq = (diffs ** 2).sum(axis=1)
    nearest = int(dists_sq.argmin())
    ddx = cx - float(pts[nearest, 0])
    ddy = cy - float(pts[nearest, 1])
    le = sqrt(ddx * ddx + ddy * ddy) or 1e-8
    nx, ny = ddx / le, ddy / le

    nv = np.array([nx, ny], dtype=np.float32)
    proj = pts @ nv
    min_p, max_p = float(proj.min()), float(proj.max())
    pc = cx * nx + cy * ny
    ov = min(pc + cr, max_p) - max(pc - cr, min_p)
    if ov <= 0:
        return None
    if ov < min_depth:
        min_depth = ov
        best_nx, best_ny = nx, ny

    # Orientation stable
    to_cx = cx - pg_cx
    to_cy = cy - pg_cy
    if best_nx * to_cx + best_ny * to_cy < 0:
        best_nx, best_ny = -best_nx, -best_ny

    return Contact(Vector._make(best_nx, best_ny), min_depth)

# ======================================== ELLIPSE VS POLYGONE ========================================
def ellipse_vs_pts(ex: float, ey: float, rx: float, ry: float, pts: NDArray[np.float32]) -> Contact | None:
    """Ellipse vs polygone convexe"""
    n = len(pts)
    min_ov = float("inf")
    best_nx, best_ny = 0.0, 1.0
    center = pts.mean(axis=0)
    pg_cx, pg_cy = float(center[0]), float(center[1])

    def _test_axis(nx: float, ny: float) -> bool:
        nonlocal min_ov, best_nx, best_ny
        le = sqrt(nx * nx + ny * ny)
        if le < 1e-10:
            return True
        nx /= le
        ny /= le
        h = sqrt(rx * rx * nx * nx + ry * ry * ny * ny)
        ec = ex * nx + ey * ny
        nv = np.array([nx, ny], dtype=np.float32)
        projs = pts @ nv
        min_p, max_p = float(projs.min()), float(projs.max())
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

    # Test axes des arêtes
    edges = np.roll(pts, -1, axis=0) - pts
    for i in range(n):
        if not _test_axis(float(-edges[i, 1]), float(edges[i, 0])):
            return None

    # Axe vers le point le plus proche sur le polygone
    min_d2 = float("inf")
    cpx, cpy = float(pts[0, 0]), float(pts[0, 1])
    for i in range(n):
        x1, y1 = float(pts[i, 0]), float(pts[i, 1])
        x2, y2 = float(pts[(i + 1) % n, 0]), float(pts[(i + 1) % n, 1])
        px_, py_ = closest_pt_on_seg(x1, y1, x2 - x1, y2 - y1, ex, ey)
        d2 = (px_ - ex) ** 2 + (py_ - ey) ** 2
        if d2 < min_d2:
            min_d2 = d2
            cpx, cpy = px_, py_
    if not _test_axis(cpx - ex, cpy - ey):
        return None

    return Contact(Vector._make(best_nx, best_ny), min_ov)

# ======================================== CAPSULE VS POLYGONE ========================================
def capsule_vs_pts(ax: float, ay: float, bx: float, by: float, r: float, pts: NDArray[np.float32]) -> Contact | None:
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
        px1, py1 = float(pts[i, 0]), float(pts[i, 1])
        px2, py2 = float(pts[(i + 1) % n, 0]), float(pts[(i + 1) % n, 1])
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

    # Cas capsule entièrement dans le polygone
    if min_dist > 1e-6 and point_in_convex_poly(mid_x, mid_y, [(float(pts[i, 0]), float(pts[i, 1])) for i in range(n)]):
        near_dist = float("inf")
        near_nx, near_ny = 0.0, 1.0
        for i in range(n):
            px1, py1 = float(pts[i, 0]), float(pts[i, 1])
            px2, py2 = float(pts[(i + 1) % n, 0]), float(pts[(i + 1) % n, 1])
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
        return Contact(Vector._make(near_nx, near_ny), r + near_dist)

    if min_dist >= r:
        return None

    # Orientation de la normale
    poly_cx = float(pts.mean(axis=0)[0])
    poly_cy = float(pts.mean(axis=0)[1])
    to_mid_x = mid_x - poly_cx
    to_mid_y = mid_y - poly_cy
    if best_nx * to_mid_x + best_ny * to_mid_y < 0:
        best_nx, best_ny = -best_nx, -best_ny

    return Contact(Vector._make(best_nx, best_ny), r - min_dist)