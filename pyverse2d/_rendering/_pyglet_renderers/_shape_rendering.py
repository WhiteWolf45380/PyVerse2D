# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...typing import BorderAlign
from ...abc import Shape, VertexShape
from ...shape import Capsule, Circle, Ellipse, RoundedRect
from ...asset import Color

from .._pipeline import Pipeline

import pyglet
import pyglet.shapes
import pyglet.gl
from pyglet.graphics import Batch, Group
from pyglet.graphics.shader import ShaderProgram

from typing import Callable
import math
import numpy as np

# ======================================== CONSTANTS ========================================
_UNSET = object()                                               # élément non défini
_CENTER_DEPS = frozenset({"x", "y", "anchor_x", "anchor_y"})    # paramètres influençant le centre

_CIRCLE_BORDER_SEGMENTS = 64        # précision des cercles
_ELLIPSE_BORDER_SEGMENTS = 64       # précision des ellipses
_CAPSULE_BORDER_SEGMENTS = 32       # précision des capsules
_ROUNDED_RECT_BORDER_SEGMENTS = 16  # Précision des rectangles arrondis

# ======================================== PUBLIC ========================================
class PygletShapeRenderer:
    """
    Renderer pyglet unifié pour une shape géométrique

    Args:
        shape: shape à rendre
        x: position horizontale
        y: position verticale
        anchor_x: ancre relative locale horizontale
        anchor_y: ancre relative locale  verticale
        scale: échelle
        rotation: rotation en degrés
        filling: remplissage
        color: couleur de remplissage
        border_width: épaisseur de la bordure
        border_align: alignement de la bordure
        border_color: couleur de la bordure
        opacity opacité [0.0; 1.0]
        z: z-order
        pipeline: pipeline de rendu
    """
    __slots__ = (
        "_shape",
        "_x", "_y", "_anchor_x", "_anchor_y",
        "_scale", "_rotation",
        "_filling", "_color", "_border_width", "_border_align", "_border_color", "_opacity",
        "_z", "_pipeline"
        "_cx", "_cy",
        "_fill", "_border"
    )

    def __init__(
        self,
        shape: Shape,
        x: float = 0.0,
        y: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
        scale: float = 1.0,
        rotation: float = 0.0,
        filling: bool = True,
        color: Color = None,
        border_width: int = 0,
        border_align: BorderAlign = "center",
        border_color: Color = None,
        opacity: float = 1.0,
        z: int = 0,
        pipeline: Pipeline = None,
    ):
        # Paramètres publics
        self._shape: Shape = shape
        self._x: float = x
        self._y: float = y
        self._anchor_x: float = anchor_x
        self._anchor_y: float = anchor_y
        self._scale: float = scale
        self._rotation: float = rotation
        self._filling: bool = filling
        self._color: Color = color
        self._border_width: int = border_width
        self._border_align: BorderAlign = border_align
        self._border_color: Color = border_color
        self._opacity: float = opacity
        self._z: int = z
        self._pipeline: Pipeline = pipeline

        # Paramètres internes
        self._cx: float = 0.0
        self._cy: float = 0.0
        self._compute_center()

        # Renderers
        self._fill: _FillRenderer = None
        self._border: _BorderRenderer = None
        self._build()

    # ======================================== INTERNALS ========================================
    def _build(self) -> None:
        """Construit les objets pyglet"""
        if self._filling and self._color is not None:
            self._fill = _FillRenderer(
                self._shape,
                self._cx, self._cy,
                self._scale, self._rotation,
                self._color, self._opacity,
                self._z, self._pipeline
            )

        if self._border_width > 0 and self._border_color is not None:
            self._border = _BorderRenderer(
                self._shape,
                self._cx, self._cy,
                self._scale, self._rotation,
                self._border_width, self._border_align,
                self._border_color, self._opacity,
                self._z, self._pipeline
            )

    def _compute_center(self) -> None:
        """Calcul le centre monde"""
        x_min, y_min, x_max, y_max = self._shape.bounding_box

        # Anchor en espace local
        local_ax = x_min + self._anchor_x * (x_max - x_min)
        local_ay = y_min + self._anchor_y * (y_max - y_min)

        # Scale + rotation de l'anchor
        rad = math.radians(-self._rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        scaled_ax = local_ax * self._scale
        scaled_ay = local_ay * self._scale
        rotated_ax = scaled_ax * cos_r - scaled_ay * sin_r
        rotated_ay = scaled_ax * sin_r + scaled_ay * cos_r

        # Centre monde
        self._cx = self._x - rotated_ax
        self._cy = self._y - rotated_ay

    # ======================================== GETTERS ========================================
    @property
    def shape(self) -> Shape:
        """Renvoie la forme"""
        return self._shape
    
    @property
    def position(self) -> tuple[float, float]:
        """Renvoie la position"""
        return (self._x, self._y)
    
    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._x
    
    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._y
    
    @property
    def scale(self) -> float:
        """Renvoie le facteur de redimensionnement"""
        return self._scale

    @property
    def rotation(self) -> float:
        """Renvoie la rotation en degrés"""
        return self._rotation

    @property
    def filling(self) -> bool:
        """Vérifie le remplissage"""
        return self._filling
    
    @property
    def color(self) -> Color:
        """Renvoie la couleur de remplissage"""
        return self._color
    
    @property
    def border_width(self) -> int:
        """Renvoie l'épaisseur de la bordure"""
        return int(self._border_width)
    
    @property
    def border_align(self) -> BorderAlign:
        """Renvoie l'alignement de la bordure"""
        return self._border_align
    
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
    def center(self) -> tuple[float, float]:
        """Renvoie la position centrale"""
        return (self._cx, self._cy)
    
    @property
    def cx(self) -> float:
        """Renvoie la position centrale horizontale"""
        return self._cx
    
    @property
    def cy(self) -> float:
        """Renoie la position centrale verticale"""
        return self._cy

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
            shape: Forme à rendre
            x: position horizontale
            y: position verticale
            anchor_x: ancre relative locale horizontale
            anchor_y: ancre relative locale verticale
            scale: facteur de redimensionnement
            rotation: rotation en degrés
            filling: remplissage
            color: couleur de remplissage
            border_width: épaisseur de bordure
            border_align: alignement de la bordure
            border_color: couleur de bordure
            opacity: opacité
            z: zorder
            pipeline: pipeline de rendu
        """
        # Flags
        recompute_center: bool = False

        # Actualisation des paramètres
        changes: set[str] = set()
        for key, value in kwargs.items():
            current = getattr(self, f"_{key}", _UNSET)
            if current is _UNSET or value == current:
                continue
            setattr(self, f"_{key}", value)
            if key in _CENTER_DEPS:
                recompute_center = True
            else:
                changes.add(key)
        
        # Modifications globales
        if recompute_center:
            self._compute_center()
            changes.add("center")

        # Remplissage
        if self._filling:
            if self._fill is not None:
                self._fill.update(self, changes)
            elif self._color is not None:
                self._fill = _FillRenderer(
                    self._shape,
                    self._cx, self._cy,
                    self._scale, self._rotation,
                    self._color, self._opacity,
                    self._z, self._pipeline
                )
        elif self._fill is not None:
            self._fill.delete()
            self._fill = None

        # Bordure
        if self._border_width > 0:
            if self._border is not None:
                self._border.update(self, changes)
            elif self._border_color is not None:
                self._border = _BorderRenderer(
                    self._shape,
                    self._cx, self._cy,
                    self._scale, self._rotation,
                    self._border_width, self._border_align,
                    self._border_color, self._opacity, 
                    self._z, self._pipeline
                )
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
    """
    Remplissage d'une shape

    Args:
        shape(Shape): forme
        cx(float): position horizontale
        cy(float): position verticale
        scale(float): facteur de redimensionnement
        rotation(float): angle de rotation en degrés
        color(Color): couleur de remplissage
        opacity(float): opacité
        z(int): z-order
        pipeline(Pipeline): pipeline de rendu
    """
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
        """
        Construit le remplissage

        Args:
            shape(Shape): forme
            cx(float): position horizontale
            cy(float): position verticale
            scale(float): facteur de redimensionnement
            rotation(float): facteur de redimensionnement
            color(Color): couleur de remplissage
            opacity(float): opacité
            z(int): z-order
            pipeline(Pipeline): pipeline de rendu
        """
        r, g, b, a = color.rgba8
        a = int(a * opacity)

        if isinstance(shape, VertexShape):
            pts = [tuple(v) for v in shape.world_vertices(cx, cy, scale, rotation)]
            self._gl_shape = pyglet.shapes.Polygon(*pts, color=(r, g, b, a), batch=pipeline.batch, group=pipeline.get_group(z=z))

        elif isinstance(shape, Circle):
            cx_, cy_, r_ = shape.world_transform(cx, cy, scale, 0)
            self._gl_shape = pyglet.shapes.Circle(cx_, cy_, r_, color=(r, g, b, a), batch=pipeline.batch, group=pipeline.get_group(z=z))

        elif isinstance(shape, Ellipse):
            cx_, cy_, rx, ry, _ = shape.world_transform(cx, cy, scale, 0)
            self._gl_shape = pyglet.shapes.Ellipse(cx_, cy_, rx, ry, color=(r, g, b, a), batch=pipeline.batch, group=pipeline.get_group(z=z))
            self._gl_shape.rotation = rotation

        elif isinstance(shape, Capsule):
            ax, ay, bx, by, r_ = shape.world_transform(cx, cy, scale, 0)
            spine = math.dist((ax, ay), (bx, by))
            self._gl_shape = _CapsuleRenderer(cx, cy, r_, spine, rotation=rotation, color=(r, g, b, a), batch=pipeline.batch, group=pipeline.get_group(z=z))

        elif isinstance(shape, RoundedRect):
            _, _, _, _, r_, _, corners = shape.world_transform(cx, cy, scale, 0)
            tl, tr, br, bl = corners
            mid_x = (tl[0] + br[0]) * 0.5
            mid_y = (tl[1] + br[1]) * 0.5
            w = shape.width  * scale
            h = shape.height * scale
            self._gl_shape = _RoundedRectRenderer(mid_x, mid_y, w, h, r_, rotation=rotation, color=(r, g, b, a), batch=pipeline.batch, group=pipeline.get_group(z=z))
    
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
            if handler and handler(psr):
                self._rebuild(psr)
                break

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._gl_shape is None:
            return
        self._gl_shape.delete()
        self._gl_shape = None
    
    # ======================================== HANDLERS ========================================
    def handle_center(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la position"""
        if isinstance(psr.shape, VertexShape):
            return True
        else:
            self._gl_shape.position = psr.center

    def handle_scale(self, psr: PygletShapeRenderer) -> None:
        """Actualisation du facteur de redimensionnement"""
        if isinstance(psr.shape, Circle):
            self._gl_shape.radius = psr.shape.radius * psr.scale
        elif isinstance(psr.shape, Ellipse):
            self._gl_shape.a = psr.shape.rx * psr.scale
            self._gl_shape.b = psr.shape.ry * psr.scale
        else:
            return True

    def handle_rotation(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'angle de rotation"""
        if isinstance(psr.shape, VertexShape):
            return True
        else:
            self._gl_shape.rotation = psr.rotation

    def handle_color(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la couleur de remplissage"""
        r, g, b, a = psr.color.rgba8
        a = int(a * psr.opacity)
        self._gl_shape.color = (r, g, b, a)

    def handle_opacity(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'opacité"""
        a = int(psr.color.a * psr.opacity)
        self._gl_shape.opacity = a
    
    def handle_z(self, psr: PygletShapeRenderer) -> None:
        """Actualisation du z-order"""
        self._gl_shape.group = psr.pipeline.get_group(z=psr.z)
    
    def handle_pipeline(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la pipeline de rendu"""
        pipeline = psr.pipeline
        self._gl_shape.batch = pipeline.batch
        self._gl_shape.group = pipeline.get_group(z=psr.z)
    
    # ======================================== HELPERS ========================================
    def _rebuild(self, psr: PygletShapeRenderer) -> None:
        """Reconstruit le remplissage avec les paramètres courants"""
        self.delete()
        self._build(psr.shape, psr.cx, psr.cy, psr.scale, psr.rotation, psr.color, psr.opacity, psr.z, psr.pipeline)

# ======================================== BORDER RENDERER ========================================
class _BorderRenderer:
    """
    Bordure d'une shape

    Args:
        shape(Shape): forme
        cx(float): position horizontale
        cy(float): position verticale
        scale(float): facteur de redimensionnement
        rotation(float): angle de rotation en degrés
        width(int): épaisseur de la bordure
        align(BorderAlign): alignement
        color(Color): couleur de la bordure
        opacité(float): opacité
        z(int): z-order
        pipeline(Pipeline): pipeline de rendu
    """
    __slots__ = ("_vlist", "_n", "_width", "_align", "_program", "_batch", "_group", "_local_contour", "_visible", "_stored_colors")

    _SHAPE_PROGRAM = pyglet.shapes.get_default_shader()
    _SHAPE_GROUP = pyglet.graphics.ShaderGroup(_SHAPE_PROGRAM, order=1)

    def __init__(
        self,
        shape: Shape,
        cx: float,
        cy: float,
        scale: float,
        rotation: float,
        width: int,
        align: BorderAlign,
        color: Color,
        opacity: float,
        z: int,
        pipeline: Pipeline,
    ):
        self._vlist = None
        self._n: int = 0
        self._width: int = width
        self._align: BorderAlign = align
        self._program: ShaderProgram = pyglet.shapes.get_default_shader()
        self._batch: Batch = None
        self._group: Group = None
        self._visible: bool = True
        self._stored_colors: list = None
        self._local_contour: np.ndarray = _local_contour(shape)
        self._build(cx, cy, scale, rotation, width, align, color, opacity, z, pipeline)

    # ======================================== BUILD ========================================
    def _build(
        self,
        cx: float,
        cy: float,
        scale: float,
        rotation: float,
        width: int,
        align: BorderAlign,
        color: Color,
        opacity: float,
        z: int,
        pipeline: Pipeline,
    ) -> None:
        """
        Construction de la bordure

        Args:
            cx(float): position horizontale
            cy(float): position verticale
            scale(float): facteur de redimensionnement
            rotation(float): angle de rotation en degrés
            width(int): épaisseur de la bordure
            color(Color): couleur de la bordure
            opacity(float): opacité
            z(int): z-order
            pipeline(Pipeline): pipeline de rendu
        """
        if self._vlist is not None:
            self._vlist.delete()

        # Paramètres
        self._batch = pipeline.batch
        self._group = pyglet.graphics.Group(order=z, parent=self._SHAPE_GROUP)
        self._width = width
        print(self._group)
        print(self._group.parent)
        print(self._group.parent.parent)

        # Meshes
        strip = self._world_strip(cx, cy, scale, rotation, width, align)
        self._n = len(strip)
        flat = strip.flatten().tolist()

        # Couleur
        r, g, b, a = color.rgba8
        a = int(a * opacity)

        # Arrêtes
        self._vlist = self._program.vertex_list(
            self._n,
            pyglet.gl.GL_TRIANGLE_STRIP,
            self._batch,
            self._group,
            position=('f', flat),
            colors=('Bn', (r, g, b, a) * self._n),
        )

    def _world_strip(self, cx: float, cy: float, scale: float, rotation: float, width: float, align: BorderAlign) -> np.ndarray:
        """Génère le contour monde + strip"""
        world = _apply_transform(self._local_contour, cx, cy, scale, rotation)
        return _build_strip(world, width, align)

    def _refresh_vertices(self, psr: PygletShapeRenderer) -> None:
        """Réactualise les arrêtes"""
        strip = self._world_strip(psr.cx, psr.cy, psr.scale, psr.rotation, psr.border_width, psr.border_align)
        flat = strip.flatten().tolist()
        self._vlist.position[:] = flat
    
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
        if value:
            self._vlist.colors[:] = self._stored_colors
        else:
            self._stored_colors = list(self._vlist.colors[:])
            self._vlist.colors[:] = (0.0, 0.0, 0.0, 0.0) * self._n

    # ======================================== LIFE CYCLE ========================================
    def update(self, psr: PygletShapeRenderer, changes: list[str]) -> None:
        """Actualisation de la bordure"""
        needs_rebuild = False
        needs_refresh = False

        for key in changes:
            handler = getattr(self, f"handle_{key}", None)
            if handler is None:
                continue
            result = handler(psr)
            if result == "rebuild":
                needs_rebuild = True
            elif result == "refresh":
                needs_refresh = True

        if needs_rebuild:
            self._rebuild(psr)
        elif needs_refresh:
            self._refresh_vertices(psr)

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._vlist is None:
            return
        self._vlist.delete()
        self._vlist = None

    # ======================================== HANDLERS ========================================
    def handle_center(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la position"""
        return "refresh"

    def handle_scale(self, psr: PygletShapeRenderer) -> None:
        """Actualisation du facteur de redimensionnement"""
        return "refresh"

    def handle_rotation(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'angle de rotation"""
        return "refresh"

    def handle_border_width(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'épaisseur de la bordure"""
        self._width = psr.border_width
        return "refresh"

    def handle_border_align(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'alignement de la bordure"""
        self._align = psr.border_align
        return "refresh"

    def handle_border_color(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la couleur"""
        r, g, b, a = psr.border_color.rgba8
        a = int(a * psr.opacity)
        self._vlist.colors[:] = (r, g, b, a) * self._n

    def handle_opacity(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de l'opacité"""
        r, g, b, a = psr.border_color.rgba8
        a = int(a * psr.opacity)
        self._vlist.colors[:] = (r, g, b, a) * self._n

    def handle_z(self, psr: PygletShapeRenderer) -> None:
        """Actualisation du z-order"""
        return "rebuild"

    def handle_pipeline(self, psr: PygletShapeRenderer) -> None:
        """Actualisation de la pipeline de rendu"""
        return "rebuild"

    # ======================================== HELPERS ========================================
    def _rebuild(self, psr: PygletShapeRenderer) -> None:
        """Reconstruit la bordure avec les paramètres courants"""
        self.delete()
        self._build(psr.cx, psr.cy, psr.scale, psr.rotation, psr.border_width, psr.border_align, psr.border_color, psr.opacity, psr.z, psr.pipeline)

# ======================================== BORDER HELPERS ========================================
def _local_contour(shape: Shape) -> np.ndarray:
    """Génère le contour local d'une shape"""
    if isinstance(shape, VertexShape):
        return np.array(shape.vertices, dtype=np.float32)
 
    elif isinstance(shape, Circle):
        angles = np.linspace(0, 2 * np.pi, _CIRCLE_BORDER_SEGMENTS, endpoint=False)
        return np.column_stack((np.cos(angles) * shape.radius, np.sin(angles) * shape.radius)).astype(np.float32)
 
    elif isinstance(shape, Ellipse):
        angles = np.linspace(0, 2 * np.pi, _ELLIPSE_BORDER_SEGMENTS, endpoint=False)
        return np.column_stack((np.cos(angles) * shape.rx, np.sin(angles) * shape.ry)).astype(np.float32)
 
    elif isinstance(shape, Capsule):
        return _capsule_local_contour(shape).astype(np.float32)

    elif isinstance(shape, RoundedRect):
        return _rounded_rect_local_contour(shape).astype(np.float32)
 
    raise TypeError(f"Shape non supportée : {type(shape)}")
 
def _capsule_local_contour(shape: Capsule) -> np.ndarray:
    """Contour d'une capsule"""
    half_len = shape.spine / 2.0
    r = shape.radius
    half = _CAPSULE_BORDER_SEGMENTS // 2

    angles_b = np.linspace(0, np.pi, half + 1)
    angles_a = np.linspace(np.pi, 2 * np.pi, half + 1)

    pts_b = np.column_stack((r * np.cos(angles_b), half_len + r * np.sin(angles_b)))
    pts_a = np.column_stack((r * np.cos(angles_a), -half_len + r * np.sin(angles_a)))

    return np.vstack((pts_b, pts_a))

def _rounded_rect_local_contour(shape: RoundedRect) -> np.ndarray:
    """Contour local d'un rectangle arrondi"""
    r = shape.radius
    hx = shape.inner_width  * 0.5
    hy = shape.inner_height * 0.5

    seg = max(_ROUNDED_RECT_BORDER_SEGMENTS, int(r * 0.75))
    corners = [
        ( hx, hy, 0.0, np.pi * 0.5),
        (-hx, hy, np.pi * 0.5, np.pi),
        (-hx, -hy, np.pi, np.pi * 1.5),
        ( hx, -hy, np.pi * 1.5, np.pi * 2.0),
    ]

    pts = []
    for cx, cy, a_start, a_end in corners:
        angles = np.linspace(a_start, a_end, seg, endpoint=False)
        arc = np.column_stack((
            cx + r * np.cos(angles),
            cy + r * np.sin(angles)
        ))
        pts.append(arc)

    contour = np.vstack(pts)
    return contour.astype(np.float32)
 
 
def _build_strip(contour: np.ndarray, width: float, align: str = "center") -> np.ndarray:
    """Génère un triangle strip (N+1)*2 points autour d'un contour fermé"""
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

    if align == "center":
        half = width / 2.0
        miter_dist = np.clip(half / dot, -width * 3, width * 3)
        outer = contour + miter * miter_dist
        inner = contour - miter * miter_dist
    elif align == "in":
        miter_dist = np.clip(width / dot, -width * 3, width * 3)
        outer = contour + miter * miter_dist
        inner = contour
    elif align == "out":
        miter_dist = np.clip(width / dot, -width * 3, width * 3)
        outer = contour
        inner = contour - miter * miter_dist

    strip = np.empty(((n + 1) * 2, 2), dtype=np.float32)
    strip[0::2][:n] = outer
    strip[1::2][:n] = inner
    strip[-2] = outer[0]
    strip[-1] = inner[0]

    return strip
 
 
def _apply_transform(pts: np.ndarray, cx: float, cy: float, scale: float, rotation: float) -> np.ndarray:
    """Applique translation + scale + rotation à un contour local"""
    rad = math.radians(-rotation)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    rot = np.array([[cos_r, -sin_r], [sin_r, cos_r]], dtype=np.float32)
    return (pts * scale) @ rot.T + np.array([cx, cy], dtype=np.float32)

# ======================================== CAPSULE RENDERER ========================================
class _CapsuleRenderer:
    """
    Capsule pyglet composite : deux cercles + rectangle central

    Args:
        x(float): position horizontale
        y(float): position verticale
        radius(float): rayon de la capsule
        spine(float): hauteur du rect central
        color(tuple[int, ...], optional): couleur
        batch(Batch, optional): batch pyglet
        group(Group, optional): groupe pyglet
    """
    __slots__ = ("_x", "_y", "_radius", "_spine", "_rotation", "_color", "_opacity", "_z", "_batch", "_group", "_top", "_bottom", "_rect")
 
    def __init__(
        self,
        x: float,
        y: float,
        radius: float,
        spine: float,
        rotation: float = 0.0,
        color: tuple[int, ...] = (255, 255, 255, 255),
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
 
    # ======================================== GETTERS ========================================
    @property
    def position(self) -> tuple[float, float]:
        """Renvoie la position"""
        return self._x, self._y

    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._x
    
    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._y
    
    @property
    def rotation(self) -> float:
        """Renvoie l'angle de rotation en degrés"""
        return self._rotation
    
    @property
    def color(self) -> tuple:
        """Renvoie la couleur de remplissage"""
        return self._color
    
    @property
    def opacity(self) -> int:
        """Renvoie l'opacité"""
        return self._opacity
    
    @property
    def batch(self) -> Batch:
        """Renvoie le batch pyglet"""
        return self._batch
    
    @property
    def group(self) -> Group:
        """Renvoie le groupe pyglet"""
        return self._group
    
    @property
    def visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._top.visible
 
    # ======================================== SETTERS ========================================
    @position.setter
    def position(self, value: tuple[float, float]) -> None:
        """Fixe la position"""
        self._x, self._y = value
        self._rebuild()

    @x.setter
    def x(self, value: float) -> None:
        """Fixe la position horizontale"""
        self._x = value
        self._rebuild()    
 
    @y.setter
    def y(self, value: float) -> None:
        """Fixe la position verticale"""
        self._y = value
        self._rebuild()
 
    @rotation.setter
    def rotation(self, value: float) -> None:
        """Fixe l'angle de rotation"""
        self._rotation = value
        self._rebuild()
 
    @color.setter
    def color(self, value: tuple) -> None:
        """Fixe la couleur de remplissage"""
        self._color = value
        self._top.color = value
        self._bottom.color = value
        self._rect.color = value
 
    @opacity.setter
    def opacity(self, value: int) -> None:
        """Fixe l'opacité"""
        self._opacity = value
        self._top.opacity = value
        self._bottom.opacity = value
        self._rect.opacity = value
 
    @batch.setter
    def batch(self, value: Batch) -> None:
        """Fixe le batch pyglet"""
        self._batch = value
        self._top.batch = value
        self._bottom.batch = value
        self._rect.batch = value
 
    @group.setter
    def group(self, value: Group) -> None:
        """Fixe la groupe pyglet"""
        self._group = value
        self._top.group = value
        self._bottom.group = value
        self._rect.group = value
    
    @visible.setter
    def visible(self, value: bool) -> None:
        """Fixe la visibilité"""
        self._top.visible = value
        self._bottom.visible = value
        self._rect.visible = value
 
    # ======================================== LIFE CYCLE ========================================
    def delete(self) -> None:
        """Libère les ressources pyglet"""
        self._top.delete()
        self._bottom.delete()
        self._rect.delete()
 
    # ======================================== HELPERS ========================================
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

# ======================================== CAPSULE HELPERS ========================================
def _capsule_centers(cx: float, cy: float, spine: float, rotation: float) -> tuple[float, float, float, float]:
    """Retourne les centres (ax, ay, bx, by) des deux demi-sphères"""
    rad = math.radians(-rotation)
    half = spine * 0.5
    return (cx - math.sin(rad) * half, cy + math.cos(rad) * half, cx + math.sin(rad) * half, cy - math.cos(rad) * half,)
 
def _capsule_rect_vertices(ax: float, ay: float, bx: float, by: float, r: float) -> list[tuple[float, float]]:
    """Retourne les 4 coins du rectangle central de la capsule"""
    dx = bx - ax
    dy = by - ay
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return [(ax - r, ay - r), (ax + r, ay - r), (ax + r, ay + r), (ax - r, ay + r)]
    nx = -dy / length * r
    ny = dx / length * r
    return [(ax + nx, ay + ny), (ax - nx, ay - ny), (bx - nx, by - ny), (bx + nx, by + ny)]

# ======================================== ROUNDED RECT RENDERER ========================================
class _RoundedRectRenderer:
    """
    Rectangle arrondi pyglet wrapper (anchor-free, centré sur (x, y))

    Args:
        x(float): position horizontale du centre
        y(float): position verticale du centre
        width(float): largeur
        height(float): hauteur
        radius(float): rayon des coins
        rotation(float, optional): angle de rotation en degrés (sens horaire)
        color(tuple[int, ...], optional): couleur RGBA
        batch(Batch, optional): batch pyglet
        group(Group, optional): groupe pyglet
    """
    __slots__ = ("_x", "_y", "_w", "_h", "_r", "_rotation", "_color", "_opacity", "_batch", "_group", "_shape")

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
        rotation: float = 0.0,
        color: tuple[int, ...] = (255, 255, 255, 255),
        batch: pyglet.graphics.Batch = None,
        group: pyglet.graphics.Group = None,
    ):
        self._x = x
        self._y = y
        self._w = width
        self._h = height
        self._r = radius
        self._rotation = rotation
        self._color = color
        self._opacity = 255
        self._batch = batch
        self._group = group
        self._shape = None

        self._rebuild()

    # ======================================== GETTERS ========================================
    @property
    def position(self) -> tuple[float, float]:
        """Renvoie la position centrale"""
        return self._x, self._y

    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._x

    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._y

    @property
    def rotation(self) -> float:
        """Renvoie l'angle de rotation en degrés"""
        return self._rotation

    @property
    def color(self) -> tuple:
        """Renvoie la couleur"""
        return self._shape.color

    @property
    def opacity(self) -> int:
        """Renvoie l'opacité"""
        return self._opacity

    @property
    def batch(self) -> Batch:
        """Renvoie le batch pyglet"""
        return self._shape.batch

    @property
    def group(self) -> Group:
        """Renvoie le groupe pyglet"""
        return self._shape.group

    @property
    def visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._shape.visible

    # ======================================== SETTERS ========================================
    @position.setter
    def position(self, value: tuple[float, float]) -> None:
        """Fixe la position"""
        self._x, self._y = value
        self._rebuild()

    @x.setter
    def x(self, value: float) -> None:
        """Fixe la position horizontale"""
        self._x = value
        self._rebuild()

    @y.setter
    def y(self, value: float) -> None:
        """Fixe la position verticale"""
        self._y = value
        self._rebuild()

    @rotation.setter
    def rotation(self, value: float) -> None:
        """Fixe l'angle de rotation"""
        self._rotation = value
        self._shape.rotation = value

    @color.setter
    def color(self, value: tuple) -> None:
        """Fixe la couleur"""
        self._color = value
        self._shape.color = value

    @opacity.setter
    def opacity(self, value: int) -> None:
        """Fixe l'opacité"""
        self._opacity = value
        self._shape.opacity = value

    @batch.setter
    def batch(self, value: Batch) -> None:
        """Fixe le batch pyglet"""
        self._batch = value
        self._shape.batch = value

    @group.setter
    def group(self, value: Group) -> None:
        """Fixe le groupe pyglet"""
        self._group = value
        self._shape.group = value

    @visible.setter
    def visible(self, value: bool) -> None:
        """Fixe la visibilité"""
        self._shape.visible = value

    # ======================================== LIFE CYCLE ========================================
    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._shape:
            self._shape.delete()
            self._shape = None

    # ======================================== HELPERS ========================================
    def _rebuild(self) -> None:
        """Reconstruit le shape pyglet à partir de l'état courant"""
        if self._shape is not None:
            self._shape.delete()

        # offset du centre vers bottom-left
        ox = -self._w * 0.5
        oy = -self._h * 0.5

        # rotation horaire → angle négatif en math
        rad = math.radians(-self._rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        # rotation de l'offset
        rx = ox * cos_r - oy * sin_r
        ry = ox * sin_r + oy * cos_r

        # position finale corrigée
        x = self._x + rx
        y = self._y + ry

        self._shape = pyglet.shapes.RoundedRectangle(x, y, self._w, self._h, self._r, color=self._color, batch=self._batch, group=self._group)
        self._shape.rotation = self._rotation
        self._shape.opacity = self._opacity