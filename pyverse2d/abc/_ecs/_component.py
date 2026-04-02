# ======================================== IMPORTS ========================================
from abc import ABC

# ======================================== ABSTRACT CLASS ========================================
class Component(ABC):
    """Classe abstraite des composants"""
    __slots__ = ()
    requires: tuple[type, ...] = ()
    conflicts: tuple[type, ...] = ()