# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, positive
from ..abc import Shape

from numbers import Real

# ======================================== TILESET ========================================
class Tileset:
    """
    Spritesheet découpée en tuiles de taille uniforme

    Args:
        image_path(str): chemin de l'image source
        tile_width(Real): largeur d'une tuile en pixels
        tile_height(Real): hauteur d'une tuile en pixels
        margin(Real, optional): marge extérieure en pixels
        spacing(Real, optional): espacement entre tuiles en pixels
    """
    __slots__ = ("_image_path", "_tile_width", "_tile_height", "_margin", "_spacing", "_meta")

    def __init__(
        self,
        image_path: str,
        tile_width: Real,
        tile_height: Real,
        margin: Real = 0,
        spacing: Real = 0,
    ):
        self._image_path: str    = expect(image_path, str)
        self._tile_width: float  = float(positive(expect(tile_width,  Real)))
        self._tile_height: float = float(positive(expect(tile_height, Real)))
        self._margin: float      = float(positive(expect(margin,  Real)))
        self._spacing: float     = float(positive(expect(spacing, Real)))
        self._meta: dict[int, TileMeta] = {}

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return (
            f"Tileset(path={self._image_path}, "
            f"tile={self._tile_width}x{self._tile_height}, "
            f"margin={self._margin}, spacing={self._spacing})"
        )

    # ======================================== GETTERS ========================================
    @property
    def image_path(self) -> str:
        """Renvoie le chemin de l'image source"""
        return self._image_path

    @property
    def tile_width(self) -> float:
        """Renvoie la largeur d'une tuile en pixels"""
        return self._tile_width

    @property
    def tile_height(self) -> float:
        """Renvoie la hauteur d'une tuile en pixels"""
        return self._tile_height

    @property
    def margin(self) -> float:
        """Renvoie la marge extérieure en pixels"""
        return self._margin

    @property
    def spacing(self) -> float:
        """Renvoie l'espacement entre tuiles en pixels"""
        return self._spacing

    def tile_region(self, tile_id: int) -> tuple[float, float, float, float]:
        """
        Renvoie la région (x, y, w, h) de la tuile dans l'image source

        Args:
            tile_id(int): identifiant local de la tuile (0-indexé)
        """
        tile_id = expect(tile_id, int)
        stride  = self._tile_width + self._spacing
        cols    = self._columns_hint(stride)
        col     = tile_id % cols
        row     = tile_id // cols
        x = self._margin + col * stride
        y = self._margin + row * stride
        return (x, y, self._tile_width, self._tile_height)

    def get_meta(self, tile_id: int) -> TileMeta | None:
        """
        Renvoie les métadonnées d'une tuile, ou None si aucune n'est définie

        Args:
            tile_id(int): identifiant local de la tuile
        """
        return self._meta.get(expect(tile_id, int))

    # ======================================== PUBLIC METHODS ========================================
    def set_meta(self, tile_id: int, meta: TileMeta) -> None:
        """
        Associe des métadonnées à une tuile

        Args:
            tile_id(int): identifiant local de la tuile
            meta(TileMeta): métadonnées à associer
        """
        self._meta[expect(tile_id, int)] = expect(meta, TileMeta)

    # ======================================== INTERNALS ========================================
    def _columns_hint(self, stride: float) -> int:
        """Placeholder, le vrai calcul nécessite la largeur image, connue au runtime par le renderer"""
        return max(1, int(stride))


# ======================================== TILE META ========================================
class TileMeta:
    """
    Métadonnées associées à un ID de tuile dans un Tileset

    Args:
        tags(str, optional): ensemble de tags (ex. "solid", "ladder")
        collision_shape(Shape, optional): forme de collision custom ; None = bounding box de la tuile
    """
    __slots__ = ("_tags", "_collision_shape")

    def __init__(
        self,
        *tags: str,
        collision_shape: Shape | None = None,
    ):
        self._tags: frozenset[str] = frozenset(expect(tags, tuple[str]))
        self._collision_shape: Shape | None = collision_shape

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return f"TileMeta(tags={self._tags}, collision_shape={self._collision_shape})"

    # ======================================== GETTERS ========================================
    @property
    def tags(self) -> frozenset[str]:
        """Renvoie les tags de la tuile"""
        return self._tags

    @property
    def collision_shape(self) -> Shape | None:
        """Renvoie la forme de collision custom, ou None si bounding box"""
        return self._collision_shape

    # ======================================== PREDICATES ========================================
    def has_tag(self, tag: str) -> bool:
        """Vérifie si la tuile possède un tag"""
        return tag in self._tags

    def is_solid(self) -> bool:
        """Raccourci — vérifie si la tuile est solide"""
        return "solid" in self._tags