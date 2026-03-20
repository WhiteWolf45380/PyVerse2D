# ======================================== IMPORTS ========================================
from __future__ import annotations

from ._tile_map import TileMap
from ._tile import TileMeta

from .._internal import expect, positive
from ..world import World, Entity, Transform, Collider, RigidBody
from ..shape import Rect

from numbers import Real

# ======================================== COLLISION MAPPER ========================================
class CollisionMapper:
    """
    Convertit les tuiles solides d'un TileMap en bodies statiques dans le World

    Args:
        tile_map(TileMap): couche source
        solid_tag(str, optional): tag identifiant les tuiles solides
        friction(Real, optional): friction par défaut pour toutes les tuiles
        restitution(Real, optional): restitution par défaut pour toutes les tuiles
    """
    __slots__ = ("_tile_map", "_solid_tag", "_friction", "_restitution")

    def __init__(
        self,
        tile_map: TileMap,
        solid_tag: str = "solid",
        friction: Real = 0.3,
        restitution: Real = 0.0,
    ):
        self._tile_map: TileMap = expect(tile_map, TileMap)
        self._solid_tag: str = expect(solid_tag, str)
        self._friction: float = float(positive(expect(friction, Real)))
        self._restitution: float = float(positive(expect(restitution, Real)))

    # ======================================== PUBLIC METHODS ========================================
    def inject(self, world: World) -> None:
        """
        Parcourt la grille, fusionne les tuiles solides adjacentes et les injecte dans le World

        Args:
            world(World): monde cible
        """
        for col, row, w, h, friction, restitution in self._merged_rects():
            x, y = self._tile_map.tile_to_world(col, row)
            entity = Entity(
                Transform(x=x + w / 2, y=y + h / 2),
                Collider(shape=Rect(w, h)),
                RigidBody(friction=friction, restitution=restitution)
            )
            world.add_entity(entity)

    # ======================================== INTERNALS ========================================
    def _is_solid(self, col: int, row: int) -> bool:
        """Vérifie si la tuile à (col, row) est solide"""
        tile_id = self._tile_map.tile_at(col, row)
        if tile_id == 0:
            return False
        meta = self._tile_map.tile.get_meta(tile_id)
        if meta is None:
            return False
        return meta.has_tag(self._solid_tag)

    def _resolve_props(self, tile_id: int) -> tuple[float, float]:
        """Résout friction et restitution pour un tile_id"""
        meta: TileMeta | None = self._tile_map.tile.get_meta(tile_id)
        friction = meta.friction if (meta and meta.friction is not None) else self._friction
        restitution = meta.restitution if (meta and meta.restitution is not None) else self._restitution
        return friction, restitution

    def _merged_rects(self) -> list[tuple[int, int, float, float, float, float]]:
        """Fusionne les tuiles solides en rectangles par sweep horizontal puis vertical"""
        tm = self._tile_map
        tw = tm.tile_width
        th = tm.tile_height
        rects = []

        visited = [[False] * tm.cols for _ in range(tm.rows)]
        for row in range(tm.rows):
            for col in range(tm.cols):
                if visited[row][col] or not self._is_solid(col, row):
                    continue

                tile_id = tm.tile_at(col, row)
                friction, restitution = self._resolve_props(tile_id)

                # Extension horizontale
                w = 1
                while (
                    col + w < tm.cols
                    and not visited[row][col + w]
                    and self._is_solid(col + w, row)
                    and self._resolve_props(tm.tile_at(col + w, row)) == (friction, restitution)
                ):
                    w += 1

                # Extension verticale
                h = 1
                while row + h < tm.rows:
                    can_extend = all(
                        not visited[row + h][col + c]
                        and self._is_solid(col + c, row + h)
                        and self._resolve_props(tm.tile_at(col + c, row + h)) == (friction, restitution)
                        for c in range(w)
                    )
                    if not can_extend:
                        break
                    h += 1

                # Marquage
                for dr in range(h):
                    for dc in range(w):
                        visited[row + dr][col + dc] = True

                rects.append((col, row, w * tw, h * th, friction, restitution))

        return rects