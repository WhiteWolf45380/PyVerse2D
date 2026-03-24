# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from .._flag import CameraMode
from .._rendering._pipeline import Pipeline
from ..abc import Layer
from ..tile._tile_map import TileMap, FLIP_H, FLIP_V, FLIP_D

import pyglet
import pyglet.image
import pyglet.sprite
import pyglet.gl as gl
from pyglet.graphics import Batch, Group

from numbers import Real

# ======================================== LAYER ========================================
class TileLayer(Layer):
    """
    Layer affichant un TileMap via des chunks de sprites pré-construits

    Args:
        tile_map(TileMap): couche de tuiles à afficher
        parallax(tuple[float, float], optional): facteur de parallax (x, y)
        z(int, optional): z_order dans le batch pipeline
        chunk_size(int, optional): nombre de tuiles par côté d'un chunk
        camera_mode(CameraMode, optional): camera behavior
    """
    def __init__(
        self,
        tile_map: TileMap,
        parallax: tuple[Real, Real] = (1.0, 1.0),
        z: int = 0,
        chunk_size: int = 16,
        camera_mode: CameraMode = CameraMode.WORLD,
    ):
        super().__init__(camera_mode)
        self._tile_map: TileMap = expect(tile_map, TileMap)
        self._parallax: tuple[float, float] = (
            float(positive(expect(parallax[0], Real))),
            float(positive(expect(parallax[1], Real))),
        )
        self._z: int = z
        self._chunk_size: int = max(1, expect(chunk_size, int))
        self._batches: dict[tuple[int, int], Batch] = {}
        self._sprites: list[pyglet.sprite.Sprite] = []
        self._image: pyglet.image.AbstractImage | None = None
        self._texture_grid: pyglet.image.TextureGrid | None = None
        self._regions: dict[int, pyglet.image.TextureRegion] = {}
        self._built: bool = False

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
    def chunk_size(self) -> int:
        """Renvoie la taille des chunks en tuiles"""
        return self._chunk_size

    # ======================================== SETTERS ========================================
    @tile_map.setter
    def tile_map(self, value: TileMap) -> None:
        """Fixe le TileMap assigné — reconstruit les chunks"""
        self._tile_map = expect(value, TileMap)
        self._invalidate()

    @parallax.setter
    def parallax(self, value: tuple[Real, Real]) -> None:
        """Fixe le facteur de parallax"""
        self._parallax = (
            float(positive(expect(value[0], Real))),
            float(positive(expect(value[1], Real))),
        )

    @chunk_size.setter
    def chunk_size(self, value: int) -> None:
        """Fixe la taille des chunks — reconstruit les chunks"""
        self._chunk_size = max(1, expect(value, int))
        self._invalidate()

    # ======================================== CYCLE DE VIE ========================================
    def preload(self):
        """Force le build immédiat des chunks — à appeler avant la boucle principale"""
        if not self._built:
            self._build()

    def on_start(self):
        """Activation du layer"""
        ...

    def on_stop(self):
        """Désactivation du layer — libère les ressources"""
        self._invalidate()

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        """Actualisation du layer — tuiles statiques, rien à faire"""
        ...

    def draw(self, pipeline: Pipeline):
        """
        Affichage du layer — ne dessine que les chunks visibles dans le viewport

        Args:
            pipeline(Pipeline): pipeline active
        """
        if not self._built:
            self._build()
        if not self._batches:
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

        # Vue parallax — décale la caméra selon le facteur
        from pyglet.math import Mat4, Vec3
        offset_x = cam.final_x - px
        offset_y = cam.final_y - py
        if offset_x != 0.0 or offset_y != 0.0:
            pipeline.set_view(Mat4.from_translation(Vec3(offset_x, offset_y, 0)) @ cam.view_matrix())

        for cr in range(cr_min, cr_max):
            for cc in range(cc_min, cc_max):
                batch = self._batches.get((cc, cr))
                if batch is not None:
                    batch.draw()

    # ======================================== BUILD ========================================
    def _build(self) -> None:
        """Pré-construit tous les sprites dans leurs chunks respectifs"""
        self._invalidate()

        try:
            self._image = pyglet.image.load(self._tile_map.tile.image_path)
        except FileNotFoundError:
            print(f"[TileLayer] Image introuvable : {self._tile_map.tile.image_path}")
            self._built = True
            return

        tm = self._tile_map
        tile = tm.tile
        tw = tm.tile_width
        th = tm.tile_height

        img_w = self._image.width
        img_h = self._image.height
        src_tw = int(tile.tile_width)
        src_th = int(tile.tile_height)
        margin = int(tile.margin)
        spacing = int(tile.spacing)
        stride = src_tw + spacing

        if spacing > 0:
            cols_ts = max(1, (img_w - margin - spacing) // stride + 1)
            total_rows = max(1, (img_h - margin - spacing) // (src_th + spacing) + 1)
            total_cols = max(1, (img_w - margin - spacing) // (src_tw + spacing) + 1)
        else:
            cols_ts = max(1, (img_w - margin) // src_tw)
            total_rows = max(1, (img_h - margin) // src_th)
            total_cols = max(1, (img_w - margin) // src_tw)

        grid = pyglet.image.ImageGrid(self._image, total_rows, total_cols)
        self._texture_grid = pyglet.image.TextureGrid(grid)

        chunk_cols = (tm.cols + self._chunk_size - 1) // self._chunk_size
        chunk_rows = (tm.rows + self._chunk_size - 1) // self._chunk_size

        for cr in range(chunk_rows):
            for cc in range(chunk_cols):
                batch = Batch()
                group = Group(order=self._z)
                has_sprite = False

                row_start = cr * self._chunk_size
                col_start = cc * self._chunk_size
                row_end = min(row_start + self._chunk_size, tm.rows)
                col_end = min(col_start + self._chunk_size, tm.cols)

                for row in range(row_start, row_end):
                    for col in range(col_start, col_end):
                        tile_id = tm.tile_at(col, row)
                        if tile_id == 0:
                            continue

                        region = self._get_region(tile_id, cols_ts, total_rows)
                        if region is None:
                            continue

                        wx, wy = tm.tile_to_world(col, row)
                        flip   = tm.flags_at(col, row)
                        sprite = pyglet.sprite.Sprite(region, x=wx, y=wy, batch=batch, group=group)
                        sx = tw / src_tw
                        sy = th / src_th
                        if flip & FLIP_D:
                            sprite.rotation = 90
                            sx, sy = sy, sx
                        if flip & FLIP_H:
                            sx = -sx
                            sprite.x = wx + tw
                        if flip & FLIP_V:
                            sy = -sy
                            sprite.y = wy + th
                        sprite.scale_x = sx
                        sprite.scale_y = sy
                        self._sprites.append(sprite)
                        has_sprite = True

                if has_sprite:
                    self._batches[(cc, cr)] = batch

        self._built = True

    # ======================================== INTERNALS ========================================
    def _get_region(self, tile_id: int, cols_ts: int, total_rows: int) -> pyglet.image.TextureRegion | None:
        """Renvoie la région de texture pour un tile_id, avec mise en cache"""
        if tile_id in self._regions:
            return self._regions[tile_id]

        local_id = tile_id - 1
        ts_col = local_id % cols_ts
        ts_row = local_id // cols_ts
        flipped_row = total_rows - 1 - ts_row

        if flipped_row < 0 or flipped_row >= total_rows:
            return None

        region = self._texture_grid[flipped_row, ts_col]

        gl.glBindTexture(region.target, region.id)
        gl.glTexParameteri(region.target, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(region.target, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        self._regions[tile_id] = region
        return region

    def _invalidate(self) -> None:
        """Libère tous les sprites et batches"""
        for sprite in self._sprites:
            sprite.delete()
        self._sprites.clear()
        self._batches.clear()
        self._regions.clear()
        self._image = None
        self._texture_grid = None
        self._built = False