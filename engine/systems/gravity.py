# ======================================== IMPORTS ========================================
from ..core import System

# ======================================== SYSTEM ========================================
class GravitySystem(System):
    """Système gérant la gravité"""
    def __init__(self):
        super().__init__()