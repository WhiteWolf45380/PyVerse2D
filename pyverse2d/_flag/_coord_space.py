# ======================================== IMPORTS ========================================
from enum import IntEnum

# ======================================== FLAG ========================================
class CoordSpace(IntEnum):
    """Espaces de coordonnées"""
    WORLD = 0
    FRUSTUM = 1
    NDC = 2
    NVC = 3
    VIEWPORT = 4
    LOGICAL = 5
    CANVAS = 6
    WINDOW = 7

# ======================================== EXPORTS ========================================
__all__ = [
    "CoordSpace",
]