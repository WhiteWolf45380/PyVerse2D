# ======================================== IMPORTS ========================================
from .._internal import expect
from .entity import Entity
from .system import System

# ======================================== MONDE ========================================
class World:
    """Gère le monde virtuel et l'organisation des entités"""
    def __init__(self):
        self.all_entities = []                  # ensemble des entités
        self.all_systems = []                   # ensemble des systèmes
    
    def add_entity(self, entity: Entity):
        """
        Ajoute une entité au monde

        Args:
            entity(Entity): entité à ajouter
        """
        self.all_entities.append(entity)