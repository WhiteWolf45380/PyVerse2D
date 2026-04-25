# ======================================== TYPE CHECK ========================================
from __future__ import annotations

from typing import Callable

# ======================================== TOOL ========================================
class CallbackList:
    """Stockage des hooks
    
    Cette objet est un ``Callable`` permettant de stocker des fonctions à appeler.
    """
    __slots__ = ("_callbacks",)

    def __init__(self):
        self._callbacks: list[Callable] = []

    # ======================================== INTERFACE ========================================
    def copy(self) -> CallbackList:
        """Renvoie une copie du CallbackList"""
        new = CallbackList()
        new._inject(self._exctract())
        return new

    def __call__(self, callback: Callable) -> Callable:
        """Ajoute une fonction"""
        self._callbacks.append(callback)
        return callback
    
    def remove(self, func: Callable) -> Callable:
        """Supprime une fonction"""
        self._callbacks.remove(func)

    def trigger(self, *args, **kwargs) -> None:
        """Appelle les fonctions"""
        for func in self._callbacks:
            func(*args, **kwargs)
    
    # ======================================== INTERNALS ========================================
    def _inject(self, callbacks: list[Callable]) -> None:
        """Injecte une liste de callbacks"""
        self._callbacks += callbacks

    def _exctract(self) -> list[Callable]:
        """Extrait les callbacks"""
        return self._callbacks