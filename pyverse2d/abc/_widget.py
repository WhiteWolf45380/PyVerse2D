# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from .._flag import Super
from ..math import Point

from abc import ABC
from bisect import insort
from numbers import Real
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .._rendering._pipeline import Pipeline

# ======================================== ABSTRACT CLASS ========================================
class Widget(ABC):
    """
    Classe abstraite des composants UI

    Args:
        parent(Widget, optional): composant parent
        pos(Point, optional): position
        anchor(Point, optional): ancre locale
        opacity(float, optional): opacité
    """
    __slots__ = ("_parent", "_children", "_pos", "_anchor", "_opacity", "_visible")

    def __init__(self, parent: Widget = None, pos: Point = (0, 0), anchor: Point = (0.5, 0.5), opacity: float = 1.0):
        self._parent: Widget = expect(parent, (Widget, None))
        self._children: list[WidgetWrapper] = []
        self._pos: Point = Point(pos)
        self._anchor: Point = Point(anchor)
        self._opacity: float = float(expect(opacity, Real))
        self._active: bool = True
        self._visible: bool = True

    # ======================================== GETTERS ========================================
    @property
    def parent(self) -> Widget| None:
        """Renvoie le composant parent"""
        return self._parent

    @property
    def children(self) -> tuple[Widget]:
        """Renvoie la liste des composants enfants"""
        return tuple(wrapper.widget for wrapper in self._children)
    
    def child(self, name: str) -> Widget:
        """
        Renvoie un composant enfant par son identifiant

        Args:
            name(str): identifiant du composant
        """
        expect(name, str)
        for child in self._children:
            if child.name == name:
                return child
        raise ValueError(f"This widget has no child named {name}")
    
    @property
    def pos(self) -> Point:
        """Renvoie la position"""
        return self._pos
    
    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._pos.x
    
    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._pos.y
    
    @property
    def anchor(self) -> Point:
        """Renvoie l'ancre locale"""
        return self._anchor
    
    @property
    def anchor_x(self) -> float:
        """Renvoie l'ancre horizontale"""
        return self._anchor.x
    
    @property
    def anchor_y(self) -> float:
        """Renvoie l'ancre verticale"""
        return self._anchor.y
    
    @property
    def opacity(self) -> float:
        """Renvoie l'opacité"""
        return self._opacity
    
    @property
    def active(self) -> bool:
        """Renvoie l'activité"""
        return self._active
    
    @property
    def visible(self) -> bool:
        """Renvoie la visibilité"""
        return self._visible

    # ======================================== SETTERS ========================================
    @pos.setter
    def pos(self, value: Point) -> None:
        """Fixe la position"""
        self._pos = Point(value)
    
    @x.setter
    def x(self, value: Real) -> None:
        """Fixe la position horizontale"""
        self._pos.x = value

    @y.setter
    def y(self, value: Real) -> None:
        """Fixe la position verticale"""
        self._pos.y = value
    
    @anchor.setter
    def anchor(self, value: Point) -> None:
        """Fixe l'ancre locale"""
        self._anchor = Point(value)

    @anchor_x.setter
    def anchor_x(self, value: Real) -> None:
        """Fixe l'ancre horizontale"""
        self._anchor.x = value

    @anchor_y.setter
    def anchor_y(self, value: Real) -> None:
        """Fixe l'ancre verticale"""
        self._anchor.y = value

    @active.setter
    def active(self, value: bool) -> None:
        """Fixe l'activité"""
        self._active = expect(value, bool)

    @visible.setter
    def visible(self, value: bool) -> None:
        """Fixe la visibilité"""
        self._visible = expect(value, bool)

    # ======================================== PREDICATES ========================================
    def is_active(self) -> bool:
        """Vérifie l'activité"""
        return self._active
    
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._visible

    # ======================================== PUBLIC METHODS ========================================
    def activate(self) -> None:
        """Active le composant"""
        self._active = True
    
    def deactivate(self) -> None:
        """Désactive le composant"""
        self._active = False
    
    def switch_activity(self) -> None:
        """Bascule l'activité"""
        self._active = not self._active

    def show(self) -> None:
        """Montre le composant"""
        self._visible = True

    def hide(self) -> None:
        """Cache le composant"""
        self._visible = False
    
    def switch_visibility(self) -> None:
        """Bascule la visibilité"""
        self._visible = not self._visible

    # ======================================== CHILDREN ========================================
    def add_child(self, child: Widget, name: str = None, z: int = 0):
        """
        Ajoute un composant enfant

        Args:
            child(Widget): composant à associer
            z(int): ordre de rendu
        """
        if child in self._children:
            raise ValueError(f"{child} is already a child of this widget")
        if child.parent is not None:
            raise ValueError(f"{child} has already a parent")
        wrapper = WidgetWrapper(expect(child, Widget), expect(name, (str, None)), expect(z, int))
        insort(self._children, wrapper)

    def remove_child(self, child: Widget) -> None:
        """
        Retire un composant enfant

        Args:
            child(Widget): composant à dissocier
        """
        if child in self._children:
            self._children.remove(child)

    def remove_child_by_name(self, name: str) -> None:
        """
        Retire un composant enfant par son identifiant

        Args:
            name(str): nom du composant à dissocier
        """
        to_remove = []
        for child in self._children:
            if child.name == name:
                to_remove.append(child.widget)
        for wrapper in to_remove:
            self._children.remove(wrapper)
    
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
    def update(self, dt: float) -> Super:
        """Actualisation"""
        if not self._active:
            return Super.STOP

        for child in self._children:
            child.update(dt)

        return Super.NONE

    def draw(self, pipeline: Pipeline) -> Super:
        """Affichage"""
        if not self._visible:
            return Super.STOP
    
        for child in self._children:
            child.draw(pipeline)

        return Super.NONE
    
    # ======================================== HELPERS ========================================
    def _get_wrapper(self, child: Widget) -> WidgetWrapper:
        """Récupère le wrapper d'un composant"""
        for wrapper in self._children:
            if wrapper.widget == child:
                return wrapper
        raise ValueError(f"{child} is not a child of this widget")


# ======================================== WRAPPER ========================================
class WidgetWrapper:
    """Wrapper des composants UI"""
    __slots__ = ("_widget", "name", "z")

    def __init__(self, widget: Widget, name: str, z: int):
        self._widget: Widget = widget
        self.name: str = name
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