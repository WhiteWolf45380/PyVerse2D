# ======================================== TYPE CHECK ========================================
from __future__ import annotations

from typing import Callable

# ======================================== TOOL ========================================
class CallbackList:
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