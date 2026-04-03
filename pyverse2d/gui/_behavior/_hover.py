# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Behavior
from ...math import Point

from pyverse2d import inputs, ui

from typing import Callable

# ======================================== BEHAVIOR ========================================
class HoverBehavior(Behavior):
    """Behavior gérant le survol"""
    __slots__ = (
        "_hovered",
        "_on_enter", "_on_leave",
        "_when_hovered", "_when_unhovered"
    )
    _ID: str = "hover"

    def __init__(self):
        # Initialisation du comportement
        super().__init__()

        # Etat
        self._hovered: bool = False

        # Hooks
        self._on_enter: _CallbackList = _CallbackList()
        self._on_leave: _CallbackList = _CallbackList()
        self._when_hovered: _CallbackList = _CallbackList()
        self._when_unhovered: _CallbackList = _CallbackList()
        
    # ======================================== PROPERTIES ========================================
    @property
    def on_enter(self) -> _CallbackList:
        """Fonctions appelées à l'entrée"""
        return self._on_enter
    
    @property
    def on_leave(self) -> _CallbackList:
        """Fonctions appelées à la sortie"""
        return self._on_leave

    @property
    def when_hovered(self) -> _CallbackList:
        """Fonctions appelées durant le survol"""
        return self._when_hovered
    
    @property
    def when_unhovered(self) -> _CallbackList:
        """Fonctions appelées durant le non-survol"""
        return self._when_unhovered

    # ======================================== PREDICATES ========================================
    def is_hovered(self) -> bool:
        """Indique si le widget est survolé"""
        return self._hovered

    # ======================================== HOOKS ========================================
    def _on_attach(self) -> None:
        """Hook d'attachement"""
        pass

    def _on_detach(self) -> None:
        """Hook de détachement"""
        if self._hovered:
            ui.unhover()

    def _on_enable(self) -> None:
        """Hook d'activation"""
        pass

    def _on_disable(self) -> None:
        """Hook de désactivation"""
        if self._hovered:
            self._on_leave.trigger()
            self._hovered = False
            ui.unhover()

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        # Détection du survol
        if ui.hovered is None and self._collides(inputs.relative_mouse_position):
            hovered = ui.ask_hover(self._owner)
        else:
            hovered = False

        # Hooks de changement d'état
        if hovered:
            if not self._hovered:
                self.on_enter.trigger()
            self.when_hovered.trigger()
        else:
            if self._hovered:
                self.on_leave.trigger()
            self.when_unhovered.trigger()
        self._hovered = hovered

    # ======================================== HELPERS ========================================
    def _collides(self, point: Point) -> bool:
        """Vérifie si un point est dans le widget"""
        return self._owner.collidespoint(point)
    
# ======================================== INTERNALS ========================================
class _CallbackList:
    """Stockage des hooks"""
    __slots__ = ("_callbacks",)

    def __init__(self):
        self._callbacks: list[Callable] = []

    def __call__(self, callback: Callable) -> Callable:
        """Ajoute une fonction"""
        self._callbacks.append(callback)
        return callback
    
    def remove(self, func: Callable) -> Callable:
        """Supprime une fonction"""
        self._callbacks.remove(func)

    def trigger(self) -> None:
        """Appelle les fonctions"""
        for func in self._callbacks:
            func()