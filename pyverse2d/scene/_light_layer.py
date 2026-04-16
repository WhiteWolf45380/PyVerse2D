# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._rendering import Pipeline, Camera
from .._flag import Activity
from ..asset import Color
from ..abc import Layer, LightSource
from ..fx import LightRenderer, PointLight, ConeLight, AreaLight

from numbers import Real

# ======================================== LAYER ========================================
class LightLayer(Layer):
    """Layer gérant la lumière

    Args:
        ambient: luminosité ambiante [0, 1]
        light_scale: facteur d'intensité des lumières *[0, inf[*
        tint: couleur d'accentuation *(RGB)*
        tint_strength: intensité de la teinte
        camera: caméra locale
    """
    __slots__ = (
        "_ambient", "_light_scale", "_tint", "_tint_strength",
        "_sources", "_active_points", "_active_cones", "_active_areas",
        "_renderer",
    )

    _IS_FX = True

    def __init__(
            self,
            ambient: Real = 1.0,
            light_scale: Real = 1.0,
            tint: Color = (255, 255, 255),
            tint_strength: Real = 0.0,
            camera: Camera = None
        ):
        # Initialisation du layer
        super().__init__(camera)

        # Paramètres publiques
        self._ambient: float = float(ambient)
        self._light_scale: float = float(light_scale)
        self._tint: Color = Color(tint)
        self._tint_strength: float = float(tint_strength)

        if __debug__:
            if not 0.0 <= self._ambient <= 1.0: raise ValueError(f"ambient must be within 0.0 and 1.0, got {self._ambient}")
            if self._light_scale < 0.0: raise ValueError(f"light_scale must be positive, got {self._light_scale}")
            if not 0.0 <= self._tint_strength <= 1.0: raise ValueError(f"tint_strength must be within 0.0 and 1.0, got {self._tint_strength}")

        # Paramètres internes
        self._renderer: LightRenderer = LightRenderer()
        self._sources: set[LightSource] = set()
        self._active_points: list[PointLight] = []
        self._active_cones: list[ConeLight] = []
        self._active_areas: list[AreaLight] = []

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
    def light_scale(self) -> float:
        """Facteur d'intensité des lumières

        Le facteur doit être un ``Réel`` positif.
        Mettre cette propriété à 1.0 pour un éclairage par défaut.
        """
        return self._light_scale
    
    @light_scale.setter
    def light_scale(self, value: Real) -> None:
        value = float(value)
        assert value >= 0.0, f"light_scale must be positive, got {value}"

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
        if source.is_enabled():
            self._get_active_list(source).append(source)

    def remove_source(self, source: LightSource) -> None:
        """Retire une source de lumière

        Args:
            source: source à retirer
        """
        if source.is_enabled():
            self._get_active_list(source).remove(source)
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
        for source in self._sources:
            state: Activity = source.update(dt)
            if state is Activity.DEFAULT:
                continue
            if state is Activity.ENABLED:
                self._get_active_list(source).append(source)
            elif state is Activity.DISABLED:
                self._get_active_list(source).remove(source)

    def _draw(self, pipeline: Pipeline) -> None:
        """Affichage"""
        self._renderer.render_ambient(pipeline, self._ambient, self._light_scale, self._active_points, self._active_cones)
        self._renderer.render_tint(pipeline, self._tint.rgb, self._tint_strength)

    # ======================================== LIFE CYCLE ========================================
    def _get_active_list(self, source: LightSource) -> list:
        """Renvoie la liste active correspondant au type de source"""
        match source:
            case PointLight(): return self._active_points
            case ConeLight():  return self._active_cones
            case AreaLight():  return self._active_areas