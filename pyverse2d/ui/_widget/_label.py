# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, positive, not_null
from ..._rendering import Pipeline, RenderContext, PygletLabelRenderer
from ...asset import Text, Color
from ...abc import Widget
from ...math import Point

from numbers import Real
from typing import Literal

# ======================================== CONSTANTS ========================================
HorizontalAlign = Literal["left", "center", "right"]

# ======================================== WIDGET ========================================
class Label(Widget):
    """
    Composant UI simple: Label

    Args:
        text(Text): texte à rendre
        position(Point, Point): position
        anchor(Point, optional): ancre relative locale
        rotation(Real, optional): rotation en degrés
        weight(str, optional): graisse ('bold', 'thin', '100'…'900', ou int pyglet)
        italic(bool, optional): italique
        underline(Color, optional): couleur du soulignement
        color(Color, optional): couleur du texte (Color)
        opacity(Real, optional): opacité globale [0.0 ; 1.0]
        width(int, optional): largeur de la boîte en pixels (None = pas de boîte)
        height(int, optional): hauteur de la boîte en pixels (None = pas de boîte)
        multiline(bool, optional): autorise les \\n explicites
        line_spacing(int, optional): espacement entre les lignes en pixels (None = défaut)
        wrap_lines(bool, optional): word-wrap automatique (nécessite width)
        align(HorizontalAlign, optional): alignement horizontal
        margin(int, optional): marge intérieure uniforme en pixels
    """
    __slots__ = (
        "_text", "_text_renderer",
        "_position", "_anchor", "_rotation",
        "_weight", "_italic", "_underline",
        "_color", "_opacity",
        "_width", "_height",
        "_multiline", "_line_spacing", "_wrap_lines",
        "_align", "_margin",
    )
    
    def __init__(
            self,
            text: Text,
            position: Point = (0.0, 0.0),
            anchor: Point = (0.5, 0.5),
            rotation: Real = 0.0,
            weight: str = "normal",
            italic: bool = False,
            underline: Color = None,
            color: Color = (255, 255, 255),
            opacity: Real = 1.0,
            width: int = None,
            height: int = None,
            multiline: bool = False,
            line_spacing: int = None,
            wrap_lines: bool = False,
            align: HorizontalAlign = "left",
            margin: int = 0,
        ):
        super().__init__(position, anchor, opacity)

        # Texte
        self._text: Text = expect(text, Text)
        self._text_renderer: PygletLabelRenderer = None

        # Transform
        self._rotation: float = float(expect(rotation, Real))

        # Style
        self._weight: str = expect(weight, str)
        self._italic: bool = expect(italic, bool)
        self._underline: Color = Color(underline) if underline is not None else None

        # Affichage
        self._color: Color = Color(color)

        # Mise en page
        self._width: int = positive(not_null(expect(width, int))) if width is not None else None
        self._height: int = positive(not_null(expect(height, int))) if height is not None else None
        self._multiline: bool = expect(multiline, bool)
        self._line_spacing: int = expect(line_spacing, int) if line_spacing is not None else None
        self._wrap_lines: bool = expect(wrap_lines, bool)
        self._align: HorizontalAlign = expect(align, HorizontalAlign)
        self._margin: int = positive(not_null(expect(margin, int)))
    
    # ======================================== PROPERTIES ========================================
    @property
    def text(self) -> Text:
        """Texte interne à rendre

        Le texte doit être un Asset Texte
        """
        return self._text
    
    @text.setter
    def text(self, value: Text) -> None:
        self._text = expect(value, Text)

    @property
    def rotation(self) -> float:
        """Rotation en degrés

        La rotation doit être un Réel
        """
        return self._rotation
    
    @rotation.setter
    def rotation(self, value: Real) -> None:
        self._rotation = float(expect(value, Real))

    @property
    def weight(self) -> str:
        """Graisse de la police

        La graisse doit être un string conforme à la norme CSS
        """
        return self._weight
    
    @weight.setter
    def weight(self, value: str) -> None:
        self._weight = expect(value, str)

    @property
    def italic(self) -> bool:
        """Mise en italique de la police

        Cette propriété fixe l'utilisation ou non de l'italique
        """
        return self._italic
    
    @italic.setter
    def italic(self, value: bool) -> None:
        self._italic = expect(value, bool)

    @property
    def underline(self) -> Color | None:
        """Couleur de soulignage du texte

        La couleur de soulignage doit être un Asset Color ou un tuple rgb/rgba
        Mettre à None pour ne pas souligner le texte
        """
        return self._underline
    
    @underline.setter
    def underline(self, value: Color | None) -> None:
        self._underline = Color(value) if value is not None else None

    @property
    def color(self) -> Color:
        """Couleur d'affichage

        La couleur doit être un Asset Color ou un tuple rgb/rgba
        """
        return self._color
    
    @color.setter
    def color(self, value: Color) -> None:
        self._color = Color(value)

    @property
    def width(self) -> int | None:
        """Largeur de la boîte de texte

        Cette propriété inclus le texte dans une boîte
        La largeur doit être un entier positif non nul
        """
        return self._width
    
    @width.setter
    def width(self, value: int | None) -> None:
        self._width = positive(not_null(expect(value, int))) if value is not None else None

    @property
    def height(self) -> int | None:
        """Hauteur de la boîte de texte

        Cette propriété inclus le texte dans une boîte
        La hauteur doit être un entier positif non nul
        """
        return self._height
    
    @height.setter
    def height(self, value: int | None) -> None:
        self._height = positive(not_null(expect(value, int))) if value is not None else None

    @property
    def multiline(self) -> bool:
        """Saut de lignes

        Cette propriété fixe l'utilisation du saut de lignes
        """
        return self._multiline
    
    @multiline.setter
    def multiline(self, value: bool) -> None:
        self._multiline = expect(value, bool)

    @property
    def line_spacing(self) -> int | None:
        """Espacement entre les lignes

        L'espacement doit être un entier positif non nul
        """
        return self._line_spacing
    
    @line_spacing.setter
    def line_spacing(self, value: int | None) -> None:
        self._line_spacing = expect(value, int) if value is not None else None
    
    @property
    def wrap_lines(self) -> bool:
        """Conservation des mots

        Cette propriété fixe l'utilisation de la conservation des mots
        Lorsqu'activée, les sauts de lignes se font de sorte à ne pas scinder les mots
        """
        return self._wrap_lines
    
    @wrap_lines.setter
    def wrap_lines(self, value: bool) -> None:
        self._wrap_lines = expect(value, bool)

    @property
    def align(self) -> HorizontalAlign:
        """Alignement horizontal du texte

        L'alignement doit être un HorizontalAlign
        Il fixe l'alignement dans texte dans la boîte
        """
        return self._align
    
    @align.setter
    def align(self, value: HorizontalAlign) -> None:
        self._align = expect(value, HorizontalAlign)

    @property
    def margin(self) -> int:
        """Marge intérieure

        Cette propriété applique un espacement entre le texte et les bordures de la boîte
        La marge doit être un entier positif non nul
        """
        return self._margin
    
    @margin.setter
    def margin(self, value: int) -> None:
        self._margin = positive(not_null(expect(value, int)))

    # ======================================== LIFE CYCLE ========================================
    def _update(self, dt: float) -> None:
        """Actualisation"""
        ...

    def _draw(self, pipeline: Pipeline, context: RenderContext) -> None:
        """Affichage"""
        if self._text_renderer is None:
            self._text_renderer = PygletLabelRenderer(
                text = self._text,
                x = context.origin.x,
                y = context.origin.y,
                anchor_x = self.anchor_x,
                anchor_y = self.anchor_y,
                rotation = self._rotation,
                weight = self._weight,
                italic = self._italic,
                underline = self._underline,
                color = self._color,
                opacity = self._opacity,
                width = self._width,
                height = self._height,
                multiline = self._multiline,
                wrap_lines = self._wrap_lines,
                align = self._align,
                margin = self._margin,
                line_spacing = self._line_spacing,
                z = context.z,
                pipeline = pipeline,
            )
    
        else:
            self._text_renderer.update(
                text = self._text,
                x = context.origin.x,
                y = context.origin.y,
                anchor_x = self.anchor_x,
                anchor_y = self.anchor_y,
                rotation = self._rotation,
                weight = self._weight,
                italic = self._italic,
                underline = self._underline,
                color = self._color,
                opacity = self._opacity,
                width = self._width,
                height = self._height,
                multiline = self._multiline,
                wrap_lines = self._wrap_lines,
                align = self._align,
                margin = self._margin,
                line_spacing = self._line_spacing,
                z = context.z,
                pipeline = pipeline,
            )

    def _destroy(self) -> None:
        """Libère les ressources pyglet"""
        if self._text_renderer:
            self._text_renderer.delete()
            self._text_renderer = None