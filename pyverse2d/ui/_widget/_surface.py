# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect
from ...asset import Color
from ...abc import Widget, Shape
from ...math import Point

from numbers import Real

# ======================================== WIDGET ========================================
class Surface(Widget):
    """
    Composant UI : Surface

    Args:
        pos(Point, optional): position
        anchor(Point, optional): ancre locale relative
        opacité(Real, optional): opacité [0; 1]
        parent(Widget, optional): Composant UI parent
    """
    __slots__ = ()

    def __init__(
            self,
            shape: Shape,
            pos: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            filling: bool = True,
            filling_color: Color = (125, 125, 125),
            border_width: int = 0,
            border_color: Color = (0, 0, 0),
            opacity: Real = 1.0,
            parent: Widget = None,
        ):
        super().__init__(parent, pos, anchor, opacity)