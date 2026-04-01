# ======================================== IMPORTS ========================================
from ..._internal import expect, positive, not_null
from ..._rendering import Pipeline, RenderContext, PygletSpriteRenderer
from ...abc import Widget
from ...asset import Image, Color
from ...math import Point

from numbers import Real

# ======================================== WIDGET ========================================
class Sprite(Widget):
    """Composant UI simple: Image

    Args:
        image: asset ``Image`` à rendre
        position: position ``(x, y)``
        anchor: ancre relative locale ``(ax, ay)``
        scale: facteur de redimensionnement
        flip_x: mirroir horizontal
        flip_y: mirroir vertical
        rotation: angle de rotation en degrés
        color: asset ``Color`` de teinte
        opacity: opacité
    """


    def __init__(
            self,
            image: Image,
            position: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            scale: Real = 1.0,
            flip_x: bool = False,
            flip_y: bool = False,
            rotation: Real = 0.0,
            color: Color = None,
            opacity: Real = 1.0,
        ):
        # Initialisation du widget
        super().__init__(position, anchor, opacity)

        # Image
        self._image: Image = expect(image, Image)
        self._image_renderer: PygletSpriteRenderer = None

        # Transform
        self._flip_x: bool = expect(flip_x, bool)
        self._flip_y: bool = expect(flip_y, bool)
        self._scale: float = positive(not_null(float(expect(scale, Real))))
        self._rotation: float = float(expect(rotation, Real))

        # Affichage
        self._color: Color = Color(color) if color is not None else None

    # ======================================== PROPERTIES ========================================
    @property
    def image(self) -> Image:
        """Image à rendre

        L'image doit être un Asset ``Image``
        """
        return self._image
    
    @image.setter
    def image(self, value: Image) -> None:
        self._image = expect(value, Image)

    @property
    def scale(self) -> float:
        """Facteur de redimensionnement

        Ce facteur doit être un ``réel`` positif non nul
        """
        return self._scale
    
    @scale.setter
    def scale(self, value: Real) -> None:
        self._scale = positive(not_null(float(expect(value, Real))))

    @property
    def flip_x(self) -> bool:
        """Mirroir horizontal

        Cette propriété appliquera ou non une inversion horizontale de l'image
        """
        return self._flip_x
    
    @flip_x.setter
    def flip_x(self, value: bool) -> None:
        self._flip_x = expect(value, bool)

    @property
    def flip_y(self) -> bool:
        """Mirroir vertical

        Cette propriété appliquera ou non une inversion verticale de l'image
        """
        return self._flip_y
    
    @flip_y.setter
    def flip_y(self, value: bool) -> None:
        self._flip_y = expect(value, bool)

    @property
    def rotation(self) -> float:
        """Angle de rotation

        La rotation se fait en ``degrés``, dans le sens ``horaire``
        """

    @rotation.setter
    def rotation(self, value: Real) -> None:
        self._rotation = float(expect(value, Real))

    @property
    def color(self) -> Color:
        """Couleur de teinte

        La couleur doit être un asset ``Color`` ou un tuple rgb/rgba
        """
        return self._color
    
    @color.setter
    def color(self, value: Color) -> None:
        self._color = Color(value) if value is not None else None
    
    # ======================================== TRANSFORMATIONS ========================================
    def resize(self, factor: Real) -> None:
        """Redimensionne l'image par un facteur

        Le facteur de redimensionnement doit être un réel positif non nul
        """
        self._scale *= positive(not_null(float(expect(factor, Real))))

    def rotate(self, angle: Real) -> None:
        """Applique une rotation à l'image

        L'angle de rotation est en ``degrés`` et la rotation se fait dans le sens ``horaire``
        """
        self._rotation += float(expect(angle, Real))

    # ======================================== LIFE CYCLE ========================================
    def _update(self, dt: float) -> None:
        """Actualisation"""
        ...

    def _draw(self, pipeline: Pipeline, context: RenderContext) -> None:
        """Affichage"""
        # Construction du renderer
        if self._image_renderer is None:
            self._image_renderer = PygletSpriteRenderer(
                image = self._image,
                x = context.origin.x,
                y = context.origin.y,
                anchor_x = self.anchor_x,
                anchor_y = self.anchor_y,
                scale_x = self._scale,
                scale_y = self._scale,
                flip_x = self._flip_x,
                flip_y = self._flip_y,
                rotation = self._rotation,
                color = self._color,
                opacity = context.opacity,
                z = context.z,
                pipeline = pipeline
            )
        
        # Mise à jour du renderer
        else:
            self._image_renderer.update(
                image = self._image,
                x = context.origin.x,
                y = context.origin.y,
                anchor_x = self.anchor_x,
                anchor_y = self.anchor_y,
                scale_x = self._scale,
                scale_y = self._scale,
                flip_x = self._flip_x,
                flip_y = self._flip_y,
                rotation = self._rotation,
                color = self._color,
                opacity = context.opacity,
                z = context.z,
                pipeline = pipeline
            )
    
    def _destroy(self):
        """Destruction du widget"""
        self._image_renderer.delete()
        self._image_renderer = None