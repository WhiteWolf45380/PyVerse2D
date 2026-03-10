# ======================================== IMPORTS ========================================
from abc import ABC, abstractmethod
from typing import Iterator

# ======================================== CLASSE ABSTRAITE ========================================
class Component(ABC):
    """Classe abstraite des composants"""
    requires: tuple[type, ...] = ()
    conflicts: tuple[type, ...] = ()

    @abstractmethod
    def __init__(self): ...

    # ======================================== CONVERSIONS ========================================
    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __iter__(self) -> Iterator: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    @abstractmethod
    def to_tuple(self) -> tuple: ...

    @abstractmethod
    def to_list(self) -> list: ...