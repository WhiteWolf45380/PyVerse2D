# ======================================== IMPORTS ========================================
from .._internal import expect
from ..core import Component, Shape

import pygame
from typing import Real

# ======================================== COMPONENT ========================================
class Sprite(Component):
    """Composant gérant le rendu"""
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