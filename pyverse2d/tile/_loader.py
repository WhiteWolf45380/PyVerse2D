# ======================================== IMPORTS ========================================
from __future__ import annotations

from ._tile import Tile
from ._tile_map import TileMap
from ._map_asset import MapAsset

import json
import numpy as np
from pathlib import Path
from xml.etree import ElementTree as ET

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
        raw = json.loads(path.read_text(encoding="utf-8"))

        tiles = _load_tiles_json(raw["tilesets"], path.parent)
        layers = {}

        for layer in raw.get("layers", []):
            if layer["type"] != "tilelayer":
                continue
            layers[layer["name"]] = _parse_layer_json(layer, raw, tiles)

        return MapAsset(layers)

    # ======================================== TILED TMX ========================================
    @staticmethod
    def from_tiled_tmx(path: str | Path) -> MapAsset:
        """
        Charge un fichier Tiled au format natif XML (.tmx)

        Args:
            path(str | Path): chemin du fichier
        """
        path = Path(path)
        root = ET.parse(path).getroot()

        map_tw = int(root.attrib["tilewidth"])
        map_th = int(root.attrib["tileheight"])

        tiles = _load_tiles_tmx(root.findall("tileset"), path.parent)
        layers = {}

        for layer in root.findall("layer"):
            layers[layer.attrib["name"]] = _parse_layer_tmx(layer, map_tw, map_th, tiles)

        return MapAsset(layers)


# ======================================== JSON INTERNALS ========================================
def _load_tiles_json(raw_tilesets: list[dict], base_dir: Path) -> list[tuple[int, Tile]]:
    result = []
    for entry in raw_tilesets:
        firstgid = entry["firstgid"]
        if "source" in entry:
            data = json.loads((base_dir / entry["source"]).read_text(encoding="utf-8"))
        else:
            data = entry
        result.append((firstgid, _tile_from_dict(data, base_dir)))
    result.sort(key=lambda t: t[0])
    return result


def _parse_layer_json(layer: dict, raw: dict, tiles: list[tuple[int, Tile]]) -> TileMap:
    cols = layer["width"]
    rows = layer["height"]
    flat_ids = layer["data"]
    firstgid, tile = _tile_for(flat_ids, tiles)
    local_ids = [(gid - firstgid + 1) if gid != 0 else 0 for gid in flat_ids]
    grid = np.array(local_ids, dtype=np.int32).reshape(rows, cols)
    return TileMap(tile=tile, grid=grid, tile_width=raw["tilewidth"], tile_height=raw["tileheight"])


# ======================================== TMX INTERNALS ========================================
def _load_tiles_tmx(tileset_nodes: list[ET.Element], base_dir: Path) -> list[tuple[int, Tile]]:
    result = []
    for node in tileset_nodes:
        firstgid = int(node.attrib["firstgid"])
        if "source" in node.attrib:
            tsx_path = base_dir / node.attrib["source"]
            tsx_root = ET.parse(tsx_path).getroot()
            tile = _tile_from_tsx(tsx_root, tsx_path.parent)
        else:
            tile = _tile_from_tsx(node, base_dir)
        result.append((firstgid, tile))
    result.sort(key=lambda t: t[0])
    return result


def _tile_from_tsx(node: ET.Element, base_dir: Path) -> Tile:
    image_node = node.find("image")
    return Tile(
        image_path = str(base_dir / image_node.attrib["source"]),
        tile_width = int(node.attrib["tilewidth"]),
        tile_height = int(node.attrib["tileheight"]),
        margin = int(node.attrib.get("margin",  0)),
        spacing = int(node.attrib.get("spacing", 0)),
    )


def _parse_layer_tmx(layer: ET.Element, map_tw: int, map_th: int, tiles: list[tuple[int, Tile]]) -> TileMap:
    cols = int(layer.attrib["width"])
    rows = int(layer.attrib["height"])
    data_node = layer.find("data")
    encoding = data_node.attrib.get("encoding", "xml")

    if encoding == "csv":
        flat_ids = [int(v) for v in data_node.text.strip().split(",")]
    elif encoding == "xml":
        flat_ids = [int(tile.attrib["gid"]) for tile in data_node.findall("tile")]
    else:
        raise NotImplementedError(f"Encodage TMX non supporté : '{encoding}' (utilisez CSV ou XML dans Tiled)")

    firstgid, tile = _tile_for(flat_ids, tiles)
    local_ids = [(gid - firstgid + 1) if gid != 0 else 0 for gid in flat_ids]
    grid = np.array(local_ids, dtype=np.int32).reshape(rows, cols)
    return TileMap(tile=tile, grid=grid, tile_width=map_tw, tile_height=map_th)


# ======================================== SHARED INTERNALS ========================================
def _tile_from_dict(data: dict, base_dir: Path) -> Tile:
    return Tile(
        image_path = str(base_dir / data["image"]),
        tile_width = data["tilewidth"],
        tile_height = data["tileheight"],
        margin = data.get("margin", 0),
        spacing = data.get("spacing", 0),
    )


def _tile_for(flat_ids: list[int], tiles: list[tuple[int, Tile]]) -> tuple[int, Tile]:
    non_empty = [gid for gid in flat_ids if gid != 0]
    if not non_empty:
        return tiles[0]
    min_gid = min(non_empty)
    candidate = tiles[0]
    for firstgid, tile in tiles:
        if firstgid <= min_gid:
            candidate = (firstgid, tile)
    return candidate