# ======================================== IMPORTS ========================================
from __future__ import annotations

from ._pipeline import Pipeline
from ..abc import Shape, VertexShape
from ..shape import Capsule, Circle, Ellipse
from ..asset import Color

import pyglet
import pyglet.shapes
import pyglet.gl
from pyglet.graphics import Batch, Group

import math

# ======================================== CONSTANTS ========================================
_CIRCLE_BORDER_SEGMENTS = 64
_ELLIPSE_BORDER_SEGMENTS = 64
_CAPSULE_BORDER_SEGMENTS = 32

# ======================================== PUBLIC ========================================
class PygletShapeRenderer:
    """
    Renderer pyglet unifié pour une shape géométrique.
    Gère fill et border, création et mise à jour des vertex lists.

    Args:
        shape(Shape): shape à rendre
        cx(float): centre monde horizontal
        cy(float): centre monde vertical
        scale(float): échelle
        rotation(float): rotation en degrés
        color(Color): couleur de remplissage
        opacity(float): opacité [0.0; 1.0]
        pipeline(Pipeline): pipeline active
        z(int): z-order
        border_color(Color, optional): couleur de la bordure
        border_width(int, optional): épaisseur de la bordure
    """
    __slots__ = ("_shape", "_fill", "_border", "_batch", "_group")

    def __init__(
        self,
        shape: Shape,
        cx: float,
        cy: float,
        scale: float,
        rotation: float,
        color: Color,
        opacity: float,
        pipeline: Pipeline,
        z: int,
        border_color: Color = None,
        border_width: int = 0,
    ):
        self._shape = shape
        self._batch = pipeline.batch
        self._group = pipeline.get_group(z)
        self._fill = None
        self._border = None
        self._build(cx, cy, scale, rotation, color, opacity, border_color, border_width)

    # ======================================== BUILD ========================================
    def _build(
        self,
        cx: float, cy: float, scale: float, rotation: float,
        color: Color, opacity: float,
        border_color: Color, border_width: int,
    ):
        self._fill = _build_fill(self._shape, cx, cy, scale, rotation, color, opacity, self._batch, self._group)

        if border_width > 0 and border_color is not None:
            self._border = _BorderRenderer(
                self._shape, cx, cy, scale, rotation,
                border_color, border_width, opacity,
                self._batch, self._group,
            )

    # ======================================== UPDATE ========================================
    def update(
        self,
        cx: float, cy: float,
        scale: float, rotation: float,
        color: Color, opacity: float,
        border_color: Color = None,
        border_width: int = 0,
    ):
        """Met à jour position, scale, couleurs et opacité"""
        if self._fill is not None:
            self._fill.visible = True
            self._fill = _update_fill(
                self._fill, self._shape, cx, cy, scale, rotation,
                color, opacity, self._batch, self._group,
            )

        if border_width > 0 and border_color is not None:
            if self._border is None:
                self._border = _BorderRenderer(
                    self._shape, cx, cy, scale, rotation,
                    border_color, border_width, opacity,
                    self._batch, self._group,
                )
            else:
                self._border.update(self._shape, cx, cy, scale, rotation, border_color, border_width, opacity)
        elif self._border is not None:
            self._border.delete()
            self._border = None

    # ======================================== GETTERS ========================================
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité du renderer"""
        f = self._fill.visible if self._fill else True
        b = self._border.visible if self._border else True
        return f or b
    
    @property
    def z(self) -> int:
        """Renvoie l'ordre de rendu"""
        return self._z

    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, v: bool):
        """Fixe la visibilité du renderer"""
        if self._fill:
            self._fill.visible = v
        if self._border:
            self._border.visible = v

    # ======================================== DELETE ========================================
    def delete(self):
        """Libère toutes les ressources pyglet"""
        if self._fill:
            self._fill.delete()
            self._fill = None
        if self._border:
            self._border.delete()
            self._border = None

# ======================================== BORDER RENDERER ========================================
class _BorderRenderer:
    """Bordure d'une shape via GL_LINE_LOOP"""
    __slots__ = ("_vlist", "_n", "_visible", "_width", "_batch", "_group")

    def __init__(
        self,
        shape: Shape, cx: float, cy: float, scale: float, rotation: float,
        color: Color, width: int, opacity: float,
        batch: Batch, group: Group,
    ):
        self._vlist = None
        self._n = 0
        self._visible = True
        self._width = width
        self._batch = batch
        self._group = group
        self._build(shape, cx, cy, scale, rotation, color, width, opacity)

    def _build(self, shape, cx, cy, scale, rotation, color, width, opacity):
        pts = _border_vertices(shape, cx, cy, scale, rotation)
        self._n = len(pts)
        flat = [c for p in pts for c in p]
        r, g, b, a = color.rgba8
        a = int(opacity * 255)
        pyglet.gl.glLineWidth(width)
        self._vlist = self._batch.add(
            self._n, pyglet.gl.GL_LINE_LOOP, self._group,
            ('v2f', flat),
            ('c4B', (r, g, b, a) * self._n),
        )

    def update(self, shape, cx, cy, scale, rotation, color, width, opacity):
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
        return self._visible

    @visible.setter
    def visible(self, v: bool):
        if self._vlist is None:
            return
        self._visible = v
        if not v:
            self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    def delete(self):
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None

# ======================================== CAPSULE RENDERER ========================================
class _CapsuleRenderer:
    """Capsule pyglet composite : deux cercles + rectangle central"""
    __slots__ = ("_top", "_bottom", "_rect", "_batch", "_group")

    def __init__(self, cx, cy, radius, spine, rotation, color, opacity, batch, group):
        self._batch = batch
        self._group = group
        ax, ay, bx, by = _capsule_centers(cx, cy, spine, rotation)
        rect_pts = _capsule_rect_vertices(ax, ay, bx, by, radius)
        rgba = color.rgba8
        self._top = pyglet.shapes.Circle(ax, ay, radius, color=rgba, batch=batch, group=group)
        self._bottom = pyglet.shapes.Circle(bx, by, radius, color=rgba, batch=batch, group=group)
        self._rect = pyglet.shapes.Polygon(*rect_pts, color=rgba, batch=batch, group=group)
        self._set_opacity(opacity)

    def update(self, cx, cy, radius, spine, rotation, color, opacity):
        ax, ay, bx, by = _capsule_centers(cx, cy, spine, rotation)
        rect_pts = _capsule_rect_vertices(ax, ay, bx, by, radius)
        rgba = color.rgba8
        self._top.x = ax; self._top.y = ay; self._top.radius = radius; self._top.color = rgba
        self._bottom.x = bx; self._bottom.y = by; self._bottom.radius = radius; self._bottom.color = rgba
        self._rect.delete()
        self._rect = pyglet.shapes.Polygon(*rect_pts, color=rgba, batch=self._batch, group=self._group)
        self._set_opacity(opacity)

    def _set_opacity(self, opacity: float):
        v = int(opacity * 255)
        self._top.opacity = v
        self._bottom.opacity = v
        self._rect.opacity = v

    @property
    def visible(self) -> bool:
        return self._top.visible

    @visible.setter
    def visible(self, v: bool):
        self._top.visible = v
        self._bottom.visible = v
        self._rect.visible = v

    def delete(self):
        self._top.delete()
        self._bottom.delete()
        self._rect.delete()


# ======================================== FILL HELPERS ========================================
def _build_fill(shape, cx, cy, scale, rotation, color, opacity, batch, group):
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


def _update_fill(fill, shape, cx, cy, scale, rotation, color, opacity, batch, group):
    """Met à jour le fill pyglet existant"""
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
        fill.x = cx_; fill.y = cy_; fill.radius = r_; fill.color = rgba; fill.opacity = a
        return fill

    if isinstance(shape, Ellipse):
        cx_, cy_, rx, ry, angle = shape.world_transform(cx, cy, scale, rotation)
        fill.x = cx_; fill.y = cy_; fill.a = rx; fill.b = ry
        fill.rotation = angle; fill.color = rgba; fill.opacity = a
        return fill

    if isinstance(shape, Capsule):
        ax, ay, bx, by, r_ = shape.world_transform(cx, cy, scale, rotation)
        spine = math.dist((ax, ay), (bx, by))
        fill.update(cx, cy, r_, spine, rotation, color, opacity)
        return fill

    return fill

# ======================================== BORDER HELPERS ========================================
def _border_vertices(shape, cx, cy, scale, rotation):
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

def _circle_vertices(cx, cy, r, n):
    step = 360.0 / n
    return [
        (cx + r * math.cos(math.radians(i * step)),
         cy + r * math.sin(math.radians(i * step)))
        for i in range(n)
    ]

def _ellipse_vertices(cx, cy, rx, ry, angle, n):
    rad = math.radians(angle)
    cos_a = math.cos(rad); sin_a = math.sin(rad)
    step = 360.0 / n
    pts = []
    for i in range(n):
        t = math.radians(i * step)
        lx = rx * math.cos(t); ly = ry * math.sin(t)
        pts.append((cx + lx * cos_a - ly * sin_a, cy + lx * sin_a + ly * cos_a))
    return pts


def _capsule_border_vertices(ax, ay, bx, by, r, n):
    dx = bx - ax; dy = by - ay
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
def _capsule_centers(cx, cy, spine, rotation):
    rad = math.radians(rotation)
    half = spine * 0.5
    return (
        cx - math.sin(rad) * half, cy + math.cos(rad) * half,
        cx + math.sin(rad) * half, cy - math.cos(rad) * half,
    )


def _capsule_rect_vertices(ax, ay, bx, by, r):
    dx = bx - ax; dy = by - ay
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return [(ax - r, ay - r), (ax + r, ay - r), (ax + r, ay + r), (ax - r, ay + r)]
    nx = -dy / length * r; ny = dx / length * r
    return [(ax + nx, ay + ny), (ax - nx, ay - ny), (bx - nx, by - ny), (bx + nx, by + ny)]