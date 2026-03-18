# ======================================== IMPORTS ========================================
from ..abc import Asset

from ._animation import Animation

from dataclasses import dataclass
from typing import Callable

# ======================================== ASSET ========================================
@dataclass(frozen=True)
class AnimationRequest(Asset):
    """
    Requête d'animation

    Args:
        animation(Animation): animation à activer
        loop(bool, optional): répétition de l'animation
        priority(int, optional): niveau de priorité de l'animation
        tag(str, optional): label de l'animation
        condition(callable, optional): condition d'activation de l'animation
        on_start(callable, optional): fonction de début d'animation
        on_end(callable, optional): fonction de fin d'animation
    """
    animation: Animation
    loop: bool = False
    priority: int = 0
    tag: str | None = None
    condition: Callable[[], bool] | None = None
    on_start: Callable[[], None] | None = None
    on_end: Callable[[], None] | None = None