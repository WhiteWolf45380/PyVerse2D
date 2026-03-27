# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._flag import UpdatePhase
from ...abc import System
from ...asset import Text, Font
from .._world import World, Entity
from .._component import Transform, SpriteRenderer, ShapeRenderer, TextRenderer
from ..._rendering import Pipeline, PygletShapeRenderer

import pyglet
import pyglet.sprite
import pyglet.text
import pyglet.image

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..._rendering._pipeline import Pipeline

# ======================================== RENDER ORDER ========================================
_ORDER_SHAPE = 0
_ORDER_SPRITE = 1
_ORDER_LABEL = 2

# ======================================== SYSTEM ========================================
class RenderSystem(System):
    """Système gérant le rendu des entités"""
    __slots__ = ("_sprites", "_shapes", "_labels", "_image_cache")
    phase = UpdatePhase.LATE
    exclusive = True

    def __init__(self):
        self._sprites: dict = {}
        self._shapes: dict[int, PygletShapeRenderer] = {}
        self._labels: dict = {}
        self._image_cache: dict = {}

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float): ...

    # ======================================== DRAW ========================================
    def draw(self, world: World, pipeline: Pipeline):
        """
        Synchronise toutes les entités renderables avec le Batch de rendu

        Args:
            world(World): monde à rendre
            pipeline(Pipeline): pipeline active
        """
        active_sprites = set()
        active_shapes = set()
        active_labels = set()

        for entity in world.query(Transform):
            eid = entity.id
            tr: Transform = entity.get(Transform)

            if entity.has(ShapeRenderer):
                active_shapes.add(eid)
                self._sync_shape(entity, tr, pipeline)

            if entity.has(SpriteRenderer):
                active_sprites.add(eid)
                self._sync_sprite(entity, tr, pipeline)

            if entity.has(TextRenderer):
                active_labels.add(eid)
                self._sync_text(entity, tr, pipeline)

        # Nettoyage des entités inactives
        for eid in list(self._sprites):
            if eid not in active_sprites:
                self._sprites.pop(eid).delete()

        for eid in list(self._shapes):
            if eid not in active_shapes:
                self._shapes.pop(eid).delete()

        for eid in list(self._labels):
            if eid not in active_labels:
                self._labels.pop(eid).delete()

    # ======================================== SYNC SHAPE ========================================
    def _sync_shape(self, entity: Entity, tr: Transform, pipeline: Pipeline):
        """Crée ou met à jour le renderer de shape de l'entité"""
        sr: ShapeRenderer = entity.get(ShapeRenderer)
        eid = entity.id

        if not sr.is_visible():
            if eid in self._shapes:
                self._shapes[eid].visible = False
            return

        cx, cy = _world_center(sr.shape, tr, sr.offset)
        z = sr.z * 3 + _ORDER_SHAPE

        if eid not in self._shapes:
            self._shapes[eid] = PygletShapeRenderer(
                shape = sr.shape,
                cx = cx,
                cy = cy,
                scale = tr.scale,
                rotation = tr.rotation,
                filling = sr.filling,
                color = sr.filling_color,
                border_width = sr.border_width,
                border_color = sr.border_color,
                opacity = sr.opacity,
                z = z,
                pipeline = pipeline,
            )
        else:
            self._shapes[eid].update(
                cx = cx,
                cy = cy,
                scale = tr.scale,
                rotation = tr.rotation,
                filling = sr.filling,
                color = sr.filling_color,
                border_width = sr.border_width,
                border_color = sr.border_color,
                opacity = sr.opacity,
                z=z
            )
            self._shapes[eid].visible = True

    # ======================================== SYNC SPRITE ========================================
    def _sync_sprite(self, entity: Entity, tr: Transform, pipeline: Pipeline):
        """Crée ou met à jour le Sprite pyglet de l'entité"""
        sr: SpriteRenderer = entity.get(SpriteRenderer)
        eid = entity.id

        if not sr.is_visible():
            if eid in self._sprites:
                self._sprites[eid].visible = False
            return

        raw = self._load_image(sr.image.path)
        if raw is None:
            return

        anchor_x = int(tr.anchor.x * raw.width)
        anchor_y = int(tr.anchor.y * raw.height)

        if eid not in self._sprites:
            region = raw.get_region(0, 0, raw.width, raw.height)
            region.anchor_x = anchor_x
            region.anchor_y = anchor_y
            group = pipeline.get_group(sr.z * 3 + _ORDER_SPRITE)
            self._sprites[eid] = pyglet.sprite.Sprite(region, batch=pipeline.batch, group=group)
        else:
            sprite = self._sprites[eid]
            if sprite.image.get_texture() is not raw.get_texture():
                region = raw.get_region(0, 0, raw.width, raw.height)
                region.anchor_x = anchor_x
                region.anchor_y = anchor_y
                sprite.image = region
            else:
                sprite.image.anchor_x = anchor_x
                sprite.image.anchor_y = anchor_y

        if sr.image.width: scale_x = sr.image.width / raw.width
        else: scale_x = None
        if sr.image.height: scale_y = sr.image.height / raw.height
        else: scale_y = None

        if scale_x is None and scale_y is None: scale_x = scale_y = 1.0
        elif scale_x is None: scale_x = scale_y
        elif scale_y is None: scale_y = scale_x

        flip_x = -1 if sr.flip_x else 1
        flip_y = -1 if sr.flip_y else 1

        sprite: pyglet.sprite.Sprite = self._sprites[eid]
        sprite.visible = True
        sprite.x = tr.x + sr.offset[0] * tr.scale
        sprite.y = tr.y + sr.offset[1] * tr.scale
        sprite.rotation = tr.rotation
        sprite.scale_x = tr.scale * scale_x * sr.image.scale_factor * flip_x
        sprite.scale_y = tr.scale * scale_y * sr.image.scale_factor * flip_y
        sprite.color = sr.tint.rgb8
        sprite.opacity = int(sr.opacity * 255)

    # ======================================== SYNC TEXT ========================================
    def _sync_text(self, entity: Entity, tr: Transform, pipeline: Pipeline):
        """Crée ou met à jour le Label pyglet de l'entité"""
        tc: TextRenderer = entity.get(TextRenderer)
        eid = entity.id

        if not tc.is_visible():
            if eid in self._labels:
                self._labels[eid].visible = False
            return

        t: Text = tc.text
        f: Font = t.font

        if eid not in self._labels:
            group = pipeline.get_group(tc.z * 3 + _ORDER_LABEL)
            self._labels[eid] = pyglet.text.Label(
                t.text,
                font_name = f.name,
                font_size = int(f.size * tr.scale),
                rotation = tr.rotation,
                weight = tc.weight,
                italic = tc.italic,
                color = tc.color.rgba8,
                multiline = tc.multiline or tc.width is not None,
                align = tc.align,
                width = tc.width,
                anchor_x = "left",
                anchor_y = "bottom",
                batch = pipeline.batch,
                group = group,
            )
            label = self._labels[eid]
            label.x = tr.x - (tr.anchor[0] * label.content_width + tc.offset[0]) * tr.scale
            label.y = tr.y - (tr.anchor[1] * label.content_height + tc.offset[1]) * tr.scale
            return

        label: pyglet.text.Label = self._labels[eid]
        label.visible = True
        label.text = t.text
        label.font_size = int(f.size * tr.scale)
        label.rotation = tr.rotation
        label.x = tr.x - (tr.anchor[0] * label.content_width + tc.offset[0]) * tr.scale
        label.y = tr.y - (tr.anchor[1] * label.content_height + tc.offset[1]) * tr.scale
        label.font_name = f.name
        label.weight = tc.weight
        label.italic = tc.italic
        label.color = tc.color.rgba8
        label.opacity = int(tc.opacity * 255)
        label.width = tc.width
        label.multiline = tc.multiline or tc.width is not None
        label.align = tc.align

    # ======================================== IMAGE CACHE ========================================
    def _load_image(self, path: str) -> pyglet.image.AbstractImage | None:
        """Charge et met en cache une image depuis son chemin"""
        if path in self._image_cache:
            return self._image_cache[path]
        try:
            img = pyglet.image.load(path)
            self._image_cache[path] = img
            return img
        except FileNotFoundError:
            print(f"[RenderSystem] Cannot load image: {path}")
            return None


# ======================================== WORLD CENTER ========================================
def _world_center(shape, tr: Transform, offset: tuple[float, float]) -> tuple[float, float]:
    """Calcule le centre géométrique monde en tenant compte de l'anchor"""
    x_min, y_min, x_max, y_max = shape.bounding_box
    anchor_x = x_min + tr.anchor.x * (x_max - x_min)
    anchor_y = y_min + tr.anchor.y * (y_max - y_min)
    return (
        tr.x - anchor_x * tr.scale + offset[0] * tr.scale,
        tr.y - anchor_y * tr.scale + offset[1] * tr.scale,
    )