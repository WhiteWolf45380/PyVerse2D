# ======================================== IMPORTS ========================================
from __future__ import annotations
from ._version import __version__

import pyglet

# ======================================== PRIMITIVES ========================================
from . import abc, math, shape, asset, request
from ._flag import Key as key

# ======================================== STATE ========================================
from ._rendering import Screen, Window, Pipeline

_window: Window | None = None
_pipeline: Pipeline | None = None
_fps: int = 60

# ======================================== MANAGERS ========================================
from ._managers import ContextManager, InputsManager, UIManager

_context_manager: ContextManager = ContextManager()

# Inputs
inputs: InputsManager = InputsManager(_context_manager)
_context_manager.inputs = inputs

# Ui
ui_manager: UIManager = UIManager(_context_manager)
_context_manager.ui_manager = ui_manager

# ======================================== NODES ========================================
from . import world, tile, ui, scene

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
    inputs.bind(window)

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
        raise RuntimeError("No window set, try set_window() before run()")

    def _update(dt: float):
        for manager in _context_manager:
            manager.update(dt)
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
    "request",
    "world",
    "tile",
    "ui",
    "scene",

    "key",

    "_context_manager",
    "inputs",
    "ui_manager",

    "set_window",
    "set_fps",
    "run",
]