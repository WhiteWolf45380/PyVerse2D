# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from ..abc import MathObject

from ._vector import Vector

from numbers import Real
from typing import Iterator
from math import sqrt

# ======================================== OBJECT ========================================
class Point(MathObject):
    """Objet mathématique 2D abstrait : Point"""
    __slots__ = ("_x", "_y")
    PRECISION = 8

    def __new__(cls, x, y=None):
        """Création d'un nouvel objet uniquement si l'argument n'est pas un point"""
        if isinstance(x, cls) and y is None:
            return x
        return super().__new__(cls)

    def __init__(self, x, y=None):
        """
        Args:
            x(Real): coordonnée horizontale, ou Point/tuple à coercer
            y(Real): coordonnée verticale (optionnel si x est un Point ou tuple)
        """
        if isinstance(x, Point) and y is None:
            return
        super().__init__()
        if isinstance(x, (tuple, list)) and y is None:
            x, y = x[0], x[1]
        self._x: float = round(float(expect(x, Real)), self.PRECISION)
        self._y: float = round(float(expect(y, Real)), self.PRECISION)

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du point"""
        return f"Point({self._x}, {self._y})"

    def __iter__(self) -> Iterator[float]:
        """Renvoie les coordonnées dans un itérateur"""
        yield self._x
        yield self._y

    def __hash__(self) -> int:
        """Renvoie l'entier hashé du point"""
        return hash((self._x, self._y))

    def to_tuple(self) -> tuple[float]:
        """Renvoie le point sous forme de tuple"""
        return (self._x, self._y)

    def to_list(self) -> list[float]:
        """Renvoie le point sous forme de liste"""
        return [self._x, self._y]

    def to_vector(self) -> Vector:
        """Renvoie le vecteur origin -> self"""
        return Vector(self._x, self._y)

    # ======================================== GETTERS ========================================
    def __getitem__(self, i: int) -> float:
        """Renvoie une coordonnée du point"""
        return (self._x, self._y)[expect(i, int)]

    @property
    def x(self) -> float:
        """Renvoie la coordonnée horizontale du point"""
        return self._x

    @property
    def y(self) -> float:
        """Renvoie la coordonnée verticale du point"""
        return self._y

    def __len__(self) -> int:
        """Renvoie la dimension du point"""
        return 2

    # ======================================== SETTERS ========================================
    def __setitem__(self, i: int, value: Real):
        """Fixe une coordonnée du point"""
        setattr(self, ("x", "y")[expect(i, int)], round(float(expect(value, Real)), self.PRECISION))

    @x.setter
    def x(self, value: Real):
        """Fixe la coordonnée horizontale du point"""
        self._x = round(float(expect(value, Real)), self.PRECISION)

    @y.setter
    def y(self, value: Real):
        """Fixe la coordonnée verticale du point"""
        self._y = round(float(expect(value, Real)), self.PRECISION)

    # ======================================== OPERATIONS ========================================
    def __add__(self, other: Vector | Point) -> Point:
        """Renvoie l'image du point par le vecteur donné"""
        if isinstance(other, Vector):
            return Point(self._x + other._x, self._y + other._y)
        if isinstance(other, Point):
            return Point(self._x + other._x, self._y + other._y)
        return NotImplemented

    def __radd__(self, other: Vector) -> Point:
        """Renvoie l'image du point par le vecteur donné"""
        if isinstance(other, Vector):
            return Point(self._x + other._x, self._y + other._y)
        return NotImplemented

    def __sub__(self, other: Point | Vector) -> Point | Vector:
        """Renvoie l'image du point par l'opposé du vecteur ou le vecteur other -> self"""
        if isinstance(other, Point):
            return Vector(self._x - other._x, self._y - other._y)
        if isinstance(other, Vector):
            return Point(self._x - other._x, self._y - other._y)
        return NotImplemented

    def __pos__(self) -> Point:
        """Renvoie une copie du point"""
        return Point(self._x, self._y)

    def __neg__(self) -> Point:
        """Renvoie l'opposé du point par rapport à l'origine"""
        return Point(-self._x, -self._y)

    def __abs__(self) -> Point:
        """Renvoie le point côté positif"""
        return Point(abs(self._x), abs(self._y))

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: Point) -> bool:
        """Vérifie la correspondance de deux points"""
        if isinstance(other, Point):
            return self._x == other._x and self._y == other._y
        return NotImplemented

    def __ne__(self, other: Point) -> bool:
        """Vérifie la non correspondance de deux points"""
        if isinstance(other, Point):
            return self._x != other._x or self._y != other._y
        return NotImplemented

    # ======================================== PREDICATES ========================================
    def is_origin(self) -> bool:
        """Vérifie que le point soit l'origine du repère"""
        return self._x == 0 and self._y == 0

    def is_aligned(self, *points: Point) -> bool:
        """
        Vérifie l'alignement avec un ensemble de points

        Args:
            points(Point): points à vérifier
        """
        if len(points) < 1:
            return True
        v0 = Vector(points[0]._x - self._x, points[0]._y - self._y)
        if v0.is_null():
            return all(
                Vector(p._x - points[0]._x, p._y - points[0]._y).is_null()
                for p in points[1:]
            )
        return all(
            v0._x * (p._y - points[0]._y) - v0._y * (p._x - points[0]._x) == 0
            for p in points[1:]
        )

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Point:
        """Renvoie une copie du point"""
        return Point(self._x, self._y)

    def vector_to(self, point: Point) -> Vector:
        """
        Renvoie le vecteur self -> point

        Args:
            point(Point): point cible
        """
        p = expect(point, Point)
        return Vector(p._x - self._x, p._y - self._y)

    def distance_to(self, point: Point) -> float:
        """
        Renvoie la distance euclidienne jusqu'à un autre point

        Args:
            point(Point): point cible
        """
        p = expect(point, Point)
        dx = p._x - self._x
        dy = p._y - self._y
        return sqrt(dx * dx + dy * dy)

    def translate(self, vector: Vector) -> Point:
        """
        Renvoie la translation du point par un vecteur donné

        Args:
            vector(Vector): vecteur de translation
        """
        v = Vector(vector)
        return Point(self._x + v._x, self._y + v._y)

    def midpoint(self, point: Point) -> Point:
        """
        Renvoie le point du milieu du segment à un autre point

        Args:
            point(Point): second point du segment
        """
        p = expect(point, Point)
        return Point((self._x + p._x) * 0.5, (self._y + p._y) * 0.5)

    def barycenter(self, *points: Point) -> Point:
        """
        Renvoie le barycentre à plusieurs autres points

        Args:
            points(Point): autres points
        """
        n = len(points) + 1
        x = (self._x + sum(p._x for p in points)) / n
        y = (self._y + sum(p._y for p in points)) / n
        return Point(x, y)

    # ======================================== INTERNAL METHODS ========================================
    def _vector_to(self, point: Point) -> Vector:
        """Vecteur à un autre point"""
        return Vector(point._x - self._x, point._y - self._y)

    def _distance_to(self, point: Point) -> float:
        """Distance à un autre point"""
        dx = point._x - self._x
        dy = point._y - self._y
        return sqrt(dx * dx + dy * dy)

    def _translate(self, vector: Vector) -> Point:
        """Translation par un vecteur"""
        return Point(self._x + vector._x, self._y + vector._y)

    def _midpoint(self, point: Point) -> Point:
        """Point du milieu à un autre point"""
        return Point((self._x + point._x) * 0.5, (self._y + point._y) * 0.5)

    def _barycenter(self, *points) -> Point:
        """Barycentre à plusieurs autres points"""
        n = len(points) + 1
        return Point(
            (self._x + sum(p._x for p in points)) / n,
            (self._y + sum(p._y for p in points)) / n,
        )