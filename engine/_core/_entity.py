# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from ._component import Component

import uuid
from typing import Type

# ======================================== CLASSE ABSTRAITE ========================================
class Entity:
    """Classe représentant les entités en accumulant des composants"""
    __slots__ = ("_id", "_components", "_tags", "_active")

    def __init__(self, *components: Component, tags: tuple[str, ...] = ()):
        """
        Args:
            components(Component, optional): ensemble des composants de l'entité
            tags(Iterable[str], optional): labels de l'entité
        """
        self._id: str = str(uuid.uuid4())
        self._components: dict[type, Component] = {}
        self._tags: set[str] = set(tags)
        self._active: bool = True

        for component in components:
            self.add(component)
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'entité"""
        components = ", ".join(t.__name__ for t in self._components.keys())
        return f"Entity(id={self._id[:8]}..., tags={self._tags}, components=[{components}])"
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé de l'entité"""
        return hash(self._id)
    
    # ======================================== GETTERS ========================================
    @property
    def id(self) -> str:
        """Renvoie l'identifiant de l'entité"""
        return self._id
    
    @property
    def tags(self) -> set[str]:
        """Renvoie les labels de l'entité"""
        return self._tags
    
    # ======================================== PREDICATES ========================================
    def __eq__(self, other: Entity) -> bool:
        """Vérifie la correspondance de deux entités"""
        if isinstance(other, Entity):
            return self._id == other._id
        return False
    
    def is_active(self) -> bool:
        """Vérifie l'activité de l'entité"""
        return self._active
    
    # ======================================== PUBLIC METHODS ========================================
    def activate(self):
        """Active l'entité"""
        self._active = True

    def deactivate(self):
        """Désactive l'entité"""
        self._active = False
    
    # ======================================== COMPONENTS ========================================
    def add(self, component: Component) -> Entity:
        """
        Ajoute un composant à l'entité

        Args:
            component(Component): composant à ajouter
        """
        T = type(expect(component, Component))

        # Exclusivité
        if self.has(T):
            raise ValueError(f"Can only have 1 {T} component")

        # Prérequis
        for req in component.requires:
            if not any(type(c).__name__ == req for c in self._components.values()):
                raise ValueError(f"{T.__name__} requires {req}")

        # Conflits
        for conflict in component.conflicts:
            if any(type(c).__name__ == conflict for c in self._components.values()):
                raise ValueError(f"{T.__name__} conflicts with {conflict}")
            
        self._components[T] = component
        return self
    
    def remove(self, component_type: Type[Component]) -> Entity:
        """
        Supprime un composant de l'entité

        Args:
            component_type(Type[Component]): type du composant
        """
        if component_type not in self._components:
            raise ValueError(f"Entity has no {component_type} component")
        self._components.pop(component_type)
        return self
    
    def get(self, component_type: Type[Component]) -> Component:
        """
        Renvoie un composant de l'entité

        Args:
            component_type(Type[Component]): type du composant
        """
        if component_type not in self._components:
            raise ValueError(f"Entity has no {component_type} component")
        return self._components[component_type]
    
    def has(self, component_type: Type[Component]) -> bool:
        """
        Vérifie la possession d'un composant

        Args:
            component_type(Type[C]): type du composant
        """
        return component_type in self._components
    
    # ======================================== TAGS ========================================
    def add_tag(self, tag: str) -> Entity:
        """
        Ajoute un label à l'entité

        Args:
            tag(str): label à ajouter
        """
        self._tags.add(expect(tag, str))
        return self
    
    def remove_tag(self, tag: str) -> Entity:
        """
        Supprime un label de l'entité

        Args:
            tag(str): label à supprimer
        """
        self._tags.discard(expect(tag, str))
        return self
    
    def has_tag(self, tag: str) -> bool:
        """
        Vérifie que l'entité possède un label

        Args:
            tag(str): label à vérifier
        """
        return expect(tag, str) in self._tags