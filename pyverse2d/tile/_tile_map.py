# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive

from ._tile import Tile

from numbers import Real
import numpy as np
from numpy.typing import NDArray

# ======================================== TILE MAP ========================================
class TileMap:
    """
    Grille 2D d'identifiants de tuiles

    Args:
        tile(Tile): tileset associé à cette couche
        grid(NDArray): tableau 2D d'entiers (rows, cols) ; 0 = tuile vide
        tile_width(Real): largeur d'une tuile en pixels monde
        tile_height(Real): hauteur d'une tuile en pixels monde
    """
    __slots__ = ("_tile", "_grid", "_tile_width", "_tile_height")

    def __init__(
        self,
        tile: Tile,
        grid: NDArray[np.int32],
        tile_width: Real,
        tile_height: Real,
    ):
        self._tile: Tile              = expect(tile, Tile)
        self._grid: NDArray[np.int32] = np.asarray(grid, dtype=np.int32)
        self._tile_width: float       = float(positive(expect(tile_width,  Real)))
        self._tile_height: float      = float(positive(expect(tile_height, Real)))

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        rows, cols = self._grid.shape
        return f"TileMap(tile={self._tile}, grid={cols}x{rows}, tile={self._tile_width}x{self._tile_height})"

    # ======================================== GETTERS ========================================
    @property
    def tile(self) -> Tile:
        """Renvoie le tileset associé"""
        return self._tile

    @property
    def grid(self) -> NDArray[np.int32]:
        """Renvoie une copie de la grille brute"""
        return self._grid.copy()

    @property
    def tile_width(self) -> float:
        """Renvoie la largeur d'une tuile en pixels monde"""
        return self._tile_width

    @property
    def tile_height(self) -> float:
        """Renvoie la hauteur d'une tuile en pixels monde"""
        return self._tile_height

    @property
    def cols(self) -> int:
        """Renvoie le nombre de colonnes"""
        return self._grid.shape[1]

    @property
    def rows(self) -> int:
        """Renvoie le nombre de lignes"""
        return self._grid.shape[0]

    @property
    def pixel_width(self) -> float:
        """Renvoie la largeur totale de la map en pixels monde"""
        return self.cols * self._tile_width

    @property
    def pixel_height(self) -> float:
        """Renvoie la hauteur totale de la map en pixels monde"""
        return self.rows * self._tile_height

    def tile_at(self, col: int, row: int) -> int:
        """
        Renvoie l'ID de la tuile à (col, row), ou 0 si hors limites

        Args:
            col(int): colonne
            row(int): ligne
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return int(self._grid[row, col])
        return 0

    # ======================================== CONVERSIONS COORDS ========================================
    def world_to_tile(self, x: float, y: float) -> tuple[int, int]:
        """
        Convertit une position monde en (col, row)

        Args:
            x(float): coordonnée horizontale monde
            y(float): coordonnée verticale monde
        """
        return int(x // self._tile_width), int(y // self._tile_height)

    def tile_to_world(self, col: int, row: int) -> tuple[float, float]:
        """
        Convertit (col, row) en position monde (coin supérieur gauche de la tuile)

        Args:
            col(int): colonne
            row(int): ligne
        """
        return col * self._tile_width, row * self._tile_height

    def tiles_in_region(self, x: float, y: float, width: float, height: float) -> tuple[int, int, int, int]:
        """
        Renvoie la plage de tuiles (col_min, row_min, col_max, row_max) couvrant la région monde

        Args:
            x(float): coin gauche de la région
            y(float): coin haut de la région
            width(float): largeur de la région
            height(float): hauteur de la région
        """
        col_min = max(0, int(x // self._tile_width))
        row_min = max(0, int(y // self._tile_height))
        col_max = min(self.cols, int((x + width) // self._tile_width) + 1)
        row_max = min(self.rows, int((y + height) // self._tile_height) + 1)
        return col_min, row_min, col_max, row_max