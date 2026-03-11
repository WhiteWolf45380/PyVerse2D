# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from .._core import MathObject

from ._vector import Vector

from numbers import Real
from typing import Iterator

# ======================================== OBJECT ========================================
class Point(MathObject):
    """Objet mathématique 2D abstrait : Point"""
    __slots__ = ("_x", "_y")
    PRECISION = 8
    def __init__(
            self,
            x: Real,
            y: Real
        ):
        """
        Args:
            x(Real): coordonnée horizontale
            y(Real): coordonnée verticale
        """
        super().__init__()
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
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[float]:
        """Renvoie le point sous forme de tuple"""
        return (self._x, self._y)
    
    def to_list(self) -> list[float]:
        """Renvoie le point sous forme de liste"""
        return [self._x, self._y]
    
    def to_vector(self) -> Vector:
        """Renvoie le vecteur origin -> self"""
        return Vector(*self)
    
    # ======================================== GETTERS ========================================
    def __getitem__(self, i: int) -> float:
        """Renvoie une coordonnée du point"""
        return (self._x, self._y)[expect(i, (int))]
    
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
        """Fixe la cordonnée horizontale du point"""
        self._x = round(float(expect(value, Real)), self.PRECISION)
    
    @y.setter
    def y(self, value: Real):
        """Fixe la coordonnée verticale du point"""
        self._y = round(float(expect(value, Real)), self.PRECISION)

    # ======================================== OPERATIONS ========================================
    def __add__(self, other: Vector | Point) -> Point:
        """Renvoie l'image du point par le vecteur donné"""
        if isinstance(other, Vector):
            return self._translate(other)
        if isinstance(other, Point):
            return self._translate(Vector(*other))
        return NotImplemented
    
    def __radd__(self, other: Vector) -> Point:
        """Renvoie l'image du point par le vecteur donné"""
        if isinstance(other, Vector):
            return self._translate(other)
        return NotImplemented
    
    def __sub__(self, other: Point | Vector) -> Point | Vector:
        """Renvoie l'image du point par l'opposé du vecteur ou le vecteur other -> self"""
        if isinstance(other, Point):
            return other._vector_to(self)
        if isinstance(other, Vector):
            return self._translate(-other)
        return NotImplemented
    
    def __pos__(self) -> Point:
        """Renvoie une copie du point"""
        return self.copy()
    
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
        return self._is_aligned(expect(points, tuple[Point]))
    
    def _is_aligned(self, *points: Point) -> bool:
        """Implémentation interne"""
        if len(points) < 2:
            return True
        vector0 = points[0] - self
        if not vector0:
            return all((point - points[0]).is_null() for point in points[1:])
        return all(vector0.is_collinear(point - points[0]) for point in points[1:])
    
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
        return self._vector_to(expect(point, Point))
    
    def distance_to(self, point: Point) -> float:
        """
        Renvoie la distance euclidienne jusqu'à un autre point

        Args:
            point(Point): point cible
        """
        return self._distance_to(expect(point, Point))
    
    def translate(self, vector: Vector) -> Point:
        """
        Renvoie la translation du point par un vecteur donné

        Args:
            vector(Vector): vecteur de translation
        """
        return self._translate(expect(vector, Vector))
    
    def midpoint(self, point: Point) -> Point:
        """
        Renvoie le point du milieu du segment à un autre point

        Args:
            point(Point): second point du segment
        """
        return self._midpoint(expect(point, Point))
    
    def barycenter(self, *points: Point) -> Point:
        """
        Renvoie le barycentre à plusieurs autres points

        Args:
            points(Point): autres points
        """
        return self._barycenter(expect(points, tuple[Point]))
    
    # ======================================== INTERNAL METHODS ========================================
    def _vector_to(self, point: Point) -> Vector:
        """Vecteur à un autre point"""
        return Vector(point._x - self._x, point._y - self._y)
    
    def _distance_to(self, point: Point) -> float:
        """Distance à un autre point"""
        return ((point._x - self._x)**2 + (point._y - self._y)**2)**0.5
    
    def _translate(self, vector: Vector) -> Point:
        """Translation par un vecteur"""
        return Point(self._x + vector._x, self._y + vector._y)
    
    def _midpoint(self, point: Point) -> Point:
        """Point du milieu à un autre point"""
        return Point((self._x + point._x) / 2, (self._y + point._y) / 2)
    
    def _barycenter(self, *points) -> Point:
        """Barycentre à plusieurs autres points"""
        n = len(points) + 1
        x = (self._x + sum(p._x for p in points)) / n
        y = (self._y + sum(p._y for p in points)) / n
        return Point(x, y)