# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._pipeline import Pipeline
from ...asset import Color, Image

import pyglet
import pyglet.sprite

# ======================================== CONSTANTS ========================================
_UNSET = object()   # élément non défini
_HANDLER_GROUPS = {
    "x": "position",
    "y": "position",
    "anchor_x": "anchor",
    "anchor_y": "anchor",
    "scale_x": "scales",
    "scale_y": "scales",
    "flip_x": "scales",
    "flip_y": "scales",
}

# ======================================== SPRITE RENDERER ========================================
class PygletSpriteRenderer:
    """
    Renderer pyglet unifié pour un sprite

    Args:
        image: descripteur d'image (asset)
        x: position horizontale
        y: position verticale
        anchor_x: ancre relative locale horizontale [0.0 ; 1.0]
        anchor_y: ancre relative locale verticale [0.0 ; 1.0]
        scale_x: facteur de redimensionnement horizontal (transform)
        scale_y: facteur de redimensionnement vertical (transform)
        flip_x: miroir horizontal
        flip_y: miroir vertical
        rotation: rotation en degrés
        color teinte multiplicative
        opacity: opacité [0.0 ; 1.0]
        z: z-order
        pipeline: pipeline de rendu
    """
    __slots__ = (
        "_image",
        "_x", "_y", "_anchor_x", "_anchor_y",
        "_scale_x", "_scale_y", "_flip_x", "_flip_y", "_rotation",
        "_color", "_opacity",
        "_z", "_pipeline"
        "_sprite",
    )
    _cache: dict[str, pyglet.image.AbstractImage] = {}

    def __init__(
        self,
        image: Image,
        x: float = 0.0,
        y: float = 0.0,
        anchor_x: float = 0.5,
        anchor_y: float = 0.5,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        flip_x: bool = False,
        flip_y: bool = False,
        rotation: float = 0.0,
        color: Color = None,
        opacity: float = 1.0,
        z: int = 0,
        pipeline: Pipeline = None,
    ):
        self._image: Image = image
        self._x: float = x
        self._y: float = y
        self._anchor_x: float = anchor_x
        self._anchor_y: float = anchor_y
        self._scale_x: float = scale_x
        self._scale_y: float = scale_y
        self._flip_x: bool = flip_x
        self._flip_y: bool = flip_y
        self._rotation: float = rotation
        self._opacity: float = opacity
        self._color: Color = color
        self._z: int = z
        self._pipeline: Pipeline = pipeline

        self._sprite: pyglet.sprite.Sprite = None
        self._build()

    # ======================================== CACHE ========================================
    @classmethod
    def _load_image(cls, path: str) -> pyglet.image.AbstractImage | None:
        """Charge et met en cache une texture depuis son chemin"""
        if path in cls._cache:
            return cls._cache[path]
        try:
            raw = pyglet.image.load(path)
            cls._cache[path] = raw
            return raw
        except FileNotFoundError:
            print(f"[PygletSpriteRenderer] Cannot load image: {path}")
            return None

    def _build(self) -> None:
        """Construit le sprite pyglet"""
        # Couleur
        r, g, b, a = self._color.rgba8 if self._color is not None else (255, 255, 255, 255)
        a = int(a * self._opacity)

        # Image brute
        raw = self._load_image(self._image.path)
        if raw is None:
            return
 
        # Travaille sur une région
        region = raw.get_region(0, 0, raw.width, raw.height)
        region.anchor_x = int(self._anchor_x * raw.width)
        region.anchor_y = int(self._anchor_y * raw.height)
 
        # Calcul des tailles effectives
        eff_sx, eff_sy = self._effective_scales(raw)
    
        # Construction du sprite
        self._sprite = pyglet.sprite.Sprite(
            region,
            x=self._x,
            y=self._y,
            batch=self._pipeline.batch if self._pipeline else None,
            group=self._pipeline.get_group(z=self._z) if self._pipeline else None,
        )
        self._sprite.scale_x = eff_sx
        self._sprite.scale_y = eff_sy
        self._sprite.rotation = self._rotation
        self._sprite.color = (r, g, b, a)

    def _effective_scales(self, raw: pyglet.image.AbstractImage) -> tuple[float, float]:
        """
        Calcule les scales effectifs en combinant :
          - scale_x / scale_y  (transform, fournis de l'extérieur)
          - dimensions cibles de l'asset Image
          - scale_factor de l'asset Image
          - flip_x / flip_y
        """
        img_sx: float | None = (self._image.width / raw.width if self._image.width else None)
        img_sy: float | None = (self._image.height / raw.height if self._image.height else None)

        if img_sx is None and img_sy is None:
            img_sx = img_sy = 1.0
        elif img_sx is None:
            img_sx = img_sy
        elif img_sy is None:
            img_sy = img_sx

        f  = self._image.scale_factor
        fx = -1 if self._flip_x else 1
        fy = -1 if self._flip_y else 1
        return self._scale_x * img_sx * f * fx, self._scale_y * img_sy * f * fy

    # ======================================== GETTERS ========================================
    @property
    def image(self) -> Image:
        """Renvoie le descripteur d'image"""
        return self._image

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
    def flip_x(self) -> bool:
        """Renvoie le miroir horizontal"""
        return self._flip_x

    @property
    def flip_y(self) -> bool:
        """Renvoie le miroir vertical"""
        return self._flip_y

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
    def ppu(self) -> int:
        """Renvoie le rapport de conversion world to screen"""
    
    @property
    def width(self) -> int:
        """Renvoie la largeur de la texture"""
        return self._sprite.width
    
    @property
    def height(self) -> int:
        """Renvoie la hauteur de la texture"""
        return self._sprite.height

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
            image: descripteur d'image
            x: position horizontale
            y: position verticale
            anchor_x: ancre relative locale horizontale
            anchor_y: ancre relative locale verticale
            scale_x: facteur de redimensionnement horizontal
            scale_y: facteur de redimensionnement vertical
            flip_x: miroir horizontal
            flip_y: miroir vertical
            rotation: rotation en degrés
            opacity: opacité
            color: teinte multiplicative
            z: z-order
            pipeline: pipeline de rendu
            ppu: rapport de conversion world to screen
        """
        changes: list[str] = set()
        for key, value in kwargs.items():
            current = getattr(self, f"_{key}", _UNSET)
            if current is _UNSET or value == current:
                continue
            setattr(self, f"_{key}", value)
            if key == "image":
                self._rebuild()
                return
            elif key in _HANDLER_GROUPS:
                changes.add(_HANDLER_GROUPS[key])
            else:
                changes.add(key)

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
    def _handle_position(self) -> None:
        """Actualisation de la position"""
        self._sprite.position = self._x, self._y, 0

    def _handle_anchor(self) -> None:
        """Actualisation de l'ancre"""
        self._sprite.image.anchor_x, self._sprite.image.anchor_y = int(self._anchor_x * self._sprite.image.width), int(self._anchor_y * self._sprite.image.height)

    def _handle_scales(self) -> None:
        """Actualisation du facteur de redimensionnement"""
        raw = self._load_image(self._image.path)
        if raw:
            self._sprite.scale_x, self._sprite.scale_y = self._effective_scales(raw)

    def _handle_rotation(self) -> None:
        """Actualisation de la rotation"""
        self._sprite.rotation = self._rotation

    def _handle_color(self) -> None:
        """Actualisation de la couleur de teinte"""
        r, g, b, a = self._color.rgba8 if self._color is not None else (255, 255, 255, 255)
        a = int(a * self._opacity)
        self._sprite.color = (r, g, b, a)

    def _handle_opacity(self) -> None:
        """Actualisation de l'opacité"""
        r, g, b, a = self._color.rgba8 if self._color is not None else (255, 255, 255, 255)
        a = int(a * self._opacity)
        self._sprite.opacity = (r, g, b, a)

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