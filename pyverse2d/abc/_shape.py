# ======================================== IMPORTS ========================================
from abc import ABC, abstractmethod
from typing import Iterator, Self, Any

# ======================================== CLASSE ABSTRAITE ========================================
class Shape(ABC):
    """Classe abstraite des formes"""
    def __init__(self):
        ...
    
    # ======================================== CONVERSIONS ========================================
    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __iter__(self) -> Iterator: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    # ======================================== GETTERS ========================================
    @property
    @abstractmethod
    def perimeter(self) -> float: ...

    @property
    @abstractmethod
    def area(self) -> float: ...

    @property
    @abstractmethod
    def bounding_box(self) -> tuple[float, float, float, float]: ...

    # ======================================== COMPARATORS ========================================
    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...

    # ======================================== PUBLIC METHODS ========================================
    @abstractmethod
    def copy(self) -> Self: ...

    @abstractmethod
    def scale(self, factor: float): ...