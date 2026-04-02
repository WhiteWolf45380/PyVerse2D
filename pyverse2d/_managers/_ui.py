# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..abc import Manager

from ._context import ContextManager

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..abc import Widget

# ======================================== GESTIONNAIRE ========================================
class UIManager(Manager):
    """Gestionnaire de l'ui"""
    __slots__ = (
        "_ctx",
        "_hovered", "_selected", "_focused",
    )

    def __init__(self, context_manager: ContextManager):
        # Contexte de managers
        self._ctx: ContextManager = context_manager

        # Widgets dominants
        self._hovered: Widget = None        # Widget survolé
        self._selected: Widget = None       # Widget selectionné
        self._focus: Widget = None          # Widget concentré

    def update(self, dt: float) -> None:
        """Actualisation"""
        ...