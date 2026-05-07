# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive, profile_section
from ..abc import Manager, Request
from ._context import ContextManager

import pyglet.media as _media
from dataclasses import dataclass
from numbers import Real
from typing import ClassVar, Callable, Any

# ======================================== HANDLES ========================================
class VideoHandle:
    """Handle de vidéo en cours de lecture"""
    __slots__ = ("source", "player", "_active")

    def __init__(self, source: _media.Source, player: _media.Player):
        self.source = source
        self.player = player
        self._active = True

    @property
    def time(self) -> float:
        return self.player.time if self._active else 0.0

    @property
    def duration(self) -> float | None:
        return self.source.duration if self._active else None

    @property
    def time_remaining(self) -> float | None:
        if self._active and self.source.duration is not None:
            return max(0.0, self.source.duration - self.player.time)
        return None

    def pause(self) -> None:
        if self._active:
            self.player.pause()

    def resume(self) -> None:
        if self._active:
            self.player.play()

    def stop(self) -> None:
        if self._active:
            self._active = False
            self.player.pause()
            self.player.delete()

    def is_active(self) -> bool:
        return self._active

# ======================================== MANAGER ========================================
class VideoManager(Manager):
    """Gestionnaire vidéo"""
    __slots__ = (
        "_master_volume",
        "_current_handle",
        "_on_end",
    )

    _ID: ClassVar[str] = "video"

    def __init__(self, context_manager: ContextManager):
        super().__init__(context_manager)
        self._master_volume: float = 1.0
        self._current_handle: VideoHandle | None = None
        self._on_end: Callable | None = None

    # ======================================== PROPERTIES ========================================
    @property
    def master_volume(self) -> float:
        return self._master_volume

    @master_volume.setter
    def master_volume(self, value: Real) -> None:
        value = float(value)
        if __debug__:
            positive(value)
        self._master_volume = value
        if self._current_handle and self._current_handle.is_active():
            self._current_handle.player.volume = value

    # ======================================== INTERFACE ========================================
    def play_video(
        self,
        path: str,
        volume: Real = 1.0,
        loop: bool = False,
        on_end: Callable[[VideoHandle], Any] | None = None,
    ) -> VideoHandle:
        """Joue une vidéo

        Args:
            path: chemin vers le fichier vidéo
            volume: volume audio de la vidéo
            loop: boucle si True
            on_end: callback de fin de lecture

        Returns:
            handle: ``VideoHandle`` de la vidéo jouée
        """
        volume = float(volume)
        loop = bool(loop)

        self._stop_immediate()

        source = _media.load(path, streaming=True)
        player = _media.Player()
        player.loop = loop
        player.volume = self._master_volume * volume
        player.queue(source)

        handle = VideoHandle(source, player)
        self._current_handle = handle
        self._on_end = on_end

        # Callback EOS
        @player.event
        def on_player_eos():
            if on_end is not None:
                on_end(handle)
            handle.stop()
            if self._current_handle is handle:
                self._current_handle = None

        player.play()
        return handle

    def pause(self) -> None:
        """Met la vidéo en cours en pause"""
        if self._current_handle:
            self._current_handle.pause()

    def resume(self) -> None:
        """Reprend la vidéo en cours"""
        if self._current_handle:
            self._current_handle.resume()

    def stop(self) -> None:
        """Arrête la vidéo en cours"""
        self._stop_immediate()

    @property
    def current_handle(self) -> VideoHandle | None:
        return self._current_handle

    @property
    def texture(self):
        """Texture pyglet de la frame courante (à blit dans ton renderer)"""
        if self._current_handle and self._current_handle.is_active():
            return self._current_handle.player.texture
        return None
    
    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation — pyglet.media gère le décodage en interne"""
        pass

    def flush(self) -> None:
        pass

    # ======================================== INTERNALS ========================================
    def _stop_immediate(self) -> None:
        if self._current_handle is not None:
            self._current_handle.stop()
            self._current_handle = None

# ======================================== EXPORTS ========================================
__all__ = ["VideoHandle", "VideoManager"]