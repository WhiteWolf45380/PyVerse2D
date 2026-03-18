# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import System
from ...asset import Animation, AnimationRequest

from .._component import Animator

# ======================================== SYSTEM ========================================
class AnimationSystem(System):
    """Met à jour les animations de toutes les entités"""
    __slots__ = ()

    # ======================================== UPDATE ========================================
    def update(self, dt: float) -> None:
        """Mise à jour des animations"""
        for entity in self.world.query(Animator):
            self._update_animator(entity.get(Animator), dt)

    # ======================================== INTERNAL ========================================
    def _update_animator(self, animator: Animator, dt: float) -> None:
        """Mise à jour d'un composant animateur"""
        target = self._resolve(animator)

        # Changement d'animation
        if target is not animator._current:
            req = self._request_of(animator, target)
            animator._current = target
            animator._frame = 0
            animator._elapsed = 0.0
            if req and req.on_start:
                req.on_start()
            return

        if animator._current is None:
            return

        # Avance la frame
        animator._elapsed += dt
        delay = 1.0 / animator._current.framerate
        if animator._elapsed >= delay:
            animator._elapsed -= delay
            animator._frame += 1

            # Fin d'animation
            if animator._frame >= len(animator._current.frames):
                req = self._request_of(animator, animator._current)

                if req and req.on_end:
                    req.on_end()

                if req and req.loop:
                    animator._frame = 0
                else:
                    animator._current = animator._idle
                    animator._frame = 0
                    animator._elapsed = 0.0

    def _resolve(self, animator: Animator) -> Animation | None:
        """Résout l'animation active selon les priorités et conditions"""
        best: AnimationRequest | None = None

        for req in animator._requests:
            if req.condition is None or req.condition():
                if best is None or req.priority >= best.priority:
                    best = req

        return best.animation if best else animator._idle

    def _request_of(self, animator: Animator, animation: Animation) -> AnimationRequest | None:
        """Retourne la requête associée à une animation"""
        for req in animator._requests:
            if req.animation is animation:
                return req
        return None