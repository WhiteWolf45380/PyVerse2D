# ======================================== IMPORTS ========================================
from __future__ import annotations

from ._shape import Shape

from abc import abstractmethod
from numbers import Real

# ======================================== SHAPE ========================================
class PrimitiveShape(Shape):
    """Classe abstraite des formes définies par des paramètres analytiques"""
    __slots__ = ("_cache_params", "_cache_world")

    def __init__(self):
        self._cache_params: tuple = None
        self._cache_world: tuple  = None

    # ======================================== CONVERSIONS ========================================
    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    # ======================================== GETTERS ========================================
    @property
    @abstractmethod
    def width(self) -> float: ...

    @property
    @abstractmethod
    def height(self) -> float: ...

    @property
    @abstractmethod
    def perimeter(self) -> float: ...

    @property
    @abstractmethod
    def area(self) -> float: ...

    @property
    def bounding_box(self) -> tuple[float, float, float, float]:
        """Renvoie le AABB de la shape (x_min, y_min, x_max, y_max)"""
        hw = self.width  * 0.5
        hh = self.height * 0.5
        return (-hw, -hh, hw, hh)

    # ======================================== COMPARATORS ========================================
    @abstractmethod
    def __eq__(self, other: object) -> bool: ...

    # ======================================== PREDICATES ========================================
    @abstractmethod
    def contains(self, point) -> bool: ...

    # ======================================== PUBLIC METHODS ========================================
    @abstractmethod
    def copy(self) -> PrimitiveShape: ...

    @abstractmethod
    def scale(self, factor: Real) -> None: ...

    def world_transform(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> tuple:
        """
        Renvoie les paramètres de la shape en coordonnées monde

        Args:
            x(float, optional): coordonnée horizontale
            y(float, optional): coordonnée verticale
            scale(float, optional): facteur d'échelle
            rotation(float, optional): angle en radians
        """
        params = (x, y, scale, rotation)
        if self._cache_params == params:
            return self._cache_world
        self._cache_world  = self._compute_world(x, y, scale, rotation)
        self._cache_params = params
        return self._cache_world
    
    @abstractmethod
    def world_bounding_box(self, x: float, y: float, scale: float, rotation: float) -> tuple[float, float, float, float]: ...

    # ======================================== INTERNALS ========================================
    @abstractmethod
    def _compute_world(self, x: float, y: float, scale: float, rotation: float) -> tuple: ...

    def _invalidate_cache(self) -> None:
        """Invalide le cache monde"""
        self._cache_params = None
        self._cache_world  = None