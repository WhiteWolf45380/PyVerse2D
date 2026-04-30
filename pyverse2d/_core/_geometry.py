# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..abc import Shape
from ..math import Point
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
        "_shape", "_transform",
        "_cache_key", "_cache_rotscale", "_cache_world",
    )

    def __init__(self, shape: Shape, transform: Transform):
        # Géométrie
        self._shape: Shape = shape
        self._transform: Transform = transform

        # Caches
        self._cache_key: tuple | None = None
        self._cache_rotscale_vertices: NDArray[np.float32] | None = None
        self._cache_world_vertices: NDArray[np.float32] | None = None
        self._cache_world_bounding_box: tuple[float, float, float, float] | None = None

    # ======================================== WORLD TRANSFORM ========================================
    def world_vertices(self) -> NDArray[np.float32]:
        """Vertices en coordonnées monde"""
        t = self._transform
        key = (t.x, t.y, t.anchor_x, t.anchor_y, t.scale, t.rotation)
        if self._cache_key == key:
            return self._cache_world_vertices

        vertices = self._shape.get_vertices()
        ax, ay = _anchor_offset(self._shape.get_bounding_box(), t.anchor_x, t.anchor_y)

        if self._cache_key is None or self._cache_key[2:] != key[2:]:
            rad = math.radians(t.rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            R = np.array([[cos_r, sin_r], [-sin_r, cos_r]], dtype=np.float32)
            self._cache_rotscale_vertices = (vertices - np.array([ax, ay], dtype=np.float32)) * t.scale @ R

        self._cache_world_vertices = self._cache_rotscale_vertices + np.array([t.x, t.y], dtype=np.float32)
        self._cache_key = key
        return self._cache_world_vertices

    def world_bounding_box(self) -> tuple[float, float, float, float]:
        """AABB ``(x_min, y_min, x_max, y_max)`` en coordonnées monde"""
        t = self._transform
        key = (t.x, t.y, t.anchor_x, t.anchor_y, t.scale, t.rotation)
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
        ax, ay = _anchor_offset(self._shape.get_bounding_box(), t.anchor_x, t.anchor_y)
        px = point[0] - t.x
        py = point[1] - t.y
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