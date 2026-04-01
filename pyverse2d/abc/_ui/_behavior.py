# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._widget import Widget

# ======================================== IMPORTS ========================================
class Behavior(ABC):
    """Class abstraite des comportements UI

    Args:
        id_: identifiant du comportement
    """
    __slots__ = ("_owner")
    _ID: str = "default"

    def __init__(self, id_: str):
        self._owner: Widget = None

    # ======================================== WIDGET ========================================
    @abstractmethod
    def _attach(self, widget: Widget) -> None: ...

    def attach(self, widget: Widget) -> None:
        """Assigne un ``Widget`` possesseur

        Args:
            widget: composant UI maître
        """
        if self._owner is not None:
            raise ValueError("This behavior is already attached")
        self._owner = expect(widget, Widget)
        self._attach(widget)
    
    @abstractmethod
    def detach(self) -> None: ...

    def detach(self) -> None:
        """Supprime l'assignation au ``Widget`` possesseur"""
        self._owner = None
        self._detach()