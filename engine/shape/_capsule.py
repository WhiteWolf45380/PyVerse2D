# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import Shape

from numbers import Real
from typing import Iterator
import math

# ======================================== SHAPE ========================================
class Capsule(Shape):
    """Forme géométrique 2D : Capsule"""
    __slots__ = ("_radius", "_height")
    def __init__(
            self,
            radius: Real,
            height: Real
        ):
        """
        Args:
            radius(Real): rayon de la capsule
            height(Real): hauteur totale de la capsule
        """
        super().__init__()
        self._height: float = float(positive(not_null(expect(height, Real))))
        self._radius: float = min(self._height / 2, float(positive(not_null(expect(radius, Real)))))
        
    # ======================================== CONVERSION ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de la capsule"""
        return f"Capsule(radius={self._radius}, height={self._height})"
    
    def __iter__(self) -> Iterator[float]:
        """Renvoie les composants dans un itérateur"""
        yield self._radius
        yield self._height

    def __hash__(self):
        """Renvoie l'entier hashé de la capsule"""
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
        """Renvoie le rayon de la capsule"""
        return self._radius
    
    @property
    def height(self) -> float:
        """Renvoie la hauteur de la capsule"""
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
        return self.width * self.spine + math.pi * self._radius**2

    # ======================================== SETTERS ========================================
    @radius.setter
    def radius(self, value: Real):
        """Fixe le rayon de la capsule"""
        self._radius = min(self._height / 2, float(positive(not_null(expect(value, Real)))))

    @height.setter
    def height(self, value: Real):
        """Fixe la hauteur de la capsule"""
        self._height = float(positive(not_null(expect(value, Real))))
        self._radius = min(self._height / 2, self._radius)

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: Capsule):
        """Vérifie la correspondance de deux capsules"""
        if isinstance(other, Capsule):
            return self._radius == other._radius and self._height == other._height
        return False
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Capsule:
        """Renvoie une copie de la capsule"""
        return Capsule(self._radius, self._height)
    
    def scale(self, factor: Real):
        """
        Redimensionne la capsule

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(expect(factor, Real))
        if factor <= 0:
            raise ValueError("factor cannot be negative or null")
        self._radius *= factor
        self._height *= factor