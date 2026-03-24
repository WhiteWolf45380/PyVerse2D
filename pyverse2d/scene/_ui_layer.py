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
    
    # ======================================== PUBLIC METHODS ========================================
    def add(self, widget: Widget, z: int) -> None:
        """
        Ajoute un composant

        Args:
            widget(Widget): composant à ajouter
        """
        self._insert(expect(widget, Widget), widget.z)
    
    def remove(self, widget: Widget) -> None:
        """
        Retire un composant

        Args:
            widget(Widget): composant à ajouter
        """
        self._widgets.remove(expect(widget, Widget))
        self._sort()

    # ======================================== CYCLE DE VIE ========================================
    def on_start(self) -> None:
        """Activation du layer"""
        ...

    def on_stop(self) -> None:
        """Désactivation du layer"""
        ...

    # ======================================== LOOP ========================================
    def update(self, dt: float) -> None:
        """Actualisation du layer"""
        for widget in self._widgets:
            widget.update(dt)

    def draw(self, pipeline: Pipeline) -> None:
        """Affichage du layer"""
        for widget in self._widgets:
            widget.draw(pipeline)
    
    # ======================================== INTERNALS ========================================