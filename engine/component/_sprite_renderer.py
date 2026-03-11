# ======================================== IMPORTS ========================================
from .._internal import expect, clamped
from .._core import Component
from ..asset import Image

from typing import Real, Iterator

# ======================================== COMPONENT ========================================
class SpriteRenderer(Component):
    """Composant gérant le rendu"""
    __slots__ = ("_image", "_offset", "_layer", "_z", "_visible", "_alpha")
    requires = ("Transform",)

    def __init__(
            self,
            image: Image,
            offset: tuple[Real, Real] = (0.0, 0.0),
            layer: int = 0,
            z: int = 0,
            visible: bool = True,
            alpha: float = 1.0,
        ):
        """
        Args:
            image(Image): image de rendu
            offset(tuple[Real, Real], optional): décalage par rapport au Transform
            layer(int, optional): couche de rendu
            z(int, optional): ordre de rendu
            visible(bool, optional): visibilité
            alpha(float, optional): facteur d'opacité de l'image
        """
        self._image: Image = expect(image, Image)
        self._offset: tuple[Real, Real] = expect(offset, tuple[Real, Real])
        self._layer: int = expect(layer, int)
        self._z: int = expect(z, int)
        self._visible: bool = expect(visible, bool)
        self._alpha: float = clamped(expect(alpha, float))
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"SpriteRenderer(image={self._image}, offset={self._offset}, layer={self._layer}, z={self._z}, visible={self._visible}, alpha={self._alpha})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Image, tuple[Real, Real], int, int, float]:
        """Renvoie le composant sous forme de tuple"""
        return (self._image, self._offset, self._layer, self._z, self._alpha)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._image, self._offset, self._layer, self._z, self._alpha]
    
    # ======================================== GETTERS ========================================
    @property
    def image(self) -> Image:
        """Renvoie l'image du sprite"""
        return self._image
    
    @property
    def offset(self) -> tuple[Real, Real]:
        """Renvoie le décalage par rapport au Transform"""
        return self._offset
    
    @property
    def layer(self) -> int:
        """Renvoie la couche de rendu"""
        return self._layer
    
    @property
    def z(self) -> int:
        """Renvoie l'ordre de rendu"""
        return self._z
    
    def get_alpha(self) -> float:
        """Renvoie le facteur d'opacité"""
        return self._alpha
    
    # ======================================== SETTERS ========================================
    def set_alpha(self, value: Real):
        """Fixe le facteur d'opacité"""
        self._alpha = clamped(float(expect(value, Real)))
    
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