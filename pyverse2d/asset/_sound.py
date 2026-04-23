# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from ..abc import Asset

from pyglet import media as _media

from typing import TYPE_CHECKING, Type
from numbers import Real

if TYPE_CHECKING:
    from .._managers._audio import AudioManager, SoundGroup

# ======================================== ASSET ========================================
class Sound(Asset):
    """Son court chargé en mémoire *(SFX)*

    Args:
        path: chemin vers le fichier audio
        volume: volume propre [0, 1]
        cooldown: délai minimal entre deux lectures *(secondes)*
        group: groupe auquel appartient ce son
    """
    __slots__ = (
        "_path", "_volume", "_cooldown", "_group",
        "_sources", "_players", "_cooldown_timer", "_playing", "_paused",
        )
    
    _GROUP_CLASS: Type[SoundGroup] = None
    _AUDIO_MANAGER: AudioManager = None
    
    @classmethod
    def _get_group_class(cls) -> Type[SoundGroup]:
        """Renvoie la class ``SoundGroup``"""
        if cls._GROUP_CLASS is None:
            from .._managers._audio import SoundGroup
            cls._GROUP_CLASS = SoundGroup
        return cls._GROUP_CLASS
    
    @classmethod
    def _get_audio_manager(cls) -> AudioManager:
        """Renvoie le gestionnaire audio"""
        if cls._AUDIO_MANAGER is None:
            from .._managers._audio import AudioManager
            cls._AUDIO_MANAGER = AudioManager
        return cls._AUDIO_MANAGER

    def __init__(
        self,
        path: str,
        volume: Real = 1.0,
        cooldown: float = 0.0,
        group: SoundGroup | None = None,
    ):
        # Attributs publiques
        self._path: str = path
        self._volume: float = float(volume)
        self._cooldown: float = float(cooldown)
        self._group: SoundGroup | None = group

        if __debug__:
            positive(self._volume)
            positive(self._cooldown)
            expect(self._group, self._get_group_class())

        # Attributs internes
        self._sources: list[_media.Source] = [_media.load(path, streaming=False)]
        self._players: set[_media.Player] = set()
        self._cooldown_timer: float = 0.0
        self._playing: bool = False
        self._paused: bool = False

    def __hash__(self) -> int:
        """Renvoie le hash du son"""
        return hash((self._path, self._volume, self._cooldown, self._group))

    # ======================================== PROPERTIES ========================================
    @property
    def path(self) -> str:
        """Chemin du fichier audio"""
        return self._path
    
    @path.setter
    def path(self, value: str) -> None:
        self._path = value

    @property
    def volume(self) -> float:
        """Volume propre
        
        Le volume doit être un ``Réel`` positif.
        """
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        value = float(value)
        assert value >= 0.0, f"volume ({value}) must be positive"
        self._volume = value

    @property
    def cooldown(self) -> float:
        """Délai minimal entre deux lectures

        Le délai doit être un ``Réel`` positif.
        Mettre cette propriété à ``0.0`` pour ne pas avoir de délai.
        """
        return self._cooldown

    @cooldown.setter
    def cooldown(self, value: float) -> None:
        value = float(value)
        assert value >= 0.0, f"cooldown ({value}) must be positive"
        self._cooldown = value

    @property
    def group(self) -> SoundGroup:
        """Groupe de sons

        Le groupe doit être un ``SoundGroup``.
        Mettre cette propriété à ``None`` pour être lu dans le groupe par défaut.
        """
        return self._group

    @group.setter
    def group(self, value: SoundGroup | None) -> None:
        assert isinstance(value, self._get_group_class()), f"group ({value}) must be a SoundGroup"
        self._group = value

    # ======================================== PREDICATES ========================================
    def __eq__(self, other: object) -> bool:
        """Vérifie la correspondance de deux sons"""
        if isinstance(other, Sound):
            return (self._path == other.path
                and self._volume == other.volume
                and self._cooldown == other.cooldown
                and self._group == other.group
            )
        return NotImplemented

    def is_ready(self) -> bool:
        """Vérifie que le son soit prêt à être joué"""
        return self._cooldown_timer == 0.0
    
    def is_playing(self) -> bool:
        """Vérifie que le son soit entrain d'être joué"""
        return self._playing
    
    def is_paused(self) -> bool:
        """Vérifie que le son soit en pause"""
        return self._paused

    # ======================================== VARIATIONS ========================================
    def add_variation(self, path: str) -> None:
        """Ajoute une variation audio à ce son.

        Args:
            path: chemin vers le fichier de variation
        """
        self._sources.append(_media.load(path, streaming=False))

    # ======================================== INTERFACE ========================================
    def play(self) -> None:
        """Joue le son si disponible"""
        self._get_audio_manager().play_sound(self)

    def resume(self) -> None:
        """Reprend le son"""
        self._get_audio_manager().resume_sound(self)

    def pause(self) -> None:
        """Met le son en pause"""
        self._get_audio_manager().pause_sound(self)

    def stop(self) -> None:
        """Arrête le son"""
        self._get_audio_manager().stop_sound(self)

    # ======================================== INTERNALS ========================================
    def _apply_cooldown(self) -> None:
        """Initialise le délai"""
        self._cooldown_timer = self._cooldown
    
    def _tick(self, dt: float) -> None:
        """Actualise le délai"""
        self._cooldown_timer -= dt
        if self._cooldown_timer <= 0.0:
            self._cooldown_timer = 0.0
            return True
        return False
    
    def _set_playing(self, value: bool) -> None:
        """Fixe l'état"""
        self._playing = value

    def _set_pause(self, value: bool) -> None:
        """Fixe la pause"""
        self._paused = value

    def _add_player(self, player: _media.Player) -> None:
        """Ajoute un lecteur"""
        self._players.add(player)

    def _remove_player(self, player: _media.Player) -> None:
        """Retire un lecteur"""
        self._players.remove(player)
    
    def _clear_players(self) -> None:
        """Retire tous les lecteurs"""
        self._players = set()