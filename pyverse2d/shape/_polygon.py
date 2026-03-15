# _polygon.py
from __future__ import annotations

from .._internal import expect
from ..abc import VertexShape
from ..math import Point

from numbers import Real
import numpy as np
from numpy.typing import NDArray


class Polygon(VertexShape):
    """
    Forme géométrique 2D avec sommets : Polygone

    Args:
        points(Point): sommets du polygone (minimum 3)
    """
    __slots__ = ("_source_vertices",)

    def __init__(self, *points: Point):
        if len(points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        if len(set(points)) != len(points):
            raise ValueError("Polygon must not have duplicate points")
        self._source_vertices: NDArray[np.float32] = np.array(
            [(p.x, p.y) for p in points], dtype=np.float32
        )
        super().__init__()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du polygone"""
        pts = [tuple(v) for v in self._vertices]
        return f"Polygon(points={pts})"

    def __str__(self) -> str:
        """Renvoie une description lisible du polygone"""
        return f"Polygon[{len(self)} pts | area={self.area:.4g} | perimeter={self.perimeter:.4g}]"

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """
        Vérifie l'égalité géométrique de deux polygones, insensible à l'offset de départ

        Args:
            other(object): objet à comparer
        """
        if not isinstance(other, Polygon) or len(self) != len(other):
            return False
        n = len(self)
        return any(
            np.allclose(self._vertices, np.roll(other._vertices, offset, axis=0))
            for offset in range(n)
        )

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Polygon:
        """Renvoie une copie du polygone"""
        return Polygon(*[Point(v[0], v[1]) for v in self._source_vertices])

    def scale(self, factor: Real) -> None:
        """
        Redimensionne le polygone

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(expect(factor, Real))
        if factor <= 0:
            raise ValueError("factor must be strictly positive")
        self._vertices *= factor
        self._source_vertices *= factor
        self._cache_sr = None

    # ======================================== INTERNALS ========================================
    def _compute_vertices(self) -> NDArray[np.float32]:
        """Renvoie les sommets bruts depuis les points source"""
        return self._source_vertices.copy()