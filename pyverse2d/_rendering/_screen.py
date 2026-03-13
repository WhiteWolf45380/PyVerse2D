# ======================================== IMPORTS ========================================
from __future__ import annotations

# ======================================== OBJET ========================================
class Screen:
    """
    Espace de rendu de référence à résolution fixe

    Args:
        width (int):  largeur
        height (int): hauteur
    """
    def __init__(self, width: int = 1920, height: int = 1080):
        self._width  = int(width)
        self._height = int(height)

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
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
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Screen:
        """Renvoie une copie de l'écran"""
        return Screen(self._width, self._height)