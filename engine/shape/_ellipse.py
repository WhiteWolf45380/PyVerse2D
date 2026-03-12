# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import Shape

from numbers import Real
from typing import Iterator
import math

# ======================================== SHAPE ========================================
class Ellipse(Shape):
    """Forme géométrique 2D : Ellipse"""
    __slots__ = ("_rx", "_ry")
    def __init__(
            self,
            rx: Real,
            ry: Real
        ):
        """
        Args:
            rx(Real): rayon horizontal de l'ellipse
            ry(Real): rayon vertical de l'ellipse
        """
        super().__init__()
        self._rx = float(positive(not_null(expect(rx, Real))))
        self._ry = float(positive(not_null(expect(ry, Real))))
        
    # ======================================== CONVERSION ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation d"""
        return f"Ellipse(rx={self._rx}, ry={self._ry})"
    
    def __iter__(self) -> Iterator[float]:
        """Renvoie l'ellipse dans un itérateur"""
        yield self._rx
        yield self._ry

    def __hash__(self):
        """Renvoie l'entier hashé de l'ellipse"""
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
        """Renvoie le rayon horizontal de l'ellispe"""
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
        h = ((self._rx - self._ry)**2) / ((self._rx + self._ry)**2)
        return math.pi * (self._rx + self._ry) * (1 + (3*h)/(10 + math.sqrt(4 - 3*h)))
    
    @property
    def area(self) -> float:
        """Renvoie l'aire de l'ellipse"""
        return math.pi * self._rx * self._ry

    # ======================================== SETTERS ========================================
    @rx.setter
    def rx(self, value: Real):
        """Fixe le rayon horizontal de l'ellipse"""
        self._rx = float(positive(not_null(expect(value, Real))))

    @ry.setter
    def ry(self, value: Real):
        """Fixe le rayon vertical de l'ellipse"""
        self._ry = float(positive(not_null(expect(value, Real))))

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: Ellipse):
        """Vérifie la correspondance de deux ellipses"""
        if isinstance(other, Ellipse):
            return self._rx == other._rx and self._ry == other._ry
        return False
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Ellipse:
        """Renvoie une copie de l'ellipse"""
        return Ellipse(self._rx, self._ry)
    
    def scale(self, factor: Real):
        """
        Redimensionne l'ellipse

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(expect(factor, Real))
        if factor <= 0:
            raise ValueError("factor cannot be negative or null")
        self._rx *= factor
        self._ry *= factor