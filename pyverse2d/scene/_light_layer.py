# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._rendering import Pipeline, Camera
from ..asset import Color
from ..abc import Layer, LightSource
from ..fx import LightRenderer

from numbers import Real

# ======================================== LAYER ========================================
class LightLayer(Layer):
    """Layer gérant la lumière

    Args:
        ambient: luminosité ambiante [0, 1]
        tint: couleur d'accentuation *(RGB)*
        tint_strength: intensité de la teinte
        camera: caméra locale
    """
    __slots__ = (
        "_ambient", "_tint", "_tint_strength",
        "_renderer", "_sources",
    )

    _IS_FX = True

    def __init__(
            self,
            ambient: Real = 1.0,
            tint: Color = (255, 255, 255),
            tint_strength: Real = 0.0,
            camera: Camera = None
        ):
        # Initialisation du layer
        super().__init__(camera)

        # Paramètres publiques
        self._ambient: float = float(ambient)
        self._tint: Color = Color(tint)
        self._tint_strength: float = float(tint_strength)

        if __debug__:
            if not 0.0 <= self._ambient <= 1.0: raise ValueError(f"ambient must be within 0.0 and 1.0, got {self._ambient}")
            if not 0.0 <= self._tint_strength <= 1.0: raise ValueError(f"tint_strength must be within 0.0 and 1.0, got {self._tint_strength}")

        # Paramètres internes
        self._renderer: LightRenderer = LightRenderer()
        self._sources: set[LightSource] = set()

    # ======================================== PROPERTIES ========================================
    @property
    def ambient(self) -> float:
        """Luminosité ambiante

        La luminosité doit être un ``Réel`` compris dans l'intervalle *[0, 1]*.
        Mettre cette propriété à 1.0 pour une luminosité maximale.
        """
        return self._ambient
    
    @ambient.setter
    def ambient(self, value: Real) -> None:
        value = float(value)
        assert 0 <= value <= 1.0, ValueError(f"ambient must be within 0 and 1, got {value}")
        self._ambient = value

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
    def tint_strength(self) -> float:
        """Itensité de la couleur d'accentuation

        Le facteur force doit être un ``Réel`` compris dans l'intervalle *[0, 1]*.
        Mettre cette propriété à 0.0 pour ne pas appliquer la couleur d'accentuation.
        """
        return self._tint_strength
    
    @tint_strength.setter
    def tint_strength(self, value: Real) -> None:
        value = float(value)
        assert 0 <= value <= 1.0, ValueError(f"tint_strength must be within 0 and 1, got {value}")
        self._tint_strength = value

    # ======================================== SOURCES ========================================
    def add_source(self, source: LightSource) -> None:
        """Ajoute une source de lumière

        Args:
            source: source à ajouter
        """
        assert isinstance(source, LightSource), f"source must be a LightSource, got {source}"
        self._sources.add(source)

    def remove_source(self, source: LightSource) -> None:
        """Retire une source de lumière

        Args:
            source: source à retirer
        """
        self._sources.discard(source)

    def get_sources(self) -> set[LightSource]:
        """Renvoie l'ensemble des sources de lumière"""
        return self._sources

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
        self._renderer.render_ambient(pipeline, self._ambient, self._sources)
        self._renderer.render_tint(pipeline, self._tint.rgb, self._tint_strength)