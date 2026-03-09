# ======================================== IMPORTS ========================================
from .._internal import expect, positive, inverse
from ..core import Component
from ..math import Point

from typing import Iterator
from numbers import Real

# ======================================== COMPONENT ========================================
class Transform(Component):
    """Composant gérant le positionnement"""
    def __init__(
        self,
        pos: Point,
        anchor: str = "center",
        rotation: float = 0.0,
        scale: float = 1.0,
    ):
        """
        Args:
            pos(Point): position
            anchor(str, optional): ancre de positionnement
            rotation(float, optional): angle de rotation en radians
            scale(float, otional): facteur de redimensionnement
        """
        super().__init__()
        self._pos: Point = expect(pos, Point)
        self._anchor: str = expect(anchor, str)
        self._rotation: float = float(expect(rotation, Real))
        self._scale: float = float(positive(inverse(expect(scale, Real))))

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Transform(x={self._point.x}, y={self._point.x}, anchor={self._anchor}, rotation={self._rotation}, scale={self._scale})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Point, str, float, float]:
        """Renvoie le composant sous forme tuple"""
        return (self._pos, self._anchor, self._rotation, self._scale)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._pos, self._anchor, self._rotation, self._scale]

    # ======================================== GETTERS ========================================
    @property
    def x(self) -> float:
        """Renvoie la coordonnée horizontale"""
        return self._point.x
    
    @property
    def y(self) -> float:
        """Renvoie la coordonnée verticale"""
        return self._point.y
    
    @property
    def pos(self) -> Point:
        """Renvoie le point de position"""
        return self._pos
    
    @property
    def anchor(self) -> str:
        """Renvoie l'ancre de positionnement"""
        return self._anchor
    
    @property
    def rotation(self) -> float:
        """Renvoie la rotation en radians"""
        return self._rotation
    
    @property
    def scale(self) -> float:
        """Renvoie le facteur de redimensionnement"""
        return self._scale

    # ======================================== SETTERS ========================================
    @x.setter
    def x(self, value: Real):
        """Fixe la coordonnée horizontale"""
        self._pos.x = float(expect(value, Real))
    
    @y.setter
    def y(self, value: Real):
        """Fixe la coordonnée verticale"""
        self._pos.y = float(expect(value, Real))

    @pos.setter
    def pos(self, value: Point):
        """Fixe le point de posiiton"""
        self._pos = expect(value, Point)

    @anchor.setter
    def anchor(self, value: str):
        """Fixe l'ancre de positionnement"""
        self._anchor = expect(value, str)
    
    @rotation.setter
    def rotation(self, value: Real):
        """Fixe la rotation"""
        self._rotation = float(expect(value, Real))
    
    @scale.setter
    def scale(self, value: Real):
        """Fixe le facteur de redimensionnement"""
        self._scale = float(positive(inverse(expect(value, Real))))