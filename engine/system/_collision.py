# ======================================== IMPORTS ========================================
from ..ecs import System, UpdatePhase

# ======================================== SYSTEM ========================================
class CollisionSystem(System):
    """Système gérant les collisions"""
    phase = UpdatePhase.UPDATE

    def __init__(self):
        ...