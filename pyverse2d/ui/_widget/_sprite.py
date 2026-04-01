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
            pass
        
        # Mise à jour du renderer
        else:
            pass