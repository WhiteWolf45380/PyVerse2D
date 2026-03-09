# ======================================== IMPORTS ========================================
from __future__ import annotations

from abc import ABC, abstractmethod

# ======================================== OBJET ========================================
class Asset(ABC):
    """Objet lien entre les assets et l'engine"""
    @abstractmethod
    def __init__(self):
        ...