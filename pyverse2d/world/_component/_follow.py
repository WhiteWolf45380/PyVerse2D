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

    Ce composant est manipulé par ``SteeringSystem``.

    Args:
        entity: ``Entité`` à suivre
        offset: ``Vecteur`` de décalage par rapport à l'offset
        smoothing: facteur de retard relatif [0, 1]
        force: force d'attraction (en N)
        radius: rayon de tolérance
    """
    __slots__ = ("_entity", "_offset", "_smoothing", "_force", "_radius")
    requires = ("Transform",)

    def __init__(
            self,
            entity: Entity,
            offset: Vector = (0.0, 0.0),
            force: Real = 5000.0,
            smoothing: Real = 0.0,
            radius: Real = 0.0,
        ):
        from .._entity import Entity
        self._entity: Entity = expect(entity, Entity)
        self._offset: Vector = Vector(offset)
        self._smoothing: float = clamped(float(expect(smoothing, Real)), include_max=False)
        self._force: float | None = over(float(expect(force, Real)), 0.0, include=False)
        self._radius: float = abs(float(expect(radius, Real)))
        if not self._entity.has("Transform"):
            raise ValueError(f"Entity {self._entity.id}... has no Transform component")

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Collider(entity={self._entity.id[:8]}..., offset={self._offset})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.get_attributes())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.get_attributes())
    
    def get_attributes(self) -> list:
        """Renvoie les attributs du composant"""
        return (self._entity, self._offset, self._smoothing, self._max_speed)
    
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
        self._radius = abs(float(expect(value, Real)))