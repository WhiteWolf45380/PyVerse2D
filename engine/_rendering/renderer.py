# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..asset import Image, Text

import pyglet
import pyglet.image
import pyglet.text
import pyglet.font
import pyglet.sprite
from pyglet.window import Window

# ======================================== OBJET ========================================
class Renderer:
    """Seul endroit qui touche pyglet"""
    _image_cache: dict[str, pyglet.image.AbstractImage] = {}
    _font_cache: dict[str, str | None] = {}
    _label_cache: dict[tuple, pyglet.text.Label] = {}

    def __init__(self, window: Window):
        self._window = window

    # ======================================== IMAGES ========================================
    def _load_image(self, path: str) -> pyglet.image.AbstractImage | None:
        """Charge et cache une image"""
        if path in self._image_cache:
            return self._image_cache[path]
        try:
            img = pyglet.image.load(path)
            self._image_cache[path] = img
            return img
        except FileNotFoundError:
            print(f"Cannot load image {path}")
            return None

    def draw_image(self, image: Image, x: float, y: float, alpha: float = 1.0):
        """
        Dessine une image

        Args:
            image(Image): descripteur de l'image
            x(float): position horizontale
            y(float): position verticale
            alpha(float): opacité
        """
        raw = self._load_image(image.path)
        if raw is None:
            return

        transformed = raw.get_transform(
            flip_x=image.flip_x,
            flip_y=image.flip_y,
            rotate=image.rotation
        )

        sprite = pyglet.sprite.Sprite(transformed, x=x, y=y)
        sprite.scale = image.scale
        sprite.opacity = int(alpha * 255)
        sprite.draw()

    # ======================================== TEXTES ========================================
    def _resolve_font(self, font: str | None) -> str | None:
        """Résout et cache le nom de la police"""
        if font in self._font_cache:
            return self._font_cache[font]

        resolved = None
        if font is not None:
            if font in pyglet.font.get_font_names():
                resolved = font
            else:
                try:
                    pyglet.font.add_file(font)
                    resolved = font
                except Exception:
                    print(f"Cannot load font {font}, falling back to default")

        self._font_cache[font] = resolved
        return resolved

    def draw_text(self, text: Text, x: float, y: float, alpha: float = 1.0):
        """
        Dessine un texte

        Args:
            text(Text): descripteur du texte
            x(float): position horizontale
            y(float): position verticale
            alpha(float): opacité
        """
        key = (text.text, text.font, text.fontsize, text.color)

        if key not in self._label_cache:
            self._label_cache[key] = pyglet.text.Label(
                text.text,
                font_name=self._resolve_font(text.font),
                font_size=text.fontsize,
                color=text.color,
            )

        label = self._label_cache[key]
        label.x, label.y = x, y
        label.opacity = int(alpha * 255)
        label.draw()

    # ======================================== UTILITAIRES ========================================
    def clear_cache(self):
        """Vide tous les caches"""
        self._image_cache.clear()
        self._font_cache.clear()
        self._label_cache.clear()