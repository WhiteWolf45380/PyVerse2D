# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._rendering import Pipeline, Camera
from ..asset import Color
from ..abc import Layer
from ..fx import LightRenderer

from numbers import Real

# ======================================== LAYER ========================================
class LightLayer(Layer):
    """Layer gérant la lumière

    Args:
        tint: couleur d'accentuation *(RGB)*
        ambient: luminosité ambiante [0, 1]
        camera: caméra locale
    """
    __slots__ = (
        "_tint", "_ambient",
        "_renderer",
    )

    def __init__(self, tint: Color, ambient: Real, camera: Camera = None):
        super().__init__(camera)
        self._tint: Color = Color(tint)
        self._ambient: float = float(ambient)
        self._renderer: LightRenderer = LightRenderer()

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

    @property
    def ambient(self) -> float:
        """Luminosité ambiante

        La luminosité doit être un ``Réel`` compris dans l'intervalle [0, 1].
        Mettre cette propriété à 1.0 pour une luminosité maximale.
        """
        return self._ambient
    
    @ambient.setter
    def ambient(self, value: Real) -> None:
        self._ambient = float(value)
        assert 0 <= self._ambient <= 1.0, ValueError("Ambient must be within 0 and 1")

    # ======================================== HOOKS ========================================
    def on_start(self):
        """Activation du layer"""
        pass

    def on_stop(self):
        """Désactivation du layer"""
        pass

    # ======================================== LIFE CYCLE ========================================
    def _preload(self):
        """Préchargement spécialisé"""
        pass

    def _update(self, dt: float) -> None:
        """Actualisation"""
        pass

    def _draw(self, pipeline: Pipeline) -> None:
        """Affichage"""
        pass