# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._pipeline import Pipeline
from ...asset import Color, Text

import pyglet
import pyglet.text

# ======================================== CONSTANTS ========================================
_UNSET = object()

# ======================================== PUBLIC ========================================
class PygletLabelRenderer:
    """
    Renderer pyglet unifié pour un label texte

    Args:
        text: texte à rendre
        x: position horizontale
        y: point verticale
        anchor_x: ancre relative locale
        anchor_y: ancre relative verticale
        rotation: rotation en degrés
        weight: graisse ('bold', 'thin', '100'…'900', ou int pyglet)
        italic: italique
        underline: couleur du soulignement
        color: couleur du texte (Color)
        opacity: opacité globale [0.0 ; 1.0]
        line_spacing: espacement entre les lignes en pixels (None = défaut)
        width: largeur de la boîte en pixels (None = pas de boîte)
        height: hauteur de la boîte en pixels (None = pas de boîte)
        multiline: autorise les \\n explicites
        wrap_lines: word-wrap automatique (nécessite width)
        align: 'left' | 'center' | 'right'
        margin: marge intérieure uniforme en pixels
        z: z-order
        pipeline: pipeline de rendu
    """
    __slots__ = (
        "_text",
        "_x", "_y", "_anchor_x", "_anchor_y",
        "_rotation",
        "_weight", "_italic", "_underline",
        "_color", "_opacity",
        "_width", "_height", "_multiline", "_wrap_lines", "_align",
        "_margin", "_line_spacing",
        "_z", "_pipeline"
        "_label",
    )

    def __init__(
        self,
        text: Text,
        x: float = 0.0,
        y: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
        rotation: float = 0.0,
        weight: str | int = "normal",
        italic: bool = False,
        underline: Color = None,
        color: Color = None,
        opacity: float = 1.0,
        width: int = None,
        height: int = None,
        multiline: bool = False,
        wrap_lines: bool = True,
        align: str = "left",
        margin: int = 0,
        line_spacing: float = None,
        z: int = 0,
        pipeline: Pipeline = None,
    ):
        # Paramètres publics
        self._text: Text = text
        self._x: float = x
        self._y: float = y
        self._anchor_x: float = anchor_x
        self._anchor_y: float = anchor_y
        self._rotation: float = rotation
        self._weight: str | int = weight
        self._italic: bool = italic
        self._underline: Color = underline
        self._color: Color = color
        self._opacity: float = opacity
        self._width: int = width
        self._height: int = height
        self._multiline: bool = multiline
        self._wrap_lines: bool = wrap_lines
        self._align: str = align
        self._margin: int = margin
        self._line_spacing: float = line_spacing
        self._z: int = z
        self._pipeline: Pipeline = pipeline

        # Construction
        self._label: pyglet.text.Label = None
        self._build()

    # ======================================== INTERNALS ========================================
    def _build(self) -> None:
        """Construit le label pyglet et applique tous les styles"""
        font = self._text.font

        r, g, b, a = self._color.rgba8 if self._color is not None else (255, 255, 255, 255)
        a = int(a * self._opacity)

        self._label = pyglet.text.Label(
            text=self._text.text,
            font_name=font.name,
            font_size=font.size,
            weight=self._weight,
            italic=self._italic,
            color=(r, g, b, a),
            anchor_x="left",
            anchor_y="bottom",
            width=self._width,
            height=self._height,
            multiline=self._multiline,
            rotation=self._rotation,
            batch=self._pipeline.batch if self._pipeline else None,
            group=self._pipeline.get_group(z=self._z) if self._pipeline else None,
        )
        self._apply_styles()
        self._refresh_position()

    def _apply_styles(self) -> None:
        """Applique les styles set_style en une passe"""
        margin = self.margin
        s = self._label.set_style
        s("wrap_lines", self._wrap_lines)
        s("align", self._align)
        s("margin_left", margin)
        s("margin_right", margin)
        s("margin_top", margin)
        s("margin_bottom", margin)
        if self._line_spacing is not None:
            s("line_spacing", self._line_spacing)
        if self._underline is not None:
            s("underline", self._underline.rgba8)

    # ======================================== GETTERS ========================================
    @property
    def text(self) -> Text:
        """Renvoie l'asset Text"""
        return self._text

    @property
    def position(self) -> tuple[float, float]:
        """Renvoie la position"""
        return (self._x, self._y)

    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._x

    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._y

    @property
    def anchor_x(self) -> float:
        """Renvoie l'ancre horizontale"""
        return self._anchor_x

    @property
    def anchor_y(self) -> float:
        """Renvoie l'ancre verticale"""
        return self._anchor_y

    @property
    def rotation(self) -> float:
        """Renvoie la rotation en degrés"""
        return self._rotation

    @property
    def weight(self) -> str | int:
        """Renvoie la graisse"""
        return self._weight

    @property
    def italic(self) -> bool:
        """Renvoie l'italique"""
        return self._italic

    @property
    def underline(self) -> Color:
        """Renvoie la couleur de soulignement"""
        return self._underline

    @property
    def color(self) -> Color:
        """Renvoie la couleur du texte"""
        return self._color

    @property
    def opacity(self) -> float:
        """Renvoie l'opacité"""
        return self._opacity

    @property
    def width(self) -> int:
        """Renvoie la largeur de la boîte"""
        return self._width

    @property
    def height(self) -> int:
        """Renvoie la hauteur de la boîte"""
        return self._height

    @property
    def multiline(self) -> bool:
        """Renvoie le multiline"""
        return self._multiline

    @property
    def wrap_lines(self) -> bool:
        """Renvoie le word-wrap"""
        return self._wrap_lines

    @property
    def align(self) -> str:
        """Renvoie l'alignement"""
        return self._align

    @property
    def margin(self) -> int:
        """Renvoie la marge intérieure"""
        return self._margin

    @property
    def line_spacing(self) -> float:
        """Renvoie l'espacement de ligne"""
        return self._line_spacing

    @property
    def z(self) -> int:
        """Renvoie le z-order"""
        return self._z

    @property
    def pipeline(self) -> Pipeline:
        """Renvoie la pipeline de rendu"""
        return self._pipeline

    @property
    def content_width(self) -> int:
        """Renvoie la largeur réelle du texte rendu"""
        return self._label.content_width if self._label else 0

    @property
    def content_height(self) -> int:
        """Renvoie la hauteur réelle du texte rendu"""
        return self._label.content_height if self._label else 0

    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        return self._label.visible if self._label else False

    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Active ou désactive la visibilité"""
        if self._label:
            self._label.visible = value

    # ======================================== PREDICATES ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._label is not None and self._label.visible

    # ======================================== LIFE CYCLE ========================================
    def update(self, **kwargs) -> None:
        """
        Met à jour le renderer label

        Args:
            text: texte à rendre
            x: position horizontale
            y: point verticale
            anchor_x: ancre relative locale
            anchor_y: ancre relative verticale
            rotation: rotation en degrés
            weight: graisse ('bold', 'thin', '100'…'900', ou int pyglet)
            italic: italique
            underline: couleur du soulignement
            color: couleur du texte (Color)
            opacity: opacité globale [0.0 ; 1.0]
            line_spacing: espacement entre les lignes en pixels (None = défaut)
            width: largeur de la boîte en pixels (None = pas de boîte)
            height: hauteur de la boîte en pixels (None = pas de boîte)
            multiline: autorise les \\n explicites
            wrap_lines: word-wrap automatique (nécessite width)
            align: 'left' | 'center' | 'right'
            margin: marge intérieure uniforme en pixels
            z: z-order
            pipeline: pipeline de rendu
        """
        rebuild: bool = False
        changes: list[str] = set()

        # Actualisation des paramètres
        for key, value in kwargs.items():
            current = getattr(self, f"_{key}", _UNSET)
            if current is _UNSET or value == current:
                continue
            setattr(self, f"_{key}", value)
            changes.add(key)

        # Appel des callbacks
        rebuild: bool = False
        refresh: bool = False

        for key in changes:
            handler = getattr(self, f"_handle_{key}", None)
            if handler:
                output: str = handler()
                if output == "rebuild":
                    rebuild = True
                elif output == "refresh":
                    refresh = True       

        if rebuild:
            self._rebuild()
        elif refresh:
            self._refresh_position()

    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._label:
            self._label.delete()
            self._label = None

    # ======================================== HANDLERS ========================================
    def _handle_text(self) -> None:
        """Actualisation du text"""
        font = self._text.font
        self._label.text = self._text.text
        self._label.font_name = font.name
        self._label.font_size = font.size
        return "refresh"

    def _handle_x(self) -> None:
        """Actualisation de la position horizontale"""
        return "refresh"

    def _handle_y(self) -> None:
        """Actualisation de la position verticale"""
        return "refresh"

    def _handle_anchor_x(self) -> None:
        """Actualisation de l'ancre horizontale"""
        return "refresh"

    def _handle_anchor_y(self) -> None:
        """Actualisation de l'ancre verticale"""
        return "refresh"

    def _handle_rotation(self) -> None:
        """Actualisation de la rotation"""
        self._label.rotation = self._rotation

    def _handle_weight(self) -> None:
        """Actualisation de la graisse"""
        self._label.weight = self._weight

    def _handle_italic(self) -> None:
        """Actualisation de l'italique"""
        self._label.italic = self._italic

    def _handle_underline(self) -> None:
        """Actualisation du soulignement"""
        self._label.set_style("underline", self.underline.rgba8 if self.underline else None)

    def _handle_color(self) -> None:
        """Actualisation de la couleur"""
        r, g, b, a = self._color.rgba8 if self._color is not None else (255, 255, 255, 255)
        a = int(a * self._opacity)
        self._label.color = (r, g, b, a)

    def _handle_opacity(self) -> None:
        """Actualisation de l'opacité"""
        a = self._color.a if self._color is not None else 255
        self._label.opacity = a * self._opacity

    def _handle_width(self) -> None:
        """Actualisation de la largeur"""
        self._label.width = self._width
        return "refresh"

    def _handle_height(self) -> None:
        """Actualisation de la hauteur"""
        self._label.height = self._height
        return "refresh"
    
    def _handle_multiline(self) -> None:
        """Actualisation du saut de ligne"""
        return "rebuild"
    
    def handle_wrap_lines(self) -> None:
        """Actualisation de la conservation"""
        return "rebuild"

    def _handle_align(self) -> None:
        """Actualisation de l'alignement"""
        self._label.set_style("align", self._align)

    def _handle_margin(self) -> None:
        """Actualisation de la marge"""
        margin = self._margin
        s = self._label.set_style
        s("margin_left", margin)
        s("margin_right", margin)
        s("margin_top", margin)
        s("margin_bottom", margin)
        return "refresh"

    def _handle_line_spacing(self) -> None:
        """Actualisation de l'espacement"""
        self._label.set_style("line_spacing", self._line_spacing)
        return "refresh"

    def _handle_z(self) -> None:
        """Actualisation du z-order"""
        if self._pipeline:
            self._label.group = self._pipeline.get_group(z=self._z)

    def _handle_pipeline(self) -> None:
        """Actualisation de la pipeline"""
        if self.pipeline:
            self._label.batch = self._pipeline.batch
            self._label.group = self._pipeline.get_group(z=self._z)

    # ======================================== HELPERS ========================================
    def _refresh_position(self) -> None:
        """Recalcule x/y pyglet à partir de l'ancre et des dimensions réelles"""
        self._label.x = self._x - self._anchor_x * self._label.content_width
        self._label.y = self._y - self._anchor_y * self._label.content_height

    def _rebuild(self) -> None:
        """Reconstruit le label avec les paramètres courants"""
        self.delete()
        self._build()