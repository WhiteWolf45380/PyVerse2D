# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect
from ..._rendering import Pipeline, RenderContext
from ...asset import Color
from ...abc import Widget, Shape
from ...math import Point

from numbers import Real

# ======================================== WIDGET ========================================
class Surface(Widget):
    """
    Composant UI : Surface

    Args:
        shape(Shape): forme de la surface
        pos(Point, optional): position
        anchor(Point, optional): ancre locale relative
        filling(bool, optional): remplissage
        color(Color, optional): couleur de remplissage
        opacité(Real, optional): opacité [0; 1]
        parent(Widget, optional): Composant UI parent
    """
    __slots__ = ()

    def __init__(
            self,
            shape: Shape,
            pos: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            filling: bool = True,
            color: Color = (125, 125, 125),
            opacity: Real = 1.0,
            parent: Widget = None,
        ):
        super().__init__(parent, pos, anchor, opacity)
        self._shape: Shape = expect(shape, Shape)
        self._filling: bool = expect(filling, bool)
        self._color: Color = Color(color)

    # ======================================== GETTERS ========================================
    @property
    def shape(self) -> Shape:
        """Renvoie la forme de la surface"""
        return self._shape
    
    @property
    def color(self) -> Color:
        """Renvoie la couleur de remplissage"""
        return self._color
    
    # ======================================== SETTERS ========================================
    @shape.setter
    def shape(self, value: Shape) -> None:
        """Fixe la forme de la surface"""
        self._shape = expect(value, Shape)
    
    @color.setter
    def color(self, value: Color) -> None:
        """Fixe la couleur de remplissage"""

    # ======================================== LIFE CYCLE ========================================
    def _update(self, dt: float) -> None:
        """Actualisation"""
    
    def _draw(self, pipeline: Pipeline, context: RenderContext) -> None:
        """Affichage"""