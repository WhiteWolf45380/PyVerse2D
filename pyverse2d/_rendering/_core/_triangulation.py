# ======================================== IMPORTS ========================================
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# ======================================== RENDER TOOL ========================================
def triangulate(vertices: NDArray[np.float32]) -> NDArray[np.int32]:
    """Renvoie les indices des triangles d'un mesh

    Args:
        vertices: array ordonnée CCW (N, 2)
    """
    n = len(vertices)
    if n < 3:
        return np.empty((0,), dtype=np.int32)

    # Cas triangle trivial
    if n == 3:
        return np.array([0, 1, 2], dtype=np.int32)

    def cross(o, a, b) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def is_ear(i0, i1, i2) -> bool:
        a, b, c = vertices[i0], vertices[i1], vertices[i2]

        # doit être convexe (CCW)
        if cross(a, b, c) <= 0:
            return False

        # aucun autre point dans le triangle
        for j in range(n):
            if j in (i0, i1, i2):
                continue
            p = vertices[j]

            # barycentric / orientation test (point in triangle)
            c1 = cross(a, b, p)
            c2 = cross(b, c, p)
            c3 = cross(c, a, p)

            if c1 >= 0 and c2 >= 0 and c3 >= 0:
                return False

        return True

    # indices actifs
    idx = list(range(n))
    triangles = []

    guard = 0

    while len(idx) > 3 and guard < 10_000:
        guard += 1
        ear_found = False

        for i in range(len(idx)):
            i0 = idx[i - 1]
            i1 = idx[i]
            i2 = idx[(i + 1) % len(idx)]

            if is_ear(i0, i1, i2):
                triangles.extend([i0, i1, i2])
                del idx[i]
                ear_found = True
                break

        if not ear_found:
            # polygon probablement dégénéré
            break

    # dernier triangle restant
    if len(idx) == 3:
        triangles.extend([idx[0], idx[1], idx[2]])

    return np.array(triangles, dtype=np.int32)