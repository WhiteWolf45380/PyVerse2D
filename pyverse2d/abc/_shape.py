from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Self
import math
import numpy as np
from numpy.typing import NDArray

from ..math import Point


class Shape(ABC):
    """Classe abstraite de base pour toutes les formes géométriques"""
    __slots__ = (
        "_vertices",
        "_cache_key", "_cache_rotscale", "_cache_world",
    )

    def __init__(self) -> None:
        self._vertices: NDArray[np.float32] | None = None
        self._cache_key: tuple | None = None
        self._cache_rotscale: NDArray[np.float32] | None = None
        self._cache_world: NDArray[np.float32] | None = None

    # ======================================== CONTRACT ========================================
    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...

    @abstractmethod
    def get_perimeter(self) -> float: ...

    @abstractmethod
    def get_area(self) -> float: ...

    @abstractmethod
    def get_vertices(self) -> NDArray[np.float32]:
        """Vertices locaux (N, 2), float32, origine = centre géométrique"""
        ...

    @abstractmethod
    def get_bounding_box(self) -> tuple[float, float, float, float]:
        """``(x_min, y_min, x_max, y_max)`` en espace local."""
        ...

    @abstractmethod
    def contains(self, point: Point) -> bool:
        """Teste si *point* est à l'intérieur de la forme en espace local."""
        ...

    @abstractmethod
    def copy(self) -> Self: ...

    @abstractmethod
    def scale(self, factor: float) -> None: ...

    # ======================================== WORLD TRANSFORM ========================================
    def world_vertices(
        self,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
        rotation: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
    ) -> NDArray[np.float32]:
        """Vertices en coordonnées monde

        Args:
            x: position horizontale monde
            y: position verticale monde
            scale: facteur d'échelle uniforme
            rotation: angle en degrés (sens trigonométrique)
            anchor_x: ancre relative horizontale [0, 1]
            anchor_y: ancre relative verticale [0, 1]
        """
        key = (scale, rotation, x, y, anchor_x, anchor_y)
        if self._cache_key == key:
            return self._cache_world

        if self._cache_key is None or self._cache_key[:2] != (scale, rotation):
            if self._vertices is None:
                self._vertices = self.get_vertices()
            rad = math.radians(rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            R = np.array(
                [[cos_r, -sin_r],
                 [sin_r,  cos_r]],
                dtype=np.float32,
            )
            self._cache_rotscale = self._vertices * scale @ R

        self._cache_world = self._cache_rotscale + self._world_translation(x, y, anchor_x, anchor_y)
        self._cache_key = key
        return self._cache_world

    def world_bounding_box(
        self,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
        rotation: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
    ) -> tuple[float, float, float, float]:
        """AABB ``(x_min, y_min, x_max, y_max)`` en coordonnées monde"""
        pts = self.world_vertices(x, y, scale, rotation, anchor_x, anchor_y)
        return (
            float(pts[:, 0].min()),
            float(pts[:, 1].min()),
            float(pts[:, 0].max()),
            float(pts[:, 1].max()),
        )

    def world_contains(
        self,
        point: Point,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
        rotation: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
    ) -> bool:
        """Hit-test en coordonnées monde

        Args:
            point: coordonnées du point à tester
            x: position horizontale monde
            y: position verticale monde
            scale: facteur d'échelle uniforme
            rotation: angle en degrés (sens trigonométrique)
            anchor_x: ancre relative horizontale [0, 1]
            anchor_y: ancre relative verticale [0, 1]
        """
        t = self._world_translation(x, y, anchor_x, anchor_y)
        px = float(point[0]) - float(t[0])
        py = float(point[1]) - float(t[1])

        if rotation:
            rad = math.radians(rotation)
            cos_r, sin_r = math.cos(rad), math.sin(rad)
            px, py = px * cos_r + py * sin_r, -px * sin_r + py * cos_r

        if scale != 1.0:
            px /= scale
            py /= scale

        return self.contains((px, py))

    # ======================================== CACHE ========================================
    def _invalidate_geometry(self) -> None:
        """Invalide la géométrie locale"""
        self._vertices = None
        self._cache_key = None
        self._cache_rotscale = None
        self._cache_world = None

    def _invalidate_transform(self) -> None:
        """Invalide le cache monde"""
        self._cache_key = None
        self._cache_rotscale = None
        self._cache_world = None

    # ======================================== INTERNALS ========================================
    def _anchor_offset(self, anchor_x: float, anchor_y: float) -> NDArray[np.float32]:
        """Offset local correspondant au point d'ancrage dans la bounding box"""
        xmin, ymin, xmax, ymax = self.bounding_box
        return np.array(
            [xmin + anchor_x * (xmax - xmin),
             ymin + anchor_y * (ymax - ymin)],
            dtype=np.float32,
        )

    def _world_translation(
        self,
        x: float,
        y: float,
        anchor_x: float,
        anchor_y: float,
    ) -> NDArray[np.float32]:
        """Translation nette"""
        return np.array([x, y], dtype=np.float32) - self._anchor_offset(anchor_x, anchor_y)