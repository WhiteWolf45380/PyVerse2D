# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import CallbackList, positive
from ...abc import Component
from ...asset import Sound
from ...math.easing import EasingFunc, is_easing, linear

from numbers import Real

# ======================================== COMPONENT ========================================
class SoundEmitter(Component):
    """Composant permettant d'émettre des sons

    Ce composant est manipulé par ``SoundSystem``.

    Args:
        inner_radius: portée du son à plein volume
        outer_radius: portée absolue du son
        falloff: fonction d'atténuation du son
    """
    __slots__ = (
        "_inner_radius", "_outer_radius",
        "_falloff",
    )

    def __init__(
            self,
            volume: Real = 1.0,
            inner_radius: Real = 0.0,
            outer_radius: Real = 0.0,
            falloff: EasingFunc = linear,
        ):
        # Attributs publiques
        self._volume: float = float(volume)
        self._inner_radius: float = abs(float(inner_radius))
        self._outer_radius: float = abs(float(outer_radius))
        self._falloff: EasingFunc = falloff

        if __debug__:
            positive(self._volume)
            if not is_easing(self._falloff): raise ValueError(f"falloff ({self._falloff}) must be an EasingFunc from math module")

        # Hooks
        self._on_start: CallbackList = CallbackList()
        self._on_end: CallbackList = CallbackList()

        # Buffer
        self._to_play: list[Sound] = []
        self._playing: set[Sound] = set()

    # ======================================== CONTRACT ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"SoundEmitter(volume={self._volume}, inner_radius={self._inner_radius}, outer_radius={self._outer_radius})"
    
    def get_attributes(self) -> tuple:
        """Renvoie les attributs du composant"""
        return (self._volume, self._inner_radius, self._outer_radius, self._falloff)
    
    def copy(self) -> SoundEmitter:
        """Renvoie une copie du composant"""
        new = SoundEmitter(
            volume = self._volume,
            inner_radius = self._inner_radius,
            outer_radius = self._outer_radius,
            falloff = self._falloff,
        )
        new._on_start._inject(self._on_start._exctract())
        new._on_end._inject(self._on_end._exctract())
        return new

    # ======================================== PROPERTIES ========================================
    @property
    def volume(self) -> float:
        """Volume propre du comosant

        Le volume doit être un ``Réel`` positif.
        """
        return self._volume
    
    @volume.setter
    def volume(self, value: Real) -> None:
        value = float(value)
        assert value >= 0.0, f"volume ({value}) must be positive"
        self._volume = value

    @property
    def inner_radius(self) -> float:
        """Portée du son à plein volume

        Cette propriété fixe un rayon dans lequel le son est au volume normal.
        """
        return self._inner_radius
    
    @inner_radius.setter
    def inner_radius(self, value: Real) -> None:
        self._inner_radius = abs(float(value))

    @property
    def outer_radius(self) -> float:
        """Portée maximale du son

        Cette propriété fixe un rayon au-delà duquel le son n'est pas audible.
        Mettre cette propriété à ``0.0`` pour une portée infinie.
        """
        return self._outer_radius
    
    @outer_radius.setter
    def outer_radius(self, value: Real) -> None:
        self._outer_radius = abs(float(value))

    @property
    def falloff(self) -> EasingFunc:
        """Fonction d'atténuation

        L'atténuation se fait uniquement en inner_radius et outer_radius.
        Ne fonctionne pas avec un rayon infinie.
        """
        return self._falloff
    
    @falloff.setter
    def falloff(self, value: EasingFunc | None) -> None:
        assert value is None or is_easing(value), f"falloff ({value}) must be an EasingFunc from math module"
        self._falloff = value or linear

    # ======================================== HOOKS ========================================
    @property
    def on_start(self) -> CallbackList:
        """Début de lecture d'un son"""
        return self._on_start
    
    @property
    def on_end(self) -> CallbackList:
        """Fin de lecture d'un son"""
        return self._on_end

    # ======================================== INTERFACE ========================================
    def play(self, sound: Sound) -> None:
        """Joue un ``Sound`` asset

        Args:
            sound: son à jouer
        """
        self._on_start.trigger()

    def resume(self) -> None:
        """Reprend la lecture des sons"""
        ...

    def pause(self) -> None:
        """Met en pause la lecture des sons"""
        ...

    def stop(self) -> None:
        """Arrête la lecture des sons"""
        self._on_end.trigger()