# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from .._flag import AudioState
from ..abc import Manager, Request
from ..asset import Sound, Music
from ..math.easing import EasingFunc, linear

from ._context import ContextManager

import pyglet.media as _media

import os
import random
from dataclasses import dataclass
from numbers import Real
from typing import ClassVar, Type, Callable, Any

# ======================================== CONSTANTS ========================================
_CROSSFADE_STEPS = 20

# ======================================== HANDLES ========================================
class SoundHandle:
    """Handle de son en cours de lecture"""
    __slots__ = (
        "sound", "player", "on_stop",
        "_active",
        "__weakref__",
    )

    def __init__(self, sound: Sound, player: _media.Player, on_stop: Callable[[SoundHandle], Any] = None):
        # Attributs publiques
        self.sound: Sound = sound
        self.player: _media.Player = player
        self.on_stop: Callable[[SoundHandle], Any] = on_stop

        # Attributs internes
        self._active: bool = True

        # Configuration du player
        self.player.push_handlers(on_player_eos=self.stop)
    
    def is_active(self) -> bool:
        """Vérifie que le handle soit actif"""
        return self._active

    def is_playing(self) -> bool:
        """Vérifie que le son est en cours de lecture"""
        return self._active and self.player.playing

    def resume(self) -> None:
        """Reprend le son"""
        if self._active:
            self.player.play()

    def pause(self) -> None:
        """Met le son en pause"""
        if self._active:
            self.player.pause()

    def stop(self) -> None:
        """Arrête le son"""
        if self._active:
            self.player.pause()
            self.player.delete()
            self.sound._remove_handle(self)
            if not self.sound._handles:
                self.sound._set_state(AudioState.SLEEPING)
            if self.on_stop:
                self.on_stop(self)
            self._active = False


class MusicHandle:
    """Handle de musique en cours de lecture"""
    __slots__ = (
        "music", "player", "on_stop",
        "_active",
        "__weakref__",
    )

    def __init__(self, music: Music, player: _media.Player, on_stop: Callable[[MusicHandle], Any] = None):
        # Attributs publiques
        self.music: Music = music
        self.player: _media.Player = player
        self.on_stop: Callable[[MusicHandle], Any] = on_stop

        # Attributs internes
        self._active: bool = True

        # Configuration du player
        self.player.push_handlers(on_player_eos=self.stop)

    def is_active(self) -> bool:
        """Vérifie que le handle soit actif"""
        return self._active

    def is_playing(self) -> bool:
        """Vérifie que la musique est en cours de lecture"""
        return self._active and self.player.playing

    def resume(self) -> None:
        """Reprend la musique"""
        if self._active:
            self.player.play()
            self.music._set_state(AudioState.PLAYING)

    def pause(self) -> None:
        """Met la musique en pause"""
        if self._active:
            self.player.pause()
            self.music._set_state(AudioState.PAUSED)

    def stop(self) -> None:
        """Arrête la musique"""
        if self._active:
            self.player.pause()
            self.player.delete()
            self.music._set_state(AudioState.SLEEPING)
            self.music._set_handle(None)
            if self.on_stop:
                self.on_stop(self)
            self._active = False

    def _set_volume(self, value: float) -> None:
        """Fixe le volume brut"""
        if self._active:
            self.player.volume = value

# ======================================== GROUPS ========================================
class SoundGroup:
    """Pool de players pour un groupe de sons

    Args:
        pool_max: nombre de lectures simultanées maximum
        volume: volume du groupe [0, 1]
        parent: groupe parent (hérite du volume)
    """
    __slots__ = (
        "_volume", "_pool_max", "_parent",
        "_handles",
    )

    def __init__(self, volume: Real = 1.0, pool_max: int = None, parent: SoundGroup = None):
        # Attributs publiques
        self._volume: float = float(volume)
        self._pool_max: int | None = pool_max
        self._parent: SoundGroup | None = parent

        if __debug__:
            positive(self._volume)
            expect(self._pool_max, (int, None))
            expect(self._parent, (SoundGroup, None))
        
        # Attributs internes
        self._handles: set[SoundHandle] = set()

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

    @property
    def parent(self) -> SoundGroup:
        """Groupe parent

        Le ``SoundGroup`` hérite du volume du parent.
        Le parent est fixe après initialisation du groupe.
        """
        return self._parent
    
    def get_absolute_volume(self) -> float:
        """Renvoie le volume absolu du groupe"""
        if self._parent is None:
            return self._volume
        return self._volume * self._parent.get_absolute_volume()
    
    def resume_all(self) -> None:
        """Reprend tous les sons du groupe"""
        for h in self._handles:
            h.resume()
    
    def pause_all(self) -> None:
        """Met en pause tous les sons du groupe"""
        for h in self._handles:
            h.pause()
    
    def stop_all(self) -> None:
        """Arrête tous les sons du groupe"""
        for h in self._handles:
            h.stop()
        self._handles.clear()

    def _get_free_handle(self, sound: Sound) -> SoundHandle | None:
        """Renvoie un cannal libre si possible"""
        self._handles = {h for h in self._handles if h.is_active()}
        if self._pool_max is not None and len(self._handles) >= self._pool_max:
            return None
        handle = SoundHandle(sound, _media.Player())
        self._handles.add(handle)
        return handle

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
        "_source_cache",
    )

    _ID: str = "audio"

    # Types alias
    AudioState: ClassVar[Type[AudioState]] = AudioState
    SoundGroup: ClassVar[Type[SoundGroup]] = SoundGroup
    SoundHandle: ClassVar[Type[SoundHandle]] = SoundHandle
    MusicHandle: ClassVar[Type[MusicHandle]] = MusicHandle

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
        self._source_cache: dict[str, _media.StaticSource] = {}

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
    
    # ======================================== INTERFACE ========================================
    def clear(self) -> None:
        """Nettoyage complet"""
        self.stop_sounds()
        self._stop_music_immediate()

    # ======================================== SOUNDS ========================================
    def play_sound(self, sound: Sound, volume: Real = 1.0) -> SoundHandle | None:
        """Joue un ``Sound`` asset

        Args:
            sound: son à jouer
            volume: volume ponctuel

        Returns:
            handle: handle du son joué, ou None si le son n'a pas pu être joué
        """
        # Vérification de la disponibilité du son
        if not sound.is_ready() or sound.is_paused():
            return None

        # Récupération d'un player
        group = sound._group
        if group is not None:
            handle = group._get_free_handle(sound)
            if handle is None:
                return None
        else:
            handle = SoundHandle(sound, _media.Player())
        handle.on_stop = lambda h: self._active_sounds.discard(h.sound)

        # Lecture du son
        path = random.choice(sound._paths)
        source = self._load_source(path)
        handle.player.queue(source)
        handle.player.play()

        # Actualisation du volume
        group_vol = group.get_absolute_volume() if group is not None else 1.0
        handle.player.volume = self._master_volume * group_vol * sound.volume * float(volume)

        # Actualisation de l'état du son
        sound._add_handle(handle)
        sound._set_state(self.AudioState.PLAYING)
        sound._apply_cooldown()
        self._active_sounds.add(sound)
        return handle

    def resume_sound(self, sound: Sound) -> None:
        """Reprend un ``Sound`` asset

        Args:
            sound: son à reprendre
        """
        if not sound.is_paused():
            return
        for handle in sound._get_handles():
            handle.resume()
        sound._set_state(AudioState.PLAYING)

    def pause_sound(self, sound: Sound) -> None:
        """Met en ``Sound`` asset en pause

        Args:
            sound: son à mettre en pause
        """
        if not sound.is_playing() or sound.is_paused():
            return
        for handle in sound._get_handles():
            handle.pause()
        sound._set_state(AudioState.PAUSED)

    def stop_sound(self, sound: Sound) -> None:
        """Arrête un ``Sound`` asset

        Args:
            sound: son à arrêter
        """
        if not sound.is_playing():
            return
        for handle in list(sound._get_handles()):
            handle.stop()

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
        for sound in list(self._active_sounds):
            if group is None or sound._group is group:
                self.stop_sound(sound)
    
    @property
    def active_sounds(self) -> frozenset[Sound]:
        """Renvoie l'ensemble des sons en cours de lecture (lecture seule)"""
        return self._active_sounds

    # ======================================== MUSICS ========================================
    def play_music(self, music: Music, volume: Real = 1.0, loop: bool = True, fade_s: float = 0.0, fade_easing: EasingFunc = linear) -> MusicHandle:
        """Joue un ``Music`` asset en remplaçant l'éventuel en cours.

        Args:
            music: musique à jouer
            volume: volume ponctuel
            loop: boucle si True
            fade_s: fade-in en secondes
            fade_easing: fonction d'atténuation du fade-in
        """
        # Arrêt de la musique en cours
        self._stop_music_immediate()

        # Génération du handle
        source = _media.load(music.path, streaming=True)
        player = _media.Player()
        player.loop = loop
        player.queue(source)
        handle = MusicHandle(music, player, on_stop=lambda h: self._clear_current_music(h.music))

        # Lecture de la musique
        handle.player.play()
        music._set_handle(handle)
        music._set_loop(loop)
        music._set_state(AudioState.PLAYING)
        self._current_music = music

        # Cas avec fade-in
        if fade_s > 0.0:
            handle.player.volume = 0.0
            self._crossfade = _CrossfadeRequest(
                music_out=None,
                music_in=music,
                steps=_CROSSFADE_STEPS,
                step_dt=fade_s / _CROSSFADE_STEPS,
                step=0,
                elapsed=0.0,
                vol_out=0.0,
                vol_in=self._master_volume * self._music_volume * music.volume * volume,
                easing=fade_easing,
                master=self._master_volume,
                music_vol=self._music_volume,
            )

        # Cas sans fade-in
        else:
            handle.player.volume = self._master_volume * self._music_volume * music.volume * volume
        
        return handle

    def resume_music(self) -> None:
        """Reprend la musique en cours"""
        if self._current_music is None or not self._current_music.is_paused():
            return
        self._current_music._handle.resume()
    
    def pause_music(self) -> None:
        """Met en pause la musique en cours"""
        if self._current_music is None or not self._current_music.is_playing():
            return
        self._current_music._handle.pause()

    def stop_music(self, fade_s: float = 0.0, fade_easing: EasingFunc = linear) -> None:
        """Arrête la musique en cours

        Args:
            fade_s: fade-out en secondes
            fade_easing: fonction d'atténuation du fade-out
        """
        # Annulation du cross-fade en cours
        if self._current_music is None:
            return
        self._cancel_crossfade()

        # Cas avec fade-out
        if fade_s > 0.0:            
            self._crossfade = _CrossfadeRequest(
                music_out=self._current_music,
                music_in=None,
                steps=_CROSSFADE_STEPS,
                step_dt=fade_s / _CROSSFADE_STEPS,
                step=0,
                elapsed=0.0,
                vol_out=self._master_volume * self._music_volume * self._current_music.volume,
                vol_in=0.0,
                easing=fade_easing,
                master=self._master_volume,
                music_vol=self._music_volume,
            )
            self._current_music = None
        
        # Cas sans Fade-out
        else:
            self._stop_music_immediate()

    def switch_music(self, music: Music, volume: Real = 1.0, fade_s: float = 1.0, fade_easing: EasingFunc = linear, loop: bool = True) -> MusicHandle:
        """Crossfade vers une nouvelle musique

        Args:
            music: musique cible
            fade_s: durée totale du crossfade en secondes
            fade_easing: fonction d'atténuation du cross-fade
            loop: boucle la nouvelle musique
        """
        # Cas sans cross-fade
        if fade_s <= 0.0:
            return self.play_music(music, loop=loop)

        # Annulation du cross-fade en cours et récupération de la musique sortante
        self._cancel_crossfade()
        music_out = self._current_music

        # Génération du handle
        source = _media.load(music.path, streaming=True)
        player = _media.Player()
        player.loop = loop
        player.volume = 0.0
        player.queue(source)
        handle = MusicHandle(music, player, on_stop=lambda h: self._clear_current_music(h.music))

        # Lecture de la musique
        handle.player.play()
        music._set_handle(handle)
        music._loop = loop
        music._set_state(AudioState.PLAYING)
        self._current_music = music

        # Création du cross-fade
        self._crossfade = _CrossfadeRequest(
            music_out=music_out,
            music_in=music,
            steps=_CROSSFADE_STEPS,
            step_dt=fade_s / _CROSSFADE_STEPS,
            step=0,
            elapsed=0.0,
            vol_out=self._master_volume * self._music_volume * (music_out.volume if music_out else 0.0),
            vol_in=self._master_volume * self._music_volume * music.volume * volume,
            easing=fade_easing,
            master=self._master_volume,
            music_vol=self._music_volume,
        )

        return handle

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
                if cf.music_out._handle:
                    cf.music_out._handle.stop()
            if cf.music_in is not None:
                cf.music_in._set_volume(cf.vol_in)
            self._crossfade = None

    def flush(self) -> None:
        """Nettoyage"""
        pass

    # ======================================== INTERNALS ========================================
    def _load_source(self, path: str) -> _media.StaticSource:
        """Charge une source audio en cacheant les résultats"""
        if path not in self._source_cache:
            self._source_cache[path] = _media.load(path, streaming=False)
        return self._source_cache[path]

    def _stop_music_immediate(self) -> None:
        """Arrête la musique brutalement"""
        self._cancel_crossfade()
        if self._current_music is not None:
            if self._current_music._handle is not None:
                self._current_music._handle.stop()
            self._current_music = None

    def _clear_current_music(self, music: Music) -> None:
        """Nettoie la musique courante si elle correspond à la musique donnée"""
        if self._current_music is music:
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