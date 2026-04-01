# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect

from ._widget import Widget

from abc import ABC, abstractmethod

# ======================================== IMPORTS ========================================
class Behavior:
    """Class abstraite des comportements UI

    Args:
        ...
    """
    __slots__ = ()

    def __init__(self):
        self._owner: Widget = None

    # ======================================== WIDGET ========================================
    @abstractmethod
    def _attach(self, widget: Widget) -> None: ...

    def attach(self, widget: Widget) -> None:
        """Assigne un ``Widget`` possesseur

        Args:
            widget: composant UI maître
        """
        self._owner = expect(widget, Widget)
        self._attach(widget)
    
    @abstractmethod
    def detach(self) -> None: ...

    def detach(self) -> None:
        """Supprime l'assignation au ``Widget`` possesseur"""
        self._owner = None
        self._detach()