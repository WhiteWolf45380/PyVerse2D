# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from .._flag import CameraMode
from .._rendering._pipeline import Pipeline
from ..abc import Layer
from ..tile import TileMap, TileRenderer

from numbers import Real
from contextlib import nullcontext
from pyglet.math import Mat4, Vec3

# ======================================== LAYER ========================================
class TileLayer(Layer):
    """
    Layer affichant un TileMap via texture array GL et VAO par chunk

    Args:
        tile_map(TileMap): couche de tuiles à afficher
        chunk_size(int, optional): nombre de tuiles par côté d'un chunk
        parallax(tuple[float, float], optional): facteur de parallax (x, y)
        parallax_clamp(bool, optional): limitation parallax
        z(int, optional): z_order dans le batch pipeline
        camera_mode(CameraMode, optional): comportement de la caméra
    """
    __slots__ = (
        "_tile_map", "_chunk_size",
        "_parallax", "_parallax_clamp",
        "_renderer",
    )

    def __init__(
        self,
        tile_map: TileMap,
        chunk_size: int = 16,
        parallax: tuple[Real, Real] = (1.0, 1.0),
        parallax_clamp: bool = False,
        camera_mode: CameraMode = CameraMode.WORLD,
    ):
        super().__init__(camera_mode)

        # TileMap
        self._tile_map: TileMap = expect(tile_map, TileMap)
        self._chunk_size: int = max(1, expect(chunk_size, int))

        # Effet parallax
        self._parallax: tuple[float, float] = (
            float(positive(expect(parallax[0], Real))),
            float(positive(expect(parallax[1], Real))),
        )
        self._parallax_clamp: bool = expect(parallax_clamp, bool)

        # Rendu
        self._renderer: TileRenderer = TileRenderer(self._tile_map, self._chunk_size)

    # ======================================== GETTERS ========================================
    @property
    def tile_map(self) -> TileMap:
        """Renvoie le TileMap assigné"""
        return self._tile_map

    @property
    def parallax(self) -> tuple[float, float]:
        """Renvoie le facteur de parallax"""
        return self._parallax
    
    @property
    def parallax_clamp(self) -> bool:
        """Renvoie la limitation parallax"""
        return self._parallax_clamp

    @property
    def chunk_size(self) -> int:
        """Renvoie la taille des chunks en tuiles"""
        return self._chunk_size

    # ======================================== SETTERS ========================================
    @tile_map.setter
    def tile_map(self, value: TileMap) -> None:
        """Fixe le TileMap assigné — reconstruit le renderer"""
        self._tile_map = expect(value, TileMap)
        self._renderer.delete()
        self._renderer = TileRenderer(self._tile_map, self._chunk_size)

    @parallax.setter
    def parallax(self, value: tuple[Real, Real]) -> None:
        """Fixe le facteur de parallax"""
        self._parallax = (
            float(positive(expect(value[0], Real))),
            float(positive(expect(value[1], Real))),
        )
    
    @parallax_clamp.setter
    def parallax_clamp(self, value: bool) -> None:
        """Fixe la limitation parallax"""
        self._parallax_clamp = expect(value, bool)

    @chunk_size.setter
    def chunk_size(self, value: int) -> None:
        """Fixe la taille des chunks — reconstruit le renderer"""
        self._chunk_size = max(1, expect(value, int))
        self._renderer.delete()
        self._renderer = TileRenderer(self._tile_map, self._chunk_size)

    # ======================================== LIFE CYCLE ========================================
    def preload(self) -> None:
        """Force le build immédiat du renderer — à appeler avant la boucle principale"""
        if not self._renderer.built:
            self._renderer.build()

    def on_start(self) -> None:
        """Activation du layer"""
        ...

    def on_stop(self) -> None:
        """Désactivation du layer — libère les ressources GL"""
        self._renderer.delete()

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
        px = cam.final_x * self._parallax[0]
        py = cam.final_y * self._parallax[1]

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
        if self._parallax_clamp:
            ctx = pipeline.scissor(ox, oy, tm.cols * tw, tm.rows * th)
        else:
            ctx = nullcontext()
        
        # Rendu
        with ctx:
            # Effet parallax
            if self._parallax != (1.0, 1.0):
                offset_x = cam.final_x - px
                offset_y = cam.final_y - py
                if offset_x != 0.0 or offset_y != 0.0:
                    pipeline.set_view(Mat4.from_translation(Vec3(offset_x, offset_y, 0)) @ cam.view_matrix())

            # Affichage des tiles
            self._renderer.begin()
            for cr in range(cr_min, cr_max):
                for cc in range(cc_min, cc_max):
                    self._renderer.draw(cc, cr)
            self._renderer.end()