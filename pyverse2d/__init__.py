# ======================================== IMPORTS ========================================
from __future__ import annotations
from ._version import __version__

import pyglet

# ======================================== PRIMITIVES ========================================
from . import typing, abc, math, shape, asset

# ======================================== STATE ========================================
from ._rendering import Window, LogicalScreen, Viewport, Camera, Pipeline

_pipeline: Pipeline | None = None

# ======================================== MANAGERS ========================================
from ._managers import ContextManager, TimeManager, EventManager, KeyManager, MouseManager, InputsManager, UiManager

_context_manager: ContextManager = ContextManager()

# Time
time: TimeManager = TimeManager(_context_manager)
_context_manager.time = time

# Event
event: EventManager = EventManager(_context_manager)
_context_manager.event = event

# Key
key: KeyManager = KeyManager(_context_manager)
_context_manager.key = key

# Mouse
mouse: MouseManager = MouseManager(_context_manager)
_context_manager.mouse = mouse

# Inputs
inputs: InputsManager = InputsManager(_context_manager)
_context_manager.inputs = inputs

# Ui
ui: UiManager = UiManager(_context_manager)
_context_manager.ui = ui

# ======================================== NODES ========================================
from . import world, tile, gui, scene

# ======================================== SETTERS ========================================
def set_window(window: Window):
    """
    Définit la fenêtre du moteur

    Args:
        window (Window): fenêtre à utiliser
    """
    global _pipeline
    if not isinstance(window, Window):
        raise TypeError("Expected a Window instance")
    _pipeline = Pipeline(window)

    for manager in _context_manager:
        manager.bind(window)

    @_pipeline.window.native.event
    def on_draw():
        _pipeline.window.clear()
        scene.draw(_pipeline)

# ======================================== LOOP ========================================
def run(update: callable = None):
    """Démarre la boucle de mise à jour"""
    if _pipeline is None:
        raise RuntimeError("No window set, try set_window() before run()")

    def _update(raw_dt: float):
        # Calcul du delta-time
        dt = time.tick(raw_dt)

        # Actualisation des gestionnaires
        for manager in _context_manager:
            manager.update(dt)
        
        # Actualisation des scenes
        scene.update(dt)

        # Appel de la fonction externe
        if update is not None:
            update(dt)

        # Nettoyage
        for manager in _context_manager:
            manager.flush()

    # Lancement
    time.schedule(_update)
    pyglet.app.run()

# ======================================== EXPORTS ========================================
__all__ = [
    "Window",
    "LogicalScreen",
    "Viewport",
    "Camera",

    "TimeManager",
    "EventManager",
    "KeyManager",
    "MouseManager",
    "InputsManager",
    "UiManager"

    "time",
    "event",
    "key",
    "mouse",
    "inputs",
    "ui",

    "typing",
    "abc",
    "math",
    "shape",
    "asset",
    "world",
    "tile",
    "gui",
    "scene",

    "set_window",
    "run",
]