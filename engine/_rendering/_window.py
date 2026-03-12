# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from ._screen import Screen

import pyglet
import pyglet.gl as gl
from pyglet.math import Mat4

# ======================================== OBJET ========================================
class Window:
    """
    Fenêtre OS redimensionnable

    Args:
        screen(Screen): space logique de référence
        width(int): largeur initiale de la fenêtre
        height(int): hauteur initiale de la fenêtre
        title(str): titre de la fenêtre
        fullscreen(bool): démarre en plein écran
        resizable(bool): autorise le redimensionnement
        vsync(bool): synchronisation verticale
        borderless(bool): fenêtre sans décoration OS
        min_width(int|None): largeur minimale (si resizable)
        min_height(int|None): hauteur minimale (si resizable)
        visible(bool): rend la fenêtre visible immédiatement
    """
    def __init__(
        self,
        screen: Screen = None,
        width: int = 1280,
        height: int = 720,
        title: str = "",
        fullscreen: bool = False,
        resizable: bool = True,
        vsync: bool = True,
        borderless: bool = False,
        min_width: int | None = None,
        min_height: int | None = None,
        visible: bool = True,
    ):
        # Espace logique de référence
        if expect(screen, (Screen, None)) is None:
            screen = Screen()
        self._screen = screen

        # Fenêtre OS
        style = (
            pyglet.window.Window.WINDOW_STYLE_BORDERLESS
            if borderless
            else pyglet.window.Window.WINDOW_STYLE_DEFAULT
        )

        self._window = pyglet.window.Window(
            width=width,
            height=height,
            caption=title,
            fullscreen=fullscreen,
            resizable=resizable,
            vsync=vsync,
            style=style,
            visible=visible,
        )

        if resizable and (min_width is not None or min_height is not None):
            self._window.set_minimum_size(
                min_width  or 1,
                min_height or 1,
            )

        # Projection
        self._viewport: tuple[int, int, int, int] = (0, 0, width, height)
        self._apply_projection(width, height)

        @self._window.event
        def on_resize(w: int, h: int):
            self._apply_projection(w, h)

    # ======================================== PROJECTION ========================================
    def _apply_projection(self, win_w: int, win_h: int):
        """Letterboxing + projection orthogonale vers l'espace logique"""
        if win_w <= 0 or win_h <= 0:
            return

        screen_ratio = self._screen.ratio
        win_ratio    = win_w / win_h

        # Bandes latérales
        if win_ratio > screen_ratio:
            h = win_h
            w = int(h * screen_ratio)
            x = (win_w - w) // 2
            y = 0
        
        # Bandes horizontales
        else:
            w = win_w
            h = int(w / screen_ratio)
            x = 0
            y = (win_h - h) // 2

        # Matrice de projection
        self._viewport = (x, y, w, h)
        gl.glViewport(x, y, w, h)

        self._window.projection = Mat4.orthogonal_projection(
            left=0,
            right=self._screen.width,
            bottom=0,
            top=self._screen.height,
            z_near=-1,
            z_far=1,
        )

    # ======================================== GETTERS ========================================
    @property
    def screen(self) -> Screen:
        """Espace logique de référence"""
        return self._screen

    @property
    def width(self) -> int:
        """Largeur actuelle de la fenêtre OS"""
        return self._window.width

    @property
    def height(self) -> int:
        """Hauteur actuelle de la fenêtre OS"""
        return self._window.height

    @property
    def size(self) -> tuple[int, int]:
        return self._window.width, self._window.height

    @property
    def viewport(self) -> tuple[int, int, int, int]:
        """(x, y, w, h) du viewport actif dans la fenêtre OS"""
        return self._viewport

    @property
    def native(self) -> pyglet.window.Window: # type: ignore
        """Fenêtre pyglet brute — usage interne uniquement"""
        return self._window

    # ======================================== CONVERSIONS ========================================
    def screen_to_window(self, x: float, y: float) -> tuple[float, float]:
        """
        Convertit des coordonnées de l'espace logique vers la fenêtre OS.

        Args:
            x (float): coordonnée horizontale logique
            y (float): coordonnée verticale logique
        """
        vx, vy, vw, vh = self._viewport
        sx = vw / self._screen.width
        sy = vh / self._screen.height
        return x * sx + vx, y * sy + vy

    def window_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """
        Convertit des coordonnées de la fenêtre OS vers l'espace logique.

        Args:
            x (float): coordonnée horizontale dans la fenêtre OS
            y (float): coordonnée verticale dans la fenêtre OS
        """
        vx, vy, vw, vh = self._viewport
        sx = self._screen.width  / vw
        sy = self._screen.height / vh
        return (x - vx) * sx, (y - vy) * sy

    # ======================================== MÉTHODES ========================================
    def clear(self):
        """Efface le contenu de la fenêtre"""
        self._window.clear()

    def set_title(self, title: str):
        self._window.set_caption(title)

    def set_fullscreen(self, value: bool):
        self._window.set_fullscreen(value)

    def set_visible(self, value: bool):
        self._window.set_visible(value)

    def set_size(self, width: int, height: int):
        """Redimensionne la fenêtre (sans effet en fullscreen)"""
        self._window.set_size(width, height)

    def set_position(self, x: int, y: int):
        """Déplace la fenêtre sur le bureau"""
        self._window.set_location(x, y)

    def center(self):
        """Centre la fenêtre sur l'écran principal"""
        display  = pyglet.display.get_display()
        monitors = display.get_screens()
        monitor  = monitors[0]
        x = (monitor.width  - self._window.width)  // 2
        y = (monitor.height - self._window.height) // 2
        self._window.set_location(x, y)

    def close(self):
        self._window.close()

    def __repr__(self) -> str:
        return (
            f"Window({self._window.width}x{self._window.height}, "
            f"screen={self._screen})"
        )