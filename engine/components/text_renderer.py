# ======================================== IMPORTS ========================================
from .._internal import expect, clamped
from ..core import Component
from ..assets import Text

from .transform import Transform

from typing import Real, Iterator

# ======================================== COMPONENT ========================================
class TextRenderer(Component):
    """Composant gérant le rendu"""
    __slots__ = ("_text", "_layer", "_z", "_visible", "_alpha")
    requires = ("Transform",)

    def __init__(
            self,
            text: Text = None,
            offset: tuple[Real, Real] = (0.0, 0.0),
            layer: int = 0,
            z: int = 0,
            visible: bool = True,
            alpha: float = 1.0,
        ):
        """
        Args:
            text(Text, optional): texte du rendu
            offset(tuple[Real, Real], optional): décalage par rapport au Transform
            layer(int, optional): couche de rendu
            z(int, optional): ordre de rendu
            visible(bool, optional): visibilité
            alpha(float, optional): facteur d'opacité de l'image
        """
        self._text: Text = expect(text, Text)
        self._offset: tuple[Real, Real] = offset
        self._layer: int = expect(layer, int)
        self._z: int = expect(z, int)
        self._visible: bool = expect(visible, bool)
        self._alpha: float = clamped(expect(alpha, float))
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"TextRenderer(text={self._text}, offset={self._offset}, layer={self._layer}, z={self._z}, visible={self._visible}, alpha={self._alpha})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Text, int, int, float]:
        """Renvoie le composant sous forme de tuple"""
        return (self._text, self._offset, self._layer, self._z, self._alpha)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._text, self._offset, self._layer, self._z, self._alpha]
    
    # ======================================== GETTERS ========================================
    @property
    def text(self) -> Text:
        """Renvoie le texte du renderer"""
        return self._text
    
    @property
    def offset(self) -> tuple[float, float]:
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
        """Montre le texte"""
        self._visible = True

    def hide(self):
        """Cache le texte"""
        self._visible = False