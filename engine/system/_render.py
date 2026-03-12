# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet
import pyglet.shapes
import pyglet.sprite
import pyglet.text
import pyglet.image

from ..ecs import System, World, UpdatePhase
from ..component import Transform, SpriteRenderer, ShapeRenderer, TextRenderer
from ..shape import Capsule, Circle, Rect, Ellipse, Segment, Polygon

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .._rendering import Renderer

# ======================================== ORDRE DE RENDU ========================================
_ORDER_SHAPE  = 0
_ORDER_SPRITE = 1
_ORDER_LABEL  = 2

# ======================================== SYSTEM ========================================
class RenderSystem(System):
    """Système gérant le rendu des entités avec cache"""
    phase = UpdatePhase.LATE

    def __init__(self):
        self._sprites: dict[str, pyglet.sprite.Sprite] = {}
        self._shapes: dict[str, object] = {}
        self._labels: dict[str, pyglet.text.Label] = {}
        self._image_cache: dict[str, pyglet.image.AbstractImage] = {}

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        """Actualisation du système"""
        ...

    # ======================================== DRAW ========================================
    def draw(self, world: World, renderer: Renderer):
        """
        Synchronise toutes les entités renderables avec le Batch de rendu

        Args:
            world(World): monde à rendre
            renderer(Renderer): renderer actif
        """
        active_sprites = set()
        active_shapes  = set()
        active_labels  = set()

        for entity in world.query(Transform):
            eid = entity.id
            tr: Transform = entity.get(Transform)

            if entity.has(ShapeRenderer):
                active_shapes.add(eid)
                self._sync_shape(entity, tr, renderer)

            if entity.has(SpriteRenderer):
                active_sprites.add(eid)
                self._sync_sprite(entity, tr, renderer)

            if entity.has(TextRenderer):
                active_labels.add(eid)
                self._sync_text(entity, tr, renderer)

        # Nettoyage des entités supprimées
        for eid in list(self._sprites):
            if eid not in active_sprites:
                self._sprites.pop(eid).delete()

        for eid in list(self._shapes):
            if eid not in active_shapes:
                self._shapes.pop(eid).delete()

        for eid in list(self._labels):
            if eid not in active_labels:
                self._labels.pop(eid).delete()

    # ======================================== SYNC SPRITE ========================================
    def _sync_sprite(self, entity, tr: Transform, renderer: Renderer):
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

        if eid not in self._sprites:
            group = renderer.get_group(sr.z * 3 + _ORDER_SPRITE)
            self._sprites[eid] = pyglet.sprite.Sprite(raw, batch=renderer.batch, group=group)

        sprite = self._sprites[eid]
        sprite.visible  = True
        sprite.x = tr.x + sr.offset[0]
        sprite.y = tr.y + sr.offset[1]
        sprite.rotation = tr.rotation
        sprite.scale = tr.scale * sr.image.scale
        sprite.opacity = int(sr.get_alpha() * 255)

        if sr.image.flip_x or sr.image.flip_y:
            sprite.scale_x = -abs(sprite.scale_x) if sr.image.flip_x else abs(sprite.scale_x)
            sprite.scale_y = -abs(sprite.scale_y) if sr.image.flip_y else abs(sprite.scale_y)

    # ======================================== SYNC SHAPE ========================================
    def _sync_shape(self, entity, tr: Transform, renderer: Renderer):
        """Crée ou met à jour la Shape pyglet de l'entité"""
        sr: ShapeRenderer = entity.get(ShapeRenderer)
        eid = entity.id

        if not sr.is_visible():
            if eid in self._shapes:
                self._shapes[eid].visible = False
            return

        x = tr.x + sr.offset[0]
        y = tr.y + sr.offset[1]

        if eid not in self._shapes:
            group = renderer.get_group(sr.z * 3 + _ORDER_SHAPE)
            obj = self._create_shape(sr.shape, x, y, renderer.batch, group)
            if obj is None:
                return
            self._shapes[eid] = obj

        obj = self._shapes[eid]
        obj.visible = True
        obj.x = x
        obj.y = y
        obj.opacity = int(sr.get_alpha() * 255)

    def _create_shape(self, shape, x, y, batch, group):
        """Instancie l'objet pyglet.shapes correspondant à la shape"""
        if isinstance(shape, Capsule):
            return _CapsuleShape(x, y, shape.radius, shape.spine, batch=batch, group=group)
        if isinstance(shape, Circle):
            return pyglet.shapes.Circle(x, y, shape.radius, batch=batch, group=group)
        if isinstance(shape, Rect):
            return pyglet.shapes.Rectangle(x, y, shape.width, shape.height, batch=batch, group=group)
        if isinstance(shape, Ellipse):
            return pyglet.shapes.Ellipse(x, y, shape.rx, shape.ry, batch=batch, group=group)
        if isinstance(shape, Segment):
            ax, ay = shape.A
            bx, by = shape.B
            return pyglet.shapes.Line(ax, ay, bx, by, width=shape.width, batch=batch, group=group)
        if isinstance(shape, Polygon):
            pts = [(p.x, p.y) for p in shape.points]
            return pyglet.shapes.Polygon(*pts, batch=batch, group=group)
        return None

    # ======================================== SYNC LABEL ========================================
    def _sync_text(self, entity, tr: Transform, renderer: Renderer):
        """Crée ou met à jour le Label pyglet de l'entité"""
        tc: TextRenderer = entity.get(TextRenderer)
        eid = entity.id

        if not tc.is_visible():
            if eid in self._labels:
                self._labels[eid].visible = False
            return

        if eid not in self._labels:
            group = renderer.get_group(tc.z * 3 + _ORDER_LABEL)
            t = tc.text
            self._labels[eid] = pyglet.text.Label(
                t.text,
                font_name=t.font,
                font_size=t.fontsize,
                color=t.color,
                batch=renderer.batch,
                group=group,
            )

        label = self._labels[eid]
        label.visible = True
        label.x = tr.x + tc.offset[0]
        label.y = tr.y + tc.offset[1]
        label.opacity = int(tc.get_alpha() * 255)

    # ======================================== IMAGE CACHE ========================================
    def _load_image(self, path: str) -> pyglet.image.AbstractImage | None:
        """Charge et cache une image depuis son chemin"""
        if path in self._image_cache:
            return self._image_cache[path]
        try:
            img = pyglet.image.load(path)
            self._image_cache[path] = img
            return img
        except FileNotFoundError:
            print(f"[RenderSystem] Cannot load image: {path}")
            return None

# ======================================== INTERNAL RENDERING SHAPES ========================================
class _CapsuleShape:
    def __init__(self, x, y, radius, spine, batch=None, group=None):
        self._rect = pyglet.shapes.Rectangle(x - radius, y, radius * 2, spine, batch=batch, group=group)
        self._top = pyglet.shapes.Circle(x, y + spine, radius, batch=batch, group=group)
        self._bottom = pyglet.shapes.Circle(x, y, radius, batch=batch, group=group)

    @property
    def visible(self):
        return self._rect.visible

    @visible.setter
    def visible(self, v):
        self._rect.visible = self._top.visible = self._bottom.visible = v

    @property
    def x(self):
        return self._bottom.x

    @x.setter
    def x(self, v):
        self._bottom.x = v
        self._top.x = v
        self._rect.x = v - self._bottom.radius

    @property
    def y(self):
        return self._bottom.y

    @y.setter
    def y(self, v):
        self._bottom.y = v
        self._top.y = v + self._rect.height
        self._rect.y = v

    @property
    def opacity(self):
        return self._rect.opacity

    @opacity.setter
    def opacity(self, v):
        self._rect.opacity = self._top.opacity = self._bottom.opacity = v

    def delete(self):
        self._rect.delete()
        self._top.delete()
        self._bottom.delete()