# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..core import Asset

import pygame

# ======================================== OBJET ========================================
class Image(Asset):
    """Image propre au moteur"""
    __slots__ = ("_name", "_surface")
    _cache: dict[str, pygame.Surface] = {}

    def __init__(self, name: str = None, path: str = None, _surface: pygame.Surface = None):
        """
        Args:
            name(str, optional): nom de l'image (par défaut path)
            path(str, optional): chemin du fichier
            _surface(Surface, optional): surface préchargée
        """
        self._name: str = expect(name, str) if name is not None else path
        self._surface: pygame.Surface = expect(_surface, (pygame.Surface, None))
        if self._surface is None and path is not None:
            self._load(expect(path, str))
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'image"""
        return f"Image(name={self._name}, width={self.width}, height={self.height})"

    # ======================================== GETTERS ========================================
    @property
    def size(self) -> tuple[float, float]:
        """Renvoie la taille de l'image"""
        return (self.width, self.height)

    @property
    def width(self) -> float:
        """Renvoie la largeur de l'image"""
        if self._surface is None:
            return 0.0
        return float(self._surface.get_width())
    
    @property
    def height(self) -> float:
        """Renvoie la hauteur de l'image"""
        if self._surface is None:
            return 0.0
        return float(self._surface.get_height())

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Image:
        """Renvoie une copie de l'image"""
        return Image(name=self._name, _surface=self._surface.copy())
    
    def copy(self) -> Image:
        """Renvoie une copie de l'image"""
        return Image(name=self._name, _surface=self._surface.copy())
    
    def scale(self, width: float = 0.0, height: float = 0.0) -> Image:
        """
        Renvoie l'image redimensionnée

        Args:
            width(Real, optional): largeur (gestion automatique si non-définie)
            height(Real, optional): hauteur (gestion automatique si non-définie)
        """
        if positive(expect(width, (int, float))) == 0 and positive(expect(height, (int, float))) == 0:
            width, height = self.width, self.height
        if width == 0:
            width = self.width * height / self.height
        elif height == 0:
            height = self.height * width / self.width
        return Image(name=self._name, _surface=pygame.transform.scale(self._surface, (width, height)))
    
    def scale_by(self, factor: float = 1.0) -> Image:
        """
        Renvoie l'image redimensionnée par un facteur

        Args:
            factor(Real, optional): facteur de redimensionnement
        """
        factor = positive(not_null(expect(factor, (int, float))))
        width, height = self.width * factor, self.height * factor
        return Image(name=self._name, _surface=pygame.transform.scale(self._surface, (width, height)))
    
    def flip(self, horizontal: bool = False, vertical: bool = False) -> Image:
        """
        Renvoie l'image mirroir

        Args:
            horizontal(bool, optional): mirroir horizontal
            vertical(bool, optional): mirroir vertical
        """
        return Image(name=self._name, _surface=pygame.transform.flip(self._surface, expect(horizontal, bool), expect(vertical, bool)))
    
    def rotate(self, angle: float = 0.0) -> Image:
        """
        Renvoie l'image tournée dans le sens trigonométrique

        Args:
            angle(float): angle de rotation en degrés
        """
        return Image(name=self._name, _surface=pygame.transform.rotate(self._surface, expect(angle, (int, float))))

    # ======================================== INTERNAL METHODS ========================================
    def _load(self, path: str):
        """
        Charge une image en mémoire

        Args:
            path(str): chemin du fichier
        """
        if self._name in self._cache:
            self._surface = self._cache[self._name]
        else:
            try:
                self._surface = pygame.image.load(path).convert_alpha()
                self._cache[self._name] = self._surface
            except FileNotFoundError:
                self._surface = None
                print(f"Cannot load image {path}")

    def _get_surface(self) -> pygame.Surface:
        """Renvoie la surface pygame de l'image"""
        return self._surface