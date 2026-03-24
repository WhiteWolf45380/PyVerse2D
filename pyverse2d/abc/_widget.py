# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect

from abc import ABC, abstractmethod
from bisect import insort
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._rendering._pipeline import Pipeline

# ======================================== ABSTRACT CLASS ========================================
class Widget(ABC):
    """Classe abstraite des composants UI"""
    def __init__(self, parent: Widget = None):
        self._parent: Widget = parent
        self._children: list[WidgetWrapper] = []
    
    # ======================================== CHILDREN ========================================
    def add_child(self, child: Widget, z: int = 0):
        """
        Ajoute un composant enfant

        Args:
            child(Widget): composant à associer
            z(int): ordre de rendu
        """
        if child in self._children:
            raise ValueError(f"{child} is already a child of this widget")
        wrapper = WidgetWrapper(expect(child, Widget), expect(z, int))
        insort(self._children, wrapper)

    def remove_child(self, child: Widget) -> None:
        """
        Retire un composant enfant

        Args:
            child(Widget): composant à dissocier
        """
        if child in self._children:
            self._children.remove(child)

    @property
    def children(self) -> list[Widget]:
        """Renvoie la liste des composants enfants"""
        return [wrapper.widget for wrapper in self._children]
    
    def reorder(self, child: Widget, z: int) -> None:
        """
        Modifie le Zorder d'un composant enfant

        Args:
            child(Widget): composant enfant
            z(int): ordre de rendu
        """
        wrapper = self._get_wrapper(expect(child, Widget))
        if wrapper.z != z:
            wrapper.z = z
            self._children.remove(child)
            insort(self._children, wrapper)

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        for child in self._children:
            child.update(dt)

    def draw(self, pipeline: Pipeline) -> None:
        """Affichage"""
        for child in self._children:
            child.draw(pipeline)
    
    # ======================================== HELPERS ========================================
    def _get_wrapper(self, child: Widget) -> WidgetWrapper:
        """Récupère le wrapper d'un composant"""
        for wrapper in self._children:
            if wrapper.widget is child:
                return wrapper
        raise ValueError(f"{child} is not a child of this widget")


# ======================================== WRAPPER ========================================
class WidgetWrapper:
    """Wrapper des composants UI"""
    def __init__(self, widget: Widget, z: int):
        self._widget: Widget = widget
        self.z: int = z
    
    @property
    def widget(self) -> Widget:
        return self._widget

    def __eq__(self, other: Widget) -> bool:
        """Vérifie la correspondance des composants"""
        return self._widget == other

    def __lt__(self, other: WidgetWrapper) -> bool:
        """Comparaison inférieure"""
        return self.z < other.z