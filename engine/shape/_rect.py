# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import Shape

from numbers import Real
from typing import Iterator

# ======================================== SHAPE ========================================
class Rect(Shape):
    """Forme géométrique 2D : Rect"""
    __slots__ = ("_width", "_height")
    def __init__(
            self,
            width: Real,
            height: Real
        ):
        """
        Args:
            width(Real): largeur du rect
            height(Real): hauteur du rect
        """
        super().__init__()
        self._width: float = float(positive(not_null(expect(width, Real))))
        self._height: float = float(positive(not_null(expect(height, Real))))
        
    # ======================================== CONVERSION ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du rect"""
        return f"Rect(width={self._width}, height={self._height})"
    
    def __iter__(self) -> Iterator[float]:
        """Renvoie le rect dans un itérateur"""
        yield self._width
        yield self._height

    def __hash__(self):
        """Renvoie l'entier hashé du rect"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[float, float]:
        """Renvoie le rect sous forme de tuple"""
        return (self._width, self._height)
    
    def to_list(self) -> list[float]:
        """Renvoie le rect sous forme de liste"""
        return [self._width, self._height]

    # ======================================== GETTERS ========================================
    @property
    def width(self) -> float:
        """Renvoie la largeur du rect"""
        return self._width
    
    @property
    def height(self) -> float:
        """Renvoie la hauteur du rect"""
        return self._height
    
    @property
    def diagonal(self) -> float:
        """Renvoie la longueur de la diagonale"""
        return (self._width**2 + self._height**2)**0.5
    
    @property
    def perimeter(self) -> float:
        """Renvoie le périmètre du rect"""
        return 2 * self._width + 2 * self._height
    
    @property
    def area(self) -> float:
        """Renvoie l'aire du rect"""
        return self._width * self._height

    # ======================================== SETTERS ========================================
    @width.setter
    def width(self, value: Real):
        """Fixe la largeur du rect"""
        self._width = float(positive(not_null(expect(value, Real))))

    @height.setter
    def height(self, value: Real):
        """Fixe la hauteur du rect"""
        self._height = float(positive(not_null(expect(value, Real))))

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: Rect):
        """Vérifie la correspondance de deux rects"""
        if isinstance(other, Rect):
            return self._width == other._width and self._height == other._height
        return False
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Rect:
        """Renvoie une copie du rect"""
        return Rect(self._width, self._height)
    
    def scale(self, factor: Real):
        """
        Redimensionne le rect

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(expect(factor, Real))
        if factor <= 0:
            raise ValueError("factor cannot be negative or null")
        self._width *= factor
        self._height *= factor