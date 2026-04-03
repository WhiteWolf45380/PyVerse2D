# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...scene import UILayer
    from ._widget import Widget

# ======================================== IMPORTS ========================================
class Behavior(ABC):
    """Class abstraite des comportements UI

    Args:
        id_: identifiant du comportement
    """
    __slots__ = ("_owner", "_enabled")
    _ID: str = "default"

    def __init__(self):
        self._owner: Widget = None
        self._enabled: bool = True

    # ======================================== PROPERTIES ========================================
    @property
    def layer(self) -> UILayer | None:
        """Layer du composant possesseur"""
        return self._layer

    @property
    def owner(self) -> Widget:
        """Composant possesseur"""
        return self._owner
    
    # ======================================== PREDICATES ========================================
    def is_enabled(self) -> bool:
        """Vérifie l'activité"""
        return self._enabled

    # ======================================== STATE ========================================
    def attach(self, widget: Widget) -> None:
        """Assigne un ``Widget`` possesseur

        Args:
            widget: composant UI maître
        """
        if self._owner is not None:
            raise ValueError("This behavior is already attached")
        self._owner = widget
        self._on_attach()

    def detach(self) -> None:
        """Supprime l'assignation au ``Widget`` possesseur"""
        self._on_detach()
        self._owner = None

    def enable(self) -> None:
        """Active le ``Behavior``"""
        if self._enabled:
            return
        self._on_enable()

    def disable(self) -> None:
        """Désactive le ``Behavior``"""
        if not self._enabled:
            return
        self._on_disable()

    # ======================================== HOOKS ========================================
    @abstractmethod
    def _on_attach(self) -> None: ...

    @abstractmethod
    def _on_detach(self) -> None: ...

    @abstractmethod
    def _on_enable(self) -> None: ...

    @abstractmethod
    def _on_disable(self) -> None: ...

    # ======================================== LIFE CYCLE ========================================
    @abstractmethod
    def update(self, dt: float) -> None: ...