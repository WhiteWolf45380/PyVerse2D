# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..abc import Asset

# ======================================== ASSET ========================================
class Color(tuple, Asset):
    """Descripteur de Couleur RGBA"""
    __slots__ = ()

    def __new__(cls, value, argument: str = "Argument"):
        if isinstance(value, cls):
            return value

        if type(value) is not tuple:
            raise TypeError(f"{argument} must be a tuple")

        n = len(value)
        if n == 3:
            r, g, b = value
            a = 1.0
        elif n == 4:
            r, g, b, a = value
        elif n < 3:
            r, g, b, a = (*value, 0, 0, 0, 1.0)[:4]
        else:
            raise ValueError(f"{argument} must have 4 elements or less")

        tr = type(r)
        if tr is int:
            if not (0 <= r <= 255):
                raise ValueError(f"{argument}: red component out of range ({r})")
        elif tr is float:
            if not (0.0 <= r <= 1.0):
                raise ValueError(f"{argument}: invalid red component ({r})")
            r = int(r * 255 + 0.5)
        else:
            raise TypeError(f"{argument}: invalid red component ({r})")

        tg = type(g)
        if tg is int:
            if not (0 <= g <= 255):
                raise ValueError(f"{argument}: green component out of range ({g})")
        elif tg is float:
            if not (0.0 <= g <= 1.0):
                raise ValueError(f"{argument}: invalid green component ({g})")
            g = int(g * 255 + 0.5)
        else:
            raise TypeError(f"{argument}: invalid green component ({g})")

        tb = type(b)
        if tb is int:
            if not (0 <= b <= 255):
                raise ValueError(f"{argument}: blue component out of range ({b})")
        elif tb is float:
            if not (0.0 <= b <= 1.0):
                raise ValueError(f"{argument}: invalid blue component ({b})")
            b = int(b * 255 + 0.5)
        else:
            raise TypeError(f"{argument}: invalid blue component ({b})")

        ta = type(a)
        if ta is float:
            if not (0.0 <= a <= 1.0):
                raise ValueError(f"{argument}: alpha component out of range ({a})")
        elif ta is int:
            if not (0 <= a <= 255):
                raise ValueError(f"{argument}: alpha component out of range ({a})")
            a = a / 255
        else:
            raise TypeError(f"{argument}: invalid alpha component ({a})")

        return tuple.__new__(cls, (r, g, b, a))

    # ======================================== GETTERS ========================================
    @property
    def r(self): return self[0]

    @property
    def g(self): return self[1]

    @property
    def b(self): return self[2]

    @property
    def a(self): return self[3]

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Color:
        """Renvoie une copie de la couleur"""
        return Color(*self)

    def copy(self) -> Color:
        """Renvoie une copie de la couleur"""
        return Color(*self)