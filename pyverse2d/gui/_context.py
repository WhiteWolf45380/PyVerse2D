# ======================================== IMPORTS ========================================
from ..math import Point
from ..abc._gui._widget import WidgetGroup
from .._rendering import Pipeline

from dataclasses import dataclass

# ======================================== RENDER CONTEXT ========================================
@dataclass(slots=True)
class RenderContext:
    """Contexte de rendu des widgets"""
    pipeline: Pipeline      # pipeline de rendu
    z: int                  # z-order global
    origin: Point           # ancre globale
    opacity: float          # opacité cumulée
    group: WidgetGroup      # groupe courant