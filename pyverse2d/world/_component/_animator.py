# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect
from ...abc import Component
from ...asset import Animation, Image
from ...request import AnimationRequest

# ======================================== COMPONENT ========================================
class Animator(Component):
    """
    Composant gérant l'animation d'une entité

    Args:
        idle(Animation, None): animation par défaut
    """
    __slots__ = ("_idle", "_current_request", "_current_animation", "_frame", "_elapsed",  "_requests")
    requires = ("SpriteRenderer",)

    def __init__(self, idle: Animation = None):
        self._idle: Animation = expect(idle, (Animation, None))
        self._requests: list[AnimationRequest] = []
        self._current_request: AnimationRequest | None = None
        self._current_animation: Animation | None = self._idle
        self._frame: int = 0
        self._elapsed: float = 0.0
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de l'animateur"""
        return f"Animator(current={self._current_animation}, frame={self._frame})"

    # ======================================== GETTERS ========================================
    @property
    def idle(self) -> Animation:
        """Renvoie l'animation par défaut"""
        return self._idle
    
    @property
    def current_request(self) -> AnimationRequest | None:
        """Renvoie la requête en cours de traitement"""
        return self._current_request

    @property
    def current_animation(self) -> Animation | None:
        """Renvoie l'animation actuelle"""
        return self._current_animation
    
    @property
    def current_index(self) -> int:
        """Renvoie l'indice courant"""
        return self._frame

    @property
    def current_frame(self) -> Image | None:
        """Renvoie la frame actuelle"""
        return self._current_animation[self._frame] if self._current_animation else None
    
    @property
    def requests(self) -> list[AnimationRequest]:
        """Renvoie la liste courante des requêtes"""
        return self._requests
    
    # ======================================== SETTERS ========================================
    @idle.setter
    def idle(self, value: Animation | None) -> None:
        """Fixe l'animation par défaut"""
        self._idle = expect(value, (Animation, None))

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