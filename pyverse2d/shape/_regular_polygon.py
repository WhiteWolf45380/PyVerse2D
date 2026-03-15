# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive, not_null
from ..abc import VertexShape

from numbers import Real, Integral
import numpy as np
from numpy.typing import NDArray
import math

# ======================================== SHAPE ========================================
class RegularPolygon(VertexShape):
    """
    Polygone régulier à N côtés égaux

    Args:
        sides(Integral): nombre de côtés (minimum 3)
        radius(Real): rayon du cercle circonscrit
    """
    __slots__ = ("_sides", "_radius")

    def __init__(self, sides: Integral, radius: Real):
        if int(sides) < 3:
            raise ValueError("RegularPolygon must have at least 3 sides")
        self._sides: int = int(sides)
        self._radius: float = float(positive(not_null(expect(radius, Real))))
        super().__init__()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du polygone régulier"""
        return f"RegularPolygon(sides={self._sides}, radius={self._radius})"

    def __str__(self) -> str:
        """Renvoie une description lisible du polygone régulier"""
        return f"RegularPolygon[{self._sides} sides | r={self._radius} | area={self.area:.4g}]"

    # ======================================== GETTERS ========================================
    @property
    def sides(self) -> int:
        """Renvoie le nombre de côtés"""
        return self._sides

    @property
    def radius(self) -> float:
        """Renvoie le rayon du cercle circonscrit"""
        return self._radius

    @property
    def side_length(self) -> float:
        """Renvoie la longueur d'un côté"""
        return 2 * self._radius * math.sin(math.pi / self._sides)

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """
        Vérifie l'égalité de deux polygones réguliers

        Args:
            other(object): objet à comparer
        """
        if isinstance(other, RegularPolygon):
            return self._sides == other._sides and math.isclose(self._radius, other._radius)
        return False

    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> RegularPolygon:
        """Renvoie une copie du polygone régulier"""
        return RegularPolygon(self._sides, self._radius)

    def scale(self, factor: Real) -> None:
        """
        Redimensionne le polygone régulier

        Args:
            factor(Real): facteur de redimensionnement
        """
        factor = float(positive(not_null(expect(factor, Real))))
        self._radius *= factor
        self._vertices = self._compute_vertices()
        self._cache_sr = None

    # ======================================== INTERNALS ========================================
    def _compute_vertices(self) -> NDArray[np.float32]:
        """Génère les sommets du polygone régulier"""
        angles = np.linspace(0, 2 * math.pi, self._sides, endpoint=False)
        return np.stack([
            np.cos(angles) * self._radius,
            np.sin(angles) * self._radius
        ], axis=1).astype(np.float32)


# ======================================== FAÇADES ========================================
class RegularTriangle(RegularPolygon):
    """
    Triangle équilatéral

    Args:
        radius(Real): rayon du cercle circonscrit
    """
    __slots__ = ()

    def __init__(self, radius: Real):
        super().__init__(3, radius)

    def __repr__(self) -> str:
        """Renvoie une représentation du triangle"""
        return f"Triangle(radius={self._radius})"

    def copy(self) -> RegularTriangle:
        """Renvoie une copie du triangle"""
        return RegularTriangle(self._radius)


class RegularPentagon(RegularPolygon):
    """
    Pentagone régulier

    Args:
        radius(Real): rayon du cercle circonscrit
    """
    __slots__ = ()

    def __init__(self, radius: Real):
        super().__init__(5, radius)

    def __repr__(self) -> str:
        """Renvoie une représentation du pentagone"""
        return f"Pentagon(radius={self._radius})"

    def copy(self) -> RegularPentagon:
        """Renvoie une copie du pentagone"""
        return RegularPentagon(self._radius)


class RegularHexagon(RegularPolygon):
    """
    Hexagone régulier

    Args:
        radius(Real): rayon du cercle circonscrit
    """
    __slots__ = ()

    def __init__(self, radius: Real):
        super().__init__(6, radius)

    def __repr__(self) -> str:
        """Renvoie une représentation de l'hexagone"""
        return f"Hexagon(radius={self._radius})"

    def copy(self) -> RegularHexagon:
        """Renvoie une copie de l'hexagone"""
        return RegularHexagon(self._radius)


class RegularOctagon(RegularPolygon):
    """
    Octogone régulier

    Args:
        radius(Real): rayon du cercle circonscrit
    """
    __slots__ = ()

    def __init__(self, radius: Real):
        super().__init__(8, radius)

    def __repr__(self) -> str:
        """Renvoie une représentation de l'octogone"""
        return f"Octagon(radius={self._radius})"

    def copy(self) -> RegularOctagon:
        """Renvoie une copie de l'octogone"""
        return RegularOctagon(self._radius)