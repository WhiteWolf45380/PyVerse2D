# ======================================== IMPORTS ========================================
from ..math import Point

from dataclasses import dataclass

# ======================================== RENDER CONTEXT ========================================
@dataclass(slots=True)
class RenderContext:
    """Contexte de rendu"""
    origin: Point       # ancre globale
    opacity: float      # opacité cumulée
    z: int              # Zorder global