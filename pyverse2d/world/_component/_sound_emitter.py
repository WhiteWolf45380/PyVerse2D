# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Component
from ...math.easing import EasingFunc, is_easing, linear

from numbers import Real

# ======================================== COMPONENT ========================================
class SoundEmitter(Component):
    """Composant permettant d'émettre des sons

    Ce composant est manipulé par ``SoundSystem``.

    Args:
        range: portée du son (0.0 pour portée infinie)
        falloff: fonction d'atténuation du son
    """
    __slots__ = (
        "_range", "_falloff",
    )

    def __init__(
            self,
            range: Real = 0.0,
            falloff: EasingFunc = linear,
        ):
        # Attributs publiques
        self._range: float = abs(float(range))
        self._falloff: EasingFunc = falloff

        if __debug__:
            if not is_easing(self._falloff): raise ValueError(f"falloff ({self._falloff}) must be an EasingFunc from math module")