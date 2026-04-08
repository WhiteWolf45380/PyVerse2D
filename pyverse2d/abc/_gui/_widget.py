# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, clamped
from ..._flag import Super
from ..._rendering import Pipeline
from ...math import Point
from ...abc import Shape

from ._behavior import Behavior

from abc import ABC, abstractmethod
from bisect import insort
from numbers import Real
from typing import Callable, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from ...scene import GuiLayer
    from ...gui import (
        RenderContext,
        ClickBehavior,
        HoverBehavior,
        SelectBehavior,
        FocusBehavior,
    )

# ======================================== ABSTRACT CLASS ========================================
class Widget(ABC):
    """Classe abstraite des composants UI

    Args:
        position(Point, optional): position
        anchor(Point, optional): ancre locale
        opacity(float, optional): opacité
    """
    __slots__ = (
        "_layer", "_parent", "_children",
        "_position", "_anchor",
        "_opacity", "_active", "_visible",
        "_activate_process", "_deactivate_process", "_show_process", "_hide_process",
        "_behaviors", "_click", "_hover", "_select", "_focus",
    )

    def __init__(
            self,
            position: Point = (0, 0),
            anchor: Point = (0.5, 0.5),
            opacity: float = 1.0
        ):
        # Arbre
        self._layer: GuiLayer = None
        self._parent: Widget = None
        self._children: list[WidgetWrapper] = []

        # position
        self._position: Point = Point(position)
        self._anchor: Point = Point(anchor)

        # Design
        self._opacity: float = clamped(float(expect(opacity, Real)))

        # Etat
        self._active: bool = True
        self._visible: bool = True

        # Hooks
        self._activate_process: list[Callable] = []
        self._deactivate_process: list[Callable] = []
        self._show_process: list[Callable] = []
        self._hide_process: list[Callable] = []

        # Behaviors
        self._behaviors: set[str] = set()
        self._click: ClickBehavior = None
        self._hover: HoverBehavior = None
        self._select: SelectBehavior = None
        self._focus: FocusBehavior = None

    # ======================================== PROPERTIES ========================================
    @property
    def layer(self) -> GuiLayer | None:
        """Layer gui maître"""
        return self._layer

    @property
    def parent(self) -> Widget| None:
        """``Widget`` parent"""
        return self._parent
    
    @property
    def root(self) -> Widget:
        """``Widget`` racine"""
        if self._parent is None:
            return self
        return self._parent.root

    @property
    def children(self) -> tuple[Widget]:
        """Liste des ``Widgets`` enfants"""
        return tuple(wrapper.widget for wrapper in self._children)
    
    @property
    def position(self) -> Point:
        """Position

        La position peut être un objet ``Point`` ou un tuple ``(x, y)``.
        """
        return self._position
    
    @position.setter
    def position(self, value: Point) -> None:
        self._position = Point(value)
    
    @property
    def x(self) -> float:
        """Position horizontale

        La coordonnée doit être un ``Réel``.
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real) -> None:
        self._position.x = value
    
    @property
    def y(self) -> float:
        """Position verticale
        
        La coordonnée doit être un ``Réel``.
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real) -> None:
        self._position.y = value
    
    @property
    def absolute_position(self) -> Point:
        """Position absolue"""
        if self._parent is None:
            return self._position
        return self._parent.absolute_position + self._position
    
    @property
    def absolute_x(self) -> float:
        """Position horizontale absolue"""
        if self._parent is None:
            return self._position.x
        return self._parent.absolute_x + self._position.x
    
    @property
    def absolute_y(self) -> float:
        """Position verticale absolue"""
        if self._parent is None:
            return self._position.y
        return self._parent.absolute_y + self._position.y
    
    @property
    def anchor(self) -> Point:
        """Ancre relative locale

        L'ancre peut être un objet ``Point`` ou un tuple ``(ax, ay)``.
        Les coordonnées de l'ancre doivent être comprises dans l'intervalle [0, 1].
        """
        return self._anchor
    
    @anchor.setter
    def anchor(self, value: Point) -> None:
        self._anchor = Point(value)
    
    @property
    def anchor_x(self) -> float:
        """Ancre horizontale relative locale

        La coordonnée doit être un réel compris dans l'invervalle [0, 1].
        """
        return self._anchor.x
    
    @anchor_x.setter
    def anchor_x(self, value: Real) -> None:
        self._anchor.x = value
    
    @property
    def anchor_y(self) -> float:
        """Ancre verticale relative locale
        
        La coordonnée doit être un réel compris dans l'intervalle [0, 1].
        """
        return self._anchor.y
    
    @anchor_y.setter
    def anchor_y(self, value: Real) -> None:
        self._anchor.y = value
    
    @property
    def opacity(self) -> float:
        """Opacité relative

        L'opacité doit être un ``Réel`` compris dans l'invervalle [0, 1].
        """
        return self._opacity
    
    @opacity.setter
    def opacity(self, value: Real) -> None:
        self._opacity: float = clamped(float(expect(value, Real)))
    
    @property
    @abstractmethod
    def hitbox(self) -> Shape: ...

    # ======================================== PREDICATES ========================================
    def is_active(self) -> bool:
        """Vérifie l'activité"""
        return self._active
    
    def is_visible(self) -> bool:
        """Vérifie la visibilité"""
        return self._visible
    
    def collidespoint(self, point: Point) -> bool:
        """Vérifie la collision avec un point"""
        scale = getattr(self, "_scale", 1.0)
        rotation = getattr(self, "_rotation", 0.0)
        return self.hitbox.world_contains(point, self.x, self.y, anchor_x=self.anchor_x, anchor_y=self.anchor_y, scale=scale, rotation=rotation)

    # ========================================  STATE ========================================
    def activate(self, propagate: bool = True) -> None:
        """
        Active le composant

        Args:
            propagate(bool, optional): propage l'état aux enfants
        """
        self._active = True

        for behavior in self._behaviors:
            getattr(self, f"_{behavior}").enable()
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
        for behavior in self._behaviors:
            getattr(self, f"_{behavior}").disable()
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
    
    # ======================================== BEHAVIORS ========================================
    def add_behavior(self, behavior: Behavior) -> None:
        """Ajoute un comportement

        Les comportements sont exclusifs par widget
        """
        expect(behavior, Behavior)
        if getattr(self, f"_{behavior._ID}", None) is not None:
            raise ValueError(f"This widget already has a {type(behavior).__name__}, try to remove it first")
        behavior.attach(self, _from_widget=True)
        self._behaviors.add(behavior._ID)
        setattr(self, f"_{behavior._ID}", behavior)

    def remove_behavior(self, behavior: Behavior | Type[Behavior]) -> None:
        """Retire un comportement

        Args:
            behavior: élément ``Behavior`` ou ``Type`` de behavior à retirer
        """
        if getattr(self, f"_{behavior._ID}", None) is None:
            raise ValueError(f"This widget has no {type(behavior).__name__}")
        elif isinstance(behavior, Behavior) and getattr(self, f"_{behavior._ID}", None) != behavior:
            raise ValueError("This widget does not own that behavior")
        behavior.detach(_from_widget=True)
        self._behaviors.remove(behavior._ID)
        setattr(self, f"_{behavior._ID}", None)

    def get_behavior(self, behavior: type[Behavior] | str) -> Behavior | None:
        """Renvoie un comportement

        Args:
            behavior: ``Type`` ou ``id`` du comportement
        """
        id_ = behavior if isinstance(behavior, str) else behavior._ID
        return getattr(self, f"_{id_}", None)
    
    def get_behaviors(self) -> tuple[Behavior]:
        """Renvoie les comportements attachés"""
        return tuple(behavior for id_ in self._behaviors if (behavior := getattr(self, f"_{id_}", None)) is not None)

    def has_behavior(self, behavior: type[Behavior] | str) -> bool:
        """Vérfie la possession d'un comportement

        Args:
            behavior: ``Type`` ou ``id`` du comportement
        """
        id_ = behavior if isinstance(behavior, str) else behavior._ID
        return getattr(self, f"_{id_}", None) is not None
    
    @property
    def behaviors(self) -> tuple[Behavior]:
        """Renvoie les comportements attachés"""
        return self.get_behaviors()

    @property
    def click(self) -> ClickBehavior:
        """Comportement de clique"""
        return self._click

    @property
    def hover(self) -> HoverBehavior:
        """Comportement de survol"""
        return self._hover

    @property
    def select(self) -> SelectBehavior:
        """Comportement de sélection"""
        return self._select

    @property
    def focus(self) -> FocusBehavior:
        """Comportement de concentration"""
        return self._focus

    # ======================================== CHILDREN ========================================
    def add_child(self, child: Widget, name: str = None, z: int = 1):
        """
        Ajoute un composant enfant

        Args:
            child(Widget): composant à associer
            name(str, optional): identifiant local du composant
            z(int, optional): ordre de rendu local
        """
        if child._layer is not None and child._layer != self._layer:
            raise ValueError(f"{child} is in another layer")
        if child.parent is not None:
            raise ValueError(f"{child} has already a parent")
        wrapper = WidgetWrapper(expect(child, Widget), expect(name, (str, None)), expect(z, int))
        child._layer = self._layer
        child._parent = self
        insort(self._children, wrapper)

    def remove_child(self, child: Widget) -> None:
        """
        Retire un composant enfant

        Args:
            child(Widget): composant à dissocier
        """
        if expect(child, Widget) in self._children:
            child._layer = None
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
            wrapper.widget._layer = None
            wrapper.widget._parent = None
            self._children.remove(wrapper)

    def clear_children(self) -> None:
        """Retire tous les enfants"""
        for child in self._children:
            child.widget._layer = None
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
    
    def child(self, name: str) -> Widget:
        """
        Renvoie un ``Widget`` enfant par son identifiant

        Args:
            name(str): identifiant du composant
        """
        expect(name, str)
        for child in self._children:
            if child.name == name:
                return child.widget
        raise ValueError(f"This widget has no child named {name}")

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
    def _update(self, dt: float) -> None: ...

    def update(self, dt: float) -> Super:
        """Actualisation"""
        if not self._active:
            return Super.STOP
        
        # Actualisation personnel
        self._update(dt)
        for behavior in self.get_behaviors():
            behavior.update(dt)

        # Actualisation des enfants
        for child in reversed(self._children):
            child.widget.update(dt)

        return Super.NONE
    
    @abstractmethod
    def _draw(self, pipeline: Pipeline, context: RenderContext): ...

    def draw(self, pipeline: Pipeline, context: RenderContext) -> Super:
        """Affichage"""
        if not self._visible:
            return Super.STOP
        
        # Sauvegarde du contexte de rendu
        opacity = context.opacity
        origin = context.origin

        # Actualisation du contexte de rendu
        self._update_render_context(context)

        # Affichage personnel
        self._draw(pipeline, context)

        # Affichage des enfants
        for child in self._children:
            child.widget.draw(pipeline, context)

        # Restauration du contexte de rendu
        context.opacity = opacity
        context.origin = origin

        return Super.NONE
    
    @abstractmethod
    def _destroy(self) -> None: ...

    def destroy(self) -> Super:
        """Destruction"""
        self._destroy()
        if self._parent is not None:
            self._parent.remove_child(self)
        for child in self._children:
            child.widget.destroy()
        return Super.NONE
    
    # ======================================== INTERNALS ========================================
    def _switch_layer(self, layer: GuiLayer | None) -> None:
        """Change le layer du composant et de ses enfants"""
        self._layer = layer
        for child in self._children:
            child.widget._switch_layer(layer)
    
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
        context.origin += self._position
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