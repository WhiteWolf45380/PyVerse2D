# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, clamped, over
from ...abc import Component
from ...math import Vector

from typing import TYPE_CHECKING, Iterator
from numbers import Real

if TYPE_CHECKING:
    from .._entity import Entity

# ======================================== COMPONENT ========================================
class Follow(Component):
    """``Component`` gérant le suivi

    Ce composant est manipulé par le ``PhysicsSystem``.

    Args:
        entity: ``Entité`` à suivre
        offset: ``Vecteur`` de décalage par rapport à l'offset
        smoothing: facteur de retard relatif [0, 1]
        max_speed: vitesse maximale en m/s
        radius: rayon de tolérance
    """
    __slots__ = ("_entity", "_offset", "_smoothing", "_max_speed")
    requires = ("Transform",)

    def __init__(
            self,
            entity: Entity,
            offset: Vector = (0.0, 0.0),
            smoothing: Real = 0.0,
            max_speed: Real = None,
            radius: Real = 0.0,
        ):
        from .._entity import Entity
        self._entity: Entity = expect(entity, Entity)
        self._offset: Vector = Vector(offset)
        self._smoothing: float = clamped(float(expect(smoothing, Real)), include_max=False)
        self._max_speed: float | None = over(float(expect(max_speed, Real)), 0.0, include=False) if max_speed is not None else None
        self._radius: float = abs(float(expect(radius, Real)))
        if not self._entity.has("Transform"):
            raise ValueError(f"Entity {self._entity.id}... has no Transform component")

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Collider(entity={self._entity.id[:8]}..., offset={self._offset}, smoothing={self._smoothing}, max_speed={self._max_speed})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Entity, Vector, float, float | None]:
        """Renvoie le composant sous forme de tuple"""
        return (self._entity, self._offset, self._smoothing, self._max_speed)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._entity, self._offset, self._smoothing, self._max_speed]
    
    # ======================================== PROPERTIES ========================================
    @property
    def entity(self) -> Entity:
        """Entité à suivre

        L'entité doit être une objet ``Entity`` avec un composant ``Transform``.
        """
        return self._entity
    
    @entity.setter
    def entity(self, value: Entity) -> None:
        from .._entity import Entity
        self._entity = expect(value, Entity)
        if not self._entity.has("Transform"):
            raise ValueError(f"Entity {self._entity.id}... has no Transform component")
        
    @property
    def offset(self) -> Vector:
        """Décalage par rapport à la cible

        Le décalage peut-être un objet ``Vector`` ou un tuple ``(vx, vy)``.
        """
        return self._offset
    
    @offset.setter
    def offset(self, value: Vector) -> None:
        self._offset = Vector(value)

    @property
    def smoothing(self) -> float:
        """Facteur de retard

        Le facteur doit être un ``Réel`` compris dans l'invervalle [0, 1[
        """
        return self._smoothing
    
    @smoothing.setter
    def smoothing(self, value: Real) -> None:
        self._smoothing = clamped(float(expect(value, Real)), include_max=False)

    @property
    def max_speed(self) -> float:
        """Vitesse maximale de suivi

        La vitesse doit être un ``Réel`` positif non nul.
        L'unité est le m/s dont l'échelle est définie dans le ``PhysicsSystem``.
        Mettre à None pour ne pas limiter la vitesse.
        """
        return self._max_speed
    
    @max_speed.setter
    def max_speed(self, value: Real | None) -> None:
        self._max_speed = over(float(expect(value, Real)), 0.0, include=False) if value is not None else None

    @property
    def radius(self) -> float:
        """Rayon de suivi
        
        Défini le rayon de tolérance autour de la cible.
        """
        return self._radius
    
    @radius.setter
    def radius(self, value: Real) -> None:
        abs(float(expect(value, Real)))