# ======================================== IMPORTS ========================================
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...scene import GuiLayer
    from ._widget import Widget

# ======================================== IMPORTS ========================================
class Behavior(ABC):
    """Class abstraite des comportements UI"""
    __slots__ = ("_owner", "_enabled")
    _ID: str = "default"

    def __init__(self):
        self._owner: Widget = None
        self._enabled: bool = True

    # ======================================== PROPERTIES ========================================
    @property
    def layer(self) -> GuiLayer | None:
        """Layer du composant possesseur"""
        return self._owner.layer if self._owner is not None else None

    @property
    def owner(self) -> Widget:
        """Composant possesseur"""
        return self._owner
    
    # ======================================== PREDICATES ========================================
    def is_enabled(self) -> bool:
        """Vérifie l'activité"""
        return self._enabled

    # ======================================== STATE ========================================
    def attach(self, widget: Widget, _from_widget: bool = False) -> None:
        """Assigne un ``Widget`` possesseur

        Args:
            widget: composant UI maître
            _from_widget: origine de l'appel
        """
        if not _from_widget:
            return widget.add_behavior(self)
        if self._owner is not None:
            raise ValueError("This behavior is already attached")
        self._owner = widget
        self._on_attach()

    def detach(self, _from_widget: bool = False) -> None:
        """Supprime l'assignation au ``Widget`` possesseur

        Args:
        _from_widget: origine de l'appel
        """
        if not _from_widget:
            return self._owner.remove_behavior(self)
        self._on_detach()
        self._owner = None

    def enable(self) -> None:
        """Active le ``Behavior``"""
        if self._enabled:
            return
        self._enabled = True
        self._on_enable()

    def disable(self) -> None:
        """Désactive le ``Behavior``"""
        if not self._enabled:
            return
        self._enabled = False
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