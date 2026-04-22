# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, clamped, over
from ..._flag import Super
from ...math import Point

from .._shape import Shape

from ._behavior import Behavior

import pyglet.gl as gl
from pyglet.graphics import Group

from abc import ABC, abstractmethod
from bisect import insort
from numbers import Real
from typing import Callable, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from ..._rendering import Pipeline
    from ...scene import GuiLayer
    from ...gui import (
        RenderContext,
        ClickBehavior,
        HoverBehavior,
        SelectBehavior,
        FocusBehavior,
    )

# ======================================== GROUP ========================================
class WidgetGroup(Group):
    """Groupe spécialisé des widgets"""
    _cache: dict[tuple, WidgetGroup] = {}

    def __init__(self, order=0, parent=None, scissor=None):
        super().__init__(order=order, parent=parent)
        self.scissor = scissor
        self.resolved = (
            intersect(parent.resolved, scissor) if scissor and isinstance(parent, WidgetGroup) and parent.resolved
            else scissor if scissor
            else parent.resolved if isinstance(parent, WidgetGroup)
            else None
        )

    def __hash__(self) -> int:
        return hash((self.order, self.parent, self.resolved))

    def __eq__(self, other: WidgetGroup) -> bool:
        return super().__eq__(other) and self.resolved == other.resolved

    def set_state(self):
        if self.resolved is not None:
            gl.glEnable(gl.GL_SCISSOR_TEST)
            gl.glScissor(*self.resolved)

    def unset_state(self):
        if self.resolved is not None:
            gl.glDisable(gl.GL_SCISSOR_TEST)

    @classmethod
    def get_group(cls, order: int, parent: WidgetGroup | None, scissor: tuple | None) -> WidgetGroup:
        key = (order, id(parent), scissor)
        if key not in cls._cache:
            cls._cache[key] = cls(order=order, parent=parent, scissor=scissor)
        return cls._cache[key]

    @classmethod
    def invalidate(cls, parent_id: int) -> None:
        cls._cache = {k: v for k, v in cls._cache.items() if k[1] != parent_id}

# ======================================== ABSTRACT CLASS ========================================
class Widget(ABC):
    """Classe abstraite des composants UI

    Args:
        position: position
        anchor: ancre locale
        scale: facteur de redimensionnement
        rotation: angle de rotation
        opacity: opacité
    """
    __slots__ = (
        "_layer", "_parent", "_children",
        "_position", "_anchor", "_scale", "_rotation",
        "_opacity", "_active", "_visible", "_clipping",
        "_activate_process", "_deactivate_process", "_show_process", "_hide_process",
        "_attr_locks", "_behaviors", "_click", "_hover", "_select", "_focus",
        "_cached_scissor", "_scissor_dirty",
    )

    _RENDER_CONTEXT_CLS: RenderContext = None

    @classmethod
    def _get_render_context(cls) -> RenderContext:
        """Renvoie la class RenderContext"""
        if cls._RENDER_CONTEXT_CLS is None:
            from ...gui import RenderContext
            cls._RENDER_CONTEXT_CLS = RenderContext
        return cls._RENDER_CONTEXT_CLS

    def __init__(
            self,
            position: Point = (0, 0),
            anchor: Point = (0.5, 0.5),
            scale: Real = 1.0,
            rotation: Real = 0.0,
            opacity: float = 1.0,
            clipping: bool = False,
        ):
        # position
        self._position: Point = Point(position)
        self._anchor: Point = Point(anchor)
        self._scale: float = float(scale)
        self._rotation: float = float(rotation)

        # Design
        self._opacity: float = float(opacity)
        self._clipping: bool = clipping

        if __debug__:
            over(self._scale, 0.0, include=False)
            clamped(self._opacity)
            if not isinstance(self._clipping, bool): raise ValueError(f"clipping ({self._clipping}) must be a boolean")
            
        # Arbre
        self._layer: GuiLayer = None
        self._parent: Widget = None
        self._children: list[WidgetWrapper] = []

        # Etat
        self._active: bool = True
        self._visible: bool = True

        # Hooks
        self._activate_process: list[Callable] = []
        self._deactivate_process: list[Callable] = []
        self._show_process: list[Callable] = []
        self._hide_process: list[Callable] = []

        # Behaviors
        self._attr_locks: dict[str, int] = {}
        self._behaviors: list[str] = []
        self._click: ClickBehavior = None
        self._hover: HoverBehavior = None
        self._select: SelectBehavior = None
        self._focus: FocusBehavior = None

        # Scissor test
        self._cached_scissor: tuple | None = None
        self._scissor_dirty: bool = True

        # Contexte courant
        self._context: RenderContext = self._get_render_context()(
            pipeline = None,
            x = self._position.x,
            y = self._position.y,
            rotation = self._rotation,
            opacity = self._opacity,
            group = None,
            z = 0,
        )

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
        self._position.x, self._position.y = value
        self._invalidate_scissor()
    
    @property
    def x(self) -> float:
        """Position horizontale

        La coordonnée doit être un ``Réel``.
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real) -> None:
        self._position.x = value
        self._invalidate_scissor()
    
    @property
    def y(self) -> float:
        """Position verticale
        
        La coordonnée doit être un ``Réel``.
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real) -> None:
        self._position.y = value
        self._invalidate_scissor()
    
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
        self._anchor.x, self._anchor.y = value
        self._invalidate_scissor()
    
    @property
    def anchor_x(self) -> float:
        """Ancre horizontale relative locale

        La coordonnée doit être un réel compris dans l'invervalle [0, 1].
        """
        return self._anchor.x
    
    @anchor_x.setter
    def anchor_x(self, value: Real) -> None:
        self._anchor.x = value
        self._invalidate_scissor()
    
    @property
    def anchor_y(self) -> float:
        """Ancre verticale relative locale
        
        La coordonnée doit être un réel compris dans l'intervalle [0, 1].
        """
        return self._anchor.y
    
    @anchor_y.setter
    def anchor_y(self, value: Real) -> None:
        self._anchor.y = value
        self._invalidate_scissor()

    @property
    def scale(self) -> float:
        """Facteur de redimensionnement

        Ce facteur doit être un ``réel`` positif non nul
        """
        return self._scale
    
    @scale.setter
    def scale(self, value: Real) -> None:
        self._scale = over(float(value), 0.0, include=False)
        self._invalidate_scissor()

    @property
    def rotation(self) -> float:
        """Angle de rotation

        La rotation se fait *en degrés*, dans le sens trigonométrique *(CCW)*.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value: Real) -> None:
        self._rotation = float(value, Real)
        self._invalidate_scissor()
    
    @property
    def opacity(self) -> float:
        """Opacité relative

        L'opacité doit être un ``Réel`` compris dans l'invervalle [0, 1].
        """
        return self._opacity
    
    @opacity.setter
    def opacity(self, value: Real) -> None:
        value = float(value)
        assert 0.0 <= value <= 1.0, f"opacity ({value}) must be within 0.0 and 1.0"
        self._opacity: float = value

    @property
    def clipping(self) -> bool:
        """Limitation du rendu

        Lorsque cette propriété est activée, les widgets enfants sont rendus strictement dans la zone de ce widget.
        """
        return self._clipping
    
    @clipping.setter
    def clipping(self, value: bool) -> None:
        assert isinstance(value, bool), f"clipping ({value}) must be a boolean"
        if value != self._clipping:
            self._clipping = value
            self._invalidate_scissor()
    
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
        self_context = self._context
        return self.hitbox.world_contains(point, self_context.x, self_context.y, anchor_x=self.anchor_x, anchor_y=self.anchor_y, scale=self_context.scale, rotation=self_context.rotation)
    
    # ======================================== INTERFACE ========================================
    @abstractmethod
    def copy(self) -> Widget: ...
    
    # ========================================  TRANSFORMATIONS ========================================
    def resize(self, factor: Real) -> None:
        """Redimensionne le widget par un facteur

        Le facteur de redimensionnement doit être un réel positif non nul.
        """
        self._scale *= over(float(factor), 0.0, include=False)
        self._invalidate_scissor()

    def rotate(self, angle: Real) -> None:
        """Applique une rotation au widget

        La rotation est *en degrés* et se fait dans le sens trigonométrique *(CCW)*.
        """
        self._rotation += float(angle)
        self._invalidate_scissor()

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
        self._attr_locks.clear()
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
        setattr(self, f"_{behavior._ID}", behavior)
        for i in range(len(self._behaviors)):
            if behavior._PRIORITY > getattr(self, self._behaviors[i])._PRIORITY:
                self._behaviors.insert(i, behavior._ID)
                return
        self._behaviors.append(behavior._ID)

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
        self._attr_locks = {attr: p for attr, p in self._attr_locks.items() if p != behavior._PRIORITY}
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
    
    # ======================================== LOCKING ========================================
    def _lock_attr(self, attr: str, priority: int) -> bool:
        """Tente de verrouiller un attribut pour un behavior de priorité donnée"""
        current = self._attr_locks.get(attr, 0)
        if priority >= current:
            self._attr_locks[attr] = priority
            return True
        return False

    def _unlock_attr(self, attr: str, priority: int) -> None:
        """Libère le verrou d'un attribut si il appartient à cette priorité"""
        if self._attr_locks.get(attr) == priority:
            del self._attr_locks[attr]

    # ======================================== CHILDREN ========================================
    def add_child(self, child: Widget, name: str = None, z: int = 1, share_scale: bool = True, share_rotation: bool = True) -> Widget:
        """
        Ajoute un composant enfant

        Args:
            child: composant à associer
            name: identifiant local du composant
            z: ordre de rendu local
            share_scale: l'enfant suit le redimensionnement du parent
            share_rotaiton: l'enfant suit la rotation du parent

        Returns:
            child: widget enfant associé
        """
        if child._layer is not None and child._layer != self._layer:
            raise ValueError(f"{child} is in another layer")
        if child.parent is not None:
            raise ValueError(f"{child} has already a parent")
        wrapper = WidgetWrapper(expect(child, Widget), expect(name, (str, None)), expect(z, int), share_scale, share_rotation)
        child._layer = self._layer
        child._parent = self
        insort(self._children, wrapper)
        return child

    def remove_child(self, child: Widget) -> Widget:
        """
        Retire un composant enfant

        Args:
            child(Widget): composant à dissocier

        Returns:
            child: widget enfant dissocié
        """
        if expect(child, Widget) in self._children:
            child._layer = None
            child._parent = None
            self._children.remove(child)
        return child

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

    def draw(self, pipeline: Pipeline, context: RenderContext, share_scale: bool = True, share_rotation: bool = True) -> Super:
        """Affichage"""
        if not self._visible:
            return Super.STOP
        self_context = self._context

        # Actualisation du contexte de rendu
        self._update_render_context(context, share_scale, share_rotation)

        # Affichage personnel
        self._draw(pipeline, context)

        # Passage au zorder des enfants
        z = self._context.z
        self_context.z = 0

        # Affichage des enfants
        for child in self._children:
            child.widget.draw(pipeline, self_context, share_scale=child.share_scale, share_rotation=child.share_rotation)

        # Restauration du zorder
        self_context.z = z

        return Super.NONE
    
    @abstractmethod
    def _destroy(self) -> None: ...

    def destroy(self) -> Super:
        """Destruction"""
        self._destroy()
        if self._parent is not None:
            self._parent.remove_child(self)
        for behavior in self._behaviors:
            behavior.delete()
        for child in self._children:
            child.widget.destroy()
        return Super.NONE
    
    # ======================================== INTERNALS ========================================
    def _switch_layer(self, layer: GuiLayer | None) -> None:
        """Change le layer du composant et de ses enfants"""
        self._layer = layer
        for child in self._children:
            child.widget._switch_layer(layer)
    
    def _get_wrapper(self, child: Widget) -> WidgetWrapper:
        """Récupère le wrapper d'un composant"""
        for wrapper in self._children:
            if wrapper.widget == child:
                return wrapper
        raise ValueError(f"{child} is not a child of this widget")
    
    def _update_render_context(self, context: RenderContext, share_scale: bool = True, share_rotation: bool = True) -> RenderContext:
        """Actualise le contexte de rendu avec les paramètres courants"""
        self_context = self._context
        self_context.x = self._position.x + context.x
        self_context.y = self._position.y + context.y
        self_context.scale = self._scale * (context.scale if share_scale else 1.0)
        self_context.rotation = self._rotation + (context.rotation if share_rotation else 0.0)
        self_context.opacity = self._opacity * context.opacity
        self_context.z = context.z + 1
        self_context.group = WidgetGroup.get_group(order=context.z, parent=context.group, scissor=self._compute_scissor())
        return self_context

    def _compute_scissor(self) -> tuple | None:
        """Calcule le scissor résolu en coordonnées framebuffer"""
        if not self._scissor_dirty:
            return self._cached_scissor
        if not self._clipping:
            result = self._parent._compute_scissor() if self._parent else None
        else:
            self_context = self._context
            xmin, ymin, xmax, ymax = self.hitbox.world_bounding_box(
                x=self_context.x, y=self_context.y,
                anchor_x=self.anchor_x, anchor_y=self.anchor_y,
                scale=self_context.scale,
                rotation=self_context.rotation,
            )
            x, y = self_context.pipeline.world_to_framebuffer(xmin, ymin)
            width, height = self_context.pipeline.scale_to_framebuffer(xmax - xmin, ymax - ymin)
            scissor = (int(x), int(y), int(width), int(height))
            parent_scissor = self._parent._compute_scissor() if self._parent else None
            result = intersect(parent_scissor, scissor) if parent_scissor else scissor
        self._cached_scissor = result
        self._scissor_dirty = False
        return result

    def _invalidate_scissor(self) -> None:
        """Propage l'invalidation du scissor aux enfants"""
        if not self._scissor_dirty:
            self._scissor_dirty = True
            WidgetGroup.invalidate(id(self))
            for child in self._children:
                child.widget._invalidate_scissor()

# ======================================== WRAPPER ========================================
class WidgetWrapper:
    """Wrapper des composants UI"""
    __slots__ = ("_widget", "name", "z", "share_scale", "share_rotation")

    def __init__(self, widget: Widget, name: str, z: int, share_scale: bool, share_rotation: bool):
        self._widget: Widget = widget
        self.name: str = name
        self.z: int = z
        self.share_scale: bool = share_scale
        self.share_rotation: bool = share_rotation
    
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
    
# ======================================== HELPERS ========================================
def intersect(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    """Renvoie l'intersection de deux Rectangles"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x = max(ax, bx)
    y = max(ay, by)
    w = max(0, min(ax + aw, bx + bw) - x)
    h = max(0, min(ay + ah, by + bh) - y)
    return x, y, w, h