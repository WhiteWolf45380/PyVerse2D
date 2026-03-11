# ======================================== IMPORTS ========================================
import pyglet

# ======================================== IMPORTS ========================================
class Window:
    """Fenêtre du jeu"""
    def __init__(self, width: int = 1280, height: int = 720, caption: str = "2D Game Engine Window"):
        self._window = pyglet.window.Window(1280, 720, caption=caption, resizable=True)