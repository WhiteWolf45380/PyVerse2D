# ======================================== IMPORTS ========================================
from __future__ import annotations
from ._version import __version__

from . import abc, math, shape, asset, world, map, ui, scene

from ._rendering import Screen, Window
from ._rendering._pipeline import Pipeline

import pyglet

# ======================================== STATE ========================================
_window: Window | None = None
_pipeline: Pipeline | None = None
_fps: int = 60

# ======================================== SETTERS ========================================
def set_window(window: Window):
    """
    Définit la fenêtre du moteur

    Args:
        window (Window): fenêtre à utiliser
    """
    global _window
    global _pipeline
    if not isinstance(window, Window):
        raise TypeError("Expected a Window instance")
    _window = window
    _pipeline = Pipeline(window)

    @_window.native.event
    def on_draw():
        _window.clear()
        scene.draw(_pipeline)

def set_fps(fps: int):
    """
    Définit le nombre de mises à jour par seconde

    Args:
        fps (int): fps cible
    """
    global _fps
    _fps = int(fps)

# ======================================== LOOP ========================================
def run(update: callable = None):
    """Démarre la boucle de mise à jour"""
    if _window is None:
        raise RuntimeError("No window set - call set_window() before run()")

    def _update(dt: float):
        scene.update(dt)
        if update is not None:
            update(dt)

    pyglet.clock.schedule_interval(_update, 1 / _fps)
    pyglet.app.run()

# ======================================== EXPORTS ========================================
__all__ = [
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