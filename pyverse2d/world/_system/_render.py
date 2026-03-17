# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._flag import UpdatePhase
from ...abc import System, Shape, VertexShape
from ...shape import Capsule, Circle, Ellipse
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

_CIRCLE_BORDER_SEGMENTS = 64
_ELLIPSE_BORDER_SEGMENTS = 64
_CAPSULE_BORDER_SEGMENTS = 32

# ======================================== SYSTEM ========================================
class RenderSystem(System):
    """Système gérant le rendu des entités"""
    phase = UpdatePhase.LATE
    exclusive = True

    def __init__(self):
        self._sprites = {}
        self._shapes = {}
        self._labels = {}
        self._image_cache = {}

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
            raw.anchor_x = int(tr.anchor.x * raw.width)
            raw.anchor_y = int(tr.anchor.y * raw.height)
            group = pipeline.get_group(sr.z * 3 + _ORDER_SPRITE)
            self._sprites[eid] = pyglet.sprite.Sprite(raw, batch=pipeline.batch, group=group)

        sprite = self._sprites[eid]
        sprite.visible = True
        sprite.x = tr.x + sr.offset[0] * tr.scale
        sprite.y = tr.y + sr.offset[1] * tr.scale
        sprite.rotation = tr.rotation
        sprite.scale = tr.scale * sr.image.scale
        sprite.color = sr.tint.rgba8
        sprite.opacity = int(sr.opacity * 255)

        if sprite.image.anchor_x != tr.anchor.x * raw.width or sprite.image.anchor_y != tr.anchor.y * raw.height:
            sprite.image.anchor_x = int(tr.anchor.x * raw.width)
            sprite.image.anchor_y = int(tr.anchor.y * raw.height)

        if sr.image.flip_x or sr.image.flip_y:
            sprite.scale_x = -abs(sprite.scale_x) if sr.image.flip_x else abs(sprite.scale_x)
            sprite.scale_y = -abs(sprite.scale_y) if sr.image.flip_y else abs(sprite.scale_y)

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

        if eid not in self._shapes:
            group = pipeline.get_group(sr.z * 3 + _ORDER_SHAPE)
            self._shapes[eid] = _ShapeRenderer(sr.shape, cx, cy, tr.scale, tr.rotation, sr, pipeline.batch, group)

        self._shapes[eid].update(cx, cy, tr.scale, tr.rotation, sr)

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
        label.color = tc.color.rgba8
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

# ======================================== SHAPE RENDERER ========================================
class _ShapeRenderer:
    """Wrapper unifié pour le rendu d'une shape géométrique"""

    def __init__(self, shape: Shape, cx: float, cy: float, scale: float, rotation: float, sr: ShapeRenderer, batch: Batch, group: Group):
        self._shape = shape
        self._fill = None
        self._border = None
        self._batch = batch
        self._group = group
        self._build(cx, cy, scale, rotation, sr)

    def _build(self, cx: float, cy: float, scale: float, rotation: float, sr: ShapeRenderer):
        """Instancie fill et border selon la config du ShapeRenderer"""
        if sr.filling:
            self._fill = _build_fill(self._shape, cx, cy, scale, rotation, sr.filling_color, sr.opacity, self._batch, self._group)

        if sr.border_width > 0:
            self._border = _BorderRenderer(self._shape, cx, cy, scale, rotation, sr.border_color, sr.border_width, sr.opacity, self._batch, self._group)

    def update(self, cx: float, cy: float, scale: float, rotation: float, sr: ShapeRenderer):
        """Met à jour position, scale, couleurs et visibilité"""
        if sr.filling and self._fill is None:
            self._fill = _build_fill(self._shape, cx, cy, scale, rotation, sr.filling_color, sr.opacity, self._batch, self._group)
        elif not sr.filling and self._fill is not None:
            self._fill.delete()
            self._fill = None

        if self._fill is not None:
            self._fill.visible = True
            self._fill = _update_fill(self._fill, self._shape, cx, cy, scale, rotation, sr.filling_color, sr.opacity, self._batch, self._group)

        if sr.border_width > 0 and self._border is None:
            self._border = _BorderRenderer(self._shape, cx, cy, scale, rotation, sr.border_color, sr.border_width, sr.opacity, self._batch, self._group)
        elif sr.border_width == 0 and self._border is not None:
            self._border.delete()
            self._border = None

        if self._border is not None:
            self._border.update(self._shape, cx, cy, scale, rotation, sr.border_color, sr.border_width, sr.opacity)

    @property
    def visible(self) -> bool:
        """Renvoie la visibilité du renderer"""
        f = self._fill.visible if self._fill else True
        b = self._border.visible if self._border else True
        return f or b

    @visible.setter
    def visible(self, v: bool):
        """Fixe la visibilité du renderer"""
        if self._fill:
            self._fill.visible = v
        if self._border:
            self._border.visible = v

    def delete(self):
        """Supprime les ressources pyglet du renderer"""
        if self._fill:
            self._fill.delete()
        if self._border:
            self._border.delete()

# ======================================== BORDER RENDERER ========================================
class _BorderRenderer:
    """Bordure d'une shape via GL_LINE_LOOP sur des vertices monde"""

    def __init__(self, shape: Shape, cx: float, cy: float, scale: float, rotation: float, color: Color, width: int, opacity: float, batch: Batch, group: Group):
        self._vlist = None
        self._n = 0
        self._visible = True
        self._width = width
        self._batch = batch
        self._group = group
        self._build(shape, cx, cy, scale, rotation, color, width, opacity)

    def _build(self, shape: Shape, cx: float, cy: float, scale: float, rotation: float, color: Color, width: int, opacity: float):
        """Construit la vertex list GL_LINE_LOOP"""
        pts = _border_vertices(shape, cx, cy, scale, rotation)
        self._n = len(pts)
        flat = [c for p in pts for c in p]
        r, g, b, a = color.rgba8
        a = int(opacity * 255)
        pyglet.gl.glLineWidth(width)
        self._vlist = self._batch.add(
            self._n, pyglet.gl.GL_LINE_LOOP, self._group,
            ('v2f', flat),
            ('c4B', (r, g, b, a) * self._n)
        )

    def update(self, shape: Shape, cx: float, cy: float, scale: float, rotation: float, color: Color, width: int, opacity: float):
        """Met à jour la bordure"""
        if self._vlist is None:
            return
        pts = _border_vertices(shape, cx, cy, scale, rotation)
        flat = [c for p in pts for c in p]
        self._vlist.vertices[:] = flat
        r, g, b, a = color.rgba8
        a = int(opacity * 255)
        self._vlist.colors[:] = (r, g, b, a) * self._n
        if width != self._width:
            pyglet.gl.glLineWidth(width)
            self._width = width

    @property
    def visible(self) -> bool:
        """Renvoie la visibilité de la bordure"""
        return self._visible

    @visible.setter
    def visible(self, v: bool):
        """Fixe la visibilité de la bordure"""
        if self._vlist is None:
            return
        self._visible = v
        if not v:
            self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    def delete(self):
        """Supprime la vertex list"""
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None

# ======================================== CAPSULE RENDERER ========================================
class _CapsuleRenderer:
    """
    Capsule pyglet composite : deux cercles + un polygone central roté

    Args:
        cx(float): centre monde horizontal
        cy(float): centre monde vertical
        radius(float): rayon des demi-cercles
        spine(float): longueur du segment central
        rotation(float): angle en degrés
        color(Color): couleur
        opacity(float): opacité [0.0; 1.0]
        batch(Batch): batch pyglet
        group(Group): group pyglet
    """

    def __init__(self, cx: float, cy: float, radius: float, spine: float, rotation: float, color: Color, opacity: float, batch: Batch, group: Group):
        self._batch = batch
        self._group = group
        ax, ay, bx, by = _capsule_centers(cx, cy, spine, rotation)
        rect_pts = _capsule_rect_vertices(ax, ay, bx, by, radius)
        rgba = color.rgba8
        self._top = pyglet.shapes.Circle(ax, ay, radius, color=rgba, batch=batch, group=group)
        self._bottom = pyglet.shapes.Circle(bx, by, radius, color=rgba, batch=batch, group=group)
        self._rect = pyglet.shapes.Polygon(*rect_pts, color=rgba, batch=batch, group=group)
        self._set_opacity(opacity)

    def update(self, cx: float, cy: float, radius: float, spine: float, rotation: float, color: Color, opacity: float):
        """Met à jour la position, taille, couleur et opacité"""
        ax, ay, bx, by = _capsule_centers(cx, cy, spine, rotation)
        rect_pts = _capsule_rect_vertices(ax, ay, bx, by, radius)
        rgba = color.rgba8
        self._top.x = ax
        self._top.y = ay
        self._top.radius = radius
        self._top.color = rgba
        self._bottom.x = bx
        self._bottom.y = by
        self._bottom.radius = radius
        self._bottom.color = rgba
        self._rect.delete()
        self._rect = pyglet.shapes.Polygon(*rect_pts, color=rgba, batch=self._batch, group=self._group)
        self._set_opacity(opacity)

    def _set_opacity(self, opacity: float):
        """Fixe l'opacité sur les trois composants"""
        v = int(opacity * 255)
        self._top.opacity = v
        self._bottom.opacity = v
        self._rect.opacity = v

    @property
    def visible(self) -> bool:
        """Renvoie la visibilité du renderer capsule"""
        return self._top.visible

    @visible.setter
    def visible(self, v: bool):
        """Fixe la visibilité du renderer capsule"""
        self._top.visible = v
        self._bottom.visible = v
        self._rect.visible = v

    def delete(self):
        """Supprime les ressources pyglet"""
        self._top.delete()
        self._bottom.delete()
        self._rect.delete()

# ======================================== FILL HELPERS ========================================
def _build_fill(shape: Shape, cx: float, cy: float, scale: float, rotation: float, color: Color, opacity: float, batch: Batch, group: Group) -> object:
    """Instancie le fill pyglet adapté au type de shape"""
    rgba = color.rgba8

    if isinstance(shape, VertexShape):
        pts = [tuple(v) for v in shape.world_vertices(cx, cy, scale, rotation)]
        fill = pyglet.shapes.Polygon(*pts, color=rgba, batch=batch, group=group)
        fill.opacity = int(opacity * 255)
        return fill

    if isinstance(shape, Circle):
        cx_, cy_, r_ = shape.world_transform(cx, cy, scale, rotation)
        fill = pyglet.shapes.Circle(cx_, cy_, r_, color=rgba, batch=batch, group=group)
        fill.opacity = int(opacity * 255)
        return fill

    if isinstance(shape, Ellipse):
        cx_, cy_, rx, ry, angle = shape.world_transform(cx, cy, scale, rotation)
        fill = pyglet.shapes.Ellipse(cx_, cy_, rx, ry, color=rgba, batch=batch, group=group)
        fill.rotation = angle
        fill.opacity = int(opacity * 255)
        return fill

    if isinstance(shape, Capsule):
        ax, ay, bx, by, r_ = shape.world_transform(cx, cy, scale, rotation)
        spine = math.dist((ax, ay), (bx, by))
        return _CapsuleRenderer(cx, cy, r_, spine, rotation, color, opacity, batch, group)

    return None

def _update_fill(fill: object, shape: Shape, cx: float, cy: float, scale: float, rotation: float, color: Color, opacity: float, batch: Batch, group: Group) -> object:
    """Met à jour le fill pyglet existant — retourne le fill (potentiellement recréé)"""
    rgba = color.rgba8
    a = int(opacity * 255)

    if isinstance(shape, VertexShape):
        pts = [tuple(v) for v in shape.world_vertices(cx, cy, scale, rotation)]
        fill.delete()
        fill = pyglet.shapes.Polygon(*pts, color=rgba, batch=batch, group=group)
        fill.opacity = a
        return fill

    if isinstance(shape, Circle):
        cx_, cy_, r_ = shape.world_transform(cx, cy, scale, rotation)
        fill.x = cx_
        fill.y = cy_
        fill.radius = r_
        fill.color = rgba
        fill.opacity = a
        return fill

    if isinstance(shape, Ellipse):
        cx_, cy_, rx, ry, angle = shape.world_transform(cx, cy, scale, rotation)
        fill.x = cx_
        fill.y = cy_
        fill.a = rx
        fill.b = ry
        fill.rotation = angle
        fill.color = rgba
        fill.opacity = a
        return fill

    if isinstance(shape, Capsule):
        ax, ay, bx, by, r_ = shape.world_transform(cx, cy, scale, rotation)
        spine = math.dist((ax, ay), (bx, by))
        fill.update(cx, cy, r_, spine, rotation, color, opacity)
        return fill

    return fill

# ======================================== BORDER HELPERS ========================================
def _border_vertices(shape: Shape, cx: float, cy: float, scale: float, rotation: float) -> list[tuple[float, float]]:
    """Génère les vertices monde pour le GL_LINE_LOOP de la bordure"""
    if isinstance(shape, VertexShape):
        return [tuple(v) for v in shape.world_vertices(cx, cy, scale, rotation)]

    if isinstance(shape, Circle):
        _, _, r = shape.world_transform(cx, cy, scale, rotation)
        return _circle_vertices(cx, cy, r, _CIRCLE_BORDER_SEGMENTS)

    if isinstance(shape, Ellipse):
        _, _, rx, ry, angle = shape.world_transform(cx, cy, scale, rotation)
        return _ellipse_vertices(cx, cy, rx, ry, angle, _ELLIPSE_BORDER_SEGMENTS)

    if isinstance(shape, Capsule):
        ax, ay, bx, by, r = shape.world_transform(cx, cy, scale, rotation)
        return _capsule_border_vertices(ax, ay, bx, by, r, _CAPSULE_BORDER_SEGMENTS)
    return []

def _circle_vertices(cx: float, cy: float, r: float, n: int) -> list[tuple[float, float]]:
    """Génère N vertices sur le périmètre d'un cercle"""
    step = 360.0 / n
    return [
        (cx + r * math.cos(math.radians(i * step)),
         cy + r * math.sin(math.radians(i * step)))
        for i in range(n)
    ]

def _ellipse_vertices(cx: float, cy: float, rx: float, ry: float, angle: float, n: int) -> list[tuple[float, float]]:
    """Génère N vertices sur le périmètre d'une ellipse rotée"""
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    step = 360.0 / n
    pts = []
    for i in range(n):
        t = math.radians(i * step)
        lx = rx * math.cos(t)
        ly = ry * math.sin(t)
        pts.append((
            cx + lx * cos_a - ly * sin_a,
            cy + lx * sin_a + ly * cos_a
        ))
    return pts

def _capsule_border_vertices(ax: float, ay: float, bx: float, by: float, r: float, n: int) -> list[tuple[float, float]]:
    """Génère les vertices du contour d'une capsule rotée"""
    dx = bx - ax
    dy = by - ay
    angle = math.atan2(dy, dx)
    perp = angle + math.pi * 0.5
    pts = []
    for i in range(n + 1):
        t = perp + math.pi * i / n
        pts.append((ax + r * math.cos(t), ay + r * math.sin(t)))
    for i in range(n + 1):
        t = perp + math.pi + math.pi * i / n
        pts.append((bx + r * math.cos(t), by + r * math.sin(t)))
    return pts

# ======================================== CAPSULE INTERNALS ========================================
def _capsule_centers(cx: float, cy: float, spine: float, rotation: float) -> tuple[float, float, float, float]:
    """Calcule les deux centres des demi-cercles d'une capsule"""
    rad = math.radians(rotation)
    sin_r = math.sin(rad)
    cos_r = math.cos(rad)
    half = spine * 0.5
    return cx - sin_r * half, cy + cos_r * half, cx + sin_r * half, cy - cos_r * half

def _capsule_rect_vertices(ax: float, ay: float, bx: float, by: float, r: float) -> list[tuple[float, float]]:
    """Calcule les 4 sommets du rectangle central d'une capsule"""
    dx = bx - ax
    dy = by - ay
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return [(ax - r, ay - r), (ax + r, ay - r), (ax + r, ay + r), (ax - r, ay + r)]
    nx = -dy / length * r
    ny = dx / length * r
    return [
        (ax + nx, ay + ny),
        (ax - nx, ay - ny),
        (bx - nx, by - ny),
        (bx + nx, by + ny),
    ]

# ======================================== WORLD CENTER ========================================
def _world_center(shape: Shape, tr: Transform, offset: tuple[float, float]) -> tuple[float, float]:
    """
    Calcule le centre géométrique monde en tenant compte de l'anchor

    Args:
        shape(Shape): shape locale
        tr(Transform): transform de l'entité
        offset(tuple[float, float]): offset du ShapeRenderer
    """
    x_min, y_min, x_max, y_max = shape.bounding_box
    anchor_x = x_min + tr.anchor.x * (x_max - x_min)
    anchor_y = y_min + tr.anchor.y * (y_max - y_min)
    cx = tr.x - anchor_x * tr.scale + offset[0] * tr.scale
    cy = tr.y - anchor_y * tr.scale + offset[1] * tr.scale
    return cx, cy