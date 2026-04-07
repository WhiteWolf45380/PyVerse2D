# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from numbers import Real

# ======================================== OBJET ========================================
class Screen:
    """
    Espace de rendu de référence à résolution fixe

    Args:
        width: largeur de l'espace virtuel
        height: hauteur de l'espace virtuel
        pixels_per_unit: rapport de conversion entre les pixels écran et les unités monde
    """
    __slots__ = (
        "_width", "_height",
        "_pixels_per_unit",
    )

    def __init__(self, width: int = 1920, height: int = 1080, pixels_per_unit: int = 10):
        self._width: int = int(expect(width, Real))
        self._height: int = int(expect(height, Real))
        self._pixels_per_unit: int = expect(pixels_per_unit, int)

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'écran"""
        return f"Screen({self._width}x{self._height})"

    # ======================================== GETTERS ========================================
    @property
    def width(self) -> int:
        """Renvoie la largeur de l'écran"""
        return self._width

    @property
    def height(self) -> int:
        """Renvoie la hauteur de l'écran"""
        return self._height

    @property
    def ratio(self) -> float:
        """Ratio largeur/hauteur de l'écran"""
        return self._width / self._height

    @property
    def size(self) -> tuple[int, int]:
        """Renvoie la taille de l'écran"""
        return self._width, self._height
    
    @property
    def half_width(self) -> float:
        """Renvoie la demi-largeur de l'écran"""
        return self._width * 0.5
    
    @property
    def half_height(self) -> float:
        """Renvoie la demi-hauteur de l'écran"""
        return self._height * 0.5

    @property
    def center(self) -> tuple[float, float]:
        """Renvoie la position du centre de l'écran"""
        return (self._width * 0.5, self._height * 0.5)
    
    @property
    def centerx(self) -> float:
        """Renvoie le centre x de l'écran"""
        return self._width * 0.5
    
    @property
    def centery(self) -> float:
        """Renvoie le centrey de l'écran"""
        return self._height * 0.5
    
    @property
    def pixels_per_unit(self) -> int:
        """Renvoie le rapport de conversion entre les pixels écran et les unités monde"""
        return self._pixels_per_unit
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Screen:
        """Renvoie une copie de l'écran"""
        return Screen(self._width, self._height, self._pixels_per_unit)