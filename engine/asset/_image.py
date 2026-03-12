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
        scale(Real, optional): facteur de redimensionnement
        flip_x(bool, optional): miroir horizontal
        flip_y(bool, optional): miroir vertical
        rotation(Real, optional): angle de rotation en degrés
    """
    __slots__ = ("_path", "_width", "_height", "_scale", "_flip_x", "_flip_y", "_rotation")

    def __init__(
            self,
            path: str,
            width: Real = None,
            height: Real = None,
            scale: Real = 1.0,
            flip_x: bool = False,
            flip_y: bool = False,
            rotation: Real = 0.0,
        ):
        self._path: str = expect(path, str)
        self._width: float | None = float(positive(expect(width, Real))) if width is not None else None
        self._height: float | None = float(positive(expect(height, Real))) if height is not None else None
        self._scale: float = float(positive(not_null(expect(scale, Real))))
        self._flip_x: bool = expect(flip_x, bool)
        self._flip_y: bool = expect(flip_y, bool)
        self._rotation: float = float(expect(rotation, Real))

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'image"""
        return f"Image(path={self._path}, width={self._width}, height={self._height}, scale={self._scale}, flip_x={self._flip_x}, flip_y={self._flip_y}, rotation={self._rotation})"

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
    def scale(self) -> float:
        """Renvoie le facteur de redimensionnement"""
        return self._scale

    @property
    def flip_x(self) -> bool:
        """Renvoie le miroir horizontal"""
        return self._flip_x

    @property
    def flip_y(self) -> bool:
        """Renvoie le miroir vertical"""
        return self._flip_y

    @property
    def rotation(self) -> float:
        """Renvoie l'angle de rotation"""
        return self._rotation

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Image:
        return Image(self._path, self._flip_x, self._flip_y, self._rotation, self._scale, self._width, self._height)

    def copy(self) -> Image:
        return Image(self._path, self._flip_x, self._flip_y, self._rotation, self._scale, self._width, self._height)
    
    def resize(self, width: Real = None, height: Real = None) -> Image:
        """
        Renvoie l'image avec des dimensions cibles

        Args:
            width(Real, optional): largeur cible
            height(Real, optional): hauteur cible
        """
        w = float(positive(expect(width, Real))) if width is not None else self._width
        h = float(positive(expect(height, Real))) if height is not None else self._height
        return Image(self._path, self._flip_x, self._flip_y, self._rotation, self._scale, w, h)
    
    def scale(self, factor: Real = 1.0) -> Image:
        """Renvoie l'image redimensionnée par un facteur"""
        factor = float(positive(not_null(expect(factor, Real))))
        return Image(self._path, self._flip_x, self._flip_y, self._rotation, factor, self._width, self._height)

    def flip(self, horizontal: bool = False, vertical: bool = False) -> Image:
        """Renvoie l'image miroir"""
        return Image(self._path, expect(horizontal, bool), expect(vertical, bool), self._rotation, self._scale, self._width, self._height)

    def rotate(self, angle: Real = 0.0) -> Image:
        """Renvoie l'image tournée"""
        return Image(self._path, self._flip_x, self._flip_y, float(expect(angle, Real)), self._scale, self._width, self._height)