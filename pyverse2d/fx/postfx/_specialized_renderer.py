# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import PostFxEffect

from typing import TYPE_CHECKING, ClassVar, Type

if TYPE_CHECKING:
    from ..._rendering import Pipeline
    from .. import PostFxRenderer

# ======================================== ABSTRACT CLASS ========================================
class SpecializedPostFxRenderer:
    """Classe abstraite des renderers d'effets post-processing spécialisés"""
    __slots__ = tuple()

    _HANDLES: ClassVar[frozenset[Type[PostFxEffect]]]

    _POSTFX_RENDERER: Type[PostFxRenderer] = None

    @classmethod
    def _get_postfx_renderer(cls) -> Type[PostFxRenderer]:
        """Renvoie le ``PostFxRenderer``"""
        if cls._POSTFX_RENDERER is None:
            from ._renderer import PostFxRenderer
            cls._POSTFX_RENDERER = PostFxRenderer
        return cls._POSTFX_RENDERER

    def __init_subclass__(cls, **kwargs: object) -> None:
        """S'enregistre en tant que renderer spécialisé"""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "_HANDLES"):
            cls._get_postfx_renderer()._register(cls)

    # ======================================== CONTRACT ========================================
    @classmethod
    def clear_shader_cache(cls) -> None:
        """Libère les ``ShaderProgram`` mis en cache"""

    def apply(self, pipeline: Pipeline, effect: PostFxEffect, intensity: float = 1.0) -> None:
        """Applique l'effet sur le framebuffer courant

        Args:
            pipeline: ``Pipeline`` de rendu courant
            effect: paramètres de l'effet
            intensity: intensité du blend *[0, 1]*
        """

# ======================================== EXPORTS ========================================
__all__ = [
    "SpecializedPostFxRenderer",
]