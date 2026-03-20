# ======================================== IMPORTS ========================================
from __future__ import annotations

from ._tile import Tile
from ._tile_map import TileMap
from ._map_asset import MapAsset

import json
import numpy as np
from pathlib import Path

# ======================================== LOADER ========================================
class MapLoader:
    """Charge un fichier de map externe et produit un MapAsset"""

    # ======================================== TILED JSON ========================================
    @staticmethod
    def from_tiled_json(path: str | Path) -> MapAsset:
        """
        Charge un fichier Tiled au format JSON (.json)

        Args:
            path(str | Path): chemin du fichier
        """
        path = Path(path)
        raw  = json.loads(path.read_text(encoding="utf-8"))

        tiles  = _load_tiles(raw["tilesets"], path.parent)
        layers = {}

        for layer in raw.get("layers", []):
            if layer["type"] != "tilelayer":
                continue

            name      = layer["name"]
            cols      = layer["width"]
            rows      = layer["height"]
            flat_ids  = layer["data"]          # IDs globaux Tiled (1-indexés, 0 = vide)
            firstgid, tile = _tile_for(flat_ids, tiles)

            # Conversion IDs globaux → IDs locaux (0-indexés), 0 reste vide
            local_ids = [
                (gid - firstgid) if gid != 0 else 0
                for gid in flat_ids
            ]
            grid = np.array(local_ids, dtype=np.int32).reshape(rows, cols)

            layers[name] = TileMap(
                tile        = tile,
                grid        = grid,
                tile_width  = raw["tilewidth"],
                tile_height = raw["tileheight"],
            )

        return MapAsset(layers)


# ======================================== INTERNALS ========================================
def _load_tiles(raw_tilesets: list[dict], base_dir: Path) -> list[tuple[int, Tile]]:
    """
    Résout et charge tous les tilesets déclarés dans le fichier

    Renvoie une liste de (firstgid, Tile) triée par firstgid croissant
    """
    result = []
    for entry in raw_tilesets:
        firstgid = entry["firstgid"]

        # Tileset externe — fichier .tsj / .tsx référencé
        if "source" in entry:
            source_path = base_dir / entry["source"]
            data = json.loads(source_path.read_text(encoding="utf-8"))
        else:
            data = entry

        tile = Tile(
            image_path  = str(base_dir / data["image"]),
            tile_width  = data["tilewidth"],
            tile_height = data["tileheight"],
            margin      = data.get("margin",  0),
            spacing     = data.get("spacing", 0),
        )
        result.append((firstgid, tile))

    result.sort(key=lambda t: t[0])
    return result


def _tile_for(flat_ids: list[int], tiles: list[tuple[int, Tile]]) -> tuple[int, Tile]:
    """
    Renvoie le (firstgid, Tile) correspondant aux IDs de la couche

    Stratégie : on prend le tileset dont le firstgid est le plus grand
    tout en restant <= au premier ID non-vide de la couche
    """
    non_empty = [gid for gid in flat_ids if gid != 0]
    if not non_empty:
        return tiles[0]

    min_gid   = min(non_empty)
    candidate = tiles[0]
    for firstgid, tile in tiles:
        if firstgid <= min_gid:
            candidate = (firstgid, tile)
    return candidate