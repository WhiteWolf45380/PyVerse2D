# ======================================== IMPORTS ========================================
from .._internal import expect
from ..core import Component, Shape

import pygame
from typing import Real, Iterator

# ======================================== COMPONENT ========================================
class Sprite(Component):
    """Composant gérant le rendu"""
    __slots__ = ("_image", "_shape", "_width", "_height")
    def __init__(
        self,
        image: pygame.Surface | str = None,
        shape: Shape = None,
        width: Real = None,
        height: Real = None,
    ):
        """
        Args:
            image(Surface|str, optional): image de rendu
            shape(Shape, optional): forme de rendu
            width(Real, optional): largeur
            height(Real, optional): hauteur
        """
        super().__init__()
        self._image = expect(image, (pygame.Surface, str, None))
        self._shape = expect(shape, Shape)
        self._width = float(expect(width, Real))
        self._height = float(expect(height, Real))
        self._load()
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Sprite(image={self._image}, shape={self._shape}, width={self._width}, height={self._height})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[pygame.Surface, Shape, float, float]:
        """Renvoie le composant sous forme de tuple"""
        return (self._image, self._shape, self._width, self._height)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._image, self._shape, self._width, self._height]
    
    # ======================================== GETTERS ========================================

    # ======================================== SETTERS ========================================