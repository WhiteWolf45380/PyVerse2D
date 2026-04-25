# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..typing import DictKeys, DictValues

from abc import ABC, abstractmethod
from typing import Any

# ======================================== ABSTRACT CLASS ========================================
class Bundle(ABC):
    """Classe abstraite des paquets d'assets"""
    __slots__ = ("_paths", "_cache")

    def __init__(self, paths: dict[str, str]):
        self._paths: dict[str, str] = paths
        self._cache: dict[str, Any] = {}

    # ======================================== PROPERTIES ========================================
    @property
    def paths(self) -> dict[str, str]:
        """Renvoie les entrées du bundle"""
        return self._paths

    # ======================================== FACTORY ========================================
    @classmethod
    @abstractmethod
    def from_folder(cls, folder_path: str, prefix: str  ="", extensions: list[str] = None, remove_prefix: bool = False, **kwargs) -> Bundle: ...

    def preload(self) -> None:
        """Précharge tous les éléments du bundle"""
        for key in self._paths:
            self.get(key, cache=True)

    # ======================================== INTERFACE ========================================
    @abstractmethod
    def get(self, key: str, cache: bool = False) -> Any: ...

    def keys(self) -> DictKeys[str]:
        """Renvoie une vue des clés du bundle"""
        return self._paths.keys()
    
    def values(self) -> DictValues[Any]:
        """Renvoie une vue des valeurs du bundle"""
        return self._paths.values()
    
    def __iter__(self):
        """Itère sur les entrées du bundle"""
        return iter(self._paths)

    def __contains__(self, key: str) -> bool:
        """Vérifie qu'une clé est présente dans le bundle"""
        return key in self._paths

    def has(self, key: str) -> bool:
        """Vérifie qu'une clé est présente dans le bundle

        Args:
            key: clé à vérifier
        """
        return self.__contains__(key)
    
    def __len__(self) -> int:
        """Renvoie le nombre d'entrées du bundle"""
        return len(self._paths)