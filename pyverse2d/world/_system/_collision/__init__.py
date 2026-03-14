# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...._flag import UpdatePhase
from ....abc import System
from ....math import Vector

from ..._world import World
from ..._component import Transform, RigidBody, Collider

from .._physics import PhysicsSystem

from ._registry import dispatch, Contact
from . import _circle, _rect, _capsule, _polygon, _segment, _ellipse  # noqa: F401

from math import sqrt

# ======================================== CONSTANTES ========================================
_SLOP      = 1.0   # pénétration ignorée (pixels) — évite la jitter au repos
_BAUMGARTE = 0.8   # fraction de correction appliquée par frame

# ======================================== HELPERS ========================================
def _shape_world_origin(tr: Transform, col: Collider) -> tuple[float, float]:
    """Retourne la position de l'origine locale de la shape dans l'espace monde"""
    ox, oy, bw, bh = col.shape.bounding_box()
    x = tr.x + (-ox - tr.anchor.x * bw) + col.offset[0]
    y = tr.y + (-oy - tr.anchor.y * bh) + col.offset[1]
    return x, y


def _bbox_center_world(tr: Transform, col: Collider) -> tuple[float, float, float, float]:
    """
    Retourne le centre monde du bounding box et ses demi-dimensions.
    Utilisé pour le pre-reject AABB.
    """
    ox, oy, bw, bh = col.shape.bounding_box()
    wx = tr.x + (-ox - tr.anchor.x * bw) + col.offset[0]
    wy = tr.y + (-oy - tr.anchor.y * bh) + col.offset[1]
    cx = wx + ox + bw * 0.5
    cy = wy + oy + bh * 0.5
    return cx, cy, bw * 0.5, bh * 0.5


# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système de détection et résolution des collisions"""
    phase = UpdatePhase.UPDATE
    exclusive = True
    requires = (PhysicsSystem,)

    def __init__(self, broadphase: bool = True, iterations: int = 3):
        self._hash: _SpatialHash | None = _SpatialHash() if broadphase else None
        self._iterations: int = max(1, int(iterations))

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

        for _ in range(self._iterations):
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
    def _detect(
        self,
        col_a: Collider, tr_a: Transform,
        col_b: Collider, tr_b: Transform,
    ) -> Contact | None:
        # Origine monde de chaque shape
        ax, ay = _shape_world_origin(tr_a, col_a)
        bx, by = _shape_world_origin(tr_b, col_b)

        # Pre-reject AABB
        a_cx, a_cy, ahw, ahh = _bbox_center_world(tr_a, col_a)
        b_cx, b_cy, bhw, bhh = _bbox_center_world(tr_b, col_b)
        if abs(a_cx - b_cx) > ahw + bhw or abs(a_cy - b_cy) > ahh + bhh:
            return None

        return dispatch(col_a.shape, ax, ay, col_b.shape, bx, by)

    # ======================================== RÉSOLUTION ========================================
    def _resolve(self, a, b, contact: Contact):
        """Correction de position (Baumgarte+slop), impulsion, friction, annulation acc"""
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

        # Correction de position
        correction = max(depth - _SLOP, 0.0) * _BAUMGARTE

        if correction > 0:
            if static_a:
                tr_b.x -= normal.x * correction
                tr_b.y -= normal.y * correction
            elif static_b:
                tr_a.x += normal.x * correction
                tr_a.y += normal.y * correction
            else:
                inv_a = 1.0 / rb_a.mass
                inv_b = 1.0 / rb_b.mass
                inv_sum = inv_a + inv_b
                if inv_sum > 0:
                    ra = inv_a / inv_sum
                    rb = inv_b / inv_sum
                    tr_a.x += normal.x * correction * ra
                    tr_a.y += normal.y * correction * ra
                    tr_b.x -= normal.x * correction * rb
                    tr_b.y -= normal.y * correction * rb

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

        # Impulsion normale
        j  = -(1.0 + restitution) * vel_along / inv_sum
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

        # Annulation de l'accélération dans la direction du contact
        if not static_a:
            proj = rb_a._acceleration.x * normal.x + rb_a._acceleration.y * normal.y
            if proj < 0:
                rb_a._acceleration = Vector(
                    rb_a._acceleration.x - proj * normal.x,
                    rb_a._acceleration.y - proj * normal.y,
                )
        if not static_b:
            proj = rb_b._acceleration.x * (-normal.x) + rb_b._acceleration.y * (-normal.y)
            if proj < 0:
                rb_b._acceleration = Vector(
                    rb_b._acceleration.x + proj * normal.x,
                    rb_b._acceleration.y + proj * normal.y,
                )

    # ======================================== PUBLIC ========================================
    def reset_calibration(self):
        """Force une recalibration au prochain update"""
        if self._hash is not None:
            self._hash._cell_size = None
            self._hash.clear_static()


# ======================================== SPATIAL HASH ========================================
class _SpatialHash:
    """Grille spatiale broadphase"""

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
            _, _, w, h = e.get(Collider).shape.bounding_box()
            hw, hh = w * 0.5, h * 0.5
            if hw > max_extent: max_extent = hw
            if hh > max_extent: max_extent = hh
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
        ox, oy, bw, bh = col.shape.bounding_box()
        cs = self._cell_size

        # Position monde de l'origine locale
        wx = tr.x + (-ox - tr.anchor.x * bw) + col.offset[0]
        wy = tr.y + (-oy - tr.anchor.y * bh) + col.offset[1]

        if rb is not None and not rb.is_static():
            # Swept AABB
            pwx = rb.prev_x + (-ox - tr.anchor.x * bw) + col.offset[0]
            pwy = rb.prev_y + (-oy - tr.anchor.y * bh) + col.offset[1]
            min_x = min(wx + ox, pwx + ox)
            max_x = max(wx + ox + bw, pwx + ox + bw)
            min_y = min(wy + oy, pwy + oy)
            max_y = max(wy + oy + bh, pwy + oy + bh)
        else:
            min_x = wx + ox
            max_x = wx + ox + bw
            min_y = wy + oy
            max_y = wy + oy + bh

        for cx in range(int(min_x // cs), int(max_x // cs) + 1):
            for cy in range(int(min_y // cs), int(max_y // cs) + 1):
                key = (cx, cy)
                if key not in cells:
                    cells[key] = []
                cells[key].append(entity)

    def get_pairs(self) -> list[tuple]:
        seen: set[tuple[int, int]] = set()
        pairs: list[tuple] = []

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