# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._component import Transform, RigidBody, Collider
from ._registry import world_center

# ======================================== SPATIAL HASH ========================================
class SpatialHash:
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
        """Calibre la taille des cellules sur les shapes dynamiques présentes"""
        extents = []
        for e in entities:
            rb = e.get(RigidBody) if e.has(RigidBody) else None
            if rb is None or rb.is_static():
                continue
            col: Collider = e.get(Collider)
            tr: Transform = e.get(Transform)
            cx_, cy_ = world_center(col.shape, tr, col.offset)
            x_min, y_min, x_max, y_max = col.shape.world_bounding_box(cx_, cy_, tr.scale, tr.rotation)
            extents.append((x_max - x_min) * 0.5)
            extents.append((y_max - y_min) * 0.5)
        if not extents:
            self._cell_size = 64.0
            return
        extents.sort()
        median = extents[len(extents) // 2]
        self._cell_size = max(median * 2.5, 16.0)

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

    def _insert(self, cells, entity, col: Collider, tr: Transform, rb):
        """Insère une entité dans les cellules qu'elle occupe"""
        cs = self._cell_size
        cx_, cy_ = world_center(col.shape, tr, col.offset)
        w_min_x, w_min_y, w_max_x, w_max_y = col.shape.world_bounding_box(cx_, cy_, tr.scale, tr.rotation)

        if rb is not None and not rb.is_static():
            prev_cx = rb.prev_x - (tr.x - cx_)
            prev_cy = rb.prev_y - (tr.y - cy_)
            prev_min_x, prev_min_y, prev_max_x, prev_max_y = col.shape.world_bounding_box(prev_cx, prev_cy, tr.scale, tr.rotation)
            min_x = min(w_min_x, prev_min_x)
            max_x = max(w_max_x, prev_max_x)
            min_y = min(w_min_y, prev_min_y)
            max_y = max(w_max_y, prev_max_y)
        else:
            min_x, max_x, min_y, max_y = w_min_x, w_max_x, w_min_y, w_max_y

        for gx in range(int(min_x // cs), int(max_x // cs) + 1):
            for gy in range(int(min_y // cs), int(max_y // cs) + 1):
                key = (gx, gy)
                if key not in cells:
                    cells[key] = []
                cells[key].append(entity)