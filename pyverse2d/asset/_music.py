# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import positive
from ..abc import Asset

from pyglet import media as _media

from typing import TYPE_CHECKING
from numbers import Real

if TYPE_CHECKING:
    from .._managers._audio import AudioManager

# ======================================== ASSET ========================================
class Music(Asset):
    """Musique streamée depuis le disque.

    Args:
        path:   chemin vers le fichier audio
        volume: volume propre [0, 1]
    """
    __slots__ = (
        "_path", "_volume",
        "_player", "_playing", "_paused", "_loop",
    )

    _AUDIO_MANAGER: AudioManager = None

    @classmethod
    def _get_audio_manager(cls) -> AudioManager:
        """Renvoie le gestionnaire audio"""
        if cls._AUDIO_MANAGER is None:
            from .._managers._audio import AudioManager
            cls._AUDIO_MANAGER = AudioManager
        return cls._AUDIO_MANAGER

    def __init__(self, path: str, volume: Real = 1.0):
        # Attributs publiques
        self._path: str = path
        self._volume: float = float(volume)

        if __debug__:
            positive(self._volume)

        # Attributs internes
        self._player: _media.Player | None = None
        self._playing: bool = False
        self._paused: bool = False
        self._loop: bool = True

    def __hash__(self) -> int:
        """Renvoie le hash de la musique"""
        return hash((self._path, self._volume))

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
        
        Le volume doit être un ``Réel``positif.
        """
        return self._volume

    @volume.setter
    def volume(self, value: Real) -> None:
        value = float(value)
        assert value >= 0.0, f"volume ({value}) must be positive"
        self._volume = value
        if self._player:
            self._player.volume = self._volume

    # ======================================== PREDICATES ========================================
    def __eq__(self, other: object) -> bool:
        """Vérifie la correspondance de deux musiques"""
        if isinstance(other, Music):
            return (self._path == other.path
                and self._volume == other.volume
            )
        return NotImplemented

    def is_playing(self) -> bool:
        """Vérifie que la musique soit en cours de lecture"""
        return self._playing
    
    def is_paused(self) -> bool:
        """Vérifie que la musique soit en pause"""
        return self._paused

    # ======================================== INTERFACE ========================================
    def play(self, loop: bool = True, fade_s: Real = 0.0) -> None:
        """Joue la musique

        Args:
            loop: boucle infinie si True
            fade_s: durée du fade-in en secondes
        """
        self._get_audio_manager().play_music(self, loop=loop, fade_s=fade_s)

    def stop(self, fade_s: Real = 0.0) -> None:
        """Arrête la musique.

        Args:
            fade_s: durée du fade-out (géré par le manager)
        """
        if self._get_audio_manager().current_music == self:
            self._get_audio_manager().stop_music(fade_s=fade_s)

    # ======================================== INTERNALS ========================================
    def _set_volume(self, value: float) -> None:
        """Volume brut sur le player"""
        if self._player:
            self._player.volume = value

    def _set_playing(self, value: bool) -> None:
        """Fixe l'état"""
        self._playing = value

    def _set_pause(self, value: bool) -> None:
        """Fixe la pause"""
        self._paused = value

    def _set_player(self, value: _media.player) -> None:
        """Fixe le lecteur"""
        self._player = value