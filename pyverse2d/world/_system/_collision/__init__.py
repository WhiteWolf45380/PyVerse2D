# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...._flag import UpdatePhase
from ....abc import System

from ..._world import World

from .._physics import PhysicsSystem

from ._spatial_hash import SpatialHash
from ._resolve import CachedContact
from ._update import UpdateContext, update_pipeline
from . import _circle, _ellipse, _capsule  # noqa: F401

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système de détection et résolution des collisions"""
    phase = UpdatePhase.UPDATE
    exclusive = True
    requires = (PhysicsSystem,)

    def __init__(self, broadphase: bool = True, iterations: int = 6):
        self._hash: SpatialHash | None = SpatialHash() if broadphase else None
        self._iterations: int = max(1, int(iterations))
        self._cache: dict[tuple[int, int], CachedContact] = {}

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Détecte et résout les collisions pour toutes les entités actives

        Args:
            world(World): monde courant
            dt(float): delta temps
        """
        ctx = UpdateContext.build(world, dt, self._hash, self._cache, self._iterations)
        update_pipeline.run(ctx)

    # ======================================== PUBLIC ========================================
    def reset_calibration(self):
        """Réinitialise la calibration du spatial hash"""
        if self._hash is not None:
            self._hash._cell_size = None
            self._hash.clear_static()

    def clear_cache(self):
        """Vide le cache d'impulsions"""
        self._cache.clear()