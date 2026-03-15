# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import PrimitiveShape

from numbers import Real
from typing import Iterator
import math

# ======================================== SHAPE ========================================
class Ellipse(PrimitiveShape):
    """
    Forme géométrique 2D : Ellipse

    Args:
        rx(Real): rayon horizontal de l'ellipse
        ry(Real): rayon vertical de l'ellipse
    """
    __slots__ = ("_rx", "_ry")

    def __init__(self, rx: Real, ry: Real):
        self._rx: float = float(positive(not_null(expect(rx, Real))))
        self._ry: float = float(positive(not_null(expect(ry, Real))))
        super().__init__()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'ellipse"""
        return f"Ellipse(rx={self._rx}, ry={self._ry})"

    def __str__(self) -> str:
        """Renvoie une description lisible de l'ellipse"""
        return f"Ellipse[rx={self._rx} ry={self._ry} | area={self.area:.4g}]"

    def __iter__(self) -> Iterator[float]:
        """Renvoie les composants dans un itérateur"""
        yield self._rx
        yield self._ry

    def __hash__(self) -> int:
        """Renvoie le hash de l'ellipse"""
        return hash(self.to_tuple())

    def to_tuple(self) -> tuple[float, float]:
        """Renvoie l'ellipse sous forme de tuple"""
        return (self._rx, self._ry)

    def to_list(self) -> list[float]:
        """Renvoie l'ellipse sous forme de liste"""
        return [self._rx, self._ry]

    # ======================================== GETTERS ========================================
    @property
    def rx(self) -> float:
        """Renvoie le rayon horizontal de l'ellipse"""
        return self._rx

    @property
    def ry(self) -> float:
        """Renvoie le rayon vertical de l'ellipse"""
        return self._ry

    @property
    def width(self) -> float:
        """Renvoie la largeur de l'ellipse"""
        return 2 * self._rx

    @property
    def height(self) -> float:
        """Renvoie la hauteur de l'ellipse"""
        return 2 * self._ry

    @property
    def perimeter(self) -> float:
        """Renvoie le périmètre de l'ellipse"""
        h = ((self._rx - self._ry) ** 2) / ((self._rx + self._ry) ** 2)
        return math.pi * (self._rx + self._ry) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))

    @property
    def area(self) -> float:
        """Renvoie l'aire de l'ellipse"""
        return math.pi * self._rx * self._ry

    # ======================================== SETTERS ========================================
    @rx.setter
    def rx(self, value: Real):
        """
        Fixe le rayon horizontal de l'ellipse

        Args:
            value(Real): nouveau rayon horizontal
        """
        self._rx = float(positive(not_null(expect(value, Real))))
        self._invalidate_cache()

    @ry.setter
    def ry(self, value: Real):
        """
        Fixe le rayon vertical de l'ellipse

        Args:
            value(Real): nouveau rayon vertical
        """
        self._ry = float(positive(not_null(expect(value, Real))))
        self._invalidate_cache()

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """
        Vérifie l'égalité de deux ellipses

        Args:
            other(object): objet à comparer
        """
        if isinstance(other, Ellipse):
            return self._rx == other._rx and self._ry == other._ry
        return False

    # ======================================== PREDICATES ========================================
    def contains(self, point) -> bool:
        """
        Teste si un point est dans l'ellipse

        Args:
            point: point à tester
        """
        px, py = float(point[0]), float(point[1])
        return (px / self._rx) ** 2 + (py / self._ry) ** 2 <= 1.0

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Ellipse:
        """Renvoie une copie de l'ellipse"""
        return Ellipse(self._rx, self._ry)

    def scale(self, factor: Real) -> None:
        """
        Redimensionne l'ellipse

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(positive(not_null(expect(factor, Real))))
        self._rx *= factor
        self._ry *= factor
        self._invalidate_cache()

    def world_bounding_box(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> tuple[float, float, float, float]:
        """Renvoie (x_min, y_min, x_max, y_max) en coordonnées monde"""
        cx, cy, rx, ry, angle = self.world_transform(x, y, scale, rotation)
        rad = math.radians(angle)
        c, s = abs(math.cos(rad)), abs(math.sin(rad))
        hw = rx * c + ry * s
        hh = rx * s + ry * c
        return cx - hw, cy - hh, cx + hw, cy + hh

    # ======================================== INTERNALS ========================================
    def _compute_world(self, x: float, y: float, scale: float, rotation: float) -> tuple[float, float, float, float, float]:
        """Calcule les paramètres monde"""
        return (x, y, self._rx * scale, self._ry * scale, rotation)