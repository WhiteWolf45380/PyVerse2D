# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import RenderObject

import numpy as np

# ======================================== RENDER OBJECT ========================================
class Mesh(RenderObject):
    __slots__ = ("vertices", "indices")

    def __init__(self, vertices: np.ndarray, indices: np.ndarray):
        self.vertices = vertices
        self.indices = indices