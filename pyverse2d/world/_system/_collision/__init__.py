# ======================================== IMPORTSs ========================================
from __future__ import annotations

from ...._flag import UpdatePhase
from ....abc import System
from ....math import Vector
from ..._world import World
from ..._component import Transform, RigidBody, Collider
from .._physics import PhysicsSystem
from ._registry import dispatch, Contact, world_center
from . import _circle, _ellipse, _capsule  # noqa: F401

from math import sqrt

# ======================================== CONSTANTES ========================================
_SLOP = 0.5
_BAUMGARTE = 0.2
_WARM_BIAS = 0.8
_MAX_CORRECTION = 8.0
_EXTRA_ITER_THRESHOLD = 4.0
_EXTRA_ITER = 4
_MAX_MASS_RATIO = 0.95

# ======================================== CACHED CONTACT ========================================
class _CachedContact:
    """
    Impulsions accumulées + normale lissée pour une paire de contacts persistante

    Args:
        jn: impulsion normale accumulée (≥ 0)
        jt: impulsion tangentielle accumulée (cône de Coulomb)
        normal: normale lissée entre frames
    """
    __slots__ = ("jn", "jt", "normal")

    def __init__(self):
        self.jn: float = 0.0
        self.jt: float = 0.0
        self.normal: tuple | None = None

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système de détection et résolution des collisions"""
    phase = UpdatePhase.UPDATE
    exclusive = True
    requires = (PhysicsSystem,)

    def __init__(self, broadphase: bool = True, iterations: int = 6):
        self._hash: _SpatialHash | None = _SpatialHash() if broadphase else None
        self._iterations: int = max(1, int(iterations))
        self._cache: dict[tuple[int, int], _CachedContact] = {}

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Détecte et résout les collisions pour toutes les entités actives

        Args:
            world(World): monde courant
            dt(float): delta temps
        """
        entities = world.query(Collider, Transform)

        if self._hash is not None:
            if self._hash._cell_size is None:
                self._hash.calibrate(entities)
            self._hash.update_dynamic(entities)
            pairs = self._hash.get_pairs()
        else:
            n = len(entities)
            pairs = [(entities[i], entities[j]) for i in range(n) for j in range(i + 1, n)]

        active_contacts = []
        active_keys: set[tuple[int, int]] = set()
        max_depth = 0.0

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

            ia, ib = id(a), id(b)
            key = (ia, ib) if ia < ib else (ib, ia)
            active_keys.add(key)

            if key not in self._cache:
                self._cache[key] = _CachedContact()

            cached = self._cache[key]

            nx, ny = contact.normal.x, contact.normal.y
            if cached.normal is not None:
                pnx, pny = cached.normal
                dot = nx * pnx + ny * pny
                if dot > 0.95:
                    mix = 0.7
                    mnx = nx * mix + pnx * (1.0 - mix)
                    mny = ny * mix + pny * (1.0 - mix)
                    n_len = sqrt(mnx * mnx + mny * mny) or 1.0
                    nx, ny = mnx / n_len, mny / n_len
                elif dot < 0:
                    cached.jn = 0.0
                    cached.jt = 0.0

            cached.normal = (nx, ny)
            contact = Contact(Vector(nx, ny), contact.depth)

            if contact.depth > max_depth:
                max_depth = contact.depth

            active_contacts.append((a, b, contact, cached))
            self._warm_start(a, b, contact, cached)

        for key in list(self._cache):
            if key not in active_keys:
                del self._cache[key]

        iterations = self._iterations
        if max_depth > _EXTRA_ITER_THRESHOLD:
            iterations += _EXTRA_ITER

        for _ in range(iterations):
            for a, b, contact, cached in active_contacts:
                self._resolve(a, b, contact, cached, dt)

    # ======================================== WARM START ========================================
    def _warm_start(self, a, b, contact: Contact, cached: _CachedContact):
        """Ré-applique les impulsions précédentes pour accélérer la convergence"""
        if not a.has(RigidBody) or not b.has(RigidBody):
            return
        rb_a: RigidBody = a.get(RigidBody)
        rb_b: RigidBody = b.get(RigidBody)
        static_a = rb_a.is_static()
        static_b = rb_b.is_static()
        if static_a and static_b:
            return

        nx, ny = contact.normal.x, contact.normal.y
        tx, ty = -ny, nx
        jn = cached.jn * _WARM_BIAS
        jt = cached.jt * _WARM_BIAS
        ix = nx * jn + tx * jt
        iy = ny * jn + ty * jt
        inv_a = 0.0 if static_a else 1.0 / rb_a.mass
        inv_b = 0.0 if static_b else 1.0 / rb_b.mass

        if not static_a:
            rb_a.velocity = Vector(rb_a.velocity.x + ix * inv_a, rb_a.velocity.y + iy * inv_a)
        if not static_b:
            rb_b.velocity = Vector(rb_b.velocity.x - ix * inv_b, rb_b.velocity.y - iy * inv_b)

    # ======================================== DÉTECTION ========================================
    def _detect(self, col_a: Collider, tr_a: Transform, col_b: Collider, tr_b: Transform) -> Contact | None:
        """Broadphase AABB puis dispatch narrowphase"""
        cx_a, cy_a = world_center(col_a.shape, tr_a, col_a.offset)
        cx_b, cy_b = world_center(col_b.shape, tr_b, col_b.offset)

        x_min_a, y_min_a, x_max_a, y_max_a = col_a.shape.bounding_box
        x_min_b, y_min_b, x_max_b, y_max_b = col_b.shape.bounding_box
        ahw = (x_max_a - x_min_a) * 0.5 * tr_a.scale
        ahh = (y_max_a - y_min_a) * 0.5 * tr_a.scale
        bhw = (x_max_b - x_min_b) * 0.5 * tr_b.scale
        bhh = (y_max_b - y_min_b) * 0.5 * tr_b.scale

        if abs(cx_a - cx_b) > ahw + bhw or abs(cy_a - cy_b) > ahh + bhh:
            return None

        return dispatch(
            col_a.shape, cx_a, cy_a, tr_a.scale, tr_a.rotation,
            col_b.shape, cx_b, cy_b, tr_b.scale, tr_b.rotation,
        )

    # ======================================== RÉSOLUTION ========================================
    def _resolve(self, a, b, contact: Contact, cached: _CachedContact, dt: float):
        """Sequential Impulse Solver avec vitesse prédictive"""
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
        nx, ny = contact.normal.x, contact.normal.y
        tx, ty = -ny, nx
        depth = contact.depth

        if not has_rb_a or not has_rb_b:
            correction = min(max(depth - _SLOP, 0.0) * _BAUMGARTE, _MAX_CORRECTION)
            if correction > 0:
                if static_a:
                    tr_b.x -= nx * correction
                    tr_b.y -= ny * correction
                else:
                    tr_a.x += nx * correction
                    tr_a.y += ny * correction
            return

        inv_a = 0.0 if static_a else 1.0 / rb_a.mass
        inv_b = 0.0 if static_b else 1.0 / rb_b.mass
        inv_sum = inv_a + inv_b
        if inv_sum == 0:
            return

        vax = rb_a.velocity.x + (rb_a._acceleration.x * dt if not static_a else 0.0)
        vay = rb_a.velocity.y + (rb_a._acceleration.y * dt if not static_a else 0.0)
        vbx = rb_b.velocity.x + (rb_b._acceleration.x * dt if not static_b else 0.0)
        vby = rb_b.velocity.y + (rb_b._acceleration.y * dt if not static_b else 0.0)
        rel_vx = vax - vbx
        rel_vy = vay - vby
        vel_along = rel_vx * nx + rel_vy * ny

        if vel_along < 0:
            correction = min(max(depth - _SLOP, 0.0) * _BAUMGARTE, _MAX_CORRECTION)
            if correction > 0:
                if static_a:
                    tr_b.x -= nx * correction
                    tr_b.y -= ny * correction
                elif static_b:
                    tr_a.x += nx * correction
                    tr_a.y += ny * correction
                else:
                    ra = min(inv_a / inv_sum, _MAX_MASS_RATIO)
                    rb = min(inv_b / inv_sum, _MAX_MASS_RATIO)
                    tr_a.x += nx * correction * ra
                    tr_a.y += ny * correction * ra
                    tr_b.x -= nx * correction * rb
                    tr_b.y -= ny * correction * rb

        restitution = min(rb_a.restitution, rb_b.restitution) if not static_a and not static_b else (rb_b.restitution if static_a else rb_a.restitution)

        if vel_along < -0.5:
            j_delta_n = -(1.0 + restitution) * vel_along / inv_sum
        else:
            bias = _BAUMGARTE * max(depth - _SLOP, 0.0)
            j_delta_n = -(vel_along + bias) / inv_sum

        old_jn = cached.jn
        cached.jn = max(0.0, old_jn + j_delta_n)
        j_delta_n = cached.jn - old_jn

        friction = (rb_a.friction + rb_b.friction) * 0.5 if not static_a and not static_b else (rb_b.friction if static_a else rb_a.friction)
        vel_tan = rel_vx * tx + rel_vy * ty
        j_delta_t = -vel_tan / inv_sum
        old_jt = cached.jt
        max_jt = friction * cached.jn
        cached.jt = max(-max_jt, min(max_jt, old_jt + j_delta_t))
        j_delta_t = cached.jt - old_jt

        ix = nx * j_delta_n + tx * j_delta_t
        iy = ny * j_delta_n + ty * j_delta_t

        if not static_a:
            rb_a.velocity = Vector(rb_a.velocity.x + ix * inv_a, rb_a.velocity.y + iy * inv_a)
        if not static_b:
            rb_b.velocity = Vector(rb_b.velocity.x - ix * inv_b, rb_b.velocity.y - iy * inv_b)

    # ======================================== PUBLIC ========================================
    def reset_calibration(self):
        """Réinitialise la calibration du spatial hash"""
        if self._hash is not None:
            self._hash._cell_size = None
            self._hash.clear_static()

    def clear_cache(self):
        """Vide le cache d'impulsions"""
        self._cache.clear()


# ======================================== SPATIAL HASH ========================================
class _SpatialHash:
    """Broadphase par grille spatiale"""

    def __init__(self):
        self._cell_size: float | None = None
        self._dynamic_cells: dict[tuple[int, int], list] = {}
        self._static_cells: dict[tuple[int, int], list] = {}
        self._static_built: bool = False

    def clear_static(self):
        """Vide les cellules statiques"""
        self._static_cells.clear()
        self._static_built = False

    def calibrate(self, entities: list):
        """Calibre la taille des cellules sur les shapes présentes"""
        max_extent = 0.0
        for e in entities:
            x_min, y_min, x_max, y_max = e.get(Collider).shape.bounding_box
            hw = (x_max - x_min) * 0.5
            hh = (y_max - y_min) * 0.5
            if hw > max_extent:
                max_extent = hw
            if hh > max_extent:
                max_extent = hh
        self._cell_size = max(max_extent * 2.0, 1.0)

    def update_dynamic(self, entities: list):
        """Met à jour les cellules dynamiques et reconstruit les statiques si nécessaire"""
        self._dynamic_cells.clear()
        rebuild = not self._static_built
        for entity in entities:
            col: Collider = entity.get(Collider)
            if not col.is_active():
                continue
            rb = entity.get(RigidBody) if entity.has(RigidBody) else None
            is_static = (rb is None) or rb.is_static()
            tr = entity.get(Transform)
            if is_static:
                if rebuild:
                    self._insert(self._static_cells, entity, col, tr, None)
            else:
                self._insert(self._dynamic_cells, entity, col, tr, rb)
        if rebuild:
            self._static_built = True

    def _insert(self, cells, entity, col: Collider, tr: Transform, rb):
        """Insère une entité dans les cellules qu'elle occupe"""
        x_min, y_min, x_max, y_max = col.shape.bounding_box
        cs = self._cell_size
        cx_, cy_ = world_center(col.shape, tr, col.offset)
        hw = (x_max - x_min) * 0.5 * tr.scale
        hh = (y_max - y_min) * 0.5 * tr.scale

        if rb is not None and not rb.is_static():
            prev_cx = rb.prev_x - (tr.x - cx_)
            prev_cy = rb.prev_y - (tr.y - cy_)
            min_x = min(cx_ - hw, prev_cx - hw)
            max_x = max(cx_ + hw, prev_cx + hw)
            min_y = min(cy_ - hh, prev_cy - hh)
            max_y = max(cy_ + hh, prev_cy + hh)
        else:
            min_x = cx_ - hw
            max_x = cx_ + hw
            min_y = cy_ - hh
            max_y = cy_ + hh

        for gx in range(int(min_x // cs), int(max_x // cs) + 1):
            for gy in range(int(min_y // cs), int(max_y // cs) + 1):
                key = (gx, gy)
                if key not in cells:
                    cells[key] = []
                cells[key].append(entity)

    def get_pairs(self) -> list[tuple]:
        """Renvoie les paires d'entités potentiellement en collision"""
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