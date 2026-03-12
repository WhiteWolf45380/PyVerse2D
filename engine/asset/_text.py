# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..abc import Asset

# ======================================== OBJET ========================================
class Text(Asset):
    """
    Descripteur de texte

    Args:
        text(str): contenu du texte
        font(str, optional): nom ou chemin de la police
        fontsize(int, optional): taille de la police
        color(tuple, optional): couleur RGBA
    """
    __slots__ = ("_text", "_font", "_fontsize", "_color")

    def __init__(
            self,
            text: str,
            font: str = None,
            fontsize: int = 16,
            color: tuple[int, ...] = (255, 255, 255, 255),
        ):
        self._text: str = expect(text, str)
        self._font: str = expect(font, (str, None))
        self._fontsize: int = positive(not_null(expect(fontsize, int)))
        self._color: tuple = expect(color, tuple[int])

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return f"Text(text={self._text}, font={self._font}, fontsize={self._fontsize}, color={self._color})"

    # ======================================== GETTERS ========================================
    @property
    def text(self) -> str:
        """Renvoie le contenu du texte"""
        return self._text

    @property
    def font(self) -> str | None:
        """Renvoie la police"""
        return self._font

    @property
    def fontsize(self) -> int:
        """Renvoie la taille de la police"""
        return self._fontsize

    @property
    def color(self) -> tuple[int, ...]:
        """Renvoie la couleur"""
        return self._color

    # ======================================== PUBLIC METHODS ========================================
    def __copy__(self) -> Text:
        return Text(self._text, self._font, self._fontsize, self._color)

    def copy(self) -> Text:
        return Text(self._text, self._font, self._fontsize, self._color)

    def with_text(self, text: str) -> Text:
        """Renvoie un nouveau Text avec un contenu différent"""
        return Text(expect(text, str), self._font, self._fontsize, self._color)

    def with_fontsize(self, fontsize: int) -> Text:
        """Renvoie un nouveau Text avec une taille différente"""
        return Text(self._text, self._font, positive(not_null(expect(fontsize, int))), self._color)

    def with_color(self, color: tuple[int, ...]) -> Text:
        """Renvoie un nouveau Text avec une couleur différente"""
        return Text(self._text, self._font, self._fontsize, expect(color, tuple))