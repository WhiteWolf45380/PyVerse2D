# ======================================== IMPORTS ========================================
from ..._internal import expect, clamped
from ...abc import Component, Shape
from ...asset import Color
from ...math import Vector

from typing import Iterator
from numbers import Real

# ======================================== COMPONENT ========================================
class ShapeRenderer(Component):
    """
    Composant gérant le rendu d'une forme

    Args:
        shape(Shape, optional): forme du rendu
        offset(Vector, optional): décalage par rapport au Transform
        filling(bool, optional): activation du remplissage
        filling_color(Color, optional): couleur de remplissage
        border_width(int, optinal): épaisseur de la bordure
        border_color(Color, optional): couleur de la bordure
        opacity(Real, optional): facteur d'opacité
        z(int, optional): ordre de rendu
        visible(bool, optional): visibilité
    """
    __slots__ = ("_shape", "_offset", "_filling", "_filling_color", "_border_width", "_border_color", "_opacity", "_z", "_visible")
    requires = ("Transform",)

    def __init__(
            self,
            shape: Shape = None,
            offset: Vector = (0.0, 0.0),
            filling: bool = True,
            filling_color: Color = (255, 255, 255, 1.0),
            border_width: int = 0,
            border_color: Color = (0, 0, 0, 1.0),
            opacity: Real = 1.0,
            z: int = 0,
            visible: bool = True,
        ):
        self._shape: Shape = expect(shape, Shape)
        self._offset: Vector =Vector(offset)
        self._filling: bool = expect(filling, bool)
        self._filling_color: Color = Color(filling_color)
        self._border_width: int = int(expect(border_width, Real))
        self._border_color: Color = Color(border_color)
        self._opacity: float = float(clamped(expect(opacity, Real)))
        self._z: int = expect(z, int)
        self._visible: bool = expect(visible, bool)
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"ShapeRenderer(shape={self._shape}, z={self._z}, visible={self._visible})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Shape, Vector, bool, Color, int, Color, float, int]:
        """Renvoie le composant sous forme de tuple"""
        return (self._shape, self._offset, self._filling, self._filling_color, self._border_width, self._border_color, self._opacity, self._z)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._shape, self._offset, self._filling, self._filling_color, self._border_width, self._border_color, self._opacity, self._z]
    
    # ======================================== GETTERS ========================================
    @property
    def shape(self) -> Shape:
        """Renvoie la forme du renderer"""
        return self._shape
    
    @property
    def offset(self) -> Vector:
        """Renvoie le décalage par rapport au Transform"""
        return self._offset
    
    @property
    def offset_x(self) -> float:
        """Renvoie le décalage horizontal"""
        return self._offset.x
    
    @property
    def offset_y(self) -> float:
        """Renvoie le décalage vertical"""
        return self._offset.y
    
    @property
    def filling(self) -> bool:
        """Renvoie l'état du remplissage"""
        return self._filling
    
    @property
    def filling_color(self) -> Color:
        """Renvoie la couleur du remplissage"""
        return self._filling_color
    
    @property
    def border_width(self) -> int:
        """Renvoie l'épaisseur de la bordure"""
        return self._border_width
    
    @property
    def border_color(self) -> Color:
        """Renvoie la couleur de la bordure"""
        return self._border_color
    
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
        """Fixe le décalage par rapport au tranform"""
        self._offset = Vector(value)

    @filling.setter
    def filling(self, value: bool):
        """Fixe l'état du remplissage"""
        self._filling = expect(value, bool)

    @filling_color.setter
    def filling_color(self, value: Color):
        """Fixe la couleur de remplissage"""
        self._filling_color = expect(value, Color)

    @border_width.setter
    def border_width(self, value: int):
        """Fixe l'épaisseur de la bordure"""
        self._border_width = int(expect(value, Real))
    
    @border_color.setter
    def border_color(self, value: Color):
        """Fixe la couleur de la bordure"""
        self._border_color = Color(value)

    @opacity.setter
    def opacity(self, value: Real):
        """Fixe le facteur d'opacité"""
        self._opacity = float(clamped(expect(value, Real)))

    @z.setter
    def z(self, value: int):
        """Fixe l'ordre de rendu"""
        self._z = expect(value, int)
    
    # ======================================== PREDICATES ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._visible

    # ======================================== PUBLIC METHODS ========================================
    def show(self):
        """Montre la forme"""
        self._visible = True

    def hide(self):
        """Cache la forme"""
        self._visible = False