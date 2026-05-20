# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._rendering import Pipeline
from ...abc import PostFxEffect, SpecializedPostFxRenderer
from ...shape import Circle, Rect

from ._zone import PostFxZone

from typing import Type, ClassVar

# ======================================== RENDERER ========================================
class PostFxRenderer:
    """Renderer central des effets post-processing

    Maintient un registre de ``SpecializedPostFxRenderer`` qui s'enregistrent
    automatiquement via ``SpecializedPostFxRenderer.__init_subclass__``.

    Le dispatch est entièrement polymorphique : ajouter un nouvel effet
    ne nécessite aucune modification de cette classe.
    """
    __slots__ = tuple()

    _registry: ClassVar[dict[Type[PostFxEffect], SpecializedPostFxRenderer]] = {}

    # ======================================== REGISTRY ========================================
    @classmethod
    def _register(cls, renderer_cls: Type[SpecializedPostFxRenderer]) -> None:
        """Enregistre un renderer spécialisé pour les effets qu'il déclare gérer.

        Args:
            renderer_cls: classe du renderer spécialisé à enregistrer
        """
        instance = renderer_cls()
        for effect_type in renderer_cls._HANDLES:
            cls._registry[effect_type] = instance

    @classmethod
    def clear_shader_cache(cls) -> None:
        """Libère tous les ``ShaderProgram`` mis en cache par les renderers enregistrés.

        À appeler lors d'un changement de contexte OpenGL ou d'un hot-reload.
        """
        seen: set[int] = set()
        for renderer in cls._registry.values():
            rid = id(renderer)
            if rid not in seen:
                seen.add(rid)
                renderer.clear_shader_cache()

    # ======================================== RENDER ========================================
    def render(self, pipeline: Pipeline, zones: list[PostFxZone]) -> None:
        """Applique tous les effets de toutes les zones actives

        Args:
            pipeline: ``Pipeline`` de rendu courant
            zones: zones actives à rendre
        """
        for zone in zones:
            if zone.is_unbounded():
                self._render_zone(pipeline, zone, intensity=1.0)
            else:
                intensity = self._compute_intensity(pipeline, zone)
                if intensity <= 0.0:
                    continue
                self._render_zone(pipeline, zone, intensity)

    def _render_zone(self, pipeline: Pipeline, zone: PostFxZone, intensity: float) -> None:
        """Applique la chaîne d'effets d'une zone

        Args:
            pipeline: ``Pipeline`` de rendu courant
            zone: zone à rendre
            intensity: intensité du blend *[0, 1]*
        """
        for effect in zone.get_effects():
            renderer = self._registry.get(type(effect))
            if renderer is not None:
                renderer.apply(pipeline, effect, intensity)

    def _compute_intensity(self, pipeline: Pipeline, zone: PostFxZone) -> float:
        """Calcule l'intensité de blend d'une zone bounded

        Args:
            pipeline: ``Pipeline`` de rendu courant
            zone: zone bounded à évaluer

        Returns:
            float: intensité *[0, 1]*
        """
        cx, cy = pipeline.world_to_screen(zone.x, zone.y)
        sx, sy = pipeline.screen_center()

        match zone.shape:
            case Circle():
                r = pipeline.scale_to_screen(zone.shape.radius)
                dist = ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5
                inner_r = r
                outer_r = r + zone.blend
                if dist >= outer_r:
                    return 0.0
                if dist <= inner_r:
                    return 1.0
                return 1.0 - (dist - inner_r) / zone.blend

            case Rect():
                hw = pipeline.scale_to_screen(zone.shape.half_width)
                hh = pipeline.scale_to_screen(zone.shape.half_height)
                dx = max(abs(sx - cx) - hw, 0.0)
                dy = max(abs(sy - cy) - hh, 0.0)
                dist = (dx ** 2 + dy ** 2) ** 0.5
                if zone.blend <= 0.0:
                    return 1.0 if dx == 0.0 and dy == 0.0 else 0.0
                if dist >= zone.blend:
                    return 0.0
                return 1.0 - dist / zone.blend

            case _:
                return 1.0

# ======================================== EXPORTS ========================================
__all__ = [
    "PostFxRenderer",
]