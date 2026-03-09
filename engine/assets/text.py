# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..core import Asset

import pygame

# ======================================== OBJET ========================================
class Text(Asset):
    """Texte propre au moteur"""
    __slots__ = ("_text", "_font", "_size", "_color", "_surface")
    _cache: dict[tuple, pygame.Surface] = {}

    def __init__(self, text: str, font: str = None, fontsize: int = 16, color: tuple[int, ...] = (255, 255, 255, 255), _surface: pygame.Surface = None):
        """
        Args:
            text(str): contenu du texte
            font(str, optional): nom ou chemin de la police
            fontsize(int, optional): taille de la police
            color(tuple, optional): couleur RGB(A)
            _surface(Surface, optional): surface préchargée
        """
        self._text: str = expect(text, str)
        self._font: str = expect(font, (str, None))
        self._fontsize: int = expect(fontsize, int)
        self._color: tuple = expect(color, tuple[int, ...])
        self._surface: pygame.Surface = expect(_surface, (pygame.Surface, None))
        
        if self._surface is None:
            self._load()

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du texte"""
        return f"Text(text={self._text}, font={self._font}, fontsize={self._fontsize}, color={self._color})"

    # ======================================== GETTERS ========================================
    @property
    def text(self) -> str:
        """Renvoie le contenu du texte"""
        return self._text
    
    @property
    def font(self) -> str | None:
        """Renvoie la police du texte"""
        return self._font
    
    @property
    def fontsize(self) -> int:
        """Renvoie la taille de la police"""
        return self._fontsize

    @property
    def size(self) -> tuple[float, float]:
        """Renvoie la taille du texte rendu"""
        return (self.width, self.height)

    @property
    def width(self) -> float:
        """Renvoie la largeur du texte rendu"""
        if self._surface is None:
            return 0.0
        return float(self._surface.get_width())

    @property
    def height(self) -> float:
        """Renvoie la hauteur du texte rendu"""
        if self._surface is None:
            return 0.0
        return float(self._surface.get_height())
    
    @property
    def color(self) -> tuple[int, ...]:
        """Renvoie la couleur du texte"""
        return self._color

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Text:
        """Renvoie une copie du texte"""
        return Text(self._text, self._font, self._fontsize, self._color, _surface=self._surface.copy())

    def copy(self) -> Text:
        """Renvoie une copie du texte"""
        return Text(self._text, self._font, self._fontsize, self._color, _surface=self._surface.copy())

    def with_text(self, text: str) -> Text:
        """
        Renvoie un nouveau Text avec un contenu différent

        Args:
            text(str): nouveau contenu
        """
        return Text(expect(text, str), self._font, self._fontsize, self._color)

    def with_size(self, size: int) -> Text:
        """
        Renvoie un nouveau Text avec une taille différente

        Args:
            size(int): nouvelle taille
        """
        return Text(self._text, self._font, positive(not_null(expect(size, int))), self._color)

    def with_color(self, color: tuple[int, int, int, int]) -> Text:
        """
        Renvoie un nouveau Text avec une couleur différente

        Args:
            color(tuple): nouvelle couleur RGBA
        """
        return Text(self._text, self._font, self._fontsize, expect(color, tuple))

    # ======================================== INTERNAL METHODS ========================================
    def _cache_key(self) -> tuple:
        """Renvoie la clé de cache"""
        return (self._text, self._font, self._fontsize, self._color)
    
    def _load_font(self) -> pygame.font.Font:
        """
        Charge la police selon la disponibilité

        Returns:
            pygame.font.Font: police chargée
        """
        if self._font is None:
            return pygame.font.SysFont(None, self._fontsize)
        
        if self._font in pygame.font.get_fonts():
            return pygame.font.SysFont(self._font, self._fontsize)
        
        try:
            return pygame.font.Font(self._font, self._fontsize)
        except FileNotFoundError:
            print(f"Cannot load font {self._font}, falling back to default")
            return pygame.font.SysFont(None, self._fontsize)

    def _load(self):
        """Charge le texte en mémoire"""
        key = self._cache_key()
        if key in self._cache:
            self._surface = self._cache[key]
        else:
            font = self._load_font()
            self._surface = font.render(self._text, True, self._color)
            self._cache[key] = self._surface

    def _get_surface(self) -> pygame.Surface:
        """Renvoie la surface pygame du texte"""
        return self._surface