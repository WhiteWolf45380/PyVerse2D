# ======================================== IMPORTS ========================================
from .._core import System

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système gérant les collisions"""
    def __init__(self):
        super().__init__()