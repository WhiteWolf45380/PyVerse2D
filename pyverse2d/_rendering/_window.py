# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from ._screen import Screen

import pyglet
from pyglet.math import Mat4
from pyglet.window import Window as PygletWindow

from numbers import Real

# ======================================== OBJET ========================================
class Window:
    """Fenêtre OS

    Args:
        screen: espace logique de référence
        width: largeur initiale de la fenêtre
        height: hauteur initiale de la fenêtre
        caption: titre de la fenêtre
        fullscreen: démarre en plein écran
        resizable: autorise le redimensionnement
        vsync: synchronisation verticale
        borderless: fenêtre sans décoration OS
        transparent: fenêtre transparente
        min_width: largeur minimale (si resizable)
        min_height: hauteur minimale (si resizable)
        visible: rend la fenêtre visible immédiatement
    """
    __slots__ = (
        "_screen", "_pyglet_window", "_viewport",
        "_framebuffer_scale_x", "_framebuffer_scale_y",
    )

    def __init__(
        self,
        screen: Screen = None,
        width: int = 1280,
        height: int = 720,
        caption: str = "",
        icon_path: str = None,
        fullscreen: bool = False,
        resizable: bool = True,
        vsync: bool = True,
        borderless: bool = False,
        transparent: bool = False,
        min_width: int | None = None,
        min_height: int | None = None,
        visible: bool = True,
    ):
        # Espace logique de référence
        if expect(screen, (Screen, None)) is None:
            screen = Screen()
        self._screen: Screen = screen

        # Style de la fenêtre
        if transparent:
            style = pyglet.window.Window.WINDOW_STYLE_TRANSPARENT
        elif borderless:
            style = pyglet.window.Window.WINDOW_STYLE_BORDERLESS
        else:
            style = pyglet.window.Window.WINDOW_STYLE_DEFAULT

        # Fenêtre OS
        self._pyglet_window: PygletWindow = pyglet.window.Window(
            width=width,
            height=height,
            caption=caption,
            fullscreen=fullscreen,
            resizable=resizable,
            vsync=vsync,
            style=style,
            visible=visible,
        )

        # Icon
        if icon_path is not None:
            try:
                icon = pyglet.image.load(icon_path)
                self._pyglet_window.set_icon(icon)
            except Exception:
                pass

        # Dimensions minimales
        if resizable and (min_width is not None or min_height is not None):
            self._pyglet_window.set_minimum_size(min_width or 1, min_height or 1,)

        # Projection
        self._viewport: tuple[int, int, int, int] = None
        self._framebuffer_scale_x: float = 1.0
        self._framebuffer_scale_y: float = 1.0
        self._apply_projection(width, height)

        @self._pyglet_window.event
        def on_resize(w: int, h: int):
            self._apply_projection(w, h)

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation de la fenêtre"""
        return (f"Window({self.width}x{self.height}, screen={self.screen})")

    # ======================================== PROPERTIES ========================================
    @property
    def native(self) -> PygletWindow:
        """Renvoie la fenêtre pyglet"""
        return self._pyglet_window

    @property
    def screen(self) -> Screen:
        """Espace logique de référence"""
        return self._screen
    
    @property
    def size(self) -> tuple[int, int]:
        """Taille actuelle de la fenpetre OS"""
        return (self._pyglet_window.width, self._pyglet_window.height)

    @property
    def width(self) -> int:
        """Largeur actuelle de la fenêtre OS"""
        return self._pyglet_window.width

    @property
    def height(self) -> int:
        """Hauteur actuelle de la fenêtre OS"""
        return self._pyglet_window.height

    @property
    def viewport(self) -> tuple[int, int, int, int]:
        """(x, y, w, h) du viewport actif dans la fenêtre OS"""
        return self._viewport
    
    @property
    def framebuffer_scale(self) -> tuple[float, float]:
        """Ratio pixels framebuffer / pixels logiques"""
        return (self._framebuffer_scale_x, self._framebuffer_scale_y)
    
    @property
    def framebuffer_scale_x(self) -> float:
        """Ratio horizontal pixels framebuffer / pixels logiques"""
        return self._framebuffer_scale_x
    
    @property
    def framebuffer_scale_y(self) -> float:
        """Ratio vertical pixels framebuffer / pixels logiques"""
        return self._framebuffer_scale_y

    # ======================================== SETTERS ========================================
    def set_caption(self, caption: str):
        """Fixe le nom de la fenêtre"""
        self._pyglet_window.set_caption(caption)

    def set_fullscreen(self, value: bool):
        """Fixe le plein écran"""
        self._pyglet_window.set_fullscreen(value)

    def set_visible(self, value: bool):
        """Fixe la visibilité"""
        self._pyglet_window.set_visible(value)

    def set_size(self, width: int, height: int):
        """Redimensionne la fenêtre"""
        self._pyglet_window.set_size(width, height)

    def set_position(self, x: int, y: int):
        """Déplace la fenêtre sur le bureau"""
        self._pyglet_window.set_location(x, y)
    
    # ======================================== COLLECTIONS ========================================
    def center(self):
        """Centre la fenêtre sur l'écran principal"""
        display = pyglet.display.get_display()
        monitors = display.get_screens()
        monitor = monitors[0]
        x = (monitor.width - self._pyglet_window.width)  // 2
        y = (monitor.height - self._pyglet_window.height) // 2
        self._pyglet_window.set_location(x, y)
    
    def clear(self):
        """Efface le contenu de la fenêtre"""
        self._pyglet_window.clear()

    def close(self):
        """Ferme la fenêtre"""
        self._pyglet_window.close()

    # ======================================== CONVERSIONS ========================================
    def screen_to_window(self, x: Real, y: Real) -> tuple[float, float]:
        """Convertit des coordonnées de l'espace logique vers la fenêtre OS

        Args:
            x : coordonnée horizontale logique
            y: coordonnée verticale logique
        """
        vx, vy, _, _ = self._viewport
        return vx + x * self._framebuffer_scale_x, vy + y * self.framebuffer_scale_y

    def window_to_screen(self, x: Real, y: Real) -> tuple[float, float]:
        """Convertit des coordonnées de la fenêtre OS vers l'espace logique

        Args:
            x: coordonnée horizontale dans la fenêtre OS
            y: coordonnée verticale dans la fenêtre OS
        """
        vx, vy, _, _ = self._viewport
        return (x - vx) * (1 / self._framebuffer_scale_x), (y - vy) * (1 / self.framebuffer_scale_y)
    
    # ======================================== INTERNALS ========================================
    def _apply_projection(self, win_w: int, win_h: int):
        """Letterboxing + projection orthogonale vers l'espace virtuel"""
        # Calcul des ratios
        screen_ratio = self._screen.ratio
        win_ratio = win_w / win_h

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
        self._pyglet_window.projection = Mat4.orthogonal_projection(
            left=0.0,
            right=self._screen.width,
            bottom=0.0,
            top=self._screen.height,
            z_near=-1.0,
            z_far=1.0,
        )

        # Mise en cache des ratios
        self._framebuffer_scale_x = w / self._screen.width
        self._framebuffer_scale_y = h / self._screen.height