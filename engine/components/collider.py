# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from ..core import Component, Shape

from numbers import Real
from typing import Iterator

# ======================================== COMPONENT ========================================
class Collider(Component):
    """Composant gérant la hitbox"""
    __slots__ = ("_shape", "_offset", "_category", "_mask", "_trigger", "_active")
    requires = ("Transform",)

    def __init__(
            self,
            shape: Shape,
            offset: tuple[Real, Real] = (0.0, 0.0),
            category: int = 0b00000001,
            mask: int = 0b11111111,
            trigger: bool = False,
            active: bool = True,
        ):
        """
        Args:
            shape(Shape): forme de la hitbox
            offset(tuple[Real, Real], optional): décalage par rapport au Transform
            category(int, optional): catégorie binaire de collision
            mask(int, optional): masque binaire de collision
            trigger(bool, optional): collision fantôme
            active(bool, optional): collision active
        """
        self._shape = expect(shape, Shape)
        self._offset = expect(offset, tuple[Real, Real])
        self._category = expect(category, int)
        self._mask = expect(mask, int)
        self._trigger = expect(trigger, bool)
        self._active = expect(active, bool)
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Collider(shape={self._shape}, offset={self._offset}, category={self._category}, mask={self._mask}, trigger={self._trigger}, active={self._active})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[Shape, tuple[Real, Real], int, int, bool]:
        """Renvoie le composant sous forme de tuple"""
        return (self._shape, self._offset, self._category, self._mask, self._trigger)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._shape, self._offset, self._category, self._mask, self._trigger]
    
    # ======================================== GETTERS ========================================
    @property
    def shape(self) -> Shape:
        """Renvoie la forme de la hitbox"""
        return self._shape
    
    @property
    def offset(self) -> tuple[Real, Real]:
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
    
    # ======================================== PREDICATES ========================================
    def is_trigger(self) -> bool:
        """Vérifie si la collision est fantôme"""
        return self._trigger

    def is_active(self) -> bool:
        """Vérifie que la hitbox soit active"""
        return self._active
    
    def collides_with(self, other: Collider) -> bool:
        """Vérification la possibilité de collision avec un autre collider"""
        return bool(self._mask & other._category)

    # ======================================== PUBLIC METHODS ========================================
    def activate(self):
        """Active la collision"""
        self._active = True

    def deactivate(self):
        """Désactive la collision"""
        self._active = False