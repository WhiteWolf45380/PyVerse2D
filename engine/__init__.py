# ======================================== IMPORTS ========================================
from __future__ import annotations

from . import abc, math, shape, asset, world, map, ui, scene

from ._rendering import Camera, Viewport, Screen, Window

import pyglet

# ======================================== STATE ========================================
_window: Window | None = None
_fps: int = 60

# ======================================== SETTERS ========================================
def set_window(window: Window):
    """
    Définit la fenêtre du moteur

    Args:
        window (Window): fenêtre à utiliser
    """
    global _window
    if not isinstance(window, Window):
        raise TypeError("Expected a Window instance")
    _window = window

    @_window.native.event
    def on_draw():
        _window.clear()
        scene.draw()

def set_fps(fps: int):
    """
    Définit le nombre de mises à jour par seconde

    Args:
        fps (int): fps cible
    """
    global _fps
    _fps = int(fps)

# ======================================== LOOP ========================================
def run():
    """Démarre la boucle de mise à jour"""
    if _window is None:
        raise RuntimeError("No window set — call engine.set_window() before engine.run()")
    pyglet.clock.schedule_interval(_update, 1 / _fps)
    pyglet.app.run()

def _update(dt: float):
    scene.update(dt)

# ======================================== EXPORTS ========================================
__all__ = [
    "Camera",
    "Viewport",
    "Screen",
    "Window",

    "abc",
    "math",
    "shape",
    "asset",
    "world",
    "map",
    "ui",
    "scene",

    "set_window",
    "set_fps",
    "run",
]