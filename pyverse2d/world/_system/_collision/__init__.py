# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....abc import System

from ..._world import World

from ._spatial_hash import SpatialHash
from ._resolve import CachedContact
from ._update import UpdateContext, update_processor
from ._constants import ConstantsDataset

from numbers import Real, Integral

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système de détection et résolution des collisions

    Args:
        broadphase: utilisation du spatial hash
        slop: pénétration tolérée avant correction
        max_position_correction: correction de position maximale par frame
        iterations: nombre d'itérations de la convergence
        extra_iterations_threshold: profondeur de pénétration à partir de laquelle des itérations supplémentaires sont ajoutées
        extra_iterations: nombre d'itérations supplémentaires
        restitution_theshold: seuil minimale de restitution
        restitution_max_velocity: vélocité maximale de la restitution
        vel_along_wake_treshold: vitesse de rapprochement minimale pour réveiller les entités
    """
    __slots__ = (
        "_hash",
        "_cache",
        "_slop", "_max_position_correction",
        "_iterations", "_extra_iterations_threshold", "_extra_iterations",
        "_restitution_threshold", "_restitution_max_velocity",
        "_vel_along_wake_treshold",
    )
    order = 70
    exclusive = True
    requires = ("PhysicsSystem",)

    def __init__(
            self,
            broadphase: bool = True,
            slop: Real = 0.5,
            max_position_correction: Real = 8.0,
            iterations: Integral = 6,
            extra_iterations_threshold: Real = 4.0,
            extra_iterations: Integral = 4,
            restitution_threshold: Real = 1.0,
            restitution_max_velocity: Real = 10.0,
            vel_along_wake_treshold: Real = 0.1,
        ):
        self._hash: SpatialHash | None = SpatialHash() if broadphase else None
        self._cache: dict[tuple[int, int], CachedContact] = {}
        self._slop: float = float(slop)
        self._max_position_correction: float = float(max_position_correction)
        self._iterations: int = max(1, int(iterations))
        self._extra_iterations_threshold: float = float(extra_iterations_threshold)
        self._extra_iterations: int = max(0, int(extra_iterations))
        self._restitution_threshold: float = float(restitution_threshold)
        self._restitution_max_velocity: float = float(restitution_max_velocity)
        self._vel_along_wake_treshold: float = float(vel_along_wake_treshold)

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """
        Détecte et résout les collisions pour toutes les entités actives

        Args:
            world(World): monde courant
            dt(float): delta temps
        """
        C: ConstantsDataset = ConstantsDataset(
            self._slop, self._max_position_correction,
            self._iterations, self._extra_iterations_threshold, self._extra_iterations,
            self._restitution_threshold, self._restitution_max_velocity,
            self._vel_along_wake_treshold,
        )
        ctx = UpdateContext.build(world, dt, self._hash, self._cache, C)
        update_processor(ctx)

    # ======================================== PUBLIC ========================================
    def reset_calibration(self):
        """Réinitialise la calibration du spatial hash"""
        if self._hash is not None:
            self._hash._cell_size = None
            self._hash.clear_static()

    def clear_cache(self):
        """Vide le cache d'impulsions"""
        self._cache.clear()