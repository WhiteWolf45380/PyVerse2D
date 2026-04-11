# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....math import Vector

from typing import Callable, NamedTuple
from math import radians, cos, sin

# ======================================== CONTACT ========================================
class Contact(NamedTuple):
    """Résultat d'une détection de collision

    Convention : normal pointe de B vers A (pousse A hors de B)
    """
    normal: Vector
    depth: float

# ======================================== REGISTRY ========================================
_handlers: dict[tuple[type, type], Callable] = {}

def register(type_a: type, type_b: type):
    """Décore une fonction de narrowphase pour la paire ``(type_a, type_b)``"""
    def decorator(fn: Callable) -> Callable:
        _handlers[(type_a, type_b)] = fn
        return fn
    return decorator


def dispatch(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b) -> Contact | None:
    """Dispatche vers le bon handler de narrowphase"""
    from ._narrow_phase import dispatch as _np_dispatch
    return _np_dispatch(sa, ax, ay, scale_a, rot_a, sb, bx, by, scale_b, rot_b)


def world_center(shape, tr, offset) -> tuple[float, float]:
    """Calcule le centre géométrique monde depuis transform, bounding_box et offset"""
    x_min, y_min, x_max, y_max = shape.bounding_box

    # Anchor en espace local
    local_ax = x_min + tr.anchor.x * (x_max - x_min)
    local_ay = y_min + tr.anchor.y * (y_max - y_min)

    # Scale + rotation de l'anchor
    rad = radians(-tr.rotation)
    cos_r, sin_r = cos(rad), sin(rad)
    scaled_ax = local_ax * tr.scale
    scaled_ay = local_ay * tr.scale
    rotated_ax = scaled_ax * cos_r - scaled_ay * sin_r
    rotated_ay = scaled_ax * sin_r + scaled_ay * cos_r

    # Centre monde
    return (tr.x - rotated_ax + offset[0] * tr.scale, tr.y - rotated_ay + offset[1] * tr.scale,)