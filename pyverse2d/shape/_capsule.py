# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import CompositeShape
from .._flag import ComponentType

from numbers import Real
from typing import Iterator
import math

# ======================================== SHAPE ========================================
class Capsule(CompositeShape):
    """
    Forme géométrique 2D : Capsule

    Args:
        radius(Real): rayon des demi-cercles
        height(Real): hauteur totale de la capsule
    """
    __slots__ = ("_radius", "_height")

    def __init__(self, radius: Real, height: Real):
        self._height: float = float(positive(not_null(expect(height, Real))))
        self._radius: float = min(self._height * 0.5, float(positive(not_null(expect(radius, Real)))))
        super().__init__()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de la capsule"""
        return f"Capsule(radius={self._radius}, height={self._height})"

    def __str__(self) -> str:
        """Renvoie une description lisible de la capsule"""
        return f"Capsule[r={self._radius} h={self._height} | area={self.area:.4g}]"

    def __iter__(self) -> Iterator[float]:
        """Renvoie les composants dans un itérateur"""
        yield self._radius
        yield self._height

    def __hash__(self) -> int:
        """Renvoie le hash de la capsule"""
        return hash(self.to_tuple())

    def to_tuple(self) -> tuple[float, float]:
        """Renvoie la capsule sous forme de tuple"""
        return (self._radius, self._height)

    def to_list(self) -> list[float]:
        """Renvoie la capsule sous forme de liste"""
        return [self._radius, self._height]

    # ======================================== GETTERS ========================================
    @property
    def radius(self) -> float:
        """Renvoie le rayon des demi-cercles"""
        return self._radius

    @property
    def height(self) -> float:
        """Renvoie la hauteur totale de la capsule"""
        return self._height

    @property
    def width(self) -> float:
        """Renvoie la largeur de la capsule"""
        return 2 * self._radius

    @property
    def spine(self) -> float:
        """Renvoie la longueur du segment central"""
        return self._height - 2 * self._radius

    @property
    def perimeter(self) -> float:
        """Renvoie le périmètre de la capsule"""
        return 2 * self.spine + 2 * math.pi * self._radius

    @property
    def area(self) -> float:
        """Renvoie l'aire de la capsule"""
        return self.width * self.spine + math.pi * self._radius ** 2

    # ======================================== SETTERS ========================================
    @radius.setter
    def radius(self, value: Real):
        """
        Fixe le rayon des demi-cercles

        Args:
            value(Real): nouveau rayon
        """
        self._radius = min(self._height * 0.5, float(positive(not_null(expect(value, Real)))))
        self._invalidate_cache()

    @height.setter
    def height(self, value: Real):
        """
        Fixe la hauteur totale de la capsule

        Args:
            value(Real): nouvelle hauteur
        """
        self._height = float(positive(not_null(expect(value, Real))))
        self._radius  = min(self._height * 0.5, self._radius)
        self._invalidate_cache()

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """
        Vérifie l'égalité de deux capsules

        Args:
            other(object): objet à comparer
        """
        if isinstance(other, Capsule):
            return self._radius == other._radius and self._height == other._height
        return False

    # ======================================== PREDICATES ========================================
    def contains(self, point) -> bool:
        """
        Teste si un point est dans la capsule

        Args:
            point: point à tester
        """
        px, py = float(point[0]), float(point[1])
        half_spine = self.spine * 0.5
        closest_y = max(-half_spine, min(half_spine, py))
        return px ** 2 + (py - closest_y) ** 2 <= self._radius ** 2

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Capsule:
        """Renvoie une copie de la capsule"""
        return Capsule(self._radius, self._height)

    def scale(self, factor: Real) -> None:
        """
        Redimensionne la capsule

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(positive(not_null(expect(factor, Real))))
        self._radius *= factor
        self._height *= factor
        self._invalidate_cache()

    def components(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> Iterator[tuple]:
        """
        Renvoie les composants de la capsule en coordonnées monde

        Args:
            x(float, optional): coordonnée horizontale
            y(float, optional): coordonnée verticale
            scale(float, optional): facteur d'échelle
            rotation(float, optional): angle en radians
        """
        ax, ay, bx, by, r = self._compute_world(x, y, scale, rotation)
        yield (ComponentType.CIRCLE,  ax, ay, r)
        yield (ComponentType.CIRCLE,  bx, by, r)
        yield (ComponentType.SEGMENT, ax, ay, bx, by, r)

    def world_bounding_box(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> tuple[float, float, float, float]:
        """Renvoie (x_min, y_min, x_max, y_max) en coordonnées monde"""
        ax, ay, bx, by, r = self.world_transform(x, y, scale, rotation)
        return min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r

    # ======================================== INTERNALS ========================================
    def _compute_world(self, x: float, y: float, scale: float, rotation: float) -> tuple[float, float, float, float, float]:
        """Calcule les paramètres monde de la capsule"""
        half_spine = self.spine * 0.5 * scale
        rad = math.radians(rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        ax = x - sin_r * half_spine
        ay = y + cos_r * half_spine
        bx = x + sin_r * half_spine
        by = y - cos_r * half_spine
        return (ax, ay, bx, by, self._radius * scale)