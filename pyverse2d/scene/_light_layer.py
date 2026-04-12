# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._rendering import Pipeline, Camera
from ..asset import Color
from ..abc import Layer

from numbers import Real

# ======================================== LAYER ========================================
class GuiLayer(Layer):
    """Layer gérant la lumière

    Args:
        tint: couleur d'accentuation *(RGB)*
        ambient: luminosité ambiante [0, 1]
        camera: caméra locale
    """
    __slots__ = (
        "_tint", "_ambient",
    )

    def __init__(self, tint: Color, ambient: Real, camera: Camera = None):
        super().__init__(camera)
        self._tint: Color = Color(tint)
        self._ambient: float = float(ambient)

        assert 0 <= self._ambient <= 1.0, ValueError("Ambient must be within 0.0 and 1.0")

    # ======================================== PROPERTIES ========================================
    @property
    def tint(self) -> Color:
        """Couleur d'accentuation

        La couleur peut être un objet ``Color`` ou un tuple ``(r, g, b)``.
        Le canal alpha n'est pas pris en considération dans la teinte.
        """
        return self._tint
    
    @tint.setter
    def tint(self, value: Color) -> None:
        self._tint = Color(value)

    # ======================================== HOOKS ========================================
    def on_start(self): ...

    def on_stop(self): ...

    # ======================================== LIFE CYCLE ========================================
    def _preload(self, pipeline: Pipeline): ...

    def _update(self, dt: float) -> None: ...

    def _draw(self, pipeline: Pipeline) -> None: ...
