# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect
from ...abc import Component, Shape
from ...math import Point, Vector

from typing import Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .._entity import Entity

# ======================================== COMPONENT ========================================
class Collider(Component):
    """Composant gérant la hitbox

    Ce composant est manipulé par ``CollisionSystem``.

    Args:
        shape(Shape): forme de la hitbox
        offset(Point, optional): décalage par rapport au Transform
        category(int, optional): catégorie binaire de collision
        mask(int, optional): masque binaire de collision
        trigger(bool, optional): collision fantôme
        active(bool, optional): collision active
    """
    __slots__ = ("_shape", "_offset", "_category", "_mask", "_trigger", "_active", "_contacts", "_coyote_elapsed")
    requires = ("Transform",)
    _COYOTE_TIME = 0.1  # temps avant perte du contact

    def __init__(
            self,
            shape: Shape,
            offset: Point = (0.0, 0.0),
            category: int = 0b00000001,
            mask: int = 0b11111111,
            trigger: bool = False,
            active: bool = True,
        ):
        self._shape: Shape = expect(shape, Shape)
        self._offset: Point = Point(offset)
        self._category: int = expect(category, int)
        self._mask: int = expect(mask, int)
        self._trigger: bool = expect(trigger, bool)
        self._active: bool = expect(active, bool)
        self._contacts: dict[Entity, Vector] = {}
        self._coyote_elapsed: float = 0.0
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Collider(category={self._category}, mask={self._mask}, trigger={self._trigger}, active={self._active})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.get_attributes())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.get_attributes())
    
    def get_attributes(self) -> tuple:
        """Renvoie les attributs du composant"""
        return (self._shape, self._offset, self._category, self._mask, self._trigger)
    
    # ======================================== GETTERS ========================================
    @property
    def shape(self) -> Shape:
        """Renvoie la forme de la hitbox"""
        return self._shape
    
    @property
    def offset(self) -> Point:
        """Renvoie le décalage par rapport au Transform"""
        return self._offset
    
    @property
    def category(self) -> int:
        """Renvoie la catégorie binaire de collision"""
        return self._category
    
    @property
    def mask(self) -> int:
        """Renvoie le masque binaire de collision"""
        return self._mask
    
    def get_contacts(self) -> dict[Entity, Vector]:
        """Renvoie le dictionnaire des contactes et de la normale de collision"""
        return self._contacts
    
    # ======================================== PREDICATES ========================================
    def is_trigger(self) -> bool:
        """Vérifie si la collision est fantôme"""
        return self._trigger

    def is_active(self) -> bool:
        """Vérifie que la hitbox soit active"""
        return self._active
    
    def collides_with(self, other: Entity) -> bool:
        """Vérification la possibilité de collision avec un autre collider"""
        other_collider = other.collider
        if other_collider is None:
            return False
        return bool(self._mask & other_collider._category)
    
    def collides(self, other: Entity) -> bool:
        """Vérifie la collision avec un autre collider"""
        return other in self._contacts

    # ======================================== PUBLIC METHODS ========================================
    def activate(self):
        """Active la collision"""
        self._active = True

    def deactivate(self):
        """Désactive la collision"""
        self._active = False

    def collision_normal(self, other: Entity) -> Vector | None:
        """Renvoie la normale de collision avec un autre ``Collider``"""
        if other is self._contacts:
            return self._contacts[other]
        return None