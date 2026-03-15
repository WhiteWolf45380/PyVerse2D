# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import VertexShape
from numbers import Real
import numpy as np
from numpy.typing import NDArray

# ======================================== SHAPE ========================================
class Rect(VertexShape):
    """
    Forme géométrique 2D avec sommets : Rectangle

    Args:
        width(Real): largeur du rectangle
        height(Real): hauteur du rectangle
    """
    __slots__ = ("_width", "_height")

    def __init__(self, width: Real, height: Real):
        self._width: float = float(positive(not_null(expect(width, Real))))
        self._height: float = float(positive(not_null(expect(height, Real))))
        super().__init__()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du rectangle"""
        return f"Rect(width={self._width}, height={self._height})"

    def __str__(self) -> str:
        """Renvoie une description lisible du rectangle"""
        return f"Rect[{self._width}x{self._height} | area={self.area:.4g} | perimeter={self.perimeter:.4g}]"

    # ======================================== GETTERS ========================================
    @property
    def width(self) -> float:
        """Renvoie la largeur du rectangle"""
        return self._width

    @property
    def height(self) -> float:
        """Renvoie la hauteur du rectangle"""
        return self._height

    @property
    def half_width(self) -> float:
        """Renvoie la demi-largeur du rectangle"""
        return 0.5 * self._width

    @property
    def half_height(self) -> float:
        """Renvoie la demi-hauteur du rectangle"""
        return 0.5 * self._height

    @property
    def diagonal(self) -> float:
        """Renvoie la longueur de la diagonale"""
        return (self._width ** 2 + self._height ** 2) ** 0.5

    # ======================================== SETTERS ========================================
    @width.setter
    def width(self, value: Real):
        """
        Fixe la largeur du rectangle

        Args:
            value(Real): nouvelle largeur
        """
        self._width = float(positive(not_null(expect(value, Real))))
        self._vertices = self._compute_vertices()
        self._cache_sr = None

    @height.setter
    def height(self, value: Real):
        """
        Fixe la hauteur du rectangle

        Args:
            value(Real): nouvelle hauteur
        """
        self._height = float(positive(not_null(expect(value, Real))))
        self._vertices = self._compute_vertices()
        self._cache_sr = None

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """
        Vérifie l'égalité de deux rectangles

        Args:
            other(object): objet à comparer
        """
        if isinstance(other, Rect):
            return self._width == other._width and self._height == other._height
        return False

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Rect:
        """Renvoie une copie du rectangle"""
        return Rect(self._width, self._height)

    def scale(self, factor: Real) -> None:
        """
        Redimensionne le rectangle

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(positive(not_null(expect(factor, Real))))
        self._width *= factor
        self._height *= factor
        self._vertices = self._compute_vertices()
        self._cache_sr = None

    # ======================================== INTERNALS ========================================
    def _compute_vertices(self) -> NDArray[np.float32]:
        """Génère les sommets du rectangle centré à l'origine"""
        hw = 0.5 * self._width
        hh = 0.5 * self._height
        return np.array([
            (-hw, -hh),
            ( hw, -hh),
            ( hw,  hh),
            (-hw,  hh),
        ], dtype=np.float32)