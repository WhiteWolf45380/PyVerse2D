# ======================================== IMPORTS ========================================
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..abc import Widget

# ======================================== GESTIONNAIRE ========================================
class UIManager:
    """Gestionnaire de l'ui"""
    __slots__ = (
        "_hovered", "_selected", "_focused"
    )

    def __init__(self):
        self._hovered: Widget = None        # Widget survolé
        self._selected: Widget = None       # Widget selectionné
        self._focus: Widget = None          # Widget concentré