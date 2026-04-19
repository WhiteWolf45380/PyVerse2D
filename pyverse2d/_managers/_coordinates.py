# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._flag import CoordSpace
from .._rendering import Window, Viewport, Camera
from ..abc import Manager

from typing import Callable
import math

# ======================================== PIPELINE ========================================
_PIPELINE = [
    CoordSpace.WORLD,
    CoordSpace.FRUSTUM,
    CoordSpace.NDC,
    CoordSpace.NVC,
    CoordSpace.VIEWPORT,
    CoordSpace.LOGICAL,
    CoordSpace.CANVAS,
    CoordSpace.WINDOW,
]

# ======================================== MANAGER ========================================
class CoordinatesManager(Manager):
    """Gestionnaire global des conversions de coordonnées"""
    __slots__ = (
        "_window",
        "_viewport", "_viewport_resolve",
        "_camera", "_camera_resolve",
        "_temporary_camera", "_temporary_camera_resolve",
    )

    _ID: str = "coordinates"

    def __init__(self, window: Window) -> None:
        self._window: Window = window
        self._viewport: Viewport = None
        self._viewport_resolve: tuple = None
        self._camera: Camera = None
        self._camera_resolve: tuple = None
        self._temporary_camera: Camera = None
        self._temporary_camera_resolve: tuple = None

    # ======================================== BIND ========================================
    def bind_viewport(self, viewport: Viewport) -> None:
        """Résout et met en cache le viewport courant.
        Appelé par Scene avant de boucler sur les temporarys.
        """
        screen = self._window.screen
        self._viewport = viewport
        self._viewport_resolve = viewport.resolve(screen.width, screen.height)
        self._camera = None
        self._camera_resolve = None
        self._temporary_camera = None
        self._temporary_camera_resolve = None

    def bind_camera(self, camera: Camera) -> None:
        """Résout et met en cache la caméra principale de la scène.
        Appelé par Scene après bind_viewport.
        """
        _, _, lw, lh, _, _ = self._viewport_resolve
        self._camera = camera
        self._camera_resolve = camera.resolve(lw, lh)

    def bind_temporary_camera(self, camera: Camera) -> None:
        """Résout et met en cache la caméra locale d'un temporary.
        Appelé par temporary si celui-ci possède sa propre caméra.
        Prend le dessus sur la caméra de scène pour la durée du temporary.
        """
        _, _, lw, lh, _, _ = self._viewport_resolve
        self._temporary_camera = camera
        self._temporary_camera_resolve = camera.resolve(lw, lh)

    def unbind_temporary_camera(self) -> None:
        """Restaure la caméra de scène comme caméra active.
        Appelé par temporary en fin d'update/render.
        """
        self._temporary_camera = None
        self._temporary_camera_resolve = None

    # ======================================== FAST CONVERSIONS ========================================
    def world_to_logical(self, x: float, y: float, viewport: Viewport = None, camera: Camera = None) -> tuple[int, int]:
        """Conversion directe World to Logical (espace LogicalScreen)"""
        vp_r, cam_r = self._resolve(viewport, camera)
        lx, ly, lw, lh, (ox, oy), (dx, dy) = vp_r
        cx, cy, vw, vh, zoom, rotation = cam_r

        fx, fy = x - cx, y - cy
        if rotation != 0.0:
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            fx, fy = fx * c + fy * s, -fx * s + fy * c

        fx = ((fx / ((vw / zoom) / 2)) + 1) / 2
        fy = ((fy / ((vh / zoom) / 2)) + 1) / 2

        return int(lx + ox + fx * lw * dx), int(ly + oy + fy * lh * dy)

    def logical_to_world(self, x: float, y: float, viewport: Viewport = None, camera: Camera = None) -> tuple[float, float]:
        """Conversion directe Logical to World"""
        vp_r, cam_r = self._resolve(viewport, camera)
        lx, ly, lw, lh, (ox, oy), (dx, dy) = vp_r
        cx, cy, vw, vh, zoom, rotation = cam_r

        nvc_x = (x - lx - ox) / (dx * lw)
        nvc_y = (y - ly - oy) / (dy * lh)

        fr_x = (nvc_x * 2 - 1) * (vw / zoom) / 2
        fr_y = (nvc_y * 2 - 1) * (vh / zoom) / 2

        if rotation != 0.0:
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            fr_x, fr_y = fr_x * c - fr_y * s, fr_x * s + fr_y * c
        return fr_x + cx, fr_y + cy

    def window_to_world(self, x: float, y: float, viewport: Viewport = None, camera: Camera = None) -> tuple[float, float]:
        """Conversion directe Window to World"""
        vp_r, cam_r = self._resolve(viewport, camera)
        lx, ly, lw, lh, (ox, oy), (dx, dy) = vp_r
        cx, cy, vw, vh, zoom, rotation = cam_r
        canvas = self._window.canvas

        log_x = (x - canvas.x) * self._window.physical_scale
        log_y = (y - canvas.y) * self._window.physical_scale

        nvc_x = (log_x - lx - ox) / (dx * lw)
        nvc_y = (log_y - ly - oy) / (dy * lh)

        fr_x = (nvc_x * 2 - 1) * (vw / zoom) / 2
        fr_y = (nvc_y * 2 - 1) * (vh / zoom) / 2

        if rotation != 0.0:
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            fr_x, fr_y = fr_x * c - fr_y * s, fr_x * s + fr_y * c
        return fr_x + cx, fr_y + cy

    def world_to_window(self, x: float, y: float, viewport: Viewport = None, camera: Camera = None) -> tuple[int, int]:
        """Conversion directe World to Window"""
        vp_r, cam_r = self._resolve(viewport, camera)
        lx, ly, lw, lh, (ox, oy), (dx, dy) = vp_r
        cx, cy, vw, vh, zoom, rotation = cam_r
        canvas = self._window.canvas

        fx, fy = x - cx, y - cy
        if rotation != 0.0:
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            fx, fy = fx * c + fy * s, -fx * s + fy * c

        fx = ((fx / ((vw / zoom) / 2)) + 1) / 2
        fy = ((fy / ((vh / zoom) / 2)) + 1) / 2

        log_x = lx + ox + fx * lw * dx
        log_y = ly + oy + fy * lh * dy

        return (
            int(canvas.x + log_x * self._window.logical_scale),
            int(canvas.y + log_y * self._window.logical_scale),
        )

    # ======================================== GLOBAL CONVERSIONS ========================================
    def convert(
        self,
        x: float,
        y: float,
        from_space: CoordSpace,
        to_space: CoordSpace,
        viewport: Viewport = None,
        camera: Camera = None,
    ) -> tuple[float, float]:
        """Convertit (x, y) entre deux espaces quelconques via le pipeline step-by-step"""
        vp_r, cam_r = self._resolve(viewport, camera)
        lx, ly, lw, lh, (ox, oy), (dx, dy) = vp_r
        cx, cy, vw, vh, zoom, rotation = cam_r
        canvas = self._window.canvas

        _ARGS = (
            (cx, cy, rotation),            # WORLD    to FRUSTUM
            (vw, vh, zoom),                # FRUSTUM  to NDC
            (),                            # NDC      to NVC
            (lw, lh, ox, oy, dx, dy),      # NVC      to VIEWPORT
            (lx, ly),                      # VIEWPORT to LOGICAL
            (self._window.logical_scale,), # LOGICAL  to CANVAS
            (canvas.x, canvas.y),          # CANVAS   to WINDOW
        )

        i_from, i_to = from_space.value, to_space.value
        if i_from == i_to:
            return x, y

        forward = i_from < i_to
        for i in (range(i_from, i_to) if forward else range(i_from, i_to, -1)):
            if forward:
                fn = _CONVERTERS[(_PIPELINE[i], _PIPELINE[i + 1])]
                args = _ARGS[i]
            else:
                fn = _CONVERTERS[(_PIPELINE[i], _PIPELINE[i - 1])]
                args = _ARGS[i - 1]
            x, y = fn(x, y, *args)

        return x, y
    
    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        pass

    def flush(self) -> None:
        """Nettoyage"""
        pass

    # ======================================== INTERNALS ========================================
    def _resolve(self, viewport: Viewport = None, camera: Camera = None) -> tuple[tuple, tuple]:
        """Renvoie (viewport_resolve, camera_resolve) en combinant overrides et contexte courant.
        
        Priorité caméra : override explicite > caméra temporary > caméra scène
        """
        if viewport is not None:
            screen = self._window.screen
            vp_r = viewport.resolve(screen.width, screen.height)
        elif self._viewport_resolve is not None:
            vp_r = self._viewport_resolve
        else:
            raise RuntimeError(
                "CoordinatesManager : no viewport available")

        if camera is not None:
            _, _, lw, lh, _, _ = vp_r
            cam_r = camera.resolve(lw, lh)
        elif self._temporary_camera_resolve is not None:
            cam_r = self._temporary_camera_resolve
        elif self._camera_resolve is not None:
            cam_r = self._camera_resolve
        else:
            raise RuntimeError(
                "CoordinatesManager : no camera available")

        return vp_r, cam_r

    # ======================================== WORLD to WINDOW ========================================
    @staticmethod
    def world_to_frustum(x: float, y: float, cx: float = 0.0, cy: float = 0.0, rotation: float = 0.0) -> tuple[float, float]:
        """World to Frustum : translation caméra + rotation"""
        fx, fy = x - cx, y - cy
        if rotation != 0.0:
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            fx, fy = fx * c + fy * s, -fx * s + fy * c
        return fx, fy

    @staticmethod
    def frustum_to_ndc(fr_x: float, fr_y: float, vw: float, vh: float, zoom: float) -> tuple[float, float]:
        """Frustum to NDC : normalisation par le demi-frustum"""
        return fr_x / ((vw / zoom) / 2), fr_y / ((vh / zoom) / 2)

    @staticmethod
    def ndc_to_nvc(ndc_x: float, ndc_y: float) -> tuple[float, float]:
        """NDC [-1, 1] to NVC [0, 1]"""
        return (ndc_x + 1) / 2, (ndc_y + 1) / 2

    @staticmethod
    def nvc_to_viewport(nvc_x: float, nvc_y: float, lw: float, lh: float, ox: float, oy: float, dx: float, dy: float) -> tuple[float, float]:
        """NVC to Viewport : mise à l'échelle + offset + direction"""
        return ox + nvc_x * lw * dx, oy + nvc_y * lh * dy

    @staticmethod
    def viewport_to_logical(vp_x: float, vp_y: float, lx: float, ly: float) -> tuple[float, float]:
        """Viewport (relatif) to Logical (absolu dans le LogicalScreen)"""
        return lx + vp_x, ly + vp_y

    @staticmethod
    def logical_to_canvas(log_x: float, log_y: float, logical_scale: float) -> tuple[int, int]:
        """Logical to Canvas : mise à l'échelle vers les pixels physiques"""
        return int(log_x * logical_scale), int(log_y * logical_scale)

    @staticmethod
    def canvas_to_window(cnv_x: float, cnv_y: float, cnv_ox: float, cnv_oy: float) -> tuple[float, float]:
        """Canvas to Window : ajout de l'offset du canvas dans la fenêtre OS"""
        return cnv_ox + cnv_x, cnv_oy + cnv_y

    # ======================================== WINDOW to WORLD ========================================
    @staticmethod
    def window_to_canvas(win_x: float, win_y: float, cnv_ox: float, cnv_oy: float) -> tuple[float, float]:
        """Window to Canvas"""
        return win_x - cnv_ox, win_y - cnv_oy

    @staticmethod
    def canvas_to_logical(cnv_x: float, cnv_y: float, logical_scale: float) -> tuple[float, float]:
        """Canvas to Logical : pixels physiques to espace logique"""
        return cnv_x / logical_scale, cnv_y / logical_scale

    @staticmethod
    def logical_to_viewport(log_x: float, log_y: float, lx: float, ly: float) -> tuple[float, float]:
        """Logical (absolu) to Viewport (relatif)"""
        return log_x - lx, log_y - ly

    @staticmethod
    def viewport_to_nvc(vp_x: float, vp_y: float, lw: float, lh: float, ox: float, oy: float, dx: float, dy: float) -> tuple[float, float]:
        """Viewport to NVC"""
        return (vp_x - ox) / (dx * lw), (vp_y - oy) / (dy * lh)

    @staticmethod
    def nvc_to_ndc(nvc_x: float, nvc_y: float) -> tuple[float, float]:
        """NVC [0, 1] to NDC [-1, 1]"""
        return nvc_x * 2 - 1, nvc_y * 2 - 1

    @staticmethod
    def ndc_to_frustum(ndc_x: float, ndc_y: float, vw: float, vh: float, zoom: float) -> tuple[float, float]:
        """NDC to Frustum"""
        return ndc_x * (vw / zoom) / 2, ndc_y * (vh / zoom) / 2

    @staticmethod
    def frustum_to_world(fr_x: float, fr_y: float, cx: float = 0.0, cy: float = 0.0, rotation: float = 0.0) -> tuple[float, float]:
        """Frustum to World : rotation inverse + translation caméra"""
        if rotation != 0.0:
            rad = math.radians(rotation)
            c, s = math.cos(rad), math.sin(rad)
            fr_x, fr_y = fr_x * c - fr_y * s, fr_x * s + fr_y * c
        return fr_x + cx, fr_y + cy

# ======================================== REGISTER ========================================
_CONVERTERS: dict[tuple[CoordSpace, CoordSpace], Callable] = {
    # World to Window
    (CoordSpace.WORLD,    CoordSpace.FRUSTUM):  CoordinatesManager.world_to_frustum,
    (CoordSpace.FRUSTUM,  CoordSpace.NDC):       CoordinatesManager.frustum_to_ndc,
    (CoordSpace.NDC,      CoordSpace.NVC):       CoordinatesManager.ndc_to_nvc,
    (CoordSpace.NVC,      CoordSpace.VIEWPORT):  CoordinatesManager.nvc_to_viewport,
    (CoordSpace.VIEWPORT, CoordSpace.LOGICAL):   CoordinatesManager.viewport_to_logical,
    (CoordSpace.LOGICAL,  CoordSpace.CANVAS):    CoordinatesManager.logical_to_canvas,
    (CoordSpace.CANVAS,   CoordSpace.WINDOW):    CoordinatesManager.canvas_to_window,
    # Window to World
    (CoordSpace.WINDOW,   CoordSpace.CANVAS):    CoordinatesManager.window_to_canvas,
    (CoordSpace.CANVAS,   CoordSpace.LOGICAL):   CoordinatesManager.canvas_to_logical,
    (CoordSpace.LOGICAL,  CoordSpace.VIEWPORT):  CoordinatesManager.logical_to_viewport,
    (CoordSpace.VIEWPORT, CoordSpace.NVC):       CoordinatesManager.viewport_to_nvc,
    (CoordSpace.NVC,      CoordSpace.NDC):       CoordinatesManager.nvc_to_ndc,
    (CoordSpace.NDC,      CoordSpace.FRUSTUM):   CoordinatesManager.ndc_to_frustum,
    (CoordSpace.FRUSTUM,  CoordSpace.WORLD):     CoordinatesManager.frustum_to_world,
}

# ======================================== EXPORTS ========================================
__all__ = ["CoordinatesManager"]