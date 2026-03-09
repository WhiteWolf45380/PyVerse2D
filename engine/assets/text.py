# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive

from .asset import Asset

import pygame

# ======================================== OBJET ========================================
class Text(Asset):
    """Texte propre au moteur"""
    def __init__(self):
        ...