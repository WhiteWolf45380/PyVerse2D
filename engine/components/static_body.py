# ======================================== IMPORTS ========================================
from ..core import Component

from numbers import Real

# ======================================== COMPONENT ========================================
class StaticBody(Component):
    """Composant gérant un corps immobile"""
    __slots__ = ("_friction", "_restitution")
    exclusive = True
    requires = ("Transform",)

    def __init__(
            self,
            friction: Real = 0.5,
            restitution: Real = 0.0,
        ):
        ...