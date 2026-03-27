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

from typing import Callable
import math
import numpy as np

# ======================================== CONSTANTS ========================================
_UNSET = object()

_CIRCLE_BORDER_SEGMENTS = 64
_ELLIPSE_BORDER_SEGMENTS = 64
_CAPSULE_BORDER_SEGMENTS = 32

# ======================================== PUBLIC ========================================
class PygletShapeRenderer:
    """
    Renderer pyglet unifié pour une shape géométrique

    Args:
        shape(Shape): shape à rendre
        cx(float, optional): centre monde horizontal
        cy(float, optional): centre monde vertical
        scale(float, optional): échelle
        rotation(float, optional): rotation en degrés
        filling(bool, optional): remplissage
        color(Color, optional): couleur de remplissage
        border_width(int, optional): épaisseur de la bordure
        border_color(Color, optional): couleur de la bordure
        opacity(float, optional): opacité [0.0; 1.0]
        z(int, optional): z-order
        pipeline(Pipeline, optional): pipeline de rendu
    """
    __slots__ = ("_shape", "_cx", "_cy", "_scale", "_rotation", "_filling", "_color", "_border_width", "_border_color", "_opacity", "_z", "_pipeline", "_fill", "_border")

    def __init__(
        self,
        shape: Shape,
        cx: float = 0.0,
        cy: float = 0.0,
        scale: float = 1.0,
        rotation: float = 0.0,
        filling: bool = True,
        color: Color = None,
        border_width: int = 0,
        border_color: Color = None,
        opacity: float = 1.0,
        z: int = 0,
        pipeline: Pipeline = None
    ):
        # Paramètres
        self._shape: Shape = shape
        self._cx: float = cx
        self._cy: float = cy
        self._scale: float = scale
        self._rotation: float = rotation
        self._filling: bool = filling
        self._color: Color = color
        self._border_width: int = border_width
        self._border_color: Color = border_color
        self._opacity: float = opacity

        # Rendering
        self._z: int = z
        self._pipeline: Pipeline = pipeline

        # Renderers
        self._fill: _FillRenderer = None
        self._border: _BorderRenderer = None
        self._build()

    # ======================================== BUILD ========================================
    def _build(self) -> None:
        """Construit les objets pyglet"""
        if self._filling and self._color is not None:
            self._fill = _FillRenderer(self._shape, self._cx, self._cy, self._scale, self._rotation, self._color, self._opacity, self._z, self._pipeline)

        if self._border_width > 0 and self._border_color is not None:
            self._border = _BorderRenderer(self._shape, self._cx, self._cy, self._scale, self._rotation, self._border_width, self._border_color, self._opacity, self._z, self._pipeline)

    # ======================================== GETTERS ========================================
    @property
    def shape(self) -> Shape:
        """Renvoie la forme"""
        return self._shape
    
    @property
    def position(self) -> tuple[float, float]:
        """Renvoie la position"""
        return (self._cx, self._cy)
    
    @property
    def cx(self) -> float:
        """Renvoie la position horizontale"""
        return self._cx
    
    @property
    def cy(self) -> float:
        """Renoie la position verticale"""
        return self._cy
    
    @property
    def scale(self) -> float:
        """Renvoie le facteur de redimensionnement"""
        return self._scale

    @property
    def rotation(self) -> float:
        """Renvoie la rotation en degrés"""
        return self._rotation

    @property
    def filling(self) -> float:
        """Vérifie le remplissage"""
        return self._filling
    
    @property
    def color(self) -> Color:
        """Renvoie la couleur de remplissage"""
        return self._color
    
    @property
    def border_width(self) -> int:
        """Renvoie l'épaisseur de la bordure"""
        return self._border_width
    
    @property
    def border_color(self) -> Color:
        """Renvoie la couleur de la bordure"""
        return self._border_color
    
    @property
    def opacity(self) -> float:
        """Renvoie l'opacité"""
        return self._opacity
    
    @property
    def z(self) -> int:
        """Renvoie le zorder"""
        return self._z
    
    @property
    def pipeline(self) -> Pipeline:
        """Renvoie la pipeline de rendu"""
        return self._pipeline
    
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        if self._fill:
            return self._fill.visible
        if self._border:
            return self._border.visible
        return False
    
    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Active ou désactive la visibilité"""
        if self._fill:
            self._fill.visible = value
        if self._border:
            self._border.visible = value

    # ======================================== PREDICATES ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self.visible and ((self._filling and self._color is not None) or (self._border_width > 0 and self._border_color is not None))

    # ======================================== LIFE CYCLE ========================================
    def update(self, **kwargs) -> None:
        """
        Met à jour le rendu de forme pyglet

        Args:
            cx(float, optional): position horizontale
            cy(float, optional): position verticale
            scale(float, optional): facteur de redimensionnement
            rotation(float, optional): rotation en degrés
            filling(bool, optional): remplissage
            color(Color, optional): couleur de remplissage
            border_width(int, optional): épaisseur de bordure
            border_color(Color, optional): couleur de bordure
            opacity(float, optional): opacité
            z(int, optional): zorder
            pipeline(Pipeline, optional): pipeline de rendu
        """
        # Actualisation des paramètres
        changes: list[str] = []
        for key, value in kwargs.items():
            current_attr = getattr(self, f"_{key}", _UNSET)
            if value != current_attr and current_attr is not _UNSET:
                setattr(self, f"_{key}", value)
                changes.append(key)

        # Remplissage
        if self._filling:
            if self._fill is not None:
                self._fill.update(self, changes)
            elif self._color is not None:
                self._fill = _FillRenderer(self._shape, self._cx, self._cy, self._scale, self._rotation, self._color, self._opacity, self._z, self._pipeline)
        elif self._fill is not None:
            self._fill.delete()
            self._fill = None

        # Bordure
        if self._border_width > 0:
            if self._border is not None:
                self._border.update(self, changes)
            elif self._border_color is not None:
                self._border = _BorderRenderer(self._shape, self._cx, self._cy, self._scale, self._rotation, self._border_width, self._border_color, self._opacity, self._z, self._pipeline)
        elif self._border is not None:
            self._border.delete()
            self._border = None

    def delete(self) -> None:
        """Libère toutes les ressources pyglet"""
        if self._fill:
            self._fill.delete()
            self._fill = None
        if self._border:
            self._border.delete()
            self._border = None

# ======================================== FILLING RENDERER ========================================
class _FillRenderer:
    """Remplissage d'une shape"""
    __slots__ = ("_gl_shape")

    def __init__(
            self,
            shape: Shape,
            cx: float,
            cy: float,
            scale: float,
            rotation: float,
            color: Color,
            opacity: float,
            z: int,
            pipeline: Pipeline,
        ):
        self._gl_shape: pyglet.shapes.ShapeBase = None
        self._build(shape, cx, cy, scale, rotation, color, opacity, z, pipeline)

    # ======================================== BUILD ========================================
    def _build(
            self,
            shape: Shape,
            cx: float,
            cy: float,
            scale: float,
            rotation: float,
            color: Color,
            opacity: float,
            z: int,
            pipeline: Pipeline,
        ) -> None:
        """Construit le remplissage"""
        rgba = color.rgba8
        a = int(opacity * 255)

        if isinstance(shape, VertexShape):
            pts = [tuple(v) for v in shape.world_vertices(cx, cy, scale, 0)]
            self._gl_shape = pyglet.shapes.Polygon(*pts, color=rgba, batch=pipeline.batch, group=pipeline.get_group(z=z))
            self._gl_shape.rotation = rotation

        elif isinstance(shape, Circle):
            cx_, cy_, r_ = shape.world_transform(cx, cy, scale, 0)
            self._gl_shape = pyglet.shapes.Circle(cx_, cy_, r_, color=rgba, batch=pipeline.batch, group=pipeline.get_group(z=z))

        elif isinstance(shape, Ellipse):
            cx_, cy_, rx, ry, _ = shape.world_transform(cx, cy, scale, 0)
            self._gl_shape = pyglet.shapes.Ellipse(cx_, cy_, rx, ry, color=rgba, batch=pipeline.batch, group=pipeline.get_group(z=z))
            self._gl_shape.rotation = rotation

        elif isinstance(shape, Capsule):
            ax, ay, bx, by, r_ = shape.world_transform(cx, cy, scale, 0)
            spine = math.dist((ax, ay), (bx, by))
            self._gl_shape = _CapsuleRenderer(cx, cy, r_, spine, rotation=rotation, color=rgba, batch=pipeline.batch, group=pipeline.get_group(z=z))

        self._gl_shape.opacity = a
        self._gl_shape.z = z
    
    # ======================================== GETTERS ========================================
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        return self._gl_shape.visible

    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Fixe la visibilité"""
        self._gl_shape.visible = value
    
    # ======================================== LIFE CYCLE ========================================
    def update(self, psr: PygletShapeRenderer, changes: list[str]) -> None:
        """Actualisation du remplissage"""
        for key in changes:
            handler: Callable = getattr(self, f"handle_{key}", None)
            if handler:
                handler(psr)

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        self._gl_shape.delete()
    
    # ======================================== HANDLERS ========================================
    def handle_cx(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la position horizontale"""
        self._gl_shape.x = psr.cx

    def handle_cy(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la position verticale"""
        self._gl_shape.y = psr.cy

    def handle_scale(self, psr: PygletShapeRenderer) -> None:
        """Actualisation du facteur de redimensionnement"""
        if isinstance(psr.shape, Circle):
            self._gl_shape.radius = psr.shape.radius * psr.scale
        elif isinstance(psr.shape, Ellipse):
            self._gl_shape.a = psr.shape.rx * psr.scale
            self._gl_shape.b = psr.shape.ry * psr.scale
        else:
            self._build(psr.shape, psr.cx, psr.cy, psr.scale, psr.rotation, psr.color, psr.opacity, psr.z, psr.pipeline)        

    def handle_rotation(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'angle de rotation"""
        self._gl_shape.rotation = psr.rotation

    def handle_color(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la couleur de remplissage"""
        self._gl_shape.color = psr.color.rgba8

    def handle_opacity(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'opacité"""
        self._gl_shape.opacity = int(255 * psr.opacity)
    
    def handle_z(self, psr: PygletShapeRenderer) -> None:
        """Actualisation du z-order"""
        self._gl_shape.z = psr.z
    
    def handle_pipeline(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la pipeline de rendu"""
        pipeline = psr.pipeline
        self._gl_shape.batch = pipeline.batch
        self._gl_shape.group = pipeline.get_group(z=psr.z)

# ======================================== BORDER RENDERER ========================================
class _BorderRenderer:
    """Bordure d'une shape"""
    __slots__ = ("_vlist", "_n", "_width", "_batch", "_group", "_local_contour", "_visible")

    def __init__(
        self,
        shape: Shape,
        cx: float,
        cy: float,
        scale: float,
        rotation: float,
        width: int,
        color: Color,
        opacity: float,
        z: int,
        pipeline: Pipeline,
    ):
        self._vlist = None
        self._n: int = 0
        self._width: int = width
        self._batch: Batch = None
        self._group: Group = None
        self._visible: bool = True
        self._local_contour: np.ndarray = _local_contour(shape)
        self._build(shape, cx, cy, scale, rotation, width, color, opacity, z, pipeline)

    # ======================================== BUILD ========================================
    def _build(
        self,
        shape: Shape,
        cx: float,
        cy: float,
        scale: float,
        rotation: float,
        width: int,
        color: Color,
        opacity: float,
        z: int,
        pipeline: Pipeline,
    ) -> None:
        """Construction de la bordure"""
        if self._vlist is not None:
            self._vlist.delete()

        self._batch = pipeline.batch
        self._group = pipeline.get_group(z=z)
        self._width = width

        strip = self._world_strip(cx, cy, scale, rotation, width)
        self._n = len(strip)
        flat = strip.flatten().tolist()

        r, g, b, _ = color.rgba8
        a = int(opacity * 255)

        self._vlist = self._batch.add(
            self._n, pyglet.gl.GL_TRIANGLE_STRIP, self._group,
            ('v2f', flat),
            ('c4B', (r, g, b, a) * self._n),
        )

    def _world_strip(self, cx: float, cy: float, scale: float, rotation: float, width: float) -> np.ndarray:
        """Contour monde + strip"""
        world = _apply_transform(self._local_contour, cx, cy, scale, rotation)
        return _build_strip(world, width)

    def _refresh_vertices(self, psr: PygletShapeRenderer) -> None:
        """Réactualise les arrêtes"""
        strip = self._world_strip(psr.cx, psr.cy, psr.scale, psr.rotation, psr.border_width)
        self._vlist.vertices[:] = strip.flatten().tolist()
    
    # ======================================== GETTERS ========================================
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        return self._visible

    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Fixe la visibilité"""
        if value == self._visible:
            return
        self._visible = value
        target_batch = self._batch if value else None
        self._vlist.migrate(target_batch, pyglet.gl.GL_TRIANGLE_STRIP, self._group, ('v2f', 'c4B'))

    # ======================================== LIFE CYCLE ========================================
    def update(self, psr: PygletShapeRenderer, changes: list[str]) -> None:
        for key in changes:
            handler: Callable = getattr(self, f"handle_{key}", None)
            if handler:
                handler(psr)

    def delete(self) -> None:
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None

    # ======================================== HANDLERS ========================================
    def handle_cx(self, psr: PygletShapeRenderer) -> None:
        self._refresh_vertices(psr)

    def handle_cy(self, psr: PygletShapeRenderer) -> None:
        self._refresh_vertices(psr)

    def handle_scale(self, psr: PygletShapeRenderer) -> None:
        self._refresh_vertices(psr)

    def handle_rotation(self, psr: PygletShapeRenderer) -> None:
        self._refresh_vertices(psr)

    def handle_border_width(self, psr: PygletShapeRenderer) -> None:
        self._width = psr.border_width
        self._refresh_vertices(psr)

    def handle_border_color(self, psr: PygletShapeRenderer) -> None:
        r, g, b, _ = psr.border_color.rgba8
        a = int(psr.opacity * 255)
        self._vlist.colors[:] = (r, g, b, a) * self._n

    def handle_opacity(self, psr: PygletShapeRenderer) -> None:
        r, g, b, _ = psr.border_color.rgba8
        a = int(psr.opacity * 255)
        self._vlist.colors[:] = (r, g, b, a) * self._n

    def handle_z(self, psr: PygletShapeRenderer) -> None:
        self._build(psr.shape, psr.cx, psr.cy, psr.scale, psr.rotation,
                    psr.border_width, psr.border_color, psr.opacity, psr.z, psr.pipeline)

    def handle_pipeline(self, psr: PygletShapeRenderer) -> None:
        self._build(psr.shape, psr.cx, psr.cy, psr.scale, psr.rotation,
                    psr.border_width, psr.border_color, psr.opacity, psr.z, psr.pipeline)

# ======================================== CAPSULE RENDERER ========================================
class _CapsuleRenderer:
    """Capsule pyglet composite : deux cercles + rectangle central"""
    __slots__ = ("_x", "_y", "_radius", "_spine", "_rotation", "_color", "_opacity", "_z", "_batch", "_group", "_top", "_bottom", "_rect")
 
    def __init__(
        self,
        x: float,
        y: float,
        radius: float,
        spine: float,
        rotation: float = 0.0,
        color: tuple = (255, 255, 255, 255),
        batch: pyglet.graphics.Batch = None,
        group: pyglet.graphics.Group = None,
    ):
        self._x = x
        self._y = y
        self._radius = radius
        self._spine = spine
        self._rotation = rotation
        self._color = color
        self._opacity = 255
        self._z = 0
        self._batch = batch
        self._group = group
        self._top = None
        self._bottom = None
        self._rect = None
        self._rebuild()
 
    # ======================================== PROPERTIES ========================================
    @property
    def x(self) -> float:
        return self._x
 
    @x.setter
    def x(self, value: float) -> None:
        self._x = value
        self._rebuild()
 
    @property
    def y(self) -> float:
        return self._y
 
    @y.setter
    def y(self, value: float) -> None:
        self._y = value
        self._rebuild()
 
    @property
    def rotation(self) -> float:
        return self._rotation
 
    @rotation.setter
    def rotation(self, value: float) -> None:
        self._rotation = value
        self._rebuild()
 
    @property
    def color(self) -> tuple:
        return self._color
 
    @color.setter
    def color(self, value: tuple) -> None:
        self._color = value
        self._top.color = value
        self._bottom.color = value
        self._rect.color = value
 
    @property
    def opacity(self) -> int:
        return self._opacity
 
    @opacity.setter
    def opacity(self, value: int) -> None:
        self._opacity = value
        self._top.opacity = value
        self._bottom.opacity = value
        self._rect.opacity = value
 
    @property
    def z(self) -> int:
        return self._z
 
    @z.setter
    def z(self, value: int) -> None:
        self._z = value
        self._top.z = value
        self._bottom.z = value
        self._rect.z = value
 
    @property
    def batch(self) -> Batch:
        return self._batch
 
    @batch.setter
    def batch(self, value: Batch) -> None:
        self._batch = value
        self._top.batch = value
        self._bottom.batch = value
        self._rect.batch = value
 
    @property
    def group(self) -> Group:
        return self._group
 
    @group.setter
    def group(self, value: Group) -> None:
        self._group = value
        self._top.group = value
        self._bottom.group = value
        self._rect.group = value

    @property
    def visible(self) -> bool:
        return self._top.visible
    
    @visible.setter
    def visible(self, value: bool) -> None:
        self._top.visible = value
        self._bottom.visible = value
        self._rect.visible = value
 
    # ======================================== LIFE CYCLE ========================================
    def delete(self) -> None:
        self._top.delete()
        self._bottom.delete()
        self._rect.delete()
 
    # ======================================== INTERNALS ========================================
    def _rebuild(self) -> None:
        """Reconstruit les trois primitives à partir de l'état courant"""
        ax, ay, bx, by = _capsule_centers(self._x, self._y, self._spine, self._rotation)
        rect_pts = _capsule_rect_vertices(ax, ay, bx, by, self._radius)
 
        if self._top is None:
            self._top = pyglet.shapes.Circle(ax, ay, self._radius, color=self._color, batch=self._batch, group=self._group)
            self._bottom = pyglet.shapes.Circle(bx, by, self._radius, color=self._color, batch=self._batch, group=self._group)
            self._rect = pyglet.shapes.Polygon(*rect_pts, color=self._color, batch=self._batch, group=self._group)
            self._top.opacity = self._opacity
            self._bottom.opacity = self._opacity
            self._rect.opacity = self._opacity
            self._top.z = self._z
            self._bottom.z = self._z
            self._rect.z = self._z
        else:
            self._top.x = ax
            self._top.y = ay
            self._top.radius = self._radius
            self._bottom.x = bx
            self._bottom.y = by
            self._bottom.radius = self._radius
            self._rect.delete()
            self._rect = pyglet.shapes.Polygon(*rect_pts, color=self._color, batch=self._batch, group=self._group)
            self._rect.opacity = self._opacity
            self._rect.z = self._z
 
# ======================================== BORDER HELPERS ========================================
def _local_contour(shape: Shape) -> np.ndarray:
    """
    Génère le contour local d'une shape (centré sur l'origine, scale=1, rotation=0).
    Retourne un array (N, 2).
    """
    if isinstance(shape, VertexShape):
        return np.array(shape.local_vertices(), dtype=np.float32)
 
    elif isinstance(shape, Circle):
        angles = np.linspace(0, 2 * np.pi, _CIRCLE_BORDER_SEGMENTS, endpoint=False)
        return np.column_stack((np.cos(angles) * shape.radius, np.sin(angles) * shape.radius)).astype(np.float32)
 
    elif isinstance(shape, Ellipse):
        angles = np.linspace(0, 2 * np.pi, _ELLIPSE_BORDER_SEGMENTS, endpoint=False)
        return np.column_stack((np.cos(angles) * shape.rx, np.sin(angles) * shape.ry)).astype(np.float32)
 
    elif isinstance(shape, Capsule):
        return _capsule_local_contour(shape).astype(np.float32)
 
    raise TypeError(f"Shape non supportée : {type(shape)}")
 
 
def _capsule_local_contour(shape: Capsule) -> np.ndarray:
    """Contour local d'une capsule alignée sur l'axe X"""
    half_len = shape.length / 2.0
    r = shape.radius
    half = _CAPSULE_BORDER_SEGMENTS // 2
 
    angles_b = np.linspace(-np.pi / 2, np.pi / 2, half + 1)
    angles_a = np.linspace(np.pi / 2, 3 * np.pi / 2, half + 1)
 
    pts_b = np.column_stack((half_len + r * np.cos(angles_b), r * np.sin(angles_b)))
    pts_a = np.column_stack((-half_len + r * np.cos(angles_a), r * np.sin(angles_a)))
 
    return np.vstack((pts_b, pts_a))
 
 
def _build_strip(contour: np.ndarray, width: float) -> np.ndarray:
    """
    Génère un triangle strip (N+1)*2 points autour d'un contour fermé.
    Retourne un array ((N+1)*2, 2).
    """
    n = len(contour)
    prev_pts = contour[(np.arange(n) - 1) % n]
    next_pts = contour[(np.arange(n) + 1) % n]
 
    def edge_normals(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        d = b - a
        lengths = np.linalg.norm(d, axis=1, keepdims=True)
        lengths = np.where(lengths == 0, 1, lengths)
        d /= lengths
        return np.column_stack((-d[:, 1], d[:, 0]))
 
    n1 = edge_normals(prev_pts, contour)
    n2 = edge_normals(contour, next_pts)
    miter = n1 + n2
    miter_len = np.linalg.norm(miter, axis=1, keepdims=True)
    miter_len = np.where(miter_len == 0, 1, miter_len)
    miter /= miter_len
 
    dot = np.einsum('ij,ij->i', n1, miter).reshape(-1, 1)
    dot = np.where(np.abs(dot) < 0.01, 0.01, dot)
    half = width / 2.0
    miter_dist = np.clip(half / dot, -width * 3, width * 3)
 
    outer = contour + miter * miter_dist
    inner = contour - miter * miter_dist
 
    strip = np.empty(((n + 1) * 2, 2), dtype=np.float32)
    strip[0::2][:n] = outer
    strip[1::2][:n] = inner
    strip[-2] = outer[0]
    strip[-1] = inner[0]
 
    return strip
 
 
def _apply_transform(pts: np.ndarray, cx: float, cy: float, scale: float, rotation: float) -> np.ndarray:
    """Applique translation + scale + rotation à un contour local"""
    rad = math.radians(rotation)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    rot = np.array([[cos_r, -sin_r], [sin_r, cos_r]], dtype=np.float32)
    return (pts * scale) @ rot.T + np.array([cx, cy], dtype=np.float32)
 
# ======================================== CAPSULE HELPERS ========================================
def _capsule_centers(
    cx: float, cy: float, spine: float, rotation: float
) -> tuple[float, float, float, float]:
    """Retourne les centres (ax, ay, bx, by) des deux demi-sphères"""
    rad = math.radians(rotation)
    half = spine * 0.5
    return (
        cx - math.sin(rad) * half, cy + math.cos(rad) * half,
        cx + math.sin(rad) * half, cy - math.cos(rad) * half,
    )
 
 
def _capsule_rect_vertices(
    ax: float, ay: float, bx: float, by: float, r: float
) -> list[tuple[float, float]]:
    """Retourne les 4 coins du rectangle central de la capsule"""
    dx = bx - ax
    dy = by - ay
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return [(ax - r, ay - r), (ax + r, ay - r), (ax + r, ay + r), (ax - r, ay + r)]
    nx = -dy / length * r
    ny = dx / length * r
    return [(ax + nx, ay + ny), (ax - nx, ay - ny), (bx - nx, by - ny), (bx + nx, by + ny)]