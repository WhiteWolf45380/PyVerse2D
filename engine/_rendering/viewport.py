# ======================================== IMPORTS ========================================
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..systems import RenderSystem

# ======================================== OBJET ========================================
class Viewport:
    """Objet gérant la zone d'affichage du rendu"""
    def __init__(self):
        self._owner = None

    # ======================================== PREDICATS ========================================
    def is_owner(self, render_system: RenderSystem):
        """Vérifie que le système de rendu soit maître du viewport"""
        return render_system == self._owner
    
    # ======================================== INTERNAL ========================================
    def _bind(self, owner: RenderSystem):
        """Assigne un sytème de rendu maître"""
        self._owner = owner