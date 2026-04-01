# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, positive, not_null
from ..._rendering import Pipeline, RenderContext, PygletShapeRenderer
from ...asset import Color
from ...abc import Widget, Shape
from ...math import Point

from numbers import Real

# ======================================== WIDGET ========================================
class Surface(Widget):
    """
    Composant UI simple: Surface

    Args:
        shape(Shape): forme de la surface
        position(Point, optional): position
        anchor(Point, optional): ancre locale relative
        filling(bool, optional): remplissage
        color(Color, optional): couleur de remplissage
        opacité(Real, optional): opacité [0; 1]
    """
    __slots__ = (
        "_shape", "_shape_renderer",
        "_color", "_scale", "_rotation"
    )

    def __init__(
            self,
            shape: Shape,
            position: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            color: Color = (125, 125, 125),
            opacity: Real = 1.0,
        ):
        # Initialisation du widget
        super().__init__(position, anchor, opacity)

        # Forme
        self._shape: Shape = expect(shape, Shape)
        self._shape_renderer: PygletShapeRenderer = None

        # Transformation
        self._scale: float = 1.0
        self._rotation: float = 0.0

        # Affichage
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
    
    @property
    def scale(self) -> float:
        """Renvoie le facteur de redimensionnement"""
        return self._scale
    
    @property
    def rotation(self) -> float:
        """Renvoie l'angle de rotation en degrés"""
        return self._rotation
    
    # ======================================== SETTERS ========================================
    @shape.setter
    def shape(self, value: Shape) -> None:
        """Fixe la forme de la surface"""
        self._shape = expect(value, Shape)
    
    @color.setter
    def color(self, value: Color) -> None:
        """Fixe la couleur de remplissage"""
        self._color = Color(value)

    @scale.setter
    def scale(self, value: Real) -> None:
        """Fixe le facteur de redimensionnement"""
        self._scale = positive(not_null(float(expect(value, Real))))
    
    @rotation.setter
    def rotation(self, value: Real) -> None:
        """Fixe l'angle de rotation en degrés"""
        self._rotation = float(expect(value, Real))

    # ======================================== TRANSFORMATIONS ========================================
    def resize(self, scale: Real) -> None:
        """
        Redimensionne la forme de la surface

        Args:
            scale(Real): facteur de redimensionnement
        """
        self._scale *= positive(not_null(float(expect(scale, Real))))
    
    def rotate(self, angle: Real) -> None:
        """
        Tourne la forme de la surface

        Args:
            angle(Real): angle de rotation en degrés
        """
        self._rotation += float(expect(angle, Real))

    # ======================================== LIFE CYCLE ========================================
    def _update(self, dt: float) -> None:
        """Actualisation"""
        ...
    
    def _draw(self, pipeline: Pipeline, context: RenderContext) -> None:
        """Affichage"""
        # Construction du renderer
        if self._shape_renderer is None:
            self._shape_renderer = PygletShapeRenderer(
                shape = self._shape,
                x = context.origin.x,
                y = context.origin.y,
                anchor_x = self.anchor_x,
                anchor_y = self.anchor_y,
                scale = self._scale,
                rotation = self._rotation,
                color = self._color,
                opacity = context.opacity,
                pipeline = pipeline,
                z = context.z,
            )

        # Mise à jour du renderer
        else:
            self._shape_renderer.update(
                x = context.origin.x,
                y = context.origin.y,
                anchor_x = self.anchor_x,
                anchor_y = self.anchor_y,
                scale = self._scale,
                rotation = self._rotation,
                color = self._color,
                opacity = context.opacity,
                pipeline=pipeline,
                z=context.z,
            )
 
    def _destroy(self) -> None:
        """
        Libère les ressources pyglet et se détache de son parent.
        À appeler explicitement quand le widget n'est plus utilisé.
        """
        if self._shape_renderer is not None:
            self._shape_renderer.delete()
            self._shape_renderer = None