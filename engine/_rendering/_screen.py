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
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Screen:
        """Renvoie une copie de l'écran"""
        return Screen(self._width, self._height)