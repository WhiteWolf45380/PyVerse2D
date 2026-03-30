# ======================================== IMPORTS ========================================
from __future__ import annotations
 
from ._pipeline import Pipeline
from ..asset import Color
 
import pyglet
import pyglet.sprite
import pyglet.text
from pyglet.graphics import Batch, Group
 
# ======================================== CONSTANTS ========================================
_UNSET = object()   # élément non défini
 
# ======================================== SPRITE RENDERER ========================================
class PygletSpriteRenderer:
    """
    Renderer pyglet unifié pour un sprite
 
    Args:
        texture(pyglet.image.AbstractImage): texture à afficher
        x(float, optional): position horizontale
        y(float, optional): position verticale
        anchor_x(float, optional): ancre relative locale horizontale [0.0 ; 1.0]
        anchor_y(float, optional): ancre relative locale verticale [0.0 ; 1.0]
        scale_x(float, optional): facteur de redimensionnement horizontal
        scale_y(float, optional): facteur de redimensionnement vertical
        rotation(float, optional): rotation en degrés
        opacity(float, optional): opacité [0.0 ; 1.0]
        color(Color, optional): teinte multiplicative
        z(int, optional): z-order
        pipeline(Pipeline, optional): pipeline de rendu
    """
    __slots__ = (
        "_texture",
        "_x", "_y", "_anchor_x", "_anchor_y",
        "_scale_x", "_scale_y", "_rotation",
        "_opacity", "_color",
        "_z", "_pipeline",
        "_sprite",
    )
 
    def __init__(
        self,
        texture: pyglet.image.AbstractImage,
        x: float = 0.0,
        y: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        rotation: float = 0.0,
        opacity: float = 1.0,
        color: Color = None,
        z: int = 0,
        pipeline: Pipeline = None,
    ):
        self._texture: pyglet.image.AbstractImage = texture
        self._x: float = x
        self._y: float = y
        self._anchor_x: float = anchor_x
        self._anchor_y: float = anchor_y
        self._scale_x: float = scale_x
        self._scale_y: float = scale_y
        self._rotation: float = rotation
        self._opacity: float = opacity
        self._color: Color = color
        self._z: int = z
        self._pipeline: Pipeline = pipeline
 
        self._sprite: pyglet.sprite.Sprite = None
        self._build()
 
    # ======================================== BUILD ========================================
    def _build(self) -> None:
        """Construit le sprite pyglet"""
        # Ancrage de la texture
        img = self._texture
        img.anchor_x = int(self._anchor_x * img.width)
        img.anchor_y = int(self._anchor_y * img.height)
 
        self._sprite = pyglet.sprite.Sprite(
            img,
            x=self._x,
            y=self._y,
            batch=self._pipeline.batch if self._pipeline else None,
            group=self._pipeline.get_group(z=self._z) if self._pipeline else None,
        )
        self._sprite.scale_x = self._scale_x
        self._sprite.scale_y = self._scale_y
        self._sprite.rotation = self._rotation
        self._sprite.opacity = int(self._opacity * 255)
        if self._color is not None:
            self._sprite.color = self._color.rgb8
 
    # ======================================== GETTERS ========================================
    @property
    def texture(self) -> pyglet.image.AbstractImage:
        """Renvoie la texture"""
        return self._texture
 
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
    def scale_x(self) -> float:
        """Renvoie le facteur de redimensionnement horizontal"""
        return self._scale_x
 
    @property
    def scale_y(self) -> float:
        """Renvoie le facteur de redimensionnement vertical"""
        return self._scale_y
 
    @property
    def rotation(self) -> float:
        """Renvoie la rotation en degrés"""
        return self._rotation
 
    @property
    def opacity(self) -> float:
        """Renvoie l'opacité"""
        return self._opacity
 
    @property
    def color(self) -> Color:
        """Renvoie la teinte multiplicative"""
        return self._color
 
    @property
    def z(self) -> int:
        """Renvoie le z-order"""
        return self._z
 
    @property
    def pipeline(self) -> Pipeline:
        """Renvoie la pipeline de rendu"""
        return self._pipeline
 
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        return self._sprite.visible if self._sprite else False
 
    # ======================================== SETTERS ========================================
    @visible.setter
    def visible(self, value: bool) -> None:
        """Active ou désactive la visibilité"""
        if self._sprite:
            self._sprite.visible = value
 
    # ======================================== PREDICATES ========================================
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._sprite is not None and self._sprite.visible
 
    # ======================================== LIFE CYCLE ========================================
    def update(self, **kwargs) -> None:
        """
        Met à jour le renderer sprite
 
        Args:
            texture(pyglet.image.AbstractImage, optional): texture
            x(float, optional): position horizontale
            y(float, optional): position verticale
            anchor_x(float, optional): ancre relative locale horizontale
            anchor_y(float, optional): ancre relative locale verticale
            scale_x(float, optional): facteur de redimensionnement horizontal
            scale_y(float, optional): facteur de redimensionnement vertical
            rotation(float, optional): rotation en degrés
            opacity(float, optional): opacité
            color(Color, optional): teinte multiplicative
            z(int, optional): z-order
            pipeline(Pipeline, optional): pipeline de rendu
        """
        changes: list[str] = []
 
        for key, value in kwargs.items():
            current = getattr(self, f"_{key}", _UNSET)
            if current is _UNSET or value == current:
                continue
            setattr(self, f"_{key}", value)
            if key == "texture":
                self._rebuild()
                return
            changes.append(key)
 
        for key in changes:
            handler = getattr(self, f"_handle_{key}", None)
            if handler:
                handler()
 
    def delete(self) -> None:
        """Libère les ressources pyglet"""
        if self._sprite:
            self._sprite.delete()
            self._sprite = None
 
    # ======================================== HANDLERS ========================================
    def _handle_x(self) -> None:
        """Actualisation de la position horizontale"""
        self._sprite.x = self._x
 
    def _handle_y(self) -> None:
        """Actualisation de la position verticale"""
        self._sprite.y = self._y
 
    def _handle_anchor_x(self) -> None:
        """Actualisation de l'ancre horizontale"""
        self._sprite.image.anchor_x = int(self._anchor_x * self._sprite.image.width)
 
    def _handle_anchor_y(self) -> None:
        """Actualisation de l'ancre verticale'"""
        self._sprite.image.anchor_y = int(self._anchor_y * self._sprite.image.height)
 
    def _handle_scale_x(self) -> None:
        """Actualisation du facteur de redimensionnement horizontal"""
        self._sprite.scale_x = self._scale_x
 
    def _handle_scale_y(self) -> None:
        """Actualisation du facteur de redimensionnement vertical"""
        self._sprite.scale_y = self._scale_y
 
    def _handle_rotation(self) -> None:
        """Actualisation de la rotation"""
        self._sprite.rotation = self._rotation
 
    def _handle_opacity(self) -> None:
        """Actualisation de l'opacité"""
        self._sprite.opacity = int(self._opacity * 255)
 
    def _handle_color(self) -> None:
        """Actualisation de la couleur de teinte"""
        self._sprite.color = self._color.rgb if self._color is not None else (255, 255, 255)
 
    def _handle_z(self) -> None:
        """Actualisation du z-order"""
        if self._pipeline:
            self._sprite.group = self._pipeline.get_group(z=self._z)
 
    def _handle_pipeline(self) -> None:
        """Actualisation de la pipeline de rendu"""
        if self._pipeline:
            self._sprite.batch = self._pipeline.batch
            self._sprite.group = self._pipeline.get_group(z=self._z)
 
    # ======================================== HELPERS ========================================
    def _rebuild(self) -> None:
        """Reconstruit le sprite avec les paramètres courants"""
        self.delete()
        self._build()