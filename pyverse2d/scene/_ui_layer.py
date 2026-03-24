# ======================================== IMPORTS ========================================
from .._internal import expect
from .._flag import CameraMode
from .._rendering._pipeline import Pipeline
from ..ui import Widget

from ..abc import Layer

# ======================================== LAYER ========================================
class UILayer(Layer):
    """
    Layer contenant un World

    Args:
        widgets(Widget, optional): composants ui
        camera_mode(CameraMode, optional): camera behavior
    """
    def __init__(self, *widgets: Widget, camera_mode: CameraMode = CameraMode.WORLD):
        super().__init__(camera_mode)
        self._widgets: list[Widget] = list(expect(widgets, tuple[Widget]))
    
    # ======================================== GETTERS ========================================
    @property
    def widgets(self) -> list[Widget]:
        """Renvoie l'ensemble des composants assignés"""
        return self._widgets

    # ======================================== CYCLE DE VIE ========================================
    def on_start(self):
        """Activation du layer"""
        ...

    def on_stop(self):
        """Désactivation du layer"""
        ...

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        """Actualisation du layer"""
        for widget in self._widgets:
            widget.update(dt)

    def draw(self, pipeline: Pipeline):
        """Affichage du layer"""
        for widget in self._widgets:
            widget.draw(pipeline)