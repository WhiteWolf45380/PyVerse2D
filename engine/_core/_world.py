# ======================================== IMPORTS ========================================
from .._internal import expect

from ._component import Component
from ._entity import Entity
from ._system import System

from typing import Type

# ======================================== MONDE ========================================
class World:
    """Gère le monde virtuel et l'organisation des entités"""
    def __init__(self):
        self._all_entities: dict[str, Entity] = {}      # ensemble des entités
        self._all_systems: list = []                    # ensemble des systèmes
    
    # ======================================== ENTITES ========================================
    def add_entity(self, entity: Entity):
        """
        Ajoute une entité au monde

        Args:
            entity(Entity): entité à ajouter
        """
        expect(entity, Entity)
        self._all_entities[entity.id] = Entity
    
    def remove_entity(self, entity: Entity):
        """
        Supprime une entité du monde

        Args:
            entity(Entity): entité à supprimer
        """
        self._all_entities.pop(entity.id, None)
    
    @property
    def entity_count(self) -> int:
        """Retourne le nombre d'entités dans le monde"""
        return len(self._all_entities)
    
    def has_entity(self, entity: Entity) -> bool:
        """Vérifie que le monde comporte une entité donnée"""
        return expect(entity, Entity).id in self._all_entities
    
    def query(self, *component_types: Type[Component]) -> list[Entity]:
        """
        Recherche filtrée par composants des entités

        Args:
            component_types(Type[Component]): types des composants requis
        """
        result = []
        for entity in self._all_entities.values():
            if entity.is_active() and all(entity.has(T) for T in component_types):
                result.append(entity)
        return result
    
    def query_tags(self, *tags: str) -> list[Entity]:
        """
        Recherche filtrée par labels des entités

        Args:
            tags(str): labels requis
        """
        result = []
        for entity in self._all_entities.values():
            if entity.is_active() and all(entity.has_tag(t) for t in tags):
                result.append(entity)
        return result

    # ======================================== SYSTEMES ========================================
    def add_system(self, system: System):
        """
        Ajoute un système au monde

        Args:
            system(System): système à ajouter
        """
        self._all_systems.append(expect(system, System))
    
    def remove_system(self, system: System):
        """
        Supprime un système du monde

        Args:
            system(System): système à supprimer
        """
        self._all_systems.remove(expect(system, System))