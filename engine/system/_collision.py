# ======================================== IMPORTS ========================================
from __future__ import annotations

from math import sqrt, cos, sin, atan2, pi as _PI

from ..ecs import System, UpdatePhase, World
from ..component import Transform, RigidBody
from ..component._collider import Collider
from ..math import Vector
from ..shape import Circle, Rect, Capsule, Ellipse, Segment, Polygon

from typing import NamedTuple

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """
    Système de détection et résolution des collisions

    Narrowphase :
        Circle   x {Circle, Rect, Capsule, Polygon, Ellipse, Segment}
        Rect     x {Rect, Capsule, Polygon, Segment}
        Capsule  x {Capsule, Rect, Polygon, Segment}
        Polygon  x {Polygon, Capsule, Segment}
        Segment  x {Circle, Rect, Capsule, Polygon, Segment}
        Ellipse  x {Ellipse, Circle}
    Fallback AABB pour les collisions non supportées

    Args:
        broadphase(bool): active la grille spatiale (False = brute-force, debug)
    """
    phase = UpdatePhase.UPDATE

    def __init__(self, broadphase: bool = True):
        self._hash: _SpatialHash | None = _SpatialHash() if broadphase else None

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        entities = world.query(Collider, Transform)

        if self._hash is not None:
            if self._hash._cell_size is None:
                self._hash.calibrate(entities)
            self._hash.update_dynamic(entities)
            pairs = self._hash.get_pairs()
        else:
            n = len(entities)
            pairs = [
                (entities[i], entities[j])
                for i in range(n)
                for j in range(i + 1, n)
            ]

        for a, b in pairs:
            col_a: Collider = a.get(Collider)
            col_b: Collider = b.get(Collider)

            if not col_a.is_active() or not col_b.is_active():
                continue
            if not col_a.collides_with(col_b):
                continue

            contact = self._detect(col_a, a.get(Transform), col_b, b.get(Transform))
            if contact is None:
                continue
            if col_a.is_trigger() or col_b.is_trigger():
                continue

            self._resolve(a, b, contact)

    # ======================================== DÉTECTION ========================================
    def _detect(self, col_a: Collider, tr_a: Transform, col_b: Collider, tr_b: Transform,) -> Contact | None:
        """Dispatche vers la bonne narrowphase selon les types de shapes"""
        ax = tr_a.x + col_a.offset[0]
        ay = tr_a.y + col_a.offset[1]
        bx = tr_b.x + col_b.offset[0]
        by = tr_b.y + col_b.offset[1]
        sa = col_a.shape
        sb = col_b.shape

        # ---- Pre-reject AABB ----
        ahw, ahh = _half_extents(sa)
        bhw, bhh = _half_extents(sb)
        if abs(ax - bx) > ahw + bhw or abs(ay - by) > ahh + bhh:
            return None

        # ---- Circle ----
        if isinstance(sa, Circle):
            if isinstance(sb, Circle):
                return self._circle_circle(ax, ay, sa.radius, bx, by, sb.radius)
            if isinstance(sb, Rect):
                return self._circle_rect(ax, ay, sa.radius, bx, by, sb.width, sb.height)
            if isinstance(sb, Capsule):
                return self._circle_capsule(ax, ay, sa.radius, bx, by, sb.radius, sb.spine)
            if isinstance(sb, Polygon):
                return self._circle_pts(ax, ay, sa.radius,
                                        [(bx + p.x, by + p.y) for p in sb.points])
            if isinstance(sb, Ellipse):
                return self._circle_ellipse(ax, ay, sa.radius, bx, by, sb.rx, sb.ry)
            if isinstance(sb, Segment):
                c = self._circle_pts(ax, ay, sa.radius, _seg_corners(bx, by, sb))
                return c

        # ---- Rect ----
        if isinstance(sa, Rect):
            if isinstance(sb, Circle):
                c = self._circle_rect(bx, by, sb.radius, ax, ay, sa.width, sa.height)
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Rect):
                return self._rect_rect(ax, ay, sa.width, sa.height, bx, by, sb.width, sb.height)
            if isinstance(sb, Capsule):
                pts = _rect_corners(ax, ay, sa.width, sa.height)
                c = self._capsule_convex(bx, by, sb.spine, sb.radius, pts)
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Polygon):
                return self._rect_polygon(ax, ay, sa.width, sa.height, bx, by, sb)
            if isinstance(sb, Segment):
                return _sat(_rect_corners(ax, ay, sa.width, sa.height),
                             _seg_corners(bx, by, sb))

        # ---- Capsule ----
        if isinstance(sa, Capsule):
            if isinstance(sb, Circle):
                c = self._circle_capsule(bx, by, sb.radius, ax, ay, sa.radius, sa.spine)
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Capsule):
                return self._capsule_capsule(
                    ax, ay, sa.radius, sa.spine,
                    bx, by, sb.radius, sb.spine,
                )
            if isinstance(sb, Rect):
                pts = _rect_corners(bx, by, sb.width, sb.height)
                return self._capsule_convex(ax, ay, sa.spine, sa.radius, pts)
            if isinstance(sb, Polygon):
                pts = [(bx + p.x, by + p.y) for p in sb.points]
                return self._capsule_convex(ax, ay, sa.spine, sa.radius, pts)
            if isinstance(sb, Segment):
                pts = _seg_corners(bx, by, sb)
                return self._capsule_convex(ax, ay, sa.spine, sa.radius, pts)

        # ---- Polygon ----
        if isinstance(sa, Polygon):
            if isinstance(sb, Polygon):
                return self._polygon_polygon(ax, ay, sa, bx, by, sb)
            if isinstance(sb, Circle):
                c = self._circle_pts(bx, by, sb.radius,
                                     [(ax + p.x, ay + p.y) for p in sa.points])
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Rect):
                c = self._rect_polygon(bx, by, sb.width, sb.height, ax, ay, sa)
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Capsule):
                pts = [(ax + p.x, ay + p.y) for p in sa.points]
                c = self._capsule_convex(bx, by, sb.spine, sb.radius, pts)
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Segment):
                return _sat(
                    [(ax + p.x, ay + p.y) for p in sa.points],
                    _seg_corners(bx, by, sb),
                )

        # ---- Segment ----
        if isinstance(sa, Segment):
            seg_pts_a = _seg_corners(ax, ay, sa)
            if isinstance(sb, Circle):
                c = self._circle_pts(bx, by, sb.radius, seg_pts_a)
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Rect):
                return _sat(seg_pts_a, _rect_corners(bx, by, sb.width, sb.height))
            if isinstance(sb, Capsule):
                c = self._capsule_convex(bx, by, sb.spine, sb.radius, seg_pts_a)
                return Contact(-c.normal, c.depth) if c else None
            if isinstance(sb, Polygon):
                return _sat(seg_pts_a, [(bx + p.x, by + p.y) for p in sb.points])
            if isinstance(sb, Segment):
                return _sat(seg_pts_a, _seg_corners(bx, by, sb))

        # ---- Ellipse ----
        if isinstance(sa, Ellipse):
            if isinstance(sb, Ellipse):
                return self._ellipse_ellipse(ax, ay, sa.rx, sa.ry, bx, by, sb.rx, sb.ry)
            if isinstance(sb, Circle):
                c = self._circle_ellipse(bx, by, sb.radius, ax, ay, sa.rx, sa.ry)
                return Contact(-c.normal, c.depth) if c else None
            # Rect, Capsule, Polygon, Segment: AABB fallback below

        return self._aabb_fallback(sa, ax, ay, sb, bx, by)

    # ======================================== NARROWPHASE ========================================
    def _circle_circle(self, ax, ay, ra, bx, by, rb) -> Contact | None:
        """Cercle vs Cercle"""
        dx = ax - bx
        dy = ay - by
        dist_sq = dx * dx + dy * dy
        radii = ra + rb
        if dist_sq >= radii * radii:
            return None
        dist = sqrt(dist_sq) or 1e-8
        return Contact(Vector(dx / dist, dy / dist), radii - dist)

    def _circle_rect(self, cx, cy, r, rx, ry, rw, rh) -> Contact | None:
        """Cercle vs Rect"""
        half_w = rw * 0.5
        half_h = rh * 0.5
        rc_x = rx + half_w
        rc_y = ry + half_h
        dx = cx - rc_x
        dy = cy - rc_y
        near_x = rc_x + max(-half_w, min(half_w, dx))
        near_y = rc_y + max(-half_h, min(half_h, dy))
        ddx = cx - near_x
        ddy = cy - near_y
        dist_sq = ddx * ddx + ddy * ddy
        if dist_sq >= r * r:
            return None
        dist = sqrt(dist_sq) or 1e-8
        return Contact(Vector(ddx / dist, ddy / dist), r - dist)

    def _rect_rect(self, ax, ay, aw, ah, bx, by, bw, bh) -> Contact | None:
        """Rect vs Rect"""
        a_cx = ax + aw * 0.5
        a_cy = ay + ah * 0.5
        b_cx = bx + bw * 0.5
        b_cy = by + bh * 0.5
        dx = a_cx - b_cx
        dy = a_cy - b_cy
        ox = (aw + bw) * 0.5 - abs(dx)
        oy = (ah + bh) * 0.5 - abs(dy)
        if ox <= 0 or oy <= 0:
            return None
        if ox < oy:
            return Contact(Vector(1.0 if dx > 0 else -1.0, 0.0), ox)
        return Contact(Vector(0.0, 1.0 if dy > 0 else -1.0), oy)

    def _circle_capsule(self, cx, cy, cr, capx, capy, cap_r, spine) -> Contact | None:
        """Cercle vs Capsule"""
        closest_x = capx                               # segment vertical : X fixe
        closest_y = max(capy, min(capy + spine, cy))   # clamp Y sur le spine
        return self._circle_circle(cx, cy, cr, closest_x, closest_y, cap_r)

    def _capsule_capsule(self, ax, ay, ar, a_spine, bx, by, br, b_spine) -> Contact | None:
        """Capsule vs Capsule"""
        px, py = _closest_pt_seg_to_seg(ax, ay, 0.0, a_spine, bx, by, 0.0, b_spine)
        qx, qy = _closest_pt_on_seg(bx, by, 0.0, b_spine, px, py)
        return self._circle_circle(px, py, ar, qx, qy, br)

    def _circle_pts(self, cx, cy, cr, pts: list) -> Contact | None:
        """Cercle vs Polygone"""
        n = len(pts)
        min_depth = float("inf")
        best_nx = 0.0
        best_ny = 0.0

        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            ex = x2 - x1
            ey = y2 - y1
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
                best_nx, best_ny = nx, ny

        near_x, near_y = min(pts, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        dx = cx - near_x
        dy = cy - near_y
        le = sqrt(dx * dx + dy * dy) or 1e-8
        nx, ny = dx / le, dy / le

        min_p = min(qx * nx + qy * ny for qx, qy in pts)
        max_p = max(qx * nx + qy * ny for qx, qy in pts)
        pc = cx * nx + cy * ny

        ov = min(pc + cr, max_p) - max(pc - cr, min_p)
        if ov <= 0:
            return None
        if ov < min_depth:
            min_depth = ov
            best_nx, best_ny = nx, ny

        cent_x = sum(p[0] for p in pts) / n
        cent_y = sum(p[1] for p in pts) / n
        if (cx - cent_x) * best_nx + (cy - cent_y) * best_ny < 0:
            best_nx, best_ny = -best_nx, -best_ny

        return Contact(Vector(best_nx, best_ny), min_depth)

    def _circle_polygon(self, cx, cy, cr, px, py, poly: Polygon) -> Contact | None:
        return self._circle_pts(cx, cy, cr, [(px + p.x, py + p.y) for p in poly.points])

    def _rect_polygon(self, rx, ry, rw, rh, px, py, poly: Polygon) -> Contact | None:
        return _sat(_rect_corners(rx, ry, rw, rh),
                    [(px + p.x, py + p.y) for p in poly.points])

    def _polygon_polygon(self, ax, ay, poly_a: Polygon, bx, by, poly_b: Polygon) -> Contact | None:
        return _sat([(ax + p.x, ay + p.y) for p in poly_a.points],
                    [(bx + p.x, by + p.y) for p in poly_b.points])

    def _capsule_convex(
        self, ax: float, ay: float, spine: float, radius: float,
        pts: list,
    ) -> Contact | None:
        """Capsule vs All"""
        n = len(pts)
        min_dist = float("inf")
        best_sx, best_sy = ax, ay + spine * 0.5
        best_ex, best_ey = pts[0]

        for i in range(n):
            px1, py1 = pts[i]
            px2, py2 = pts[(i + 1) % n]
            edx = px2 - px1
            edy = py2 - py1

            sp_x, sp_y = _closest_pt_seg_to_seg(ax, ay, 0.0, spine, px1, py1, edx, edy)
            ep_x, ep_y = _closest_pt_on_seg(px1, py1, edx, edy, sp_x, sp_y)

            ddx = sp_x - ep_x
            ddy = sp_y - ep_y
            dist = sqrt(ddx * ddx + ddy * ddy)

            if dist < min_dist:
                min_dist = dist
                best_sx, best_sy = sp_x, sp_y
                best_ex, best_ey = ep_x, ep_y

        mid_x = ax
        mid_y = ay + spine * 0.5
        if min_dist > 1e-6 and _point_in_convex_poly(mid_x, mid_y, pts):
            near_dist = float("inf")
            near_ex, near_ey = pts[0]
            for i in range(n):
                px1, py1 = pts[i]
                px2, py2 = pts[(i + 1) % n]
                ep_x, ep_y = _closest_pt_on_seg(px1, py1, px2 - px1, py2 - py1, mid_x, mid_y)
                ddx = mid_x - ep_x
                ddy = mid_y - ep_y
                d = sqrt(ddx * ddx + ddy * ddy)
                if d < near_dist:
                    near_dist = d
                    near_ex, near_ey = ep_x, ep_y
            ddx = mid_x - near_ex
            ddy = mid_y - near_ey
            d = sqrt(ddx * ddx + ddy * ddy) or 1e-8
            return Contact(Vector(ddx / d, ddy / d), radius + near_dist)

        if min_dist >= radius:
            return None

        depth = radius - min_dist
        ddx = best_sx - best_ex
        ddy = best_sy - best_ey
        dist = sqrt(ddx * ddx + ddy * ddy)
        if dist < 1e-8:
            cent_x = sum(p[0] for p in pts) / n
            cent_y = sum(p[1] for p in pts) / n
            ddx = mid_x - cent_x
            ddy = mid_y - cent_y
            dist = sqrt(ddx * ddx + ddy * ddy) or 1e-8
        return Contact(Vector(ddx / dist, ddy / dist), depth)

    def _circle_ellipse(self, cx, cy, cr, ex, ey, rx, ry) -> Contact | None:
        """Cercle vs Ellipse"""
        lx = (cx - ex) / rx
        ly = (cy - ey) / ry
        inside = lx * lx + ly * ly <= 1.0

        cpx, cpy = _closest_pt_on_ellipse(ex, ey, rx, ry, cx, cy)
        dx = cx - cpx
        dy = cy - cpy
        dist = sqrt(dx * dx + dy * dy) or 1e-8

        if inside:
            return Contact(Vector(dx / dist, dy / dist), cr + dist)
        if dist >= cr:
            return None
        return Contact(Vector(dx / dist, dy / dist), cr - dist)

    def _ellipse_ellipse(self, ax, ay, rx_a, ry_a, bx, by, rx_b, ry_b) -> Contact | None:
        """Ellipse vs Ellipse"""
        cdx = bx - ax
        cdy = by - ay

        if cdx == 0.0 and cdy == 0.0:
            return Contact(Vector(1.0, 0.0), rx_a + rx_b)

        _STEP = _PI / 12
        best_ov = float("inf")
        best_theta = atan2(cdy, cdx) % _PI

        for i in range(12):
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

            ov_pp = h_a_pp + h_b_pp + c_proj_abs  # +|c·d| car d²|c·d|/dθ² = -|c·d|

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

    def _aabb_fallback(self, sa, ax, ay, sb, bx, by) -> Contact | None:
        """Fallback AABB pour les combinaisons sans narrowphase dédiée (ex. Ellipse×Rect)"""
        def bounds(shape, x, y):
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

        ax2, ay2, aw, ah = bounds(sa, ax, ay)
        bx2, by2, bw, bh = bounds(sb, bx, by)
        return self._rect_rect(ax2, ay2, aw, ah, bx2, by2, bw, bh)

    # ======================================== RÉSOLUTION ========================================
    def _resolve(self, a, b, contact: Contact):
        """Résout la collision : correction de position pondérée + impulsion + friction"""
        has_rb_a = a.has(RigidBody)
        has_rb_b = b.has(RigidBody)
        rb_a: RigidBody | None = a.get(RigidBody) if has_rb_a else None
        rb_b: RigidBody | None = b.get(RigidBody) if has_rb_b else None
        static_a = (not has_rb_a) or rb_a.is_static()
        static_b = (not has_rb_b) or rb_b.is_static()

        if static_a and static_b:
            return

        if has_rb_a and rb_a.is_sleeping():
            rb_a.wake()
        if has_rb_b and rb_b.is_sleeping():
            rb_b.wake()

        tr_a: Transform = a.get(Transform)
        tr_b: Transform = b.get(Transform)
        normal = contact.normal
        depth = contact.depth

        # Correction de position pondérée par la masse inverse
        if static_a:
            tr_b.x -= normal.x * depth
            tr_b.y -= normal.y * depth
        elif static_b:
            tr_a.x += normal.x * depth
            tr_a.y += normal.y * depth
        else:
            inv_a = 1.0 / rb_a.mass
            inv_b = 1.0 / rb_b.mass
            inv_sum = inv_a + inv_b
            if inv_sum > 0:
                ra = inv_a / inv_sum
                rb = inv_b / inv_sum
                tr_a.x += normal.x * depth * ra
                tr_a.y += normal.y * depth * ra
                tr_b.x -= normal.x * depth * rb
                tr_b.y -= normal.y * depth * rb

        if not has_rb_a or not has_rb_b:
            return

        rel_vx = rb_a.velocity.x - rb_b.velocity.x
        rel_vy = rb_a.velocity.y - rb_b.velocity.y
        vel_along = rel_vx * normal.x + rel_vy * normal.y

        if vel_along > 0:
            return

        restitution = min(rb_a.restitution, rb_b.restitution)
        inv_a = 0.0 if static_a else 1.0 / rb_a.mass
        inv_b = 0.0 if static_b else 1.0 / rb_b.mass
        inv_sum = inv_a + inv_b

        if inv_sum == 0:
            return

        j = -(1.0 + restitution) * vel_along / inv_sum
        ix = normal.x * j
        iy = normal.y * j

        if not static_a:
            rb_a.velocity = Vector(rb_a.velocity.x + ix * inv_a, rb_a.velocity.y + iy * inv_a)
        if not static_b:
            rb_b.velocity = Vector(rb_b.velocity.x - ix * inv_b, rb_b.velocity.y - iy * inv_b)

        # Friction tangentielle
        friction = (rb_a.friction + rb_b.friction) * 0.5
        tx = rel_vx - vel_along * normal.x
        ty = rel_vy - vel_along * normal.y
        t_len = sqrt(tx * tx + ty * ty) or 1e-8
        tx /= t_len
        ty /= t_len
        jt = -(rel_vx * tx + rel_vy * ty) / inv_sum
        jt = max(-abs(j) * friction, min(abs(j) * friction, jt))

        if not static_a:
            rb_a.velocity = Vector(
                rb_a.velocity.x + tx * jt * inv_a,
                rb_a.velocity.y + ty * jt * inv_a,
            )
        if not static_b:
            rb_b.velocity = Vector(
                rb_b.velocity.x - tx * jt * inv_b,
                rb_b.velocity.y - ty * jt * inv_b,
            )

    # ======================================== PUBLIC ========================================
    def reset_calibration(self):
        """Force une recalibration au prochain update (changement de scène, etc.)"""
        if self._hash is not None:
            self._hash._cell_size = None
            self._hash.clear_static()


# ======================================== SPATIAL HASH ========================================
class _SpatialHash:
    """
    Grille spatiale broadphase.
    - Statiques : insérés une seule fois dans _static_cells, recyclés entre frames.
    - Dynamiques : reconstruits chaque frame avec AABB swept (anti-tunneling).
    - Pairs statique-statique : ignorées.
    - Pair keys : id() Python (int natif, O(1)).
    """

    def __init__(self):
        self._cell_size: float | None = None
        self._dynamic_cells: dict[tuple[int, int], list] = {}
        self._static_cells: dict[tuple[int, int], list] = {}
        self._static_built: bool = False

    def clear_static(self):
        self._static_cells.clear()
        self._static_built = False

    def calibrate(self, entities: list):
        max_extent = 0.0
        for e in entities:
            hw, hh = _half_extents(e.get(Collider).shape)
            if hw > max_extent:
                max_extent = hw
            if hh > max_extent:
                max_extent = hh
        self._cell_size = max(max_extent * 2.0, 1.0)

    def update_dynamic(self, entities: list):
        self._dynamic_cells.clear()
        rebuild = not self._static_built
        for entity in entities:
            col: Collider = entity.get(Collider)
            if not col.is_active():
                continue
            rb = entity.get(RigidBody) if entity.has(RigidBody) else None
            is_static = (rb is None) or rb.is_static()
            if is_static:
                if rebuild:
                    self._insert(self._static_cells, entity, col, entity.get(Transform), None)
            else:
                self._insert(self._dynamic_cells, entity, col, entity.get(Transform), rb)
        if rebuild:
            self._static_built = True

    def _insert(self, cells, entity, col: Collider, tr: Transform, rb):
        x = tr.x + col.offset[0]
        y = tr.y + col.offset[1]
        hw, hh = _half_extents(col.shape)
        cs = self._cell_size
        if rb is not None and not rb.is_static():
            px = rb.prev_x + col.offset[0]
            py = rb.prev_y + col.offset[1]
            min_x, max_x = min(x, px) - hw, max(x, px) + hw
            min_y, max_y = min(y, py) - hh, max(y, py) + hh
        else:
            min_x, max_x = x - hw, x + hw
            min_y, max_y = y - hh, y + hh

        for cx in range(int(min_x // cs), int(max_x // cs) + 1):
            for cy in range(int(min_y // cs), int(max_y // cs) + 1):
                key = (cx, cy)
                if key not in cells:
                    cells[key] = []
                cells[key].append(entity)

    def get_pairs(self) -> list[tuple]:
        seen: set[tuple[int, int]] = set()
        pairs: list[tuple] = []

        # Dynamique-dynamique
        for cell in self._dynamic_cells.values():
            n = len(cell)
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = cell[i], cell[j]
                    ia, ib = id(a), id(b)
                    key = (ia, ib) if ia < ib else (ib, ia)
                    if key not in seen:
                        seen.add(key)
                        pairs.append((a, b))

        # Dynamique-statique
        for ck, dyn in self._dynamic_cells.items():
            stat = self._static_cells.get(ck)
            if not stat:
                continue
            for d in dyn:
                for s in stat:
                    id_d, id_s = id(d), id(s)
                    key = (id_d, id_s) if id_d < id_s else (id_s, id_d)
                    if key not in seen:
                        seen.add(key)
                        pairs.append((d, s))

        return pairs


# ======================================== SAT POLYGON ========================================
def _sat(pts_a: list, pts_b: list) -> Contact | None:
    """
    SAT pour deux polygones convexes en coordonnées monde.
    Normale orientée de B vers A.
    Note : pour les polygones concaves, décomposer en convexes avant appel.
    """
    min_depth = float("inf")
    best_nx = 0.0
    best_ny = 0.0

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

    # Orienter de B vers A
    ca_x = sum(p[0] for p in pts_a) / len(pts_a)
    ca_y = sum(p[1] for p in pts_a) / len(pts_a)
    cb_x = sum(p[0] for p in pts_b) / len(pts_b)
    cb_y = sum(p[1] for p in pts_b) / len(pts_b)
    if (ca_x - cb_x) * best_nx + (ca_y - cb_y) * best_ny < 0:
        best_nx, best_ny = -best_nx, -best_ny

    return Contact(Vector(best_nx, best_ny), min_depth)


# ======================================== HELPERS GÉOMÉTRIQUES ========================================
def _rect_corners(x: float, y: float, w: float, h: float) -> list:
    """Renvoie les 4 sommets d'un Rect en coordonnées monde (sens anti-horaire)"""
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _seg_corners(x: float, y: float, seg: Segment) -> list:
    """
    Renvoie les 4 sommets OBB d'un Segment en coordonnées monde.
    Le segment est un rectangle orienté selon AB, d'épaisseur totale seg.width.
    """
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
            (wx_a - hw, wy_a - hw),
            (wx_a + hw, wy_a - hw),
            (wx_a + hw, wy_a + hw),
            (wx_a - hw, wy_a + hw),
        ]

    ux, uy = dx / le, dy / le   # direction AB
    nx, ny = -uy, ux             # normale perpendiculaire
    hw = seg.width * 0.5         # demi-épaisseur

    return [
        (wx_a + nx * hw, wy_a + ny * hw),
        (wx_b + nx * hw, wy_b + ny * hw),
        (wx_b - nx * hw, wy_b - ny * hw),
        (wx_a - nx * hw, wy_a - ny * hw),
    ]


def _closest_pt_on_seg(
    sx: float, sy: float, sdx: float, sdy: float,
    px: float, py: float,
) -> tuple[float, float]:
    """Point le plus proche de (px,py) sur le segment (sx,sy)→(sx+sdx,sy+sdy)"""
    len_sq = sdx * sdx + sdy * sdy
    if len_sq < 1e-10:
        return sx, sy
    t = max(0.0, min(1.0, ((px - sx) * sdx + (py - sy) * sdy) / len_sq))
    return sx + t * sdx, sy + t * sdy


def _closest_pt_seg_to_seg(
    ax: float, ay: float, adx: float, ady: float,
    bx: float, by: float, bdx: float, bdy: float,
) -> tuple[float, float]:
    """
    Point sur le segment A le plus proche du segment B.
    Algorithme Ericson (Real-Time Collision Detection §5.1.9).
    """
    a_len_sq = adx * adx + ady * ady
    b_len_sq = bdx * bdx + bdy * bdy
    rx, ry = ax - bx, ay - by
    e = rx * bdx + ry * bdy
    f = adx * bdx + ady * bdy

    if a_len_sq < 1e-10 and b_len_sq < 1e-10:
        return ax, ay
    if a_len_sq < 1e-10:
        t = 0.0
        s = max(0.0, min(1.0, e / b_len_sq))
    else:
        c = rx * adx + ry * ady
        if b_len_sq < 1e-10:
            s = 0.0
            t = max(0.0, min(1.0, -c / a_len_sq))
        else:
            denom = a_len_sq * b_len_sq - f * f
            t = max(0.0, min(1.0, (f * e - c * b_len_sq) / denom)) if abs(denom) > 1e-10 else 0.0
            s = max(0.0, min(1.0, (f * t + e) / b_len_sq))
            t = max(0.0, min(1.0, (f * s - c) / a_len_sq))

    return ax + t * adx, ay + t * ady


def _closest_pt_on_ellipse(
    cx: float, cy: float, rx: float, ry: float,
    px: float, py: float,
) -> tuple[float, float]:
    """
    Point le plus proche sur l'ellipse (cx,cy,rx,ry) du point (px,py).
    Newton-Raphson sur la dérivée de la distance carrée.

    f(t) = -rx·sin(t)·(rx·cos(t)-lx) + ry·cos(t)·(ry·sin(t)-ly) = 0
    Estimation initiale : angle de (lx/rx, ly/ry) dans l'espace elliptique.
    """
    lx = px - cx
    ly = py - cy
    t = atan2(ly * rx, lx * ry)  # angle dans l'espace normalisé

    for _ in range(25):
        ct, st = cos(t), sin(t)
        ex = rx * ct
        ey = ry * st

        f = -rx * st * (ex - lx) + ry * ct * (ey - ly)
        fp = (-rx * ct * (ex - lx) + rx * rx * st * st
              - ry * st * (ey - ly) + ry * ry * ct * ct)

        if abs(fp) < 1e-12:
            break
        delta = f / fp
        t -= delta
        if abs(delta) < 1e-9:
            break

    ct, st = cos(t), sin(t)
    return cx + rx * ct, cy + ry * st


def _point_in_convex_poly(px: float, py: float, pts: list) -> bool:
    """
    Vérifie si (px,py) est à l'intérieur d'un polygone convexe.
    Agnostique au sens de rotation (CW ou CCW).
    """
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


# ======================================== AABB HELPER ========================================
def _half_extents(shape) -> tuple[float, float]:
    """Renvoie les demi-dimensions AABB d'une shape"""
    if isinstance(shape, Circle):
        return shape.radius, shape.radius
    if isinstance(shape, Rect):
        return shape.width * 0.5, shape.height * 0.5
    if isinstance(shape, Capsule):
        return shape.radius, (shape.spine + shape.radius * 2) * 0.5
    if isinstance(shape, Ellipse):
        return shape.rx, shape.ry
    if isinstance(shape, Polygon):
        xs = [p.x for p in shape.points]
        ys = [p.y for p in shape.points]
        return (max(xs) - min(xs)) * 0.5, (max(ys) - min(ys)) * 0.5
    if isinstance(shape, Segment):
        dx = abs(shape.B.x - shape.A.x)
        dy = abs(shape.B.y - shape.A.y)
        return dx * 0.5 + shape.width * 0.5, dy * 0.5 + shape.width * 0.5
    return 32.0, 32.0


# ======================================== CONTACT ========================================
class Contact(NamedTuple):
    """Résultat d'une détection de collision"""
    normal: Vector
    depth: float