# ======================================== IMPORTS ========================================
from typing import Protocol

# ======================================== PROTOCOLS ========================================
class Positionnal(Protocol):
    """Objet exposant une position ``(x, y)``"""
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...