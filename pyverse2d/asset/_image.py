# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import Asset

from numbers import Real

# ======================================== OBJET ========================================
class Image(Asset):
    """
    Descripteur d'image

    Args:
        path(str): chemin du fichier
        width(Real, optional): largeur cible en pixels
        height(Real, optional): hauteur cible en pixels
        scale_factor(Real, optional): facteur de redimensionnement
    """
    __slots__ = ("_path", "_width", "_height", "_scale_factor")

    def __init__(
            self,
            path: str,
            width: Real = None,
            height: Real = None,
            scale_factor: Real = 1.0,
        ):
        self._path: str = expect(path, str)
        self._width: float | None = float(positive(expect(width, Real))) if width is not None else None
        self._height: float | None = float(positive(expect(height, Real))) if height is not None else None
        self._scale_factor: float = float(positive(not_null(expect(scale_factor, Real))))

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'image"""
        return f"Image(path={self._path}, width={self._width}, height={self._height}, scale={self._scale_factor})"

    # ======================================== GETTERS ========================================
    @property
    def path(self) -> str:
        """Renvoie le chemin du fichier"""
        return self._path

    @property
    def width(self) -> float | None:
        """Renvoie la largeur cible"""
        return self._width

    @property
    def height(self) -> float | None:
        """Renvoie la hauteur cible"""
        return self._height
    
    @property
    def scale_factor(self) -> float:
        """Renvoie le facteur de redimensionnement"""
        return self._scale_factor
    
    @property
    def original(self) -> Image:
        """Renvoie l'image d'origine"""
        return Image(self._path)

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Image:
        return Image(self._path, self._width, self._height, self._scale_factor)

    def copy(self) -> Image:
        return self.__copy__()
    
    def resize(self, width: Real = None, height: Real = None) -> None:
        """
        Modifie la taille de l'image avec des dimensions cibles
        Par défaut, une valeur à None entraîne une conservation du ratio

        Args:
            width(Real, optional): largeur cible
            height(Real, optional): hauteur cible
        """
        self._width = float(positive(expect(width, Real))) if width is not None else self._width
        self._height = float(positive(expect(height, Real))) if height is not None else self._height
        self._scale_factor = 1.0
    
    def scale(self, factor: Real = 1.0) -> None:
        """
        Modifie la taille de l'image par un facteur

        Args:
            factor(Real): facteur de redimensionnement
        """
        self._scale_factor *= float(positive(not_null(expect(factor, Real))))
    
    def reset(self) -> None:
        """Rétablit l'image d'origine"""
        self._width = None
        self._height = None
        self._scale_factor = 1.0