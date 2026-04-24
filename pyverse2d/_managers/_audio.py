# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from ..abc import Manager, Request
from ..asset import Sound, Music
from ..math.easing import EasingFunc, linear

from ._context import ContextManager

import pyglet.media as _media

import os
import random
from dataclasses import dataclass
from numbers import Real
from typing import ClassVar, Type

# ======================================== CONSTANTS ========================================
_CROSSFADE_STEPS = 20

# ======================================== GROUPS ========================================
class SoundGroup:
    """Pool de players pour un groupe de sons

    Args:
        pool_max: nombre de lectures simultanées maximum
        volume: volume du groupe [0, 1]
    """
    __slots__ = (
        "_volume", "_pool_max",
        "_players",
    )

    def __init__(self, volume: Real = 1.0, pool_max: int = None):
        # Attributs publiques
        self._volume: float = float(volume)
        self._pool_max: int | None = pool_max

        if __debug__:
            positive(self._volume)
            expect(self._pool_max, (int, None))
        
        # Attributs internes
        self._players: set[_media.Player] = set()

    @property
    def volume(self) -> float:
        """Volume du groupe

        Le volume doit être un ``Réel`` positif.
        """
        return self._volume
    
    @volume.setter
    def volume(self, value: Real) -> None:
        value = float(value)
        assert value >= 0.0, f"volume ({value}) must be positive"
        self._volume = value

    @property
    def pool_max(self) -> int | None:
        """Nombre de lectures simultanées maximum

        Cette propriété limite le nombre de sons du groupe joués en même temps.
        Mettre cette propriété à ``None`` pour ne pas imposer de limite.
        """
        return self._pool_max
    
    @pool_max.setter
    def pool_max(self, value: int | None) -> None:
        assert value is None or isinstance(value, int), f"pool_max ({value}) must be an integer or None"
        self._pool_max = value

    def _get_free_player(self) -> _media.Player | None:
        """Renvoie un cannal libre si possible"""
        self._players = {p for p in self._players if p.playing}
        if self._pool_max is not None and len(self._players) >= self.pool_max:
            return None
        player = _media.Player()
        self._players.add(player)
        return player

    def stop_all(self) -> None:
        """Arrête tous les sons du groupe"""
        for p in self._players:
            p.pause()
        self._players.clear()

# ======================================== REQUESTS ========================================
@dataclass(slots=True)
class _CrossfadeRequest(Request):
    music_out: Music | None
    music_in: Music | None
    steps: int
    step_dt: float
    step: int
    elapsed: float
    vol_out: float
    vol_in: float
    easing: EasingFunc
    master: float
    music_vol: float

# ======================================== MANAGER ========================================
class AudioManager(Manager):
    """Gestionnaire audio"""
    __slots__ = (
        "_master_volume", "_music_volume",
        "_active_sounds", "_current_music", "_crossfade",
    )

    _ID: str = "audio"

    SoundGroup: ClassVar[Type[SoundGroup]] = SoundGroup

    def __init__(self, context_manager: ContextManager):
        # Initialisation du gestionnaire
        super().__init__(context_manager)

        # Attributs publiques
        self._master_volume: float = 1.0
        self._music_volume: float = 1.0

        # Attributs privés
        self._active_sounds: set[Sound] = set()
        self._current_music: Music | None = None
        self._crossfade: _CrossfadeRequest | None = None

    # ======================================== PROPERTIES ========================================
    @property
    def master_volume(self) -> float:
        """Volume général
        
        Le volume doit être un ``Réel`` positif.
        """
        return self._master_volume

    @master_volume.setter
    def master_volume(self, value: float) -> None:
        value = float(value)
        assert value >= 0.0, f"master_volume ({value}) must be positive"
        self._master_volume = value
        self._refresh_volumes()

    @property
    def music_volume(self) -> float:
        """Volume musical
        
        Le volume doit être un ``Réel`` positif non nul.
        """
        return self._music_volume

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        value = float(value)
        assert value >= 0.0, f"music_volume ({value}) must be positive"
        self._music_volume = value
        self._refresh_volumes()

    # ======================================== FACTORY ========================================
    @staticmethod
    def create_sound(
        path: str,
        volume: Real = 1.0,
        cooldown: Real = 0.0,
        group: SoundGroup = None,
    ) -> Sound:
        """Crée et retourne un ``Sound`` asset

        Args:
            path: chemin vers le fichier audio
            volume: volume propre [0, 1]
            cooldown: délai minimal entre deux lectures (secondes)
            group: groupe SFX
        """
        return Sound(path, volume=volume, cooldown=cooldown, group=group)

    @staticmethod
    def create_music(
        path: str,
        volume: Real = 1.0,
    ) -> Music:
        """Crée et retourne un ``Music``asset

        Args:
            path: chemin vers le fichier audio
            volume: volume propre [0, 1]
        """
        return Music(path, volume=volume)

    @staticmethod
    def load_sounds(
        folder_path: str,
        prefix: str = "",
        extensions: list[str] = None,
        remove_prefix: bool = False,
        volume: Real = 1.0,
        cooldown: Real = 0.0,
        group: SoundGroup = None,
    ) -> dict[str, Sound]:
        """Charge un ensemble de sons

        Args:
            folder_path: chemin du dossier
            prefix: préfixe des fichiers à charger
            extensions: extensions acceptées (toutes si None)
            remove_prefix: retirer le préfixe au chargement            
            volume: volume appliqué à tous les sons
            cooldown: cooldown appliqué à tous les sons
            group: groupe SFX à assigner
        """
        if extensions is None:
            extensions = [".wav", ".ogg", ".mp3", ".flac"]

        result: dict[str, Sound] = {}
        for filename in sorted(os.listdir(folder_path)):
            name, ext = os.path.splitext(filename)
            if ext.lower() not in extensions:
                continue
            key = name
            if prefix != "":
                if not key.startswith(prefix):
                    continue
                if remove_prefix:
                    key = key[len(prefix):]
            path = os.path.join(folder_path, filename)
            result[key] = Sound(path, volume=volume, cooldown=cooldown, group=group)

        return result
    
    @staticmethod
    def load_musics(
        folder_path: str,
        prefix: str = "",
        extensions: list[str] = None,
        remove_prefix: bool = False,
        volume: Real = 1.0,
    ) -> dict[str, Music]:
        """Charge un ensemble de musiques

        Args:
            folder_path: chemin du dossier
            prefix: préfixe des fichiers à charger
            extensions: extensions acceptées (toutes si None)
            remove_prefix: retirer le préfixe au chargement            
            volume: volume appliqué à toutes les musiques
        """
        if extensions is None:
            extensions = [".wav", ".ogg", ".mp3", ".flac"]

        result: dict[str, Music] = {}
        for filename in sorted(os.listdir(folder_path)):
            name, ext = os.path.splitext(filename)
            if ext.lower() not in extensions:
                continue
            key = name
            if prefix != "":
                if not key.startswith(prefix):
                    continue
                if remove_prefix:
                    key = key[len(prefix):]
            path = os.path.join(folder_path, filename)
            result[key] = Music(path, volume=volume)

        return result

    # ======================================== SOUNDS ========================================
    def play_sound(self, sound: Sound) -> None:
        """Joue un ``Sound`` asset

        Args:
            sound: son à jouer
        """
        if not sound.is_ready():
            return

        group = sound._group
        if group is not None:
            player = group._get_free_player()
            if player is None:
                return
        else:
            player = _media.Player()

        source = random.choice(sound._sources)
        player.queue(source)
        player.play()

        group_vol = group.volume if group is not None else 1.0
        player.volume = self._master_volume * group_vol * sound.volume

        def _on_eos() -> None:
            sound._remove_player(player)
            if not sound._players:
                sound._set_playing(False)

        player.push_handlers(on_player_eos=_on_eos)

        sound._add_player(player)
        sound._set_playing(True)
        sound._set_pause(False)
        sound._apply_cooldown()
        self._active_sounds.add(sound)

    def resume_sound(self, sound: Sound) -> None:
        """Reprend un ``Sound`` asset

        Args:
            sound: son à reprendre
        """
        if not sound.is_paused():
            return
        for player in sound._players:
            player.play()
        sound._set_pause(False)
        sound._set_playing(True)

    def pause_sound(self, sound: Sound) -> None:
        """Met en ``Sound`` asset en pause

        Args:
            sound: son à mettre en pause
        """
        if not sound.is_playing() or sound.is_paused():
            return
        for player in sound._players:
            player.pause()
        sound._set_pause(True)
        sound._set_playing(False)

    def stop_sound(self, sound: Sound) -> None:
        """Arrête un ``Sound`` asset

        Args:
            sound: son à arrêter
        """
        for player in sound._players:
            player.pause()
        sound._clear_players()
        sound._set_playing(False)
        sound._set_pause(False)
        self._active_sounds.discard(sound)

    # ======================================== GROUPS ========================================
    def resume_sounds(self, group: SoundGroup = None) -> None:
        """Reprend les SFX en cours

        Args:
            group: si fourni, reprend uniquement ce groupe
        """
        for sound in list(self._active_sounds):
            if group is None or sound._group is group:
                self.resume_sound(sound)

    def pause_sounds(self, group: SoundGroup = None) -> None:
        """Met en pause les SFX en cours

        Args:
            group: si fourni, met en pause uniquement ce groupe
        """
        for sound in list(self._active_sounds):
            if group is None or sound._group is group:
                self.pause_sound(sound)

    def stop_sounds(self, group: SoundGroup = None) -> None:
        """Arrête les SFX en cours.

        Args:
            group: si fourni, arrête uniquement ce groupe
        """
        targets = {s for s in self._active_sounds if group is None or s._group is group}
        for sound in targets:
            for player in sound._players:
                player.pause()
            sound._clear_players()
            sound._set_playing(False)
            sound._set_pause(False)
        self._active_sounds -= targets
    
    @property
    def active_sounds(self) -> frozenset[Sound]:
        """Renvoie l'ensemble des sons en cours de lecture (lecture seule)"""
        return self._active_sounds

    # ======================================== MUSICS ========================================
    def play_music(self, music: Music, loop: bool = True, fade_s: float = 0.0, fade_easing: EasingFunc = linear) -> None:
        """Joue un ``Music`` asset en remplaçant l'éventuel en cours.

        Args:
            music: musique à jouer
            loop: boucle si True
            fade_s: fade-in en secondes
            fade_easing: fonction d'atténuation du fade-in
        """
        self._stop_music_immediate()

        source = _media.load(music.path, streaming=True)
        player = _media.Player()
        player.loop = loop
        player.queue(source)

        if fade_s > 0.0:
            player.play()
            player.volume = 0.0
            music._set_player(player)
            music._loop = loop
            music._set_playing(True)
            music._set_pause(False)
            self._current_music = music
            self._crossfade = _CrossfadeRequest(
                music_out=None,
                music_in=music,
                steps=_CROSSFADE_STEPS,
                step_dt=fade_s / _CROSSFADE_STEPS,
                step=0,
                elapsed=0.0,
                vol_out=0.0,
                vol_in=self._master_volume * self._music_volume * music.volume,
                easing=fade_easing,
                master=self._master_volume,
                music_vol=self._music_volume,
            )
        else:
            player.play()
            player.volume = self._master_volume * self._music_volume * music.volume
            music._set_player(player)
            music._loop = loop
            music._set_playing(True)
            music._set_pause(False)
            self._current_music = music

    def resume_music(self) -> None:
        """Reprend la musique en cours"""
        if self._current_music is None or not self._current_music.is_paused():
            return
        self._current_music._player.play()
        self._current_music._set_pause(False)
        self._current_music._set_playing(True)

    def pause_music(self) -> None:
        """Met en pause la musique en cours"""
        if self._current_music is None or not self._current_music.is_playing():
            return
        self._current_music._player.pause()
        self._current_music._set_pause(True)
        self._current_music._set_playing(False)

    def stop_music(self, fade_s: float = 0.0, fade_easing: EasingFunc = linear) -> None:
        """Arrête la musique en cours

        Args:
            fade_s: fade-out en secondes
            fade_easing: fonction d'atténuation du fade-out
        """
        if self._current_music is None:
            return
        self._cancel_crossfade()

        if fade_s <= 0.0:
            self._stop_music_immediate()
        else:
            music = self._current_music
            self._current_music = None
            self._crossfade = _CrossfadeRequest(
                music_out=music,
                music_in=None,
                steps=_CROSSFADE_STEPS,
                step_dt=fade_s / _CROSSFADE_STEPS,
                step=0,
                elapsed=0.0,
                vol_out=self._master_volume * self._music_volume * music.volume,
                vol_in=0.0,
                easing=fade_easing,
                master=self._master_volume,
                music_vol=self._music_volume,
            )

    def switch_music(self, music: Music, fade_s: float = 1.0, fade_easing: EasingFunc = linear, loop: bool = True) -> None:
        """Crossfade vers une nouvelle musique

        Args:
            music: musique cible
            fade_s: durée totale du crossfade en secondes
            fade_easing: fonction d'atténuation du cross-fade
            loop: boucle la nouvelle musique
        """
        if fade_s <= 0.0:
            self.play_music(music, loop=loop)
            return

        self._cancel_crossfade()
        music_out = self._current_music

        source = _media.load(music.path, streaming=True)
        player = _media.Player()
        player.loop = loop
        player.volume = 0.0
        player.queue(source)
        player.play()
        music._set_player(player)
        music._loop = loop
        music._set_playing(True)
        music._set_pause(False)
        self._current_music = music

        self._crossfade = _CrossfadeRequest(
            music_out=music_out,
            music_in=music,
            steps=_CROSSFADE_STEPS,
            step_dt=fade_s / _CROSSFADE_STEPS,
            step=0,
            elapsed=0.0,
            vol_out=self._master_volume * self._music_volume * music_out.volume if music_out else 0.0,
            vol_in=self._master_volume * self._music_volume * music.volume,
            easing=fade_easing,
            master=self._master_volume,
            music_vol=self._music_volume,
        )

    @property
    def current_music(self) -> Music:
        """Renvoie le musique courante"""
        return self._current_music

    # ======================================== CYCLE DE VIE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        # Mise à jour des cooldowns
        done: set[Sound] = set()
        for sound in self._active_sounds:
            if sound.is_paused():
                continue
            if sound._tick(dt) and not sound.is_playing():
                done.add(sound)
        self._active_sounds -= done

        # Fade musical
        if self._crossfade is None:
            return

        cf = self._crossfade
        cf.elapsed += dt

        while cf.elapsed >= cf.step_dt and cf.step < cf.steps:
            cf.step += 1
            cf.elapsed -= cf.step_dt
            t = max(0.0, min(cf.easing(cf.step / cf.steps), 1.0))
            if cf.music_out is not None:
                cf.music_out._set_volume(cf.vol_out * (1.0 - t))
            if cf.music_in is not None:
                cf.music_in._set_volume(cf.vol_in * t)

        if cf.step >= cf.steps:
            if cf.music_out is not None:
                cf.music_out._set_volume(0.0)
                if cf.music_out._player:
                    cf.music_out._player.pause()
                cf.music_out._set_playing(False)
                cf.music_out._set_player(None)
            if cf.music_in is not None:
                cf.music_in._set_volume(cf.vol_in)
            self._crossfade = None

    def flush(self) -> None:
        """Nettoyage"""
        pass

    def clear(self) -> None:
        """Nettoyage complet"""
        self.stop_sounds()
        self._stop_music_immediate()

    # ======================================== INTERNALS ========================================
    def _stop_music_immediate(self) -> None:
        """Arrête la musique brutalement"""
        self._cancel_crossfade()
        if self._current_music is not None:
            if self._current_music._player:
                self._current_music._player.pause()
            self._current_music._set_playing(False)
            self._current_music._set_pause(False)
            self._current_music._set_player(None)
            self._current_music = None

    def _cancel_crossfade(self) -> None:
        """Annule le cross-fade"""
        self._crossfade = None

    def _refresh_volumes(self) -> None:
        """Actualise les volumes"""
        if self._crossfade is not None:
            cf = self._crossfade
            cf.master = self._master_volume
            cf.music_vol = self._music_volume
            t = cf.step / cf.steps if cf.steps else 1.0
            if cf.music_out is not None:
                cf.music_out._set_volume(cf.vol_out * (1.0 - t))
            if cf.music_in is not None:
                cf.music_in._set_volume(cf.vol_in * t)
        elif self._current_music is not None:
            self._current_music._set_volume(self._master_volume * self._music_volume * self._current_music.volume)

# ======================================== EXPORTS ========================================
__all__ = [
    "AudioManager",
    "SoundGroup",
]