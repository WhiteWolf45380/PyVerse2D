# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from ..math import Point, Vector

from numbers import Real

# ======================================== VIEWPORT ========================================
class Viewport:
    """Zone de l'espace logique

    Args:
        position: position du coin bas gauche du viewport
        width: largeur en pixels logiques (0.0 = tout)
        height: hauteur en pixels logiques (0.0 = tout)
        origin: origine relative du viewport
        direction: direction des coordonnées
    """
    __slots__ = (
        "_position",
        "_width", "_height",
        "_origin", "_direction",
    )

    def __init__(
        self,
        position: Point = (0.0, 0.0),
        width: Real = 0.0,
        height: Real = 0.0,
        origin: Point = (0.0, 0.0),
        direction: Vector = (1.0, 1.0),
    ):
        self._position: Point = Point(position)
        self._width: float = positive(float(expect(width, Real)), arg="width")
        self._height: float = positive(float(expect(height, Real)), arg="height")
        self._origin: Point = Point(origin)
        self._direction: Vector = Vector(direction)

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position du coin bas gauche

        La position peut-être un objet mathématique ``Point`` ou un tuple ``(x, y)``
        """
        return self._position
    
    @position.setter
    def position(self, value: Point):
        self._position.x = value[0]
        self._position.y = value[1]

    @property
    def x(self) -> float:
        """Cordonnée horizontale du coin bas gauche
        
        La valeur doit être un ``Réel``.
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real):
        self._position.x = value

    @property
    def y(self) -> float:
        """Coordonnée verticale du coin bas gauche

        La valeur doit être un ``Réel``.
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real):
        self._position.y = value

    @property
    def width(self) -> float:
        """Largeur du viewport
        
        La largeur doit être un ``Réel`` positif non nul.
        """
        return self._width
    
    @width.setter
    def width(self, value: Real):
        self._width = positive(float(expect(value, Real)), arg="width")

    @property
    def height(self) -> float:
        """Hauteur du viewport
        
        La hauteur doit être un ``Réel`` positif non nul.
        """
        return self._height
    
    @height.setter
    def height(self, value: Real):
        self._height = positive(float(expect(value, Real)), arg="height")

    @property
    def origin(self) -> Point:
        """Origine relative du viewport

        L'origine peut être un objet ``Point`` ou un tuple ``(ox, oy)``.
        Les coordonnées de l'origine doivent être dans l'intervalle [0, 1].
        """
        return self._origin
    
    @origin.setter
    def origin(self, value: Point) -> None:
        self._origin.x = value[0]
        self._origin.y = value[1]

    @property
    def direction(self) -> Vector:
        """Vecteur directionnel des coordonnées

        Le vecteur peut être un objet ``Vector`` ou un tuple ``(dx, dy)``
        """
        return self._direction

    @direction.setter
    def direction(self, value: Vector) -> None:
        self._direction.x = value[0]
        self._direction.y = value[1]

    # ======================================== RESOLVING ========================================
    def resolve(self, screen_width: int, screen_height: int) -> tuple[float, float, float, float]:
        """Renvoie ``(left, right, bottom, top)`` résolus dans l'espace logique

        Args:
            screen_width: largeur de l'espace logique
            screen_height: hauteur de l'espace logique
        """
        w = self._width  if self._width  != 0.0 else screen_width
        h = self._height if self._height != 0.0 else screen_height

        # Origine en pixels dans le viewport
        ox = self._origin.x * w
        oy = self._origin.y * h

        # Coin bas-gauche dans l'espace logique
        x = self._position.x - ox * self._direction.x
        y = self._position.y - oy * self._direction.y

        left   = x
        right  = x + w * self._direction.x
        bottom = y
        top    = y + h * self._direction.y

        return (left, right, bottom, top)