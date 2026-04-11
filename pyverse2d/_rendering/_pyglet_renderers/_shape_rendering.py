# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...typing import BorderAlign
from ...asset import Color
from .._pipeline import Pipeline

import pyglet
import pyglet.gl
from pyglet.graphics import ShaderGroup
from pyglet.graphics.shader import ShaderProgram

import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...abc import Shape

# ======================================== CONSTANTS ========================================
_UNSET = object()
_TRANSFORM_DEPS = frozenset({"x", "y", "anchor_x", "anchor_y", "scale", "rotation"})

# ======================================== PUBLIC ========================================
class PygletShapeRenderer:
    """Renderer pyglet unifié pour une shape géométrique

    Args:
        shape: shape à rendre
        x: position horizontale monde
        y: position verticale monde
        anchor_x: ancre relative locale horizontale [0, 1]
        anchor_y: ancre relative locale verticale [0, 1]
        scale: facteur d'échelle uniforme
        rotation: rotation en degrés (sens trigonométrique)
        filling: activer le remplissage
        color: couleur de remplissage
        border_width: épaisseur de la bordure en pixels
        border_align: alignement de la bordure ("center" | "in" | "out")
        border_color: couleur de la bordure
        opacity: opacité globale [0.0, 1.0]
        z: z-order
        pipeline: pipeline de rendu
    """
    __slots__ = (
        "_shape",
        "_x", "_y", "_anchor_x", "_anchor_y",
        "_scale", "_rotation",
        "_filling", "_color",
        "_border_width", "_border_align", "_border_color",
        "_opacity", "_z", "_pipeline",
        "_fill", "_border",
    )

    # Cache partagé des shader groups
    _PROGRAM: ShaderProgram = None
    _GROUPS: dict[tuple[int, int], ShaderGroup] = {}

    @classmethod
    def get_program(cls) -> ShaderProgram:
        """Renvoie le shader programme des formes"""
        if cls._PROGRAM is None:
            cls._PROGRAM = pyglet.shapes.get_default_shader()
        return cls._PROGRAM

    @classmethod
    def get_group(cls, pipeline: Pipeline, z: int = 0, order: int = 0) -> ShaderGroup:
        """Renvoie le groupe correspondant avec mise en cache"""
        key = (z, order)
        if key not in cls._GROUPS:
            cls._GROUPS[key] = ShaderGroup(cls.get_program(), order=order, parent=pipeline.get_group(z=z))
        return cls._GROUPS[key]

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
        self._shape = shape
        self._x = x
        self._y = y
        self._anchor_x = anchor_x
        self._anchor_y = anchor_y
        self._scale = scale
        self._rotation = rotation
        self._filling = filling
        self._color = color
        self._border_width = border_width
        self._border_align = border_align
        self._border_color = border_color
        self._opacity = opacity
        self._z = z
        self._pipeline = pipeline

        self._fill: _FillRenderer = None
        self._border: _BorderRenderer = None
        self._build()

    # ======================================== INTERNALS ========================================
    def _build(self) -> None:
        """Construit les sous-renderers fill et border"""
        if self._filling and self._color is not None:
            self._fill = _FillRenderer(self)
        if self._border_width > 0 and self._border_color is not None:
            self._border = _BorderRenderer(self)

    # ======================================== GETTERS ========================================
    @property
    def shape(self) -> Shape: return self._shape
    @property
    def position(self) -> tuple: return (self._x, self._y)
    @property
    def x(self) -> float: return self._x
    @property
    def y(self) -> float: return self._y
    @property
    def anchor_x(self) -> float: return self._anchor_x
    @property
    def anchor_y(self) -> float: return self._anchor_y
    @property
    def scale(self) -> float: return self._scale
    @property
    def rotation(self) -> float: return self._rotation
    @property
    def filling(self) -> bool: return self._filling
    @property
    def color(self) -> Color: return self._color
    @property
    def border_width(self) -> int: return int(self._border_width)
    @property
    def border_align(self) -> BorderAlign: return self._border_align
    @property
    def border_color(self) -> Color: return self._border_color
    @property
    def opacity(self) -> float: return self._opacity
    @property
    def z(self) -> int: return self._z
    @property
    def pipeline(self) -> Pipeline: return self._pipeline
    
    # ======================================== VISIBILITY ========================================
    @property
    def visible(self) -> bool:
        """Visibilité"""
        if self._fill: return self._fill.visible
        if self._border: return self._border.visible
        return False

    @visible.setter
    def visible(self, value: bool) -> None:
        if self._fill: self._fill.visible = value
        if self._border: self._border.visible = value

    def is_visible(self) -> bool:
        """Vérifie la visibilité effective"""
        return self.visible and ((self._filling and self._color is not None) or (self._border_width > 0 and self._border_color is not None))

    # ======================================== LIFE CYCLE ========================================
    def update(self, **kwargs) -> None:
        """Actualisation

        Args:
            shape: nouvelle forme
            x: position horizontale
            y: position verticale
            anchor_x: ancre horizontale
            anchor_y: ancre verticale
            scale: facteur de redimensionnement
            rotation: rotation en degrés
            filling: remplissage activé
            color: couleur de remplissage
            border_width: épaisseur de bordure
            border_align: alignement de la bordure
            border_color: couleur de bordure
            opacity: opacité
            z: z-order
        """
        changes: set[str] = set()
        for key, value in kwargs.items():
            current = getattr(self, f"_{key}", _UNSET)
            if current is _UNSET or value == current:
                continue
            setattr(self, f"_{key}", value)
            changes.add(key)

        if not changes:
            return

        # Remplissage
        if self._filling:
            if self._fill is not None:
                self._fill.update(self, changes)
            elif self._color is not None:
                self._fill = _FillRenderer(self)
        elif self._fill is not None:
            self._fill.delete()
            self._fill = None

        # Bordure
        if self._border_width > 0:
            if self._border is not None:
                self._border.update(self, changes)
            elif self._border_color is not None:
                self._border = _BorderRenderer(self)
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


# ======================================== FILL RENDERER ========================================
class _FillRenderer:
    """Remplissage mesh-based"""
    __slots__ = ("_vlist", "_n", "_visible", "_stored_colors")

    def __init__(self, psr: PygletShapeRenderer):
        self._vlist = None
        self._n: int = 0
        self._visible: bool = True
        self._stored_colors = None
        self._build(psr)

    # ======================================== BUILD ========================================
    def _build(self, psr: PygletShapeRenderer) -> None:
        """Construit le ``vertex_list_indexed`` depuis le Mesh de la shape"""
        if self._vlist is not None:
            self._vlist.delete()

        vertices = psr.shape.world_vertices(psr.x, psr.y, psr.scale, psr.rotation, psr.anchor_x, psr.anchor_y)
        indexes = psr.shape.get_indexes()
        self._n = len(vertices)

        r, g, b, a = psr.color.rgba8
        a = int(a * psr.opacity)

        self._vlist = psr.get_program().vertex_list_indexed(
            count = self._n,
            mode = pyglet.gl.GL_TRIANGLES,
            indices = indexes.flatten().tolist(),
            batch = psr.pipeline.batch,
            group = psr.get_group(pipeline=psr.pipeline, z=psr.z, order=0),
            position = ('f', vertices.flatten().tolist()),
            colors = ('Bn', (r, g, b, a) * self._n),
        )

    # ======================================== PROPERTIES ========================================
    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """Active ou masque via alpha"""
        if value == self._visible:
            return
        self._visible = value
        if value:
            self._vlist.colors[:] = self._stored_colors
            self._stored_colors = None
        else:
            self._stored_colors = list(self._vlist.colors[:])
            self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    # ======================================== LIFE CYCLE ========================================
    def update(self, psr: PygletShapeRenderer, changes: set[str]) -> None:
        """Actualisation"""
        # Changement de z-order
        if "z" in changes:
            self._build(psr)
            return
        
        # Changement de position
        if changes & _TRANSFORM_DEPS:
            vertices = psr.shape.world_vertices(psr.x, psr.y, psr.scale, psr.rotation, psr.anchor_x, psr.anchor_y)
            self._vlist.position[:] = vertices.flatten().tolist()

        # Changement de style
        if "color" in changes or "opacity" in changes:
            r, g, b, a = psr.color.rgba8
            a = int(a * psr.opacity)
            self._vlist.colors[:] = (r, g, b, a) * self._n

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None


# ======================================== BORDER RENDERER ========================================
class _BorderRenderer:
    """Bordure via triangle strip"""
    __slots__ = ("_vlist", "_n", "_visible", "_stored_colors")

    def __init__(self, psr: PygletShapeRenderer):
        self._vlist = None
        self._n: int = 0
        self._visible: bool = True
        self._stored_colors = None
        self._build(psr)

    # ======================================== BUILD ========================================
    def _build(self, psr: PygletShapeRenderer) -> None:
        """Construit le ``vertex_list`` du triangle strip"""
        if self._vlist is not None:
            self._vlist.delete()

        strip = _world_strip(psr)
        self._n = len(strip)

        r, g, b, a = psr.border_color.rgba8
        a = int(a * psr.opacity)

        self._vlist = psr.get_program().vertex_list(
            count = self._n,
            mode = pyglet.gl.GL_TRIANGLE_STRIP,
            batch = psr.pipeline.batch,
            group = psr.get_group(pipeline=psr.pipeline, z=psr.z, order=1),
            position = ('f', strip.flatten().tolist()),
            colors = ('Bn', (r, g, b, a) * self._n),
        )

    def _refresh_strip(self, psr: PygletShapeRenderer) -> None:
        """Rebuild du strip monde si border_width ou border_align changent"""
        strip = _world_strip(psr)
        self._n = len(strip)
        self._vlist.position[:] = strip.flatten().tolist()

    # ======================================== PROPERTIES ========================================
    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if value == self._visible:
            return
        self._visible = value
        if value:
            self._vlist.colors[:] = self._stored_colors
            self._stored_colors = None
        else:
            self._stored_colors = list(self._vlist.colors[:])
            self._vlist.colors[:] = (0, 0, 0, 0) * self._n

    # ======================================== LIFE CYCLE ========================================
    def update(self, psr: PygletShapeRenderer, changes: set[str]) -> None:
        """Actualisation"""
        # Changement de z-order
        if "z" in changes:
            self._build(psr)
            return

        # Changement de bordure
        if changes & (_TRANSFORM_DEPS | {"border_width", "border_align"}):
            self._refresh_strip(psr)

        # Changement de style
        if "border_color" in changes or "opacity" in changes:
            r, g, b, a = psr.border_color.rgba8
            a = int(a * psr.opacity)
            self._vlist.colors[:] = (r, g, b, a) * self._n

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._vlist is not None:
            self._vlist.delete()
            self._vlist = None


# ======================================== HELPERS ========================================
def _world_strip(psr: PygletShapeRenderer) -> np.ndarray:
    """Génère le triangle strip en espace monde"""
    world = psr.shape.world_vertices(psr.x, psr.y, psr.scale, psr.rotation, psr.anchor_x, psr.anchor_y)
    return _build_strip(world, psr.border_width, psr.border_align)

def _build_strip(contour: np.ndarray, width: float, align: str = "center") -> np.ndarray:
    """Génère un triangle strip ``(N+1)*2`` points autour d'un contour fermé"""
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