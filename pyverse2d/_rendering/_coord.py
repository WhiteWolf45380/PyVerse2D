# ======================================== IMPORTS ========================================
from .._flag import CoordSpace

from . import Window, LogicalScreen, Viewport, Camera

import math
from typing import Callable
from dataclasses import dataclass

# ======================================== CONSTANTS ========================================
_PIPELINE = [
    CoordSpace.WORLD,
    CoordSpace.FRUSTUM,
    CoordSpace.NDC,
    CoordSpace.NVC,
    CoordSpace.VIEWPORT,
    CoordSpace.LOGICAL,
    CoordSpace.CANVAS,
    CoordSpace.FRAMEBUFFER,
]

# ======================================== REGISTRY ========================================
_converters: dict[tuple[CoordSpace, CoordSpace], Callable] = {}

def register(from_space: CoordSpace, to_space: CoordSpace) -> Callable:
    """Enregistre une fonction de conversion"""
    def decorator(fn: Callable) -> Callable:
        _converters[(from_space, to_space)] = fn
        return fn
    return decorator

# ======================================== WORLD to FRAMEBUFFER ========================================
@register(CoordSpace.WORLD, CoordSpace.FRUSTUM)
def world_to_frustum(x: float, y: float, cx: float = 0.0, cy: float = 0.0, rotation: float = 0.0) -> tuple[float, float]:
    """Conversion de l'espace *World* à l'espace *Frustum*

    Args:
        x: coordonnée horizontale dans l'espace *monde*
        y: coordonnée verticale dans l'espace *monde*
        cx: centre horizontal de la caméra
        cy: centre vertical de la caméra
        zoom: facteur de zoom de la caméra
        rotation: angle de rotation de la caméra
    """
    fr_x, fr_y = x - cx, y - cy     # Translation
    if rotation != 0.0:         # Rotation
        rad = math.radians(rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        fr_x, fy = fr_x * cos_r + fr_y * sin_r, -fr_x * sin_r + fr_y * cos_r
    return fr_x, fr_y

@register(CoordSpace.FRUSTUM, CoordSpace.NDC)
def frustum_to_ndc(fr_x: float, fr_y: float, vw: float, vh: float, zoom: float) -> tuple[float, float]:
    """Conversion de l'espace *Frustum* à l'espace *NDC*

    Args:
        fr_x: coordonnée horizontale dans l'espace *frustum*
        fr_y: coordonnée verticale dans l'espace *frustum*
        vw: largeur de la caméra
        vh: hauteur de la caméra
        zoom: facteur de zoom de la caméra
    """
    fr_w = (vw / zoom) / 2
    fr_h = (vh / zoom) / 2
    return fr_x / fr_w, fr_y / fr_h

@register(CoordSpace.NDC, CoordSpace.NVC)
def ndc_to_nvc(ndc_x: float, ndc_y: float) -> tuple[float, float]:
    """Conversion de l'espace *NDC* à l'espace *NVC*
    
    Args:
        ndc_x: coordonnée horizontale dans l'espace *NDC*
        ndc_y: coordonnée verticale dans l'espace *NDC*
    """
    return (ndc_x + 1) / 2, (ndc_y + 1) / 2

@register(CoordSpace.NVC, CoordSpace.VIEWPORT)
def nvc_to_viewport(nvc_x: float, nvc_y: float, lw: float, lh: float, ox: float, oy: float, dx: float, dy: float) -> tuple[float, float]:
    """Conversion de l'espace *NVC* à l'espace *Viewport*

    Args:
        nvc_x: coordonnée horizontale dans l'espace *NVC*
        nvc_y: coordonnée verticale dans l'espace *NVC*
        lw: largeur du viewport
        lh: hauteur du viewport
        ox: origine horizontale du viewport
        oy: origine verticale du viewport
        dx: direction horizontale du viewport
        dy: direction verticale du viewport
    """
    return ox + nvc_x * lw * dx, oy + nvc_y * lh * dy

@register(CoordSpace.VIEWPORT, CoordSpace.LOGICAL)
def viewport_to_logical(vw_x: float, vw_y: float, lx: float, ly: float) -> tuple[float, float]:
    """Conversion de l'espace *Viewport* à l'espace *Logical*

    Args:
        vw_x: coordonnée horizontale dans l'espace *Viewport*
        vw_y: coordonnée verticale dans l'espace *Viewport*
        lx: position horizontale du viewport
        ly: position verticale du viewport
    """
    return lx + vw_x, ly + vw_y

@register(CoordSpace.LOGICAL, CoordSpace.CANVAS)
def logical_to_canvas(logic_x: float, logic_y: float, fb_scale_x: float, fb_scale_y: float) -> tuple[float, float]:
    """Conversion de l'espace *Logical* à l'espace *Canvas*

    Args:
        logic_x: coordonnée horizontale dans l'espace *Logical*
        logic_y: coordonnée verticale dans l'espace *Logical*
        fb_scale_x: ratio horizontal pixels framebuffer / pixels logiques
        fb_scale_x: ratio vertical pixels framebuffer / pixels logiques
    """
    return int(logic_x * fb_scale_x), int(logic_y * fb_scale_y)

@register(CoordSpace.CANVAS, CoordSpace.FRAMEBUFFER)
def canvas_to_framebuffer(cnv_x: float, cnv_y: float, cnv_ox: float, cnv_oy: float) -> tuple[float, float]:
    """Conversion de l'espace *Canvas* à l'espace *FrameBuffer*
    
    Args:
        cnv_x: coordonnée horizontale dans l'espace *Canvas*
        cnv_y: coordonnée verticale dans l'espace *Canvas*
        cnv_ox: position horizontale du viewport OpenGL
        cnv_oy: position verticale du viewport OpenGl
    """
    return cnv_ox + cnv_x, cnv_oy + cnv_y

# ======================================== FRAMEBUFFER to WORLD ========================================
@register(CoordSpace.FRAMEBUFFER, CoordSpace.CANVAS)
def framebuffer_to_canvas(fb_x: float, fb_y: float, cnv_ox: float, cnv_oy: float) -> tuple[float, float]:
    """Conversion de l'espace *FrameBuffer* à l'espace *Canvas*

    Args:
        fb_x: coordonnée horizontale dans l'espace *FrameBuffer*
        fb_y: coordonnée verticale dans l'espace *FrameBuffer*
        cnv_ox: position horizontale du canvas
        cnv_oy: position verticale du canvas
    """
    return fb_x - cnv_ox, fb_y - cnv_oy

@register(CoordSpace.CANVAS, CoordSpace.LOGICAL)
def canvas_to_logical(cnv_x: float, cnv_y: float, fb_scale_x: float, fb_scale_y: float) -> tuple[float, float]:
    """Conversion de l'espace *Canvas* à l'espace *Logical*

    Args:
        cnv_x: coordonnée horizontale dans l'espace *Canvas*
        cnv_y: coordonnée verticale dans l'espace *Canvas*
        fb_scale_x: ratio horizontal pixels framebuffer / pixels logiques
        fb_scale_y: ratio vertical pixels framebuffer / pixels logiques
    """
    return cnv_x / fb_scale_x, cnv_y / fb_scale_y

@register(CoordSpace.LOGICAL, CoordSpace.VIEWPORT)
def logical_to_viewport(logic_x: float, logic_y: float, lx: float, ly: float) -> tuple[float, float]:
    """Conversion de l'espace *Logical* à l'espace *Viewport*

    Args:
        logic_x: coordonnée horizontale dans l'espace *Logical*
        logic_y: coordonnée verticale dans l'espace *Logical*
        lx: position horizontale du viewport
        ly: position verticale du viewport
    """
    return logic_x - lx, logic_y - ly

@register(CoordSpace.VIEWPORT, CoordSpace.NVC)
def viewport_to_nvc(vw_x: float, vw_y: float, lw: float, lh: float, ox: float, oy: float, dx: float, dy: float) -> tuple[float, float]:
    """Conversion de l'espace *Viewport* à l'espace *NVC*

    Args:
        vw_x: coordonnée horizontale dans l'espace *Viewport*
        vw_y: coordonnée verticale dans l'espace *Viewport*
        lw: largeur du viewport
        lh: hauteur du viewport
        ox: origine horizontale du viewport
        oy: origine verticale du viewport
        dx: direction horizontale du viewport
        dy: direction verticale du viewport
    """
    return (vw_x - ox) / (dx * lw), (vw_y - oy) / (dy * lh)

@register(CoordSpace.NVC, CoordSpace.NDC)
def nvc_to_ndc(nvc_x: float, nvc_y: float) -> tuple[float, float]:
    """Conversion de l'espace *NVC* à l'espace *NDC*

    Args:
        nvc_x: coordonnée horizontale dans l'espace *NVC*
        nvc_y: coordonnée verticale dans l'espace *NVC*
    """
    return nvc_x * 2 - 1, nvc_y * 2 - 1

@register(CoordSpace.NDC, CoordSpace.FRUSTUM)
def ndc_to_frustum(ndc_x: float, ndc_y: float, vw: float, vh: float, zoom: float) -> tuple[float, float]:
    """Conversion de l'espace *NDC* à l'espace *Frustum*

    Args:
        ndc_x: coordonnée horizontale dans l'espace *NDC*
        ndc_y: coordonnée verticale dans l'espace *NDC*
        vw: largeur de la caméra
        vh: hauteur de la caméra
        zoom: facteur de zoom de la caméra
    """
    fr_w = (vw / zoom) / 2
    fr_h = (vh / zoom) / 2
    return ndc_x * fr_w, ndc_y * fr_h

@register(CoordSpace.FRUSTUM, CoordSpace.WORLD)
def frustum_to_world(fr_x: float, fr_y: float, cx: float = 0.0, cy: float = 0.0, rotation: float = 0.0) -> tuple[float, float]:
    """Conversion de l'espace *Frustum* à l'espace *World*

    Args:
        fr_x: coordonnée horizontale dans l'espace *Frustum*
        fr_y: coordonnée verticale dans l'espace *Frustum*
        cx: centre horizontal de la caméra
        cy: centre vertical de la caméra
        rotation: angle de rotation de la caméra
    """
    if rotation != 0.0:
        rad = math.radians(rotation)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        fr_x, fr_y = fr_x * cos_r - fr_y * sin_r, fr_x * sin_r + fr_y * cos_r
    return fr_x + cx, fr_y + cy

# ======================================== CONTEXT ========================================
@dataclass(slots=True)
class CoordContext:
    """Converter portant un contexte"""
    window: Window = None
    screen: LogicalScreen = None
    viewport: Viewport = None
    camera: Camera = None

    def convert(
            x: float, y: float,
            from_space: CoordSpace, to_space: CoordSpace,
            window: Window = None, screen: LogicalScreen = None, viewport: Viewport = None, camera: Camera = None,
            viewport_resolve: tuple = None, camera_resolve: tuple = None,
        ) -> tuple[float, float]:
        """Conversion d'une position d'un espace à un autre

        Args:
            x: coordonnée horizontale
            y: coordonnée verticale
            from_space: espace source
            to_space: espace cible
            window: override de la fenêtre
            screen: override de l'espace logique
            viewport: override du viewport
            camera: override de la caméra
            viewport_resolve: résolution précalculée du viewport
            camera_resolve: résolution précalculée de la caméra
        """
        window = window or self.window
        screen = screen or self.screen
        viewport = viewport or self.viewport
        camera = camera or self.camera

        # Résolution des espaces
        lx, ly, lw, lh, (ox, oy), (dx, dy) = viewport.resolve(screen.width, screen.height) if viewport_resolve is None else viewport_resolve
        cx, cy, vw, vh, zoom, rotation, (ax, ay) = camera.resolve(lw, lh) if camera_resolve is None else camera_resolve
        fb_scale_x = window.framebuffer_scale_x
        fb_scale_y = window.framebuffer_scale_y
        cnv_ox = window.viewport.x
        cnv_oy = window.viewport.y
        
        # Arguments par transition
        _ARGS = (
            (cx + ax, cy + ay, rotation),                          # WORLD to FRUSTUM
            (vw, vh, zoom),                              # FRUSTUM to NDC
            (),                                          # NDC to NVC
            (lw, lh, ox, oy, dx, dy),                    # NVC to VIEWPORT
            (lx, ly),                                    # VIEWPORT to LOGICAL
            (fb_scale_x, fb_scale_y),                    # LOGICAL to CANVAS
            (cnv_ox, cnv_oy),                              # CANVAS to FRAMEBUFFER
        )

        i_from = from_space.value
        i_to = to_space.value
        if i_from == i_to:
            return x, y

        forward = i_from < i_to
        steps = range(i_from, i_to) if forward else range(i_from, i_to, -1)
        for i in steps:
            if forward:
                fn = _converters.get((_PIPELINE[i], _PIPELINE[i + 1]))
                args = _ARGS[i]
            else:
                fn = _converters.get((_PIPELINE[i], _PIPELINE[i - 1]))
                args = _ARGS[i - 1]
            x, y = fn(x, y, *args)

        return x, y

# ======================================== EXPORTS ========================================
__all__ = [
    "CoordSpace",

    "world_to_frustum",
    "frustum_to_ndc",
    "ndc_to_nvc",
    "nvc_to_viewport",
    "viewport_to_logical",
    "logical_to_canvas",
    "canvas_to_framebuffer",
    "framebuffer_to_canvas",
    "canvas_to_logical",
    "logical_to_viewport",
    "viewport_to_nvc",
    "nvc_to_ndc",
    "ndc_to_frustum",
    "frustum_to_world",

    "CoordContext",

]