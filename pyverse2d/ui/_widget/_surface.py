# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect
from ..._rendering import Pipeline, RenderContext, PygletShapeRenderer
from ...asset import Color
from ...abc import Widget, Shape, CompositeShape
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
    __slots__ = ("_shape", "_color")

    def __init__(
            self,
            shape: Shape,
            pos: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            color: Color = (125, 125, 125),
            opacity: Real = 1.0,
            parent: Widget = None,
        ):
        super().__init__(parent, pos, anchor, opacity)
        self._shape: Shape = expect(shape, Shape)
        self._shape_renderer: PygletShapeRenderer = None
        self._color: Color = Color(color)
        if isinstance(self._shape, CompositeShape):
            raise ValueError("Surface does not support CompositeShape")

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
        if self._renderer is None:
            self._renderer = PygletShapeRenderer(
                shape = self._shape,
                cx = context.origin.x,
                cy = context.origin.y,
                scale = 1.0,
                rotation = 0.0,
                color = self._color,
                opacity = context.opacity,
                pipeline = pipeline,
                z = context.z,
            )

        else:
            self._renderer.update(
                cx = context.origin.x,
                cy = context.origin.y,
                scale = 1.0,
                rotation = 0.0,
                color = self._color,
                opacity = context.opacity,
            )
 
    def destroy(self) -> None:
        """
        Libère les ressources pyglet et se détache de son parent.
        À appeler explicitement quand le widget n'est plus utilisé.
        """
        if self._renderer is not None:
            self._renderer.delete()
            self._renderer = None
 
        if self._parent is not None:
            self._parent.remove_child(self)