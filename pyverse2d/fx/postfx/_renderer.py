# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._rendering import Pipeline
from ...abc import PostFxEffect
from ...shape import Circle, Rect

from ._specialized_renderer import SpecializedPostFxRenderer
from ._mask import MaskData, MASK_FULL
from ._zone import PostFxZone

from typing import Type, ClassVar

# ======================================== RENDERER ========================================
class PostFxRenderer:
    """Renderer central des effets post-processing"""
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
        """Libère tous les ``ShaderProgram`` mis en cache par les renderers enregistrés"""
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
                self._render_zone(pipeline, zone, MASK_FULL)
            else:
                mask = self._build_mask(pipeline, zone)
                if mask is None:
                    continue
                self._render_zone(pipeline, zone, mask)

    def _render_zone(self, pipeline: Pipeline, zone: PostFxZone, mask: MaskData) -> None:
        """Applique la chaîne d'effets d'une zone

        Args:
            pipeline: ``Pipeline`` de rendu courant
            zone: zone à rendre
            mask: données de masque spatial à transmettre aux shaders
        """
        for effect in zone.get_effects():
            renderer = self._registry.get(type(effect))
            if renderer is not None:
                renderer.apply(pipeline, effect, mask)

    def _build_mask(self, pipeline: Pipeline, zone: PostFxZone) -> MaskData | None:
        """Construit le ``MaskData`` d'une zone bounded en coordonnées framebuffer.

        Args:
            pipeline: ``Pipeline`` de rendu courant
            zone: zone bounded à évaluer

        Returns:
            ``MaskData`` si la zone est visible, ``None`` sinon
        """
        cx, cy = pipeline.world_to_framebuffer(zone.x, zone.y)
        sx, sy = pipeline.screen.center

        match zone.shape:
            case Circle():
                r = pipeline.scale_to_framebuffer(zone.shape.radius)
                dist = ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5
                if dist >= r + zone.blend:
                    return None
                return MaskData(
                    type=1,
                    center_x=cx,
                    center_y=cy,
                    radius=r,
                    blend=zone.blend,
                )

            case Rect():
                hw, hh = pipeline.scale_to_framebuffer(width=zone.shape.half_width, height=zone.shape.half_height)
                dx = max(abs(sx - cx) - hw, 0.0)
                dy = max(abs(sy - cy) - hh, 0.0)
                dist = (dx ** 2 + dy ** 2) ** 0.5
                if zone.blend <= 0.0:
                    if dx > 0.0 or dy > 0.0:
                        return None
                elif dist >= zone.blend:
                    return None
                return MaskData(
                    type=2,
                    center_x=cx,
                    center_y=cy,
                    half_w=hw,
                    half_h=hh,
                    blend=zone.blend,
                )

            case _:
                return MASK_FULL

# ======================================== EXPORTS ========================================
__all__ = [
    "PostFxRenderer",
]