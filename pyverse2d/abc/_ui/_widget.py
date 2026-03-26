# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect
from ..._flag import Super
from ...math import Point
from ..._rendering import Pipeline, RenderContext

from abc import ABC, abstractmethod
from bisect import insort
from numbers import Real
from typing import Callable

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
    __slots__ = ("_parent", "_children", "_pos", "_anchor", "_opacity", "_active", "_visible", "_activate_process", "_deactivate_process", "_show_process", "_hide_process")

    def __init__(
            self,
            parent: Widget = None,
            pos: Point = (0, 0),
            anchor: Point = (0.5, 0.5),
            opacity: float = 1.0
        ):
        # Arbre
        self._parent: Widget = expect(parent, (Widget, None))
        self._children: list[WidgetWrapper] = []

        # Position
        self._pos: Point = Point(pos)
        self._anchor: Point = Point(anchor)

        # Design
        self._opacity: float = float(expect(opacity, Real))

        # Etat
        self._active: bool = True
        self._visible: bool = True

        # Hooks
        self._activate_process: list[Callable] = []
        self._deactivate_process: list[Callable] = []
        self._show_process: list[Callable] = []
        self._hide_process: list[Callable] = []

    # ======================================== GETTERS ========================================
    @property
    def parent(self) -> Widget| None:
        """Renvoie le composant parent"""
        return self._parent
    
    @property
    def root(self) -> Widget:
        """Renvoie le composant racine"""
        if self._parent is None:
            return self
        return self._parent.root

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
                return child.widget
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
    def absolute_pos(self) -> Point:
        """Renvoie la position absolue"""
        if self._parent is None:
            return self._pos
        return self._parent.absolute_pos + self._pos
    
    @property
    def absolute_x(self) -> float:
        """Renvoie la position horizontale absolue"""
        if self._parent is None:
            return self._pos.x
        return self._parent.absolute_x + self._pos.x
    
    @property
    def absolute_y(self) -> float:
        """Renvoie la position verticale absolue"""
        if self._parent is None:
            return self._pos.y
        return self._parent.absolute_y + self._pos.y
    
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

    # ========================================  STATE ========================================
    def activate(self, propagate: bool = True) -> None:
        """
        Active le composant

        Args:
            propagate(bool, optional): propage l'état aux enfants
        """
        self._active = True
        for fn in self._activate_process:
            fn(self)
        if propagate:
            for child in self._children:
                child.widget.activate()
    
    def deactivate(self, propagate: bool = True) -> None:
        """
        Désactive le composant

        Args:
            propagate(bool, optional): propage l'état aux enfants
        """
        self._active = False
        for fn in self._deactivate_process:
            fn(self)
        if propagate:
            for child in self._children:
                child.widget.deactivate()
    
    def switch_activity(self, propagate: bool = True) -> None:
        """
        Bascule l'activité

        Args:
            propagate(bool, optional): propage l'état aux enfants
        """
        if self._active:
            self.deactivate(propagate=propagate)
        else:
            self.activate(propagate=propagate)

    def show(self, propagate: bool = True) -> None:
        """
        Montre le composant

        Args:
            propagate(bool, optional): propage l'état aux enfants
        """
        self._visible = True
        for fn in self._show_process:
            fn(self)
        if propagate:
            for child in self._children:
                child.widget.show()

    def hide(self, propagate: bool = True) -> None:
        """
        Cache le composant

        Args:
            propagate(bool, optional): propage l'état aux enfants
        """
        self._visible = False
        for fn in self._hide_process:
            fn(self)
        if propagate:
            for child in self._children:
                child.widget.hide()
    
    def switch_visibility(self, propagate: bool = True) -> None:
        """
        Bascule la visibilité

        Args:
            propagate(bool, optional): propage l'état aux enfants
        """
        if self._visible:
            self.hide(propagate=propagate)
        else:
            self.show(propagate=propagate)

    # ======================================== CHILDREN ========================================
    def add_child(self, child: Widget, name: str = None, z: int = 1):
        """
        Ajoute un composant enfant

        Args:
            child(Widget): composant à associer
            name(str, optional): identifiant local du composant
            z(int, optional): ordre de rendu local
        """
        if child in self._children:
            raise ValueError(f"{child} is already a child of this widget")
        if child.parent is not None:
            raise ValueError(f"{child} has already a parent")
        wrapper = WidgetWrapper(expect(child, Widget), expect(name, (str, None)), expect(z, int))
        child._parent = self
        insort(self._children, wrapper)

    def remove_child(self, child: Widget) -> None:
        """
        Retire un composant enfant

        Args:
            child(Widget): composant à dissocier
        """
        if expect(child, Widget) in self._children:
            child._parent = None
            self._children.remove(child)

    def remove_child_by_name(self, name: str) -> None:
        """
        Retire un composant enfant par son identifiant

        Args:
            name(str): nom du composant à dissocier
        """
        to_remove: list[WidgetWrapper] = []
        for child in self._children:
            if child.name == name:
                to_remove.append(child)
        for wrapper in to_remove:
            wrapper.widget._parent = None
            self._children.remove(wrapper)

    def clear_children(self) -> None:
        """Retire tous les enfants"""
        for child in self._children:
            child.widget._parent = None
        self._children.clear()
    
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

    # ======================================== HOOKS ========================================
    def on_activate(self, fn: Callable) -> Callable:
        """Ajoute une fonction à l'activation et retourne un token d'invalidation"""
        self._activate_process.append(fn)
        return lambda: self._activate_process.remove(fn)
    
    def on_deactivate(self, fn: Callable) -> Callable:
        """Ajoute une fonction à la désactivation et retourne un token d'invalidation"""
        self._deactivate_process.append(fn)
        return lambda: self._deactivate_process.remove(fn)
    
    def on_show(self, fn: Callable) -> Callable:
        """Ajoute une fonction à l'apparition et retourne un token d'invalidation"""
        self._show_process.append(fn)
        return lambda: self._show_process.remove(fn)

    def on_hide(self, fn: Callable) -> Callable:
        """Ajoute une fonction à la dispartion et retourne un token d'invalidation"""
        self._hide_process.append(fn)
        return lambda: self._hide_process.remove(fn)

    # ======================================== LIFE CYCLE ========================================
    @abstractmethod
    def update(self, dt: float) -> None: ...

    def _update(self, dt: float) -> Super:
        """Actualisation"""
        if not self._active:
            return Super.STOP
        
        # Actualisation personnel
        self.update(dt)

        # Actualisation des enfants
        for child in self._children:
            child.widget._update(dt)

        return Super.NONE
    
    @abstractmethod
    def draw(self, pipeline: Pipeline, context: RenderContext): ...

    def _draw(self, pipeline: Pipeline, context: RenderContext) -> Super:
        """Affichage"""
        if not self._visible:
            return Super.STOP
        
        # Sauvegarde du contexte de rendu
        opacity = context.opacity
        origin = context.origin

        # Actualisation du contexte de rendu
        self._update_render_context(context)

        # Affichage personnel
        self.draw(pipeline, context)

        # Affichage des enfants
        for child in self._children:
            child.widget._draw(pipeline, context)

        # Restauration du contexte de rendu
        context.opacity = opacity
        context.origin = origin

        return Super.NONE
    
    # ======================================== HELPERS ========================================
    def _get_wrapper(self, child: Widget) -> WidgetWrapper:
        """Récupère le wrapper d'un composant"""
        for wrapper in self._children:
            if wrapper.widget == child:
                return wrapper
        raise ValueError(f"{child} is not a child of this widget")
    
    def _update_render_context(self, context: RenderContext) -> None:
        """Actualise le contexte de rendu avec les paramètres courants"""
        context.z += 1
        context.origin += self._pos
        context.opacity *= self._opacity


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

    def __eq__(self, other: Widget | WidgetWrapper) -> bool:
        """Vérifie la correspondance des composants"""
        if isinstance(other, Widget):
            return self._widget == other
        elif isinstance(other, WidgetWrapper):
            return self._widget == other._widget
        return NotImplemented

    def __lt__(self, other: WidgetWrapper) -> bool:
        """Comparaison inférieure"""
        return self.z < other.z