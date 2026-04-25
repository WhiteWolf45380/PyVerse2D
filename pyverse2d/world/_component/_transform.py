# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Component
from ...math import Point, Vector

from numbers import Real

# ======================================== COMPONENT ========================================
class Transform(Component):
    """Composant gérant le positionnement

    Ce composant est manipulé par ``PhysicsSystem``, ``CollisionSystem`` et ``SteeringSystem``.

    Args:
        position: position
        anchor: ancre de positionnement
        rotation: angle de rotation en degrés
        scale: facteur de redimensionnement
    """
    __slots__ = ("_position", "_anchor", "_rotation", "_scale")

    def __init__(
            self,
            position: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            rotation: float = 0.0,
            scale: float = 1.0,
        ):
        self._position: Point = Point(position)
        self._anchor: Point = Point(anchor)
        self._rotation: float = float(rotation)
        self._scale: float = float(scale)
        assert self._scale != 0, ValueError("Scale cannot be null")

    # ======================================== CONTRACT ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Transform(x={self._position.x}, y={self._position.y}, anchor={self._anchor}, rotation={self._rotation}, scale={self._scale})"
    
    def get_attributes(self) -> tuple:
        """Renvoie les attributs du composant"""
        return (self._position, self._anchor, self._rotation, self._scale)
    
    def copy(self) -> Transform:
        """Renvoie une copie du composant"""
        return Transform(self._position.copy(), self._anchor.copy(), self._rotation, self._scale)

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position

        La position peut être un objet ``Point`` ou un tuple ``(x, y)``.
        """
        return self._position
    
    @position.setter
    def position(self, value: Point) -> None:
        self._position.x, self._position.y = value

    @property
    def x(self) -> float:
        """Position horizontale
        
        La coordonnée doit être un ``Réel``.
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real) -> None:
        self._position.x = value
    
    @property
    def y(self) -> float:
        """Position verticale

        La coordonnée doit être un ``Réel``.
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real) -> None:
        self._position.y = value
    
    @property
    def anchor(self) -> Point:
        """Ancre locale normalisée
        
        L'ancre peut être un objet ``Point`` ou un tuple ``(ax, ay)``.
        Les coordonnées de l'ancre doivent être dans l'intervalle [0, 1].
        """
        return self._anchor
    
    @anchor.setter
    def anchor(self, value: Point) -> None:
        self._anchor.x, self._anchor.y = value
    
    @property
    def anchor_x(self) -> float:
        """Ancre locale horizontale normalisée
        
        La coordonnée doit être un ``Réel`` compris dans l'intervalle [0, 1].
        """
        return self._anchor.x
    
    @anchor_x.setter
    def anchor_x(self, value: Real) -> None:
        self._anchor.x = value
    
    @property
    def anchor_y(self) -> float:
        """Ancre locale verticale normalisée
        
        La coordonnée doit être un ``Réel`` compris dans l'intervalle [0, 1].
        """
        return self._anchor.y
    
    @anchor_y.setter
    def anchor_y(self, value: Real) -> None:
        self._anchor.y = value
    
    @property
    def rotation(self) -> float:
        """Angle de rotation
        
        La rotation doit être un ``Réel``.
        L'angle est en *degrés*.
        La rotation se fait dans le sens trigonométrique *(CCW)*.
        """
        return self._rotation
    
    @rotation.setter
    def rotation(self, value: Real) -> None:
        self._rotation = float(value)
    
    @property
    def scale(self) -> float:
        """Facteur de redimensionnement
        
        Le facteur doit être un ``Réel`` positif non nul.
        """
        return self._scale
    
    @scale.setter
    def scale(self, value: Real) -> None:
        self._scale = float(value)
        assert self._scale != 0, ValueError("Scale cannot be null")

    # ======================================== COLLECTIONS ========================================
    def copy(self) -> Transform:
        """Renvoie une copie du composant"""
        return Transform(self._position.copy(), self._anchor, self._rotation, self._scale)
    
    def translate(self, vector: Vector) -> None:
        """Applique une translation

        Args:
            vector: vecteur de translation
        """
        self._position.x += vector[0]
        self._position.y += vector[1]

    def rotate(self, angle: Real) -> None:
        """Applique une rotation dans le sens trigonométrique *(CCW)*
        
        Args:
            angle: angle de rotation *en degrés*
        """
        self._rotation += float(angle)

    def resize(self, factor: Real) -> None:
        """Applique un redimensionnement
        
        Args:
            factor: facteur de redimensionnement
        """
        assert factor != 0, "Scale factor cannot be null"
        self._scale *= float(factor)