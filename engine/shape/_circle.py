# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import Shape

from numbers import Real
from typing import Iterator
import math

# ======================================== SHAPE ========================================
class Circle(Shape):
    """Forme géométrique 2D : Cercle"""
    __slots__ = ("_radius",)
    def __init__(
            self,
            radius: Real,
        ):
        """
        Args:
            radius(Real): rayon
        """
        super().__init__()
        self._radius: float = float(positive(not_null(expect(radius, Real))))
        
    # ======================================== CONVERSION ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du cercle"""
        return f"Circle(radius={self._radius})"
    
    def __iter__(self) -> Iterator[float]:
        """Renvoie le cercle dans un itérateur"""
        yield self._radius

    def __hash__(self):
        """Renvoie l'entier hashé du cercle"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[float]:
        """Renvoie le rect sous forme de tuple"""
        return (self._radius,)
    
    def to_list(self) -> list[float]:
        """Renvoie le rect sous forme de liste"""
        return [self._radius]

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
    def perimeter(self) -> float:
        """Renvoie le périmètre du cercle"""
        return 2 * math.pi * self._radius
    
    @property
    def area(self) -> float:
        """Renvoie l'aire du cercle"""
        return math.pi * self._radius**2

    # ======================================== SETTERS ========================================
    @radius.setter
    def radius(self, value: Real):
        """Fixe la largeur du cercle"""
        self._radius = float(positive(not_null(expect(value, Real))))

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: Circle):
        """Vérifie la correspondance de deux rects"""
        if isinstance(other, Circle):
            return self._radius == other._radius
        return False
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Circle:
        """Renvoie une copie du rect"""
        return Circle(self._radius)
    
    def scale(self, factor: Real):
        """
        Redimensionne le cercle

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(expect(factor, Real))
        if factor <= 0:
            raise ValueError("factor cannot be negative or null")
        self._radius *= factor