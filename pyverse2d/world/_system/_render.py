# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._flag import UpdatePhase
from ...abc import System
from ...shape import Shape, Capsule, Circle, Rect, Ellipse, Segment, Polygon

from .._world import World, Entity
from .._component import Transform, SpriteRenderer, ShapeRenderer, TextRenderer

import pyglet
import pyglet.shapes
import pyglet.sprite
import pyglet.text
import pyglet.image
import pyglet.gl
from typing import TYPE_CHECKING

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
        sprite.x = tr.x + sr.offset[0]
        sprite.y = tr.y + sr.offset[1]
        sprite.rotation = tr.rotation
        sprite.scale = tr.scale * sr.image.scale
        sprite.opacity = int(sr.opacity * 255)

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
            obj = _ShapeObject(sr.shape, x, y, scale, sr, pipeline.batch, group)
            self._shapes[eid] = obj

        obj = self._shapes[eid]
        obj.update(x, y, scale, sr)

    # ======================================== SYNC LABEL ========================================
    def _sync_text(self, entity: Entity, tr: Transform, pipeline: Pipeline):
        """Crée ou met à jour le Label pyglet de l'entité"""
        tc: TextRenderer = entity.get(TextRenderer)
        eid = entity.id

        if not tc.is_visible():
            if eid in self._labels:
                self._labels[eid].visible = False
            return

        if eid not in self._labels:
            group = pipeline.get_group(tc.z * 3 + _ORDER_LABEL)
            t = tc.text
            self._labels[eid] = pyglet.text.Label(
                t.text,
                font_name=t.font,
                font_size=t.fontsize,
                color=t.color,
                anchor_x="left",
                anchor_y="bottom",
                batch=pipeline.batch,
                group=group,
            )

        label = self._labels[eid]
        label.visible = True
        label.x = tr.x + tc.offset[0]
        label.y = tr.y + tc.offset[1]
        label.font_size = tc.text.fontsize * tr.scale
        label.opacity = int(tc.opacity * 255)

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
    def __init__(self, shape: Shape, x: float, y: float, scale: float, sr: ShapeRenderer, batch: pyglet.graphics.Batch, group: pyglet.graphics.Group):
        self._shape = shape
        self._fill = None
        self._border = None
        self._batch = batch
        self._group = group
        self._poly_scale = None
        self._build(x, y, scale, sr)

    def _build(self, x: float, y: float, scale: float, sr: ShapeRenderer):
        """Instancie fill et/ou border selon la config du ShapeRenderer"""
        shape = self._shape

        # Remplissage
        if sr.filling:
            color = sr.filling_color.rgb
            s = scale
            if isinstance(shape, Capsule):
                self._fill = _CapsuleShape(x, y, shape.radius * s, shape.spine * s, color=color, batch=self._batch, group=self._group)
            elif isinstance(shape, Circle):
                self._fill = pyglet.shapes.Circle(x, y, shape.radius * s, color=color, batch=self._batch, group=self._group)
            elif isinstance(shape, Rect):
                self._fill = pyglet.shapes.Rectangle(x, y, shape.width * s, shape.height * s, color=color, batch=self._batch, group=self._group)
            elif isinstance(shape, Ellipse):
                self._fill = pyglet.shapes.Ellipse(x, y, shape.rx * s, shape.ry * s, color=color, batch=self._batch, group=self._group)
            elif isinstance(shape, Segment):
                self._fill = pyglet.shapes.Line(x + shape.A.x * s, y + shape.A.y * s, x + shape.B.x * s, y + shape.B.y * s, thickness=shape.width * s, color=color, batch=self._batch, group=self._group)
            elif isinstance(shape, Polygon):
                pts = [(x + p.x * s, y + p.y * s) for p in shape.points]
                self._fill = pyglet.shapes.Polygon(*pts, color=color, batch=self._batch, group=self._group)
                self._poly_scale = s

        # Bordure
        if sr.border_width > 0:
            self._border = _BorderObject(shape, x, y, scale, sr.border_color.rgb, sr.border_width, self._batch, self._group)

    def update(self, x, y, scale, sr: ShapeRenderer):
        """Met à jour position, scale, couleurs et visibilité"""
        shape = self._shape
        opacity = int(sr.opacity * 255)
        s = scale

        # Remplissage
        if sr.filling and self._fill is None:
            self._build(x, y, scale, sr)
            return
        if not sr.filling and self._fill is not None:
            self._fill.delete()
            self._fill = None

        if self._fill is not None:
            self._fill.visible = True
            self._fill.opacity = opacity
            self._fill.color   = sr.filling_color.rgb
            if isinstance(shape, Polygon):
                if self._poly_scale != s:
                    self._fill.delete()
                    pts = [(x + p.x * s, y + p.y * s) for p in shape.points]
                    self._fill = pyglet.shapes.Polygon(*pts, color=sr.filling_color.rgb, batch=self._batch, group=self._group)
                    self._poly_scale = s
                else:
                    ox = self._fill.x - x
                    oy = self._fill.y - y
                    if ox != 0.0 or oy != 0.0:
                        self._fill.delete()
                        pts = [(x + p.x * s, y + p.y * s) for p in shape.points]
                        self._fill = pyglet.shapes.Polygon(*pts, color=sr.filling_color.rgb, batch=self._batch, group=self._group)
            else:
                _apply_fill_position(self._fill, shape, x, y, s)

        # Bordure
        if sr.border_width > 0 and self._border is None:
            self._border = _BorderObject(shape, x, y, scale, sr.border_color.rgb, sr.border_width, self._batch, self._group)
        if sr.border_width == 0 and self._border is not None:
            self._border.delete()
            self._border = None

        if self._border is not None:
            self._border.update(shape, x, y, scale, sr.border_color.rgb, sr.border_width, opacity)

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
    """
    Bordure d'une shape via GL_LINE_LOOP sur ses vertices().
    Utilise une vertex list mise à jour en place pour éviter les réallocations.
    """

    def __init__(self, shape, x, y, scale, color, width, batch, group):
        self._vlist = None
        self._visible = True
        self._width = width
        self._n = 0
        self._batch = batch
        self._group = group
        self._build(shape, x, y, scale, color, width)

    def _build(self, shape, x, y, scale, color, width):
        pts = shape.vertices(scale)
        self._n = len(pts)
        flat = []
        for px, py in pts:
            flat += [x + px, y + py]
        r, g, b = color
        self._vlist = self._batch.add(self._n, pyglet.gl.GL_LINE_LOOP, self._group, ('v2f', flat), ('c4B', (r, g, b, 255) * self._n))
        pyglet.gl.glLineWidth(width)

    def update(self, shape, x, y, scale, color, width, opacity):
        if self._vlist is None:
            return
        pts = shape.vertices(scale)
        flat = []
        for px, py in pts:
            flat += [x + px, y + py]
        self._vlist.vertices[:] = flat
        r, g, b = color
        a = opacity
        self._vlist.colors[:] = (r, g, b, a) * self._n
        if width != self._width:
            pyglet.gl.glLineWidth(width)
            self._width = width

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        self._visible = v
        if self._vlist is not None:
            if not v:
                self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    def delete(self):
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None


# ======================================== FILL POSITION HELPER ========================================
def _apply_fill_position(obj, shape, x, y, scale: float):
    """
    Met à jour la position et les dimensions du fill pyglet.
    Pyglet ne touche au vertex buffer que si la valeur change.
    """
    if isinstance(shape, (Circle, Rect, Ellipse)):
        obj.x = x
        obj.y = y
    if isinstance(shape, Circle):
        obj.radius = shape.radius * scale
    elif isinstance(shape, Rect):
        obj.x = x
        obj.y = y
        obj.width = shape.width * scale
        obj.height = shape.height * scale
    elif isinstance(shape, Ellipse):
        obj.a = shape.rx * scale
        obj.b = shape.ry * scale
    elif isinstance(shape, Capsule):
        obj.x = x
        obj.y = y
        obj.set_scale(scale)
    elif isinstance(shape, Segment):
        s = scale
        obj.x = x + shape.A.x * s
        obj.y = y + shape.A.y * s
        obj.x2 = x + shape.B.x * s
        obj.y2 = y + shape.B.y * s
        obj.thickness = shape.width * s

# ======================================== CAPSULE SHAPE ========================================
class _CapsuleShape:
    """
    Capsule pyglet composite : rect central + deux demi-cercles.
    Origine = centre du demi-cercle bas = bas de la spine.
    """
    def __init__(self, x, y, radius, spine, color=(255, 255, 255), batch=None, group=None):
        self._base_radius = radius
        self._base_spine = spine
        self._rect = pyglet.shapes.Rectangle(x - radius, y, radius * 2, spine, color=color, batch=batch, group=group)
        self._top = pyglet.shapes.Circle(x, y + spine, radius, color=color, batch=batch, group=group)
        self._bottom = pyglet.shapes.Circle(x, y, radius, color=color, batch=batch, group=group)

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
    def opacity(self, v):
        self._rect.opacity = self._top.opacity = self._bottom.opacity = v

    def delete(self):
        self._rect.delete()
        self._top.delete()
        self._bottom.delete()