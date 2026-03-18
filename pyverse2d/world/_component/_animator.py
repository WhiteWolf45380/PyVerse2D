# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Component
from ...asset import Animation

# ======================================== COMPONENT ========================================
class Animator(Component):
    """
    Composant gérant l'animation d'une entité

    Args:
        idle(Animation, None): animation par défaut
    """
    __slots__ = ()

    def __init__(self, idle: Animation = None):
        self._current = idle
        self._frame = 0
        self._elapsed = 0.0
        self._requests: list[AnimationRequest] = []