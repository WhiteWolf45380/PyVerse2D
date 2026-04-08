# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from .._flag import CameraMode
from .._rendering._pipeline import Pipeline
from ..abc import Layer
from ..tile import TileMap, TileRenderer

from numbers import Real
from contextlib import nullcontext

# ======================================== LAYER ========================================
class TileLayer(Layer):
    """
    Layer affichant un TileMap via texture array GL et VAO par chunk

    Args:
        tile_map(TileMap): couche de tuiles à afficher
        chunk_size(int, optional): nombre de tuiles par côté d'un chunk
        parallax(tuple[float, float], optional): facteur de parallax (x, y)
        clip(bool, optional): limitation parallax
        z(int, optional): z_order dans le batch pipeline
        camera_mode(CameraMode, optional): comportement de la caméra
    """
    __slots__ = (
        "_tile_map", "_chunk_size",
        "_parallax", "_clip",
        "_renderer",
    )

    def __init__(
        self,
        tile_map: TileMap,
        chunk_size: int = 16,
        clip: bool = False,
    ):
        super().__init__()

        # TileMap
        self._tile_map: TileMap = expect(tile_map, TileMap)
        self._chunk_size: int = max(1, expect(chunk_size, int))
        self._clip: bool = expect(clip, bool)

        # Rendu
        self._renderer: TileRenderer = TileRenderer(self._tile_map, self._chunk_size)

    # ======================================== GETTERS ========================================
    @property
    def tile_map(self) -> TileMap:
        """TileMap assigné"""
        return self._tile_map
    
    @tile_map.setter
    def tile_map(self, value: TileMap) -> None:
        self._tile_map = expect(value, TileMap)
        self._renderer.delete()
        self._renderer = TileRenderer(self._tile_map, self._chunk_size)
    
    @property
    def chunk_size(self) -> int:
        """Taille des chunks en tuiles"""
        return self._chunk_size
    
    @chunk_size.setter
    def chunk_size(self, value: int) -> None:
        self._chunk_size = max(1, expect(value, int))
        self._renderer.delete()
        self._renderer = TileRenderer(self._tile_map, self._chunk_size)
    
    @property
    def clip(self) -> bool:
        """Limitation du rendu à la zone initiale
        
        Cette propriété sert à notamment à éviter l'overflow du parallax.
        """
        return self._clip
    
    @clip.setter
    def clip(self, value: bool) -> None:
        self._clip = expect(value, bool)

    # ======================================== HOOKS========================================
    def on_start(self) -> None:
        """Activation du layer"""
        ...

    def on_stop(self) -> None:
        """Désactivation du layer — libère les ressources GL"""
        self._renderer.delete()

    # ======================================== LIFE CYCLE ========================================
    def preload(self) -> None:
        """Force le build immédiat du renderer — à appeler avant la boucle principale"""
        if not self._renderer.built:
            self._renderer.build()

    def update(self, dt: float) -> None:
        """Actualisation du layer — tuiles statiques, rien à faire"""
        ...

    def draw(self, pipeline: Pipeline) -> None:
        """
        Affichage du layer — ne rend que les chunks visibles

        Args:
            pipeline(Pipeline): pipeline active
        """
        if not self._renderer.built:
            self._renderer.build()
        if not self._renderer.has_chunks:
            return

        cam = pipeline.camera
        screen = pipeline.screen
        px = cam.x * self._parallax[0]
        py = cam.y * self._parallax[1]

        vx = px - screen.half_width
        vy = py - screen.half_height
        vw = screen.width
        vh = screen.height

        tm = self._tile_map
        tw = tm.tile_width
        th = tm.tile_height
        ox, oy = tm.origin
        chunk_w = self._chunk_size * tw
        chunk_h = self._chunk_size * th

        chunk_cols = (tm.cols + self._chunk_size - 1) // self._chunk_size
        chunk_rows = (tm.rows + self._chunk_size - 1) // self._chunk_size

        cc_min = max(0, int((vx - ox) // chunk_w))
        cc_max = min(chunk_cols, int((vx + vw - ox) // chunk_w) + 1)
        cr_min = max(0, int((vy - oy) // chunk_h))
        cr_max = min(chunk_rows, int((vy + vh - oy) // chunk_h) + 1)

        # Génération du contexte de rendu
        if self._clip:
            ctx = pipeline.scissor(ox + 1, oy + 1, tm.cols * tw - 2, tm.rows * th - 2)
        else:
            ctx = nullcontext()
        
        # Affichage des tiles
        with ctx:
            self._renderer.begin()
            for cr in range(cr_min, cr_max):
                for cc in range(cc_min, cc_max):
                    self._renderer.draw(cc, cr)
            self._renderer.end()