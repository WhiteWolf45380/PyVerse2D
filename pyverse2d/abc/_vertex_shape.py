# ======================================== IMPORTS ========================================
from __future__ import annotations

from ._shape import Shape
from ._vertex import Vertex

from abc import abstractmethod
from typing import Iterator

import numpy as np
from numpy.typing import NDArray
import math

# ======================================== SHAPE ========================================
class VertexShape(Shape):
    """Classe abstraite des formes définies par leurs sommets"""
    __slots__ = ("_vertices", "_cache_sr", "_cache_transformation", "_cache_pos", "_cache_world")

    def __init__(self):
        # Cache de transformation (scale, rotation)
        self._cache_sr: tuple[float, float] = None
        self._cache_transformation: NDArray[np.float32] = None

        # Cache monde (x, y)
        self._cache_pos: tuple[float, float] = None
        self._cache_world: NDArray[np.float32] = None

        # Génération des sommets
        self._vertices: NDArray[np.float32] = self._compute_vertices()
        self._order_vertices()
        self._recenter()

    # ======================================== CONVERSIONS ========================================
    @abstractmethod
    def __repr__(self) -> str: ...

    def __iter__(self) -> Iterator[Vertex]:
        """Renvoie les sommets dans un itérateur de tuples"""
        return iter(map(tuple, self._vertices))

    def __hash__(self) -> int:
        """Renvoie le hash de la forme"""
        return hash(self._vertices.tobytes())

    # ======================================== GETTERS ========================================
    @property
    def vertices(self) -> NDArray[np.float32]:
        """Renvoie une copie des sommets en repère local"""
        return self._vertices.copy()

    def __getitem__(self, key: int | slice) -> NDArray[np.float32]:
        """Renvoie le sommet ou le slice correspondant"""
        return self._vertices[key]

    def __len__(self) -> int:
        """Renvoie le nombre de sommets"""
        return self._vertices.shape[0]

    @property
    def edges(self) -> NDArray[np.float32]:
        """Renvoie les vecteurs des arêtes"""
        return np.roll(self._vertices, -1, axis=0) - self._vertices

    @property
    def signed_area(self) -> float:
        """Renvoie l'aire signée, positive si CCW"""
        x, y = self._vertices[:, 0], self._vertices[:, 1]
        return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))

    @property
    def area(self) -> float:
        """Renvoie l'aire de la forme"""
        return abs(self.signed_area)

    @property
    def perimeter(self) -> float:
        """Renvoie le périmètre de la forme"""
        return float(np.sum(np.linalg.norm(self.edges, axis=1)))

    @property
    def bounding_box(self) -> tuple[float, float, float, float]:
        """Renvoie (x_min, y_min, x_max, y_max)"""
        mins = self._vertices.min(axis=0)
        maxs = self._vertices.max(axis=0)
        return (float(mins[0]), float(mins[1]), float(maxs[0]), float(maxs[1]))

    @property
    def ccw(self) -> NDArray[np.float32]:
        """Renvoie les sommets en sens anti-horaire"""
        return self._vertices.copy()

    @property
    def cw(self) -> NDArray[np.float32]:
        """Renvoie les sommets en sens horaire"""
        return self._vertices[::-1].copy()

    # ======================================== COMPARATORS ========================================
    @abstractmethod
    def __eq__(self, other: VertexShape) -> bool: ...

    # ======================================== PREDICATES ========================================
    def is_convex(self) -> bool:
        """Vérifie que le polygone est convexe"""
        edges = self.edges
        cross = np.cross(edges, np.roll(edges, -1, axis=0))
        return bool(np.all(cross >= 0) or np.all(cross <= 0))

    def is_ccw(self) -> bool:
        """Vérifie que les sommets sont en sens anti-horaire"""
        return self.signed_area > 0

    def is_cw(self) -> bool:
        """Vérifie que les sommets sont en sens horaire"""
        return self.signed_area < 0

    # ======================================== TRANSFORMATIONS ========================================
    @abstractmethod
    def copy(self) -> VertexShape: ...

    @abstractmethod
    def scale(self, factor: float) -> None: ...

    def world_vertices(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> NDArray[np.float32]:
        """
        Renvoie les sommets en coordonnées monde

        Args:
            x(float, optional): coordonnée horizontale
            y(float, optional): coordonnée verticale
            scale(float, optional): facteur d'échelle
            rotation(float, optional): angle en degrés
        """
        same_sr = self._cache_sr == (scale, rotation)
        same_pos = self._cache_pos == (x, y)

        if same_sr and same_pos:
            return self._cache_world

        if not same_sr:
            rad = math.radians(rotation)
            cos_r = math.cos(rad)
            sin_r = math.sin(rad)
            R = np.array([[cos_r, -sin_r], [sin_r, cos_r]], dtype=np.float32)
            self._cache_transformation = self._vertices * scale @ R
            self._cache_sr = (scale, rotation)

        self._cache_world = self._cache_transformation + np.array([x, y], dtype=np.float32)
        self._cache_pos = (x, y)
        return self._cache_world
    
    def world_bounding_box(self, x: float = 0.0, y: float = 0.0, scale: float = 1.0, rotation: float = 0.0) -> tuple[float, float, float, float]:
        """Renvoie (x_min, y_min, x_max, y_max) en coordonnées monde"""
        pts = self.world_vertices(x, y, scale, rotation)
        xs = pts[:, 0]
        ys = pts[:, 1]
        return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())

    # ======================================== INTERNALS ========================================
    @abstractmethod
    def _compute_vertices(self) -> NDArray[np.float32]: ...

    def _recenter(self) -> None:
        """Déplace les sommets pour que le centroïde géométrique soit à l'origine"""
        x, y = self._vertices[:, 0], self._vertices[:, 1]
        cross = x * np.roll(y, -1) - np.roll(x, -1) * y
        A = 0.5 * np.sum(cross)
        cx = float(np.sum((x + np.roll(x, -1)) * cross) / (6 * A))
        cy = float(np.sum((y + np.roll(y, -1)) * cross) / (6 * A))
        self._vertices -= np.array([cx, cy], dtype=np.float32)

    def _order_vertices(self) -> None:
        """Trie les sommets en CCW autour du barycentre brut"""
        center = self._vertices.mean(axis=0)
        angles = np.arctan2(self._vertices[:, 1] - center[1], self._vertices[:, 0] - center[0])
        self._vertices = self._vertices[np.argsort(angles)]