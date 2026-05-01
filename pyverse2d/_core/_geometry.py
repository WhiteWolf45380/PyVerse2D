# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..abc import Shape
from ..math import Point, Vector

from ._transform import Transform

import math
import numpy as np
from numpy.typing import NDArray

# ======================================== GEOMETRY ========================================
class Geometry:
    """Objet géométrique positionnel
    
    Args:
        shape: géométrie locale ``Shape``
        transform: transformation monde ``Transform``
    """
    __slots__ = (
        "_shape", "_transform", "_offset",
        "_cache_key", "_cache_rotscale_vertices", "_cache_world_vertices", "_cache_world_bounding_box",
    )

    def __init__(self, shape: Shape, transform: Transform, offset: Vector = None):
        # Géométrie
        self._shape: Shape = shape
        self._transform: Transform = transform
        self._offset: Vector | None = offset

        # Caches
        self._cache_key: tuple | None = None
        self._cache_rotscale_vertices: NDArray[np.float32] | None = None
        self._cache_world_vertices: NDArray[np.float32] | None = None
        self._cache_world_bounding_box: tuple[float, float, float, float] | None = None

    # ======================================== WORLD TRANSFORM ========================================
    def world_vertices(self) -> NDArray[np.float32]:
        """Vertices en coordonnées monde"""
        t = self._transform
        tx, ty = self._effective_position()
        key = self._make_key(tx, ty)
        if self._cache_key == key:
            return self._cache_world_vertices

        vertices = self._shape.get_vertices()
        ax, ay = _anchor_offset(self._shape.get_bounding_box(), t.anchor_x, t.anchor_y)

        if self._cache_key is None or self._cache_key[2:] != key[2:]:
            rad = math.radians(t.rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            R = np.array([[cos_r, sin_r], [-sin_r, cos_r]], dtype=np.float32)
            self._cache_rotscale_vertices = (vertices - np.array([ax, ay], dtype=np.float32)) * t.scale @ R

        self._cache_world_vertices = self._cache_rotscale_vertices + np.array([tx, ty], dtype=np.float32)
        self._cache_key = key
        return self._cache_world_vertices

    def world_bounding_box(self) -> tuple[float, float, float, float]:
        """AABB ``(x_min, y_min, x_max, y_max)`` en coordonnées monde"""
        t = self._transform
        tx, ty = self._effective_position()
        key = self._make_key(tx, ty)
        if self._cache_world_bounding_box is None or self._cache_key != key:
            pts = self.world_vertices()
            self._cache_world_bounding_box (
                float(pts[:, 0].min()),
                float(pts[:, 1].min()),
                float(pts[:, 0].max()),
                float(pts[:, 1].max()),
            )      
        return self._cache_world_bounding_box

    def world_contains(self, point: Point) -> bool:
        """Hit-test en coordonnées monde"""
        t = self._transform
        tx, ty = self._effective_position()
        ax, ay = _anchor_offset(self._shape.get_bounding_box(), t.anchor_x, t.anchor_y)
        px = point[0] - tx
        py = point[1] - ty
        if t.rotation != 0.0:
            rad = math.radians(t.rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            px, py = px * cos_r + py * sin_r, -px * sin_r + py * cos_r
        if t.scale != 1.0:
            px /= t.scale
            py /= t.scale
        return self._shape.contains((px + ax, py + ay))

    # ======================================== CACHE ========================================
    def _invalidate_transform(self) -> None:
        """Invalide le cache monde"""
        self._cache_key = None
        self._cache_rotscale_vertices = None
        self._cache_world_vertices = None
        self._cache_world_bounding_box = None

    def _effective_position(self) -> tuple[float, float]:
        """Renvoie la position effective"""
        t = self._transform
        if self._offset is not None:
            return t.x + self._offset.x, t.y + self._offset.y
        return t.x, t.y

    def _make_key(self, tx: float, ty: float) -> tuple:
        """Construit la clé de cache
        
        Args:
            tx: position effective horizontale
            ty: position effective verticale
        """
        t = self._transform
        return (tx, ty, t.anchor_x, t.anchor_y, t.scale, t.rotation)

# ======================================== HELPERS ========================================
def _anchor_offset(
        bounding_box: tuple[float, float, float, float],
        anchor_x: float,
        anchor_y: float,
    ) -> NDArray[np.float32]:
    """Calcul le décalage généré par l'ancre
    
    Args:
        bounding_box: hitbox locale
        anchor_x: ancre relative locale horizontale
        anchor_y: ancre relative locale verticale
    """
    xmin, ymin, xmax, ymax = bounding_box
    return np.array(
        [xmin + anchor_x * (xmax - xmin),
         ymin + anchor_y * (ymax - ymin)],
        dtype=np.float32,
    )