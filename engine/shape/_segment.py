# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import Shape
from ..math import Point, Vector

from numbers import Real
from typing import Iterator

# ======================================== SHAPE ========================================
class Segment(Shape):
    """Forme géométrique 2D : Segment"""
    __slots__ = ("_A", "_B", "_width")
    def __init__(
            self,
            A: Point, 
            B: Point,
            width: Real = 1.0
        ):
        """
        Args:
            A(Point): point de départ
            B(Point): point d'arrivé
            width(Real, optional): épaisseur
        """
        super().__init__()
        self._A: Point = Point(A)
        self._B: Point = Point(B)
        self._width: float = float(positive(not_null(expect(width, Real))))
        
    # ======================================== CONVERSION ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du segment"""
        return f"Segment(A={self._A}, B={self._B}, width={self._width})"
    
    def __iter__(self) -> Iterator[float]:
        """Renvoie le segment dans un itérateur"""
        yield self._A
        yield self._B
        yield self._width

    def __hash__(self):
        """Renvoie l'entier hashé du segment"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Point, Point, float]:
        """Renvoie le segment sous forme de tuple"""
        return (self._A, self._B, self._width)
     
    def to_list(self) -> list:
        """Renvoie le segment sous forme de liste"""
        return [self._A, self._B, self._width]

    # ======================================== GETTERS ========================================
    @property
    def A(self) -> Point:
        """Renvoie le point de départ du segment"""
        return self._A
    
    @property
    def B(self) -> Point:
        """Renvoie le point d'arrivé du segment"""
        return self._B
    
    @property
    def width(self) -> float:
        """Renvoie la largeur du segment"""
        return self._width
    
    @property
    def center(self) -> Point:
        """Renvoie le centre local du segment"""
        return self._A + 0.5 * self.vector
    
    @property
    def vector(self) -> Vector:
        """Renvoie le vecteur correspondant au segment"""
        return self._B - self._A
    
    @property
    def length(self) -> float:
        """Renvoie la longueur du segment"""
        return self._A.distance_to(self._B)
    
    @property
    def perimeter(self) -> float:
        """Renvoie le périmètre du segment"""
        return 2 * self._width + 2 * self.length
    
    @property
    def area(self) -> float:
        """Renvoie l'aire du segment"""
        return self._width * self.length

    # ======================================== SETTERS ========================================
    @A.setter
    def A(self, value: Point):
        """Fixe le point de départ"""
        self._A = Point(value)

    @B.setter
    def B(self, value: Point):
        """Fixe le point d'arrivé"""
        self._B = Point(value)

    @width.setter
    def width(self, value: Real):
        """Fixe la largeur du segment"""
        self._width = float(positive(not_null(expect(value, Real))))

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: Segment):
        """Vérifie la correspondance de deux segments"""
        if isinstance(other, Segment):
            return self._width == other._width and self.vector in (other.vector, -other.vector)
        return False
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Segment:
        """Renvoie une copie du segment"""
        return Segment(self._A.copy(), self._B.copy(), self._width)
    
    def scale(self, factor: Real):
        """
        Redimensionne le segment

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(expect(factor, Real))
        if factor <= 0:
            raise ValueError("factor cannot be negative or null")
        C = self.center
        self._A = C + factor * (self._A - C)
        self._B = C + factor * (self._B - C)
        self._width *= factor