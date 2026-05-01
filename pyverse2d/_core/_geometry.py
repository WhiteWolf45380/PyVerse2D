from __future__ import annotations

from ..abc import Shape
from ..math import Point, Vector
from ._transform import Transform

import math
import numpy as np
from numpy.typing import NDArray

class Geometry:
    """Objet géométrique positionnel
    
    Args:
        shape: géométrie locale ``Shape``
        transform: transformation monde ``Transform``
        offset: décalage optionnel par rapport au transform
    """
    __slots__ = (
        "_shape", "_transform", "_offset",
        "_cache_key",
        "_cache_rotscale_vertices",
        "_cache_world_vertices",
        "_cache_world_bounding_box",
        "_cache_world_center",
        "_dirty_rotscale",
        "_dirty_world_vertices",
        "_dirty_world_bounding_box",
        "_dirty_world_center",
        "_cached_tx", "_cached_ty",
        "_cached_ax", "_cached_ay",
        "_cached_cos_r", "_cached_sin_r",
    )

    def __init__(self, shape: Shape, transform: Transform, offset: Vector = None):
        # Attributs publiques
        self._shape: Shape = shape
        self._transform: Transform = transform
        self._offset: Vector | None = offset

        # Caches de données
        self._cache_key: tuple | None = None
        self._cache_rotscale_vertices: NDArray[np.float32] | None = None
        self._cache_world_vertices: NDArray[np.float32] | None = None
        self._cache_world_bounding_box: tuple[float, float, float, float] | None = None
        self._cache_world_center: tuple[float, float] | None = None

        # Caches de valeurs
        self._cached_tx: float = 0.0
        self._cached_ty: float = 0.0
        self._cached_ax: float = 0.0
        self._cached_ay: float = 0.0
        self._cached_cos_r: float = 1.0
        self._cached_sin_r: float = 0.0
        
        # Flags
        self._dirty_rotscale: bool = True
        self._dirty_world_vertices: bool = True
        self._dirty_world_bounding_box: bool = True
        self._dirty_world_center: bool = True

    # ======================================== PROPERTIES ========================================
    @property
    def shape(self) -> Shape:
        """Forme géométrique"""
        return self._shape
    
    @property
    def transform(self) -> Transform:
        """Transformation monde"""
        return self._transform
    
    @property
    def offset(self) -> Vector:
        """Décalage par rapport au ``Transform``"""

    # ======================================== WORLD TRANSFORM ========================================
    def world_vertices(self) -> NDArray[np.float32]:
        """Vertices en coordonnées monde"""
        self._check_dirty()
        if self._dirty_world_vertices:
            self._compute_world_vertices()
        return self._cache_world_vertices

    def world_bounding_box(self) -> tuple[float, float, float, float]:
        """AABB ``(x_min, y_min, x_max, y_max)`` en coordonnées monde"""
        self._check_dirty()
        if self._dirty_world_bounding_box:
            self._compute_world_bounding_box()
        return self._cache_world_bounding_box

    def world_center(self) -> tuple[float, float]:
        """Centre géométrique monde"""
        self._check_dirty()
        if self._dirty_world_center:
            self._compute_world_center()
        return self._cache_world_center

    def world_contains(self, point: Point) -> bool:
        """Hit-test en coordonnées monde"""
        self._check_dirty()
        px = point[0] - self._cached_tx
        py = point[1] - self._cached_ty
        if self._transform.rotation != 0.0:
            px, py = (
                px * self._cached_cos_r + py * self._cached_sin_r,
                -px * self._cached_sin_r + py * self._cached_cos_r,
            )
        if self._transform.scale != 1.0:
            s = self._transform.scale
            px /= s
            py /= s
        return self._shape.contains((px + self._cached_ax, py + self._cached_ay))

    # ======================================== CACHE ========================================
    def _check_dirty(self) -> None:
        """Détecte les changements du transform et lève les dirty flags concernés"""
        t = self._transform
        if self._offset is not None:
            tx = t.x + self._offset.x
            ty = t.y + self._offset.y
        else:
            tx = t.x
            ty = t.y
        key = (tx, ty, t.anchor_x, t.anchor_y, t.scale, t.rotation)
        if key == self._cache_key:
            return

        prev = self._cache_key
        self._cache_key = key
        self._cached_tx = tx
        self._cached_ty = ty

        if prev is None or key[2:] != prev[2:]:
            xmin, ymin, xmax, ymax = self._shape.get_bounding_box()
            self._cached_ax = xmin + t.anchor_x * (xmax - xmin)
            self._cached_ay = ymin + t.anchor_y * (ymax - ymin)
            rad = math.radians(t.rotation)
            self._cached_cos_r = math.cos(rad)
            self._cached_sin_r = math.sin(rad)
            self._dirty_rotscale = True
            self._dirty_world_vertices = True
            self._dirty_world_bounding_box = True
            self._dirty_world_center = True
        else:
            self._dirty_world_vertices = True
            self._dirty_world_bounding_box = True
            self._dirty_world_center = True

    def _invalidate_transform(self) -> None:
        """Invalide tous les caches"""
        self._cache_key = None
        self._dirty_rotscale = True
        self._dirty_world_vertices = True
        self._dirty_world_bounding_box = True
        self._dirty_world_center = True

    # ======================================== COMPUTE ========================================
    def _compute_rotscale(self) -> None:
        """Calcule les vertices après rotation et scale (sans translation)"""
        R = np.array(
            [[self._cached_cos_r,  self._cached_sin_r],
             [-self._cached_sin_r, self._cached_cos_r]],
            dtype=np.float32,
        )
        vertices = self._shape.get_vertices()
        anchor = np.array([self._cached_ax, self._cached_ay], dtype=np.float32)
        self._cache_rotscale_vertices = (vertices - anchor) * self._transform.scale @ R
        self._dirty_rotscale = False

    def _compute_world_vertices(self) -> None:
        """Calcule les vertices en coordonnées monde"""
        if self._dirty_rotscale:
            self._compute_rotscale()
        self._cache_world_vertices = self._cache_rotscale_vertices + np.array(
            [self._cached_tx, self._cached_ty], dtype=np.float32,
        )
        self._dirty_world_vertices = False

    def _compute_world_bounding_box(self) -> None:
        """Calcule l'AABB en coordonnées monde"""
        if self._dirty_world_vertices:
            self._compute_world_vertices()
        pts = self._cache_world_vertices
        self._cache_world_bounding_box = (
            float(pts[:, 0].min()),
            float(pts[:, 1].min()),
            float(pts[:, 0].max()),
            float(pts[:, 1].max()),
        )
        self._dirty_world_bounding_box = False

    def _compute_world_center(self) -> None:
        """Calcule le centre géométrique en coordonnées monde"""
        ax, ay = self._cached_ax, self._cached_ay
        s = self._transform.scale
        scaled_ax = ax * s
        scaled_ay = ay * s
        self._cache_world_center = (
            self._cached_tx - (scaled_ax * self._cached_cos_r - scaled_ay * self._cached_sin_r),
            self._cached_ty - (scaled_ax * self._cached_sin_r + scaled_ay * self._cached_cos_r),
        )
        self._dirty_world_center = False