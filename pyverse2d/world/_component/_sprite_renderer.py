# ======================================== IMPORTS ========================================
from ..._internal import expect, clamped
from ...abc import Component
from ...asset import Image, Color
from ...math import Vector

from typing import Iterator
from numbers import Real

# ======================================== COMPONENT ========================================
class SpriteRenderer(Component):
    """Composant gérant le rendu d'une image"""
    __slots__ = ("_image", "_offset", "_z", "_visible", "_opacity")
    requires = ("Transform",)

    def __init__(
            self,
            image: Image,
            offset: Vector = (0.0, 0.0),
            tint: Color = (255, 255, 255),
            opacity: Real = 1.0,
            z: int = 0,
            visible: bool = True,
        ):
        """
        Args:
            image(Image): image de rendu
            offset(Vector, optional): décalage par rapport au Transform
            tint(Color, optional): couleur de teinte
            opacity(float, optional): facteur d'opacité de l'image
            z(int, optional): ordre de rendu
            visible(bool, optional): visibilité
        """
        self._image: Image = expect(image, Image)
        self._offset: Vector = Vector(offset)
        self._tint: Color = Color(tint)
        self._opacity: float = clamped(expect(opacity, Real))
        self._z: int = expect(z, int)
        self._visible: bool = expect(visible, bool)
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"SpriteRenderer(image={self._image}, opacity={self._opacity}, z={self._z}, visible={self._visible})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Image, Vector, float, int]:
        """Renvoie le composant sous forme de tuple"""
        return (self._image, self._offset, self._opacity, self._z)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._image, self._offset, self._opacity, self._z]
    
    # ======================================== GETTERS ========================================
    @property
    def image(self) -> Image:
        """Renvoie l'image du sprite"""
        return self._image
    
    @property
    def offset(self) -> Vector:
        """Renvoie le décalage par rapport au Transform"""
        return self._offset
    
    @property
    def tint(self) -> Color:
        """Renvoie la couleur de teinte"""
        return self._tint
    
    @property
    def opacity(self) -> float:
        """Renvoie le facteur d'opacité"""
        return self._opacity
    
    @property
    def z(self) -> int:
        """Renvoie l'ordre de rendu"""
        return self._z
    
    # ======================================== SETTERS ========================================
    @offset.setter
    def offset(self, value: Vector):
        """Fixe le décalage par rapport au Transform"""
        self._offset = Vector(value)

    @tint.setter
    def tint(self, value: Color):
        """Fixe la couleur de teinte"""
        self._tint = Color(value)

    @opacity.setter
    def opacity(self, value: Real):
        """Fixe le facteur d'opacité"""
        self._opacity = float(clamped(expect(value, Real)))
    
    # ======================================== PREDICATES ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._visible

    # ======================================== PUBLIC METHODS ========================================
    def show(self):
        """Montre le sprite"""
        self._visible = True

    def hide(self):
        """Cache le sprite"""
        self._visible = False