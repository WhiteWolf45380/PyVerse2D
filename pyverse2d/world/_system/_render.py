# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._flag import UpdatePhase
from ...abc import System, Shape
from ...shape import Capsule, Circle, Rect, Ellipse, Segment, Polygon
from ...asset import Text, Font, Color

from .._world import World, Entity
from .._component import Transform, SpriteRenderer, ShapeRenderer, TextRenderer

import pyglet
import pyglet.shapes
import pyglet.sprite
import pyglet.text
import pyglet.image
import pyglet.gl
from pyglet.graphics import Batch, Group
from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from ..._rendering._pipeline import Pipeline

# ======================================== RENDER ORDER ========================================
_ORDER_SHAPE = 0
_ORDER_SPRITE = 1
_ORDER_LABEL = 2

# ======================================== SYSTEM ========================================
class RenderSystem(System):
    """Système gérant le rendu des entités avec cache"""
    phase = UpdatePhase.LATE
    exclusive = True

    def __init__(self):
        self._sprites: dict[str, pyglet.sprite.Sprite] = {}
        self._shapes: dict[str, _ShapeObject] = {}
        self._labels: dict[str, pyglet.text.Label] = {}
        self._image_cache: dict[str, pyglet.image.AbstractImage] = {}

    # ======================================== UPDATE ========================================
    def update(self, world: World, dt: float):
        ...

    # ======================================== DRAW ========================================
    def draw(self, world: World, pipeline: Pipeline):
        """
        Synchronise toutes les entités renderables avec le Batch de rendu

        Args:
            world(World): monde à rendre
            pipeline(Pipeline): pipeline active
        """
        active_sprites = set()
        active_shapes  = set()
        active_labels  = set()

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

        if eid not in self._sprites:
            raw.anchor_x = tr.anchor.x * raw.width
            raw.anchor_y = tr.anchor.y * raw.height
            group = pipeline.get_group(sr.z * 3 + _ORDER_SPRITE)
            self._sprites[eid] = pyglet.sprite.Sprite(raw, batch=pipeline.batch, group=group)

        sprite = self._sprites[eid]
        sprite.visible = True
        sprite.x = tr.x + sr.offset[0] * tr.scale
        sprite.y = tr.y + sr.offset[1] * tr.scale
        sprite.rotation = tr.rotation
        sprite.scale = tr.scale * sr.image.scale
        sprite.color = sr.tint
        sprite.opacity = int(sr.opacity * 255)

        if sprite.image.anchor_x != tr.anchor.x * raw.width or sprite.image.anchor_y != tr.anchor.y * raw.height:
            sprite.image.anchor_x = tr.anchor.x * raw.width
            sprite.image.anchor_y = tr.anchor.y * raw.height

        if sr.image.flip_x or sr.image.flip_y:
            sprite.scale_x = -abs(sprite.scale_x) if sr.image.flip_x else abs(sprite.scale_x)
            sprite.scale_y = -abs(sprite.scale_y) if sr.image.flip_y else abs(sprite.scale_y)

    # ======================================== SYNC SHAPE ========================================
    def _sync_shape(self, entity: Entity, tr: Transform, pipeline: Pipeline):
        """Crée ou met à jour la Shape pyglet de l'entité"""
        sr: ShapeRenderer = entity.get(ShapeRenderer)
        eid = entity.id

        if not sr.is_visible():
            if eid in self._shapes:
                self._shapes[eid].visible = False
            return

        scale = tr.scale
        bx, by, bw, bh = sr.shape.bounding_box()
        local_x = (-bx - tr.anchor.x * bw + sr.offset[0]) * scale
        local_y = (-by - tr.anchor.y * bh + sr.offset[1]) * scale
        x = tr.x + local_x
        y = tr.y + local_y

        if eid not in self._shapes:
            group = pipeline.get_group(sr.z * 3 + _ORDER_SHAPE)
            obj = _ShapeObject(sr.shape, x, y, scale, tr.rotation, sr, pipeline.batch, group)
            self._shapes[eid] = obj

        obj = self._shapes[eid]
        obj.update(x, y, scale, tr.rotation, sr)

    # ======================================== SYNC LABEL ========================================
    def _sync_text(self, entity: Entity, tr: Transform, pipeline: Pipeline) -> None:
        """Crée ou met à jour le Label pyglet de l'entité."""
        tc: TextRenderer = entity.get(TextRenderer)
        eid = entity.id

        if not tc.is_visible():
            if eid in self._labels:
                self._labels[eid].visible = False
            return

        t: Text = tc.text
        f: Font = t.font

        # Création du label
        if eid not in self._labels:
            group = pipeline.get_group(tc.z * 3 + _ORDER_LABEL)
            self._labels[eid] = pyglet.text.Label(
                t.text,
                font_name=f.name,
                font_size=int(f.size * tr.scale),
                rotation=tr.rotation,
                weight=tc.weight,
                italic=tc.italic,
                color=_final_color(tc),
                multiline=tc.multiline or tc.width is not None,
                align=tc.align,
                width=tc.width,
                anchor_x="left",
                anchor_y="bottom",
                batch=pipeline.batch,
                group=group,
            )
            label = self._labels[eid]
            label.x = tr.x - (tr.anchor[0] * label.content_width  + tc.offset[0]) * tr.scale
            label.y = tr.y - (tr.anchor[1] * label.content_height + tc.offset[1]) * tr.scale
            return

        # Mise à jour
        label = self._labels[eid]
        label.visible = True
        label.text = t.text
        label.font_size = int(f.size * tr.scale)
        label.rotation = tr.rotation
        label.x = tr.x - (tr.anchor[0] * label.content_width + tc.offset[0]) * tr.scale
        label.y = tr.y - (tr.anchor[1] * label.content_height + tc.offset[1]) * tr.scale
        label.font_name = f.name
        label.weight = tc.weight
        label.italic = tc.italic
        label.color = _final_color(tc)
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


# ======================================== SHAPE OBJECT ========================================
class _ShapeObject:
    """Wrapper unifié pour le rendu d'une shape géométrique"""
    def __init__(self, shape: Shape, x: float, y: float, scale: float, rotation: float, sr: ShapeRenderer, batch: pyglet.graphics.Batch, group: pyglet.graphics.Group):
        self._shape = shape
        self._fill = None
        self._border = None
        self._batch = batch
        self._group = group
        self._poly_scale = None
        self._build(x, y, scale, rotation, sr)

    def _build(self, x: float, y: float, scale: float, rotation: float, sr: ShapeRenderer):
        """Instancie fill et/ou border selon la config du ShapeRenderer"""
        shape = self._shape

        # Remplissage
        if sr.filling:
            color = sr.filling_color.rgba8
            s = scale
            if isinstance(shape, Capsule):
                self._fill = _CapsuleShape(x, y, shape.radius * s, shape.spine * s, color=color, batch=self._batch, group=self._group)
            elif isinstance(shape, Circle):
                self._fill = pyglet.shapes.Circle(x, y, shape.radius * s, color=color, batch=self._batch, group=self._group)
                self._fill.rotation = rotation
            elif isinstance(shape, Rect):
                self._fill = pyglet.shapes.Rectangle(x, y, shape.width * s, shape.height * s, color=color, batch=self._batch, group=self._group)
                self._fill.rotation = rotation
            elif isinstance(shape, Ellipse):
                self._fill = pyglet.shapes.Ellipse(x, y, shape.rx * s, shape.ry * s, color=color, batch=self._batch, group=self._group)
                self._fill.rotation = rotation
            elif isinstance(shape, Segment):
                ax, ay = x + shape.A.x * s, y + shape.A.y * s
                bx, by = x + shape.B.x * s, y + shape.B.y * s
                cx, cy = (ax + bx) / 2, (ay + by) / 2
                ax, ay = _rotate(ax, ay, cx, cy, rotation)
                bx, by = _rotate(bx, by, cx, cy, rotation)
                self._fill = pyglet.shapes.Line(ax, ay, bx, by, thickness=shape.width * s, color=color, batch=self._batch, group=self._group)
            elif isinstance(shape, Polygon):
                pts = [_rotate(x + p.x * s, y + p.y * s, x, y, rotation) for p in shape.points]
                self._fill = pyglet.shapes.Polygon(*pts, color=color, batch=self._batch, group=self._group)
                self._poly_scale = s

        # Bordure
        if sr.border_width > 0:
            self._border = _BorderObject(shape, x, y, scale, rotation, sr.border_color.rgba8, sr.border_width, self._batch, self._group)

    def update(self, x: float, y: float, scale: float, rotation: float, sr: ShapeRenderer):
        """Met à jour position, scale, couleurs et visibilité"""
        shape = self._shape
        opacity = int(round(255 * sr.opacity))

        # Remplissage
        if sr.filling and self._fill is None:
            self._build(x, y, scale, rotation, sr)
            return
        if not sr.filling and self._fill is not None:
            self._fill.delete()
            self._fill = None

        if self._fill is not None:
            self._fill.visible = True
            self._fill.opacity = opacity
            self._fill.color = sr.filling_color.rgba8
            if isinstance(shape, Polygon):
                if self._poly_scale != scale:
                    self._fill.delete()
                    pts = [_rotate(x + p.x * scale, y + p.y * scale, x, y, rotation) for p in shape.points]
                    self._fill = pyglet.shapes.Polygon(*pts, color=sr.filling_color.rgb8, batch=self._batch, group=self._group)
                    self._fill.opacity = opacity
                    self._poly_scale = scale
                else:
                    ox = self._fill.x - x
                    oy = self._fill.y - y
                    if ox != 0.0 or oy != 0.0:
                        self._fill.delete()
                        pts = [_rotate(x + p.x * scale, y + p.y * scale, x, y, rotation) for p in shape.points]
                        self._fill = pyglet.shapes.Polygon(*pts, color=sr.filling_color.rgb8, batch=self._batch, group=self._group)
                        self._fill.opacity = opacity
            else:
                _apply_fill_position(self._fill, shape, x, y, scale, rotation)

        # Bordure
        if sr.border_width > 0 and self._border is None:
            self._border = _BorderObject(shape, x, y, scale, rotation, sr.border_color.rgba8, sr.border_width, self._batch, self._group)
        if sr.border_width == 0 and self._border is not None:
            self._border.delete()
            self._border = None

        if self._border is not None:
            self._border.update(shape, x, y, scale, rotation, sr.border_color.rgba8, sr.border_width, sr.opacity)

    @property
    def visible(self):
        f = self._fill.visible if self._fill else True
        b = self._border.visible if self._border else True
        return f or b

    @visible.setter
    def visible(self, v):
        if self._fill:
            self._fill.visible = v
        if self._border:
            self._border.visible = v

    def delete(self):
        if self._fill:
            self._fill.delete()
        if self._border:
            self._border.delete()


# ======================================== BORDER OBJECT ========================================
class _BorderObject:
    """Bordure d'une shape via GL_LINE_LOOP sur ses vertices()"""
    def __init__(self, shape: Shape, x: float, y: float, scale: float, rotation: float, color: tuple[int, ...], width: int, batch: Batch, group: Group):
        self._vlist: list = None
        self._visible: bool = True
        self._color: tuple[int, ...] = color
        self._width: int = width
        self._n: int = 0
        self._batch: Batch = batch
        self._group: Group = group
        self._build(shape, x, y, scale, rotation, color, width)

    def _build(self, shape: Shape, x: float, y: float, scale: float, rotation: float, color: tuple[int, ...], width: int):
        pts = shape.vertices(scale)
        self._n = len(pts)
        flat = []
        for px, py in pts:
            rx, ry = _rotate(x + px, y + py, x, y, rotation)
            flat += [rx, ry]
        self._vlist = self._batch.add(self._n, pyglet.gl.GL_LINE_LOOP, self._group, ('v2f', flat), ('c4B', color * self._n))
        pyglet.gl.glLineWidth(width)

    def update(self, shape: Shape, x: float, y: float, scale: float, rotation: float, color: tuple[int, ...], width: int, opacity: float):
        if self._vlist is None:
            return
        self._color = color
        pts = shape.vertices(scale)
        flat = []
        for px, py in pts:
            rx, ry = _rotate(x + px, y + py, x, y, rotation)
            flat += [rx, ry]
        self._vlist.vertices[:] = flat
        r, g, b, a = color
        self._vlist.colors[:] = (r, g, b, int(a * opacity)) * self._n
        if width != self._width:
            pyglet.gl.glLineWidth(width)
            self._width = width

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        if self._vlist is None:
            return
        self._visible = v
        if v:
            self._vlist.colors[:] = self._color * self._n
        else:
            self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    def delete(self):
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None

# ======================================== INTERNALS ========================================
def _apply_fill_position(obj: object, shape: Shape, x: float, y: float, scale: float, rotation: float = 0.0):
    """Met à jour la position et les dimensions du fill pyglet"""
    if isinstance(shape, Circle):
        obj.x = x
        obj.y = y
        obj.radius = shape.radius * scale
        obj.rotation = rotation

    elif isinstance(shape, Rect):
        obj.x = x
        obj.y = y
        obj.width = shape.width * scale
        obj.height = shape.height * scale
        obj.rotation = rotation

    elif isinstance(shape, Ellipse):
        obj.x = x
        obj.y = y
        obj.a = shape.rx * scale
        obj.b = shape.ry * scale
        obj.rotation = rotation

    elif isinstance(shape, Capsule):
        obj.x = x
        obj.y = y
        obj.set_scale(scale)

    elif isinstance(shape, Segment):
        s = scale
        cx = x + (shape.A.x + shape.B.x) / 2 * s
        cy = y + (shape.A.y + shape.B.y) / 2 * s
        ax, ay = _rotate(x + shape.A.x * s, y + shape.A.y * s, cx, cy, rotation)
        bx, by = _rotate(x + shape.B.x * s, y + shape.B.y * s, cx, cy, rotation)
        obj.x  = ax
        obj.y  = ay
        obj.x2 = bx
        obj.y2 = by
        obj.thickness = shape.width * s

def _final_color(renderer: TextRenderer) -> tuple[int, int, int, int]:
    """Fusionne color et opacity en un seul RGBA8"""
    r, g, b, a = renderer.color.rgba8
    return (r, g, b, int(a * renderer.opacity))

def _rotate(px: float, py: float, cx: float, cy: float, angle: float) -> tuple[float, float]:
    """Fait tourner (px, py) autour de (cx, cy) d'un angle en degrés"""
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    dx, dy = px - cx, py - cy
    return cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a

# ======================================== CAPSULE SHAPE ========================================
class _CapsuleShape:
    """
    Capsule pyglet composite : rect central + deux demi-cercles
    Origine = centre du demi-cercle bas = bas de la spine
    """
    def __init__(self, x: float, y: float, radius: float, spine: float, color: tuple[int, ...]=(255, 255, 255, 255), batch: Batch=None, group: Group=None):
        self._base_radius: float = radius
        self._base_spine: float = spine
        self._rect: pyglet.shapes.Rectangle = pyglet.shapes.Rectangle(x - radius, y, radius * 2, spine, color=color, batch=batch, group=group)
        self._top: pyglet.shapes.Circle = pyglet.shapes.Circle(x, y + spine, radius, color=color, batch=batch, group=group)
        self._bottom: pyglet.shapes.Circle = pyglet.shapes.Circle(x, y, radius, color=color, batch=batch, group=group)

    def set_scale(self, scale: float):
        r = self._base_radius * scale
        s = self._base_spine * scale
        cx = self._bottom.x
        cy = self._bottom.y
        self._bottom.radius = r
        self._top.radius = r
        self._rect.x = cx - r
        self._rect.width = r * 2
        self._rect.height = s
        self._top.y = cy + s

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
        r = self._bottom.radius
        self._bottom.x = v
        self._top.x = v
        self._rect.x = v - r

    @property
    def y(self):
        return self._bottom.y

    @y.setter
    def y(self, v):
        self._bottom.y = v
        self._top.y = v + self._rect.height
        self._rect.y = v

    @property
    def color(self):
        return self._rect.color

    @color.setter
    def color(self, v):
        self._rect.color = self._top.color = self._bottom.color = v

    @property
    def opacity(self):
        return self._rect.opacity

    @opacity.setter
    def opacity(self, value: float):
        self._rect.opacity = self._top.opacity = self._bottom.opacity = value

    def delete(self):
        self._rect.delete()
        self._top.delete()
        self._bottom.delete()