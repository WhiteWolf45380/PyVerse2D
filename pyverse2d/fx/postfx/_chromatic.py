# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import positive
from ..._rendering import Pipeline
from ...abc import FxEffect, FxRenderer

from dataclasses import dataclass
from numbers import Real
from typing import ClassVar
import math

import pyglet.gl as gl
from pyglet.graphics.shader import Shader, ShaderProgram

# ======================================== SHADERS ========================================
_VERT = """
#version 330 core
layout(location = 0) in vec2 in_position;
layout(location = 1) in vec2 in_uv;
out vec2 v_uv;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
}
"""

_FRAG = """
#version 330 core
uniform sampler2D u_texture;
uniform vec2 u_offset;
in vec2 v_uv;
out vec4 out_color;

void main() {
    float r = texture(u_texture, clamp(v_uv + u_offset, 0.0, 1.0)).r;
    float g = texture(u_texture, v_uv).g;
    float b = texture(u_texture, clamp(v_uv - u_offset, 0.0, 1.0)).b;
    float a = texture(u_texture, v_uv).a;
    out_color = vec4(r, g, b, a);
}
"""

# ======================================== EFFECT ========================================
@dataclass(slots=True, frozen=True)
class Chromatic(FxEffect):
    """Effet post-processing: aberration chromatique

    Args:
        strength: intensité du décalage en fraction de la largeur d'écran *[0, 1]*
        angle: angle du décalage en degrés *(0 = horizontal)*
    """
    strength: Real = 0.005
    angle: Real = 0.0

    _ID: ClassVar[str] = "chromatic"

    def __post_init__(self) -> None:
        """Transtypage et vérifications"""
        object.__setattr__(self, "strength", float(self.strength))
        object.__setattr__(self, "angle", float(self.angle))

        if __debug__:
            positive(self.strength, include=True)

# ======================================== RENDERER ========================================
class ChromaticFxRenderer(FxRenderer):
    """Renderer spécialisé pour l'effet ``Chromatic``"""
    __slots__ = tuple()

    _HANDLES: ClassVar[frozenset[type[FxEffect]]] = frozenset({Chromatic})

    _program: ClassVar[ShaderProgram | None] = None

    @classmethod
    def _get_program(cls) -> ShaderProgram:
        """Retourne (en le créant si nécessaire) le shader d'aberration chromatique"""
        if cls._program is None:
            cls._program = ShaderProgram(Shader(_VERT, 'vertex'), Shader(_FRAG, 'fragment'))
        return cls._program

    @classmethod
    def clear_shader_cache(cls) -> None:
        """Libère le ``ShaderProgram`` mis en cache"""
        cls._program = None

    def apply(self, pipeline: Pipeline, effect: Chromatic, intensity: float) -> None:
        """Applique l'aberration chromatique

        Args:
            pipeline: ``Pipeline`` de rendu courant
            effect: paramètres de l'aberration
            intensity: intensité du blend *[0, 1]*
        """
        theta = math.radians(effect.angle)
        strength = effect.strength * intensity
        dx = strength * math.cos(theta)
        dy = strength * math.sin(theta)

        pipeline.apply_shader(
            self._get_program(),
            u_offset=(dx, dy),
        )

# ======================================== EXPORTS ========================================
__all__ = [
    "Chromatic",
    "ChromaticFxRenderer",
]