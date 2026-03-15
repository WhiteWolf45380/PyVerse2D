# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import PrimitiveShape

from numbers import Real
from typing import Iterator
import math

# ======================================== SHAPE ========================================
class Circle(PrimitiveShape):
    """
    Forme géométrique 2D : Cercle

    Args:
        radius(Real): rayon du cercle
    """
    __slots__ = ("_radius",)

    def __init__(self, radius: Real):
        self._radius: float = float(positive(not_null(expect(radius, Real))))
        super().__init__()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du cercle"""
        return f"Circle(radius={self._radius})"

    def __str__(self) -> str:
        """Renvoie une description lisible du cercle"""
        return f"Circle[r={self._radius} | area={self.area:.4g}]"

    def __iter__(self) -> Iterator[float]:
        """Renvoie les composants dans un itérateur"""
        yield self._radius

    def __hash__(self) -> int:
        """Renvoie le hash du cercle"""
        return hash(self.to_tuple())

    # ======================================== GETTERS ========================================
    @property
    def radius(self) -> float:
        """Renvoie le rayon du cercle"""
        return self._radius

    @property
    def diameter(self) -> float:
        """Renvoie le diamètre du cercle"""
        return 2 * self._radius

    @property
    def width(self) -> float:
        """Renvoie la largeur du cercle"""
        return self.diameter

    @property
    def height(self) -> float:
        """Renvoie la hauteur du cercle"""
        return self.diameter

    @property
    def perimeter(self) -> float:
        """Renvoie le périmètre du cercle"""
        return 2 * math.pi * self._radius

    @property
    def area(self) -> float:
        """Renvoie l'aire du cercle"""
        return math.pi * self._radius ** 2

    # ======================================== SETTERS ========================================
    @radius.setter
    def radius(self, value: Real):
        """
        Fixe le rayon du cercle

        Args:
            value(Real): nouveau rayon
        """
        self._radius = float(positive(not_null(expect(value, Real))))
        self._invalidate_cache()

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """
        Vérifie l'égalité de deux cercles

        Args:
            other(object): objet à comparer
        """
        if isinstance(other, Circle):
            return self._radius == other._radius
        return False

    # ======================================== PREDICATES ========================================
    def contains(self, point) -> bool:
        """
        Teste si un point est dans le cercle

        Args:
            point: point à tester
        """
        return float(point[0]) ** 2 + float(point[1]) ** 2 <= self._radius ** 2

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Circle:
        """Renvoie une copie du cercle"""
        return Circle(self._radius)

    def scale(self, factor: Real) -> None:
        """
        Redimensionne le cercle

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(positive(not_null(expect(factor, Real))))
        self._radius *= factor
        self._invalidate_cache()

    def world_bounding_box(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> tuple[float, float, float, float]:
        """Renvoie (x_min, y_min, x_max, y_max) en coordonnées monde"""
        cx, cy, r = self.world_transform(x, y, scale, rotation)
        return cx - r, cy - r, cx + r, cy + r

    # ======================================== INTERNALS ========================================
    def _compute_world(self, x: float, y: float, scale: float, rotation: float) -> tuple[float, float, float]:
        """Calcule les paramètres monde"""
        return (x, y, self._radius * scale)