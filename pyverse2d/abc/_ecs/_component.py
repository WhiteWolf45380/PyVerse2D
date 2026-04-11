# ======================================== IMPORTS ========================================
from abc import ABC, abstractmethod
from typing import Iterator

# ======================================== ABSTRACT CLASS ========================================
class Component(ABC):
    """Classe abstraite des composants"""
    __slots__ = ()
    requires: tuple[type, ...] = ()
    conflicts: tuple[type, ...] = ()

    # ======================================== CONTRACT ========================================
    @abstractmethod
    def __init__(self): ...

    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __iter__(self) -> Iterator: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    @abstractmethod
    def get_attributes(self) -> tuple: ...

    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: object) -> bool:
        """Vérifie la correspondance de deux composants"""
        if isinstance(other, Component):
            return self.get_attributes() == other.get_attributes()
        return NotImplemented