# ======================================== IMPORTS ========================================
from typing import Protocol

# ======================================== PROTOCOLS ========================================
class Positionnal(Protocol):
    """Objet positionnel
    
    L'objet doit exposé deux attributs ou propriétés ``x`` et ``y``.
    """
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...