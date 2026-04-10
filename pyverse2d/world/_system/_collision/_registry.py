# ======================================== IMPORTS ========================================
from __future__ import annotations

from ....math import Vector

from typing import Callable, NamedTuple

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