# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect
from ...abc import Component
from ...asset import Animation, AnimationRequest

# ======================================== COMPONENT ========================================
class Animator(Component):
    """
    Composant gérant l'animation d'une entité

    Args:
        idle(Animation, None): animation par défaut
    """
    __slots__ = ("_idle", "_current", "_frame", "_elapsed",  "_requests")
    requires = ("SpriteRenderer",)

    def __init__(self, idle: Animation = None):
        self._idle: Animation = idle
        self._requests: list[AnimationRequest] = []
        self._current: Animation | None = idle
        self._frame: int = 0
        self._elapsed: float = 0.0
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'animateur"""
        return f"Animator(current={self._current}, frame={self._frame})"

    # ======================================== GETTERS ========================================
    @property
    def idle(self) -> Animation:
        """Renvoie l'animation par défaut"""
        return self._idle

    @property
    def current(self) -> Animation:
        """Renvoie l'animation actuelle"""
        return self._current
    
    @property
    def current_index(self) -> int:
        """Renvoie l'indice courant"""
        return self._frame

    @property
    def current_frame(self) -> Animation:
        """Renvoie la frame actuelle"""
        return self._current[self._frame]
    
    @property
    def requests(self) -> list[AnimationRequest]:
        """Renvoie la liste courante des requêtes"""
        return self._requests

    # ======================================== PUBLIC ========================================
    def register(self, request: AnimationRequest) -> None:
        """
        Enregistre une requête d'animation

        Args:
            request(AnimationRequest): requête d'animation à enregistrer
        """
        self._requests.append(expect(request, AnimationRequest))

    def unregister(self, request: AnimationRequest) -> None:
        """
        Retire une requête d'animation

        Args:
            request(AnimationRequest): requête d'animation à retirer
        """
        self._requests.remove(request)
    
    def unregister_tag(self, tag: str) -> None:
        """
        Retire les requêtes d'animation avec un certain label

        Args:
            tag(str): label des requêtes à supprimer
        """
        self._requests = [request for request in self._requests if request.tag != tag]