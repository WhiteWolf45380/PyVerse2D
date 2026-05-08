# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from .._rendering import Camera
from ..abc import Layer
from ..video import VideoPlayer, VideoRenderer

import pyglet.sprite as _sprite
from dataclasses import dataclass

# ======================================== WRAPPER ========================================
@dataclass(slots=True, frozen=True)
class PlayerWrapper:
    player: VideoLayer
    z: int = 0

    def __post_init__(self) -> None:
        """Transtypage et vérifications"""
        object.__setattr__(self, "z", int(self.z))
        
        if __debug__:
            expect(self.player, VideoPlayer)

# ======================================== RENDERER ========================================
class VideoLayer(Layer):
    """Layer portant des ``VideoPlayer``"""
    __slots__ = (
        "_wrappers", "_sprites",
    )

    def __init__(self, camera: Camera | None = None):
        # Initialisation du layer
        super().__init__(camera)

        # Attributs internes
        self._wrappers: set[PlayerWrapper] = set()
        self._sprites: dict[VideoPlayer, _sprite.Sprite] = {}

    # ======================================== INTERFACE ========================================
    def add(self, player: VideoPlayer, z: int = 0) -> None:
        """Ajoute un player au layer

        Args:
            player: ``VideoPlayer`` à ajouter
            z: z-order
        """
        self._wrappers.add(PlayerWrapper(
            player = player,
            z = z,
        ))

    def remove(self, player: VideoPlayer) -> None:
        """Retire un player du layer

        Args:
            player: ``VideoPlayer`` à retirer
        """
        wrapper = self._get_wrapper(player)
        if wrapper is None:
            raise ValueError(f"This layer has no player {id(player)}")
        player.stop()
        sprite = self._sprites.pop(player, None)
        if sprite is not None:
            sprite.delete()
        self._wrappers.remove(wrapper)

    def clear(self) -> None:
        """Arrête et retire tous les players"""
        for wrapper in self._wrappers:
            wrapper.player.stop()
        for sprite in self._sprites.values():
            sprite.delete()
        self._wrappers.clear()
        self._sprites.clear()

    @property
    def players(self) -> tuple[VideoPlayer, ...]:
        """Players actifs *(lecture seule)*"""
        return tuple(wrapper.player for wrapper in self._wrappers)
    
    # ======================================== HOOKS ========================================
    def on_start(self):
        """Hook d'activation"""
        pass
    
    def on_stop(self):
        """Hook de désactivation"""
        pass

    # ======================================== CYCLE DE VIE ========================================
    def _preload(self):
        """Préchargement spécialisé"""
        pass

    def _update(self, dt: float) -> None:
        """Actualisation des frames courantes

        Args:
            dt: delta-time
        """
        for wrapper in self._wrappers:
            player = wrapper.player
            player.update(dt)
            sprite = self._sprites.get(player)
            if sprite is not None:
                VideoRenderer.update(player, sprite)

    def _draw(self, pipeline) -> None:
        """Rendu de tous les players via le batch monde du pipeline

        Args:
            pipeline: pipeline de rendu courant
        """
        for wrapper in self._wrappers:
            player = wrapper.player
            if player not in self._sprites:
                sprite = VideoRenderer.attach(player, pipeline.batch, group=pipeline.get_group(z=wrapper.z))
                if sprite is not None:
                    self._sprites[player] = sprite

    # ======================================== INTERNALS ========================================
    def _get_wrapper(self, player: VideoPlayer) -> PlayerWrapper | None:
        """Renvoie le wrapper d'un player"""
        for wrapper in self._wrappers:
            if wrapper.player is player:
                return wrapper
        return None