# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive, not_null, over
from ..abc import Manager

from ._context import ContextManager

from collections import deque
from numbers import Real

# ======================================== GESTIONNAIRE ========================================
class TimeManager(Manager):
    """Gestionnaire du temps"""
    __slots__ = (
        "_raw_dt", "_dt"
        "_target_fps", "_fps", "_fps_buffer",
    )

    def __init__(self, context_manager: ContextManager):
        # Initialisation du gestionnaire
        super().__init__(context_manager)

        # Delta time
        self._raw_dt: float = 0.0
        self._dt: float = 0.0

        # Frame-rate
        self._fps: float = 0.0
        self._fps_buffer: deque[float] = deque(maxlen=50)
        self._target_fps: int = 60

    # ======================================== PROPERTIES ========================================
    @property
    def raw_dt(self) -> float:
        """Delta-time brute"""
        return self._raw_dt
    
    @property
    def dt(self) -> float:
        """Delta-time utilisé"""
    
    @property
    def fps(self) -> float:
        """Frame-rate"""
    
    @property
    def smooth_fps(self) -> float:
        """Frame-rate lissé"""
        return  sum(self._fps_buffer) / len(self._fps_buffer)
    
    @property
    def target_fps(self) -> float:
        """Frame-rate cible

        Le frame-rate doit être un ``int`` positif non nul supérieur ou égale à 15.
        Mettre à ``None`` pour ne pas limiter les fps.
        """
        return self._target_fps
    
    @target_fps.setter
    def target_fps(self, value: Real) -> None:
        self._target_fps = float(expect(value, Real))

    def _compute_dt(self, raw_dt: float) -> float:
        """Calcul le delta-time affiné"""
        return raw_dt
    
# ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        ...

    def flush(self) -> None:
        """Nettoyage"""
        ...