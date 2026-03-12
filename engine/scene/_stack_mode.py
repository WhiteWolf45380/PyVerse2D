# ======================================== IMPORTS ========================================
from enum import Enum

# ======================================== FLAG ========================================
class StackMode(Enum):
    PAUSE = "pause"    # scene du dessous stop tout
    SUSPEND = "suspend"  # scene du dessous stop update mais continue draw
    OVERLAY = "overlay"  # scene du dessous continue tout