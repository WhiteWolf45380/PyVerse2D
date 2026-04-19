# ======================================== IMPORTS ========================================
from __future__ import annotations

from ...abc import Widget

from ...typing import BorderAlign

# ======================================== WIDGET ========================================
class Button(Widget):
    """Composant GUI composé: Bouton
    
    Args:
        position: positionnement
        anchor: ancre relative locale
        back: forme de fond du bouton
        back_color: couleur de fond
        text: texte du bouton
        text_anchor: ancre relative du texte dans le bouton
        text_color: couleur du texte
        text_weight: graisse ('bold', 'thin', '100'…'900', ou int pyglet)
        text_italic: italique
        text_underline: couleur de soulignement
        border_width: épaisseur de la bordure
        border_align: alignement de la bordure
        border_color: couleur de la bordure
        opacity: opacité [0, 1]
        clipping: rendu des widgets enfants strictement dans le AABB de la hitbox
    """