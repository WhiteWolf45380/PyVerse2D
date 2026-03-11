# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..core import Shape
from ..math import Point, Vector

from numbers import Real
from typing import Iterator

# ======================================== SHAPE ========================================
class Polygon(Shape):
    """Forme géométrique 2D : Polygone"""
    __slots__ = ("_points",)
    def __init__(
            self,
            *points: Point, 
        ):
        """
        Args:
            points(Point): points du polygone
        """
        super().__init__()
        self._points: tuple[Point, ...] = expect(points, tuple[Point])
        if len(self._points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        if self._has_duplicate_points():
            raise ValueError("Polygon cannot have duplicate consecutive points")
        
    # ======================================== CONVERSION ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du polygone"""
        return f"Polygon({', '.join(map(str, self._points))})"
    
    def __str__(self) -> str:
        return f"Polygon[{len(self)} pts | area={self.area:.4g} | perimeter={self.perimeter:.4g}]"
    
    def __iter__(self) -> Iterator[float]:
        """Renvoie le polygone dans un itérateur"""
        return iter(self._points)

    def __hash__(self):
        """Renvoie l'entier hashé du polygone"""
        return hash(self._points)
    
    def to_tuple(self) -> tuple[Point, Point, float]:
        """Renvoie le polygone sous forme de tuple"""
        return self._points
     
    def to_list(self) -> list:
        """Renvoie le polygone sous forme de liste"""
        return list(self._points)

    # ======================================== GETTERS ========================================
    @property
    def points(self) -> tuple[Point, ...]:
        """Renvoie le point de départ du polygone"""
        return self._points
    
    def get_edges(self) -> tuple[tuple[Point, Point], ...]:
        """
        Renvoie les arêtes du polygone sous forme de paires de points.
        """
        n = len(self._points)
        return tuple((self._points[i], self._points[(i + 1) % n]) for i in range(n))
    
    def __getitem__(self, key: int | slice) -> Point | tuple[Point]:
        """Renvoie le point d'indice key ou le slice correspondant"""
        return self._points[key]
    
    def __len__(self) -> int:
        """Renvoie le nombre de points du polygone"""
        return len(self._points)
    
    @property
    def barycenter(self) -> Point:
        """Renvoie le centre local du polygone"""
        return self[0].barycenter(self[1:])
    
    @property
    def perimeter(self) -> float:
        """
        Renvoie le périmètre du polygone

        Note:
            Inclut l'arête entre le dernier et le premier sommet.
        """
        n = len(self._points)
        return sum(
            self._points[i].distance_to(self._points[(i + 1) % n])
            for i in range(n)
        )

    @property
    def area(self) -> float:
        """Renvoie l'aire du polygone"""
        pts = self._points
        n = len(pts)
        return 0.5 * sum(
            pts[i].x * pts[(i + 1) % n].y - pts[(i + 1) % n].x * pts[i].y
            for i in range(n)
        )

    @property
    def is_convex(self) -> bool:
        """Vérifie si le polygone est convexe"""
        pts = self._points
        n = len(pts)
        sign = None
        for i in range(n):
            o = pts[i]
            a = pts[(i + 1) % n]
            b = pts[(i + 2) % n]
            cross = (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
            if cross != 0:
                s = cross > 0
                if sign is None:
                    sign = s
                elif sign != s:
                    return False
        return True

    @property
    def is_clockwise(self) -> bool:
        """Renvoie True si les sommets sont ordonnés dans le sens horaire"""
        return self.area < 0

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """
        Vérifie l'égalité géométrique de deux polygones

        Note:
            Deux polygones sont égaux s'ils partagent les mêmes sommets dans le même
            ordre cyclique (rotation autorisée, réflexion non).
        """
        if not isinstance(other, Polygon):
            return False
        if len(self) != len(other):
            return False
        n = len(self._points)
        sp = self._points
        op = other._points
        return any(
            all(sp[i] == op[(i + offset) % n] for i in range(n))
            for offset in range(n)
        )

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Polygon:
        """Renvoie une copie du polygone"""
        return Polygon(*self._points)

    def scale(self, factor: Real, origin: Point | None = None) -> Polygon:
        """
        Redimensionne le polygone par rapport à un point d'origine.

        Args:
            factor (Real): facteur de redimensionnement (> 0)
            origin (Point | None): centre de la mise à l'échelle
        """
        factor = float(expect(factor, Real))
        if factor <= 0:
            raise ValueError("factor must be strictly positive")
        center = origin if origin is not None else self.barycenter
        new_points = tuple(
            Point(
                center.x + (p.x - center.x) * factor,
                center.y + (p.y - center.y) * factor,
            )
            for p in self._points
        )
        self._points = new_points

    def reverse(self) -> Polygon:
        """Inverse l'ordre des sommets (change le sens de parcours)"""
        return Polygon(*reversed(self._points))

    def normalize(self) -> Polygon:
        """Normalise l'orientation du polygone en sens anti-horaire"""
        return self if self.area >= 0 else self.reverse()

    # ======================================== INTERAL METHODS ========================================
    def _has_duplicate_points(self) -> bool:
        """Vérifie la présence de points consécutifs identiques"""
        n = len(self._points)
        return any(self._points[i] == self._points[(i + 1) % n] for i in range(n))