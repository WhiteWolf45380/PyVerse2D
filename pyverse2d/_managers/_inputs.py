# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._flag import Key
from ..abc import Manager
from ..math import Point

from ._context import ContextManager

from pyglet.window import Window as PygletWindow

from typing import TYPE_CHECKING, Any, Callable
if TYPE_CHECKING:
    from .._rendering import Window

# ======================================== GESTIONNAIRE ========================================
class InputsManager(Manager):
    """Gestionnaire des entrées utilisateur"""
    __slots__ = (
        "_ctx",
        "_window",
        "_listeners", "_any_listeners", "_all_listeners",
        "_step", "_pressed", "_released_this_frame", "_triggered_combos",
        "_relative_origin", "_mouse_x", "_mouse_y", "_mouse_out",
        "_mouse_dx", "_mouse_dy", "_drag_dx", "_drag_dy", "_scroll_dx", "_scroll_dy",
    )

    def __init__(self, context_manager: ContextManager):
        # Contexte de managers
        self._ctx: ContextManager = context_manager

        # Fenêtre
        self._window: Window = None

        # Listeners
        self._listeners: dict[int, list[_Listener]] = {}
        self._any_listeners: list[_Listener] = []
        self._all_listeners: list[_Listener] = []

        # Events
        self._step: list = []
        self._pressed: dict = {}
        self._released_this_frame: list = []
        self._triggered_combos: set = set()

        # Souris
        self._relative_origin: Point = Point(0, 0)
        self._mouse_x: float = 0.0
        self._mouse_y: float = 0.0
        self._mouse_out: float = False
        self._mouse_dx: float = 0.0
        self._mouse_dy: float = 0.0
        self._drag_dx: float = 0.0
        self._drag_dy: float = 0.0
        self._scroll_dx: float = 0.0
        self._scroll_dy: float = 0.0

    # ======================================== BIND WINDOW ========================================
    def bind(self, window: Window) -> None:
        """
        Lie le gestionnaire à une fenêtre pyglet

        Args:
            window: fenêtre à assigner
        """
        self._window = window
        pyglet_window: PygletWindow = window.native

        @pyglet_window.event
        def on_key_press(symbol, modifiers):
            self._on_press(symbol)

        @pyglet_window.event
        def on_key_release(symbol, modifiers):
            self._on_release(symbol)

        @pyglet_window.event
        def on_mouse_press(x, y, button, modifiers):
            self._compute_mouse(x, y)
            self._on_press(button)

        @pyglet_window.event
        def on_mouse_release(x, y, button, modifiers):
            self._compute_mouse(x, y)
            self._on_release(button)

        @pyglet_window.event
        def on_mouse_motion(x, y, dx, dy):
            self._compute_mouse(x, y)
            self._mouse_dx = dx * self._window.width / self._window.screen.width
            self._mouse_dy = dy * self._window.height / self._window.screen.height

        @pyglet_window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self._compute_mouse(x, y)
            self._drag_dx = dx * self._window.width / self._window.screen.width
            self._drag_dy = dy * self._window.height / self._window.screen.height

        @pyglet_window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):
            self._scroll_dx = scroll_x
            self._scroll_dy = scroll_y

    # ======================================== LISTENERS ========================================
    def add_listener(
            self,
            key: Key.Input,
            callback: Callable,
            args: list[Any] = None,
            kwargs: dict[str, Any] = None,
            up: bool = False,
            condition: Callable = None,
            once: bool = False,
            repeat: bool = False,
            priority: int = 0,
            give_key: bool = False
        ) -> _Listener:
        """Ajoute un listener sur une entrée utilisateur

        Args:
            key(Key.Input): identifiant de l'événement
            callback(callable): fonction à appeler
            args(list): arguments positionnels
            kwargs(dict): arguments nommés
            up(bool): déclenche au relâchement si True
            condition(callable): condition booléenne
            once(bool): supprime après première activation
            repeat(bool): déclenche chaque frame tant que pressé
            priority(int): priorité d'exécution
            give_key(bool): passe event_id en paramètre key au callback
        """
        if args is None: args = []
        if kwargs is None: kwargs = {}

        def _remove(l: _Listener):
            lst = self._listeners.get(key)
            if lst and l in lst:
                lst.remove(l)
                if not lst:
                    del self._listeners[key]

        listener = _Listener(
            callback, args, kwargs, priority, _remove,
            up=up, condition=condition, once=once,
            repeat=repeat, give_key=give_key,
        )

        if key not in self._listeners:
            self._listeners[key] = []
        self._insert_by_priority(self._listeners[key], listener)
        return listener

    def remove_listener(self, key: Key.Input, callback: Callable) -> None:
        """Supprime un listener sur une entrée par callback

        Args:
            key(Key.Input): identifiant de l'événement
            callback(callable): callback à supprimer
        """
        if key in self._listeners:
            for l in list(self._listeners[key]):
                if l.callback == callback:
                    l.invalidate()

    def when_any(
            self,
            callback: Callable,
            exclude: list[Key.Input] = None,
            args: list[Any] = None,
            kwargs: dict[str, Any] = None,
            once: bool = False,
            condition: Callable = None,
            priority: int = 0,
            give_key: bool = False
        ) -> _Listener:
        """Déclenche le callback sur n'importe quelle pression sauf les exclusions

        Args:
            callback(callable): fonction à appeler
            exclude(list): event_id à exclure
            args(list): arguments positionnels
            kwargs(dict): arguments nommés
            once(bool): supprime après première activation
            condition(callable): condition booléenne
            priority(int): priorité d'exécution
            give_key(bool): passe event_id en paramètre key

        Returns:
            Listener: le listener créé (appeler .invalidate() pour le retirer)
        """
        if exclude is None: exclude = []
        if args is None: args = []
        if kwargs is None: kwargs = {}

        def _remove(l: _Listener):
            if l in self._any_listeners:
                self._any_listeners.remove(l)

        listener = _Listener(
            callback, args, kwargs, priority, _remove,
            once=once, condition=condition,
            give_key=give_key, exclude=set(exclude),
        )

        self._insert_by_priority(self._any_listeners, listener)
        return listener

    def when_all(
            self,
            keys: list[Key.Input],
            callback: Callable,
            args: list[Any] = None,
            kwargs: dict[str, Any] = None,
            once: bool = False,
            condition: Callable = None,
            repeat: bool = False,
            priority: int = 0
        ) -> _Listener:
        """Déclenche le callback quand toutes les touches sont pressées simultanément

        Args:
            keys(list): touches devant être pressées simultanément
            callback(callable): fonction à appeler
            args(list): arguments positionnels
            kwargs(dict): arguments nommés
            once(bool): supprime après première activation
            condition(callable): condition booléenne
            repeat(bool): déclenche chaque frame tant que le combo est maintenu
            priority(int): priorité d'exécution
        """
        if args is None: args = []
        if kwargs is None: kwargs = {}

        def _remove(l: _Listener):
            if l in self._all_listeners:
                self._all_listeners.remove(l)

        listener = _Listener(callback, args, kwargs, priority, _remove, once=once, condition=condition, repeat=repeat, keys=set(keys))
        self._insert_by_priority(self._all_listeners, listener)
        return listener

    # ======================================== LIFE CYCLE ========================================
    def remove_callback(self, callback: Callable) -> None:
        """
        Supprime un callback de tous les types de listeners

        Args:
            callback(callable): callback à supprimer partout
        """
        for lst in self._listeners.values():
            for l in list(lst):
                if l.callback == callback:
                    l.invalidate()

        for l in list(self._any_listeners):
            if l.callback == callback:
                l.invalidate()

        for l in list(self._all_listeners):
            if l.callback == callback:
                l.invalidate()

    # ======================================== FLUSH ========================================
    def flush(self) -> None:
        """Nettoie les états courants"""
        # Repeat sur touches individuelles
        for event_id, listeners in list(self._listeners.items()):
            if not self._is_currently_pressed(event_id):
                continue
            for listener in list(listeners):
                if not listener.is_active():
                    continue
                if not listener.is_enabled():
                    continue
                if not listener.repeat:
                    continue
                if listener.condition and not listener.condition():
                    continue
                listener._fire(event_id)

        # Combos (when_all)
        for listener in list(self._all_listeners):
            if not listener.is_active():
                continue
            if not listener.is_enabled():
                    continue
            if not all(self._is_currently_pressed(k) for k in listener.keys):
                continue
            if listener.condition and not listener.condition():
                continue

            combo_key = frozenset(listener.keys)

            if listener.repeat:
                listener._fire()
            else:
                if combo_key not in self._triggered_combos:
                    listener._fire()
                    self._triggered_combos.add(combo_key)

        # Nettoie les combos qui ne sont plus maintenus
        self._triggered_combos = {
            combo for combo in self._triggered_combos
            if all(self._is_currently_pressed(k) for k in combo)
        }

        # Consolide _pressed
        for event_id in self._step:
            if event_id not in self._released_this_frame:
                self._pressed[event_id] = True

        self._step.clear()
        self._released_this_frame.clear()
        self._scroll_dx = 0.0
        self._scroll_dy = 0.0

    # ======================================== KEY EVENTS ========================================
    def _is_currently_pressed(self, event_id: int) -> bool:
        """
        Vérifie si une touche est pressée cette frame ou maintenue

        Args:
            event_id(int): identifiant de la touche
        """
        return self._pressed.get(event_id, False) or event_id in self._step

    def is_pressed(self, event_id: int) -> bool:
        """
        Vérifie si une touche est maintenue enfoncée

        Args:
            event_id(int): identifiant de la touche
        """
        return self._pressed.get(event_id, False)

    def just_pressed(self, event_id: int) -> bool:
        """
        Vérifie si une touche vient d'être pressée cette frame

        Args:
            event_id(int): identifiant de la touche
        """
        return event_id in self._step

    def just_released(self, event_id: int) -> bool:
        """
        Vérifie si une touche vient d'être relâchée cette frame

        Args:
            event_id(int): identifiant de la touche
        """
        return event_id in self._released_this_frame

    # ======================================== MOUSE ========================================
    @property
    def mouse_x(self) -> float:
        """Renvoie la position X absolue de la souris"""
        return self._mouse_x

    @property
    def mouse_y(self) -> float:
        """Renvoie la position Y absolue de la souris"""
        return self._mouse_y

    @property
    def mouse_position(self) -> tuple[float, float]:
        """Renvoie la position absolue de la souris"""
        return self._mouse_x, self._mouse_y
    
    @property
    def relative_origin(self) -> Point:
        """Renvoie l'origine relative pour les coordonnées de la souris"""
        return self._relative_origin
    
    @property
    def relative_mouse_x(self) -> float:
        """Renvoie la position X relative de la souris"""
        return self._mouse_x - self._relative_origin.x

    @property
    def relative_mouse_y(self) -> float:
        """Renvoie la position Y relative de la souris"""
        return self._mouse_y - self._relative_origin.y
    
    @property
    def relative_mouse_position(self) -> tuple[float, float]:
        """Renvoie la position relative de la souris"""
        return self.relative_mouse_x, self.relative_mouse_y
    
    @property
    def mouse_dx(self) -> float:
        """Renvoie le déplacement horizontal de la souris"""
        return self._mouse_dx
    
    @property
    def mouse_dy(self) -> float:
        """Renvoie le déplacement vertical de la souris"""
        return self._mouse_dy
    
    @property
    def drag_dx(self) -> float:
        """Renvoie le glissement horizontal du maintient"""
        return self._drag_dx
    
    @property
    def drag_dy(self) -> float:
        """Renvoie le glissement vertical du maintient"""
        return self._drag_dy

    @property
    def scroll_x(self) -> float:
        """Renvoie le défilement horizontal de la molette cette frame"""
        return self._scroll_dx

    @property
    def scroll_y(self) -> float:
        """Renvoie le défilement vertical de la molette cette frame"""
        return self._scroll_dy
    
    def set_relative_origin(self, point: Point) -> None:
        """Définit l'origine relative pour les coordonnées de la souris

        Args:
            x(float): coordonnée X de l'origine relative
            y(float): coordonnée Y de l'origine relative
        """
        self._relative_origin = Point(point)

    def is_mouse_out(self) -> bool:
        """Vérifie la souris est en dehors de l'écran"""
        return self._mouse_out
    
    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        self.flush()

    # ======================================== INTERNALS ========================================
    def _on_press(self, event_id: int) -> None:
        """Traite une pression"""
        self._step.append(event_id)

        for listener in list(self._listeners.get(event_id, [])):
            if not listener.is_active():
                continue
            if not listener.is_enabled():
                continue
            if listener.up:
                continue
            if listener.repeat:
                continue
            if listener.condition and not listener.condition():
                continue
            listener._fire(event_id)

        for listener in list(self._any_listeners):
            if not listener.is_active():
                continue
            if not listener.is_enabled():
                continue
            if event_id in listener.exclude:
                continue
            if listener.condition and not listener.condition():
                continue
            listener._fire(event_id)

    def _on_release(self, event_id: int) -> None:
        """Traite un relâchement"""
        self._pressed[event_id] = False
        self._released_this_frame.append(event_id)

        for listener in list(self._listeners.get(event_id, [])):
            if not listener.is_active():
                continue
            if not listener.is_enabled():
                continue
            if not listener.up:
                continue
            if listener.condition and not listener.condition():
                continue
            listener._fire(event_id)

    # ======================================== HELPERS ========================================
    def _insert_by_priority(self, lst: list, listener: _Listener) -> None:
        """Insère un listener dans une liste triée par priorité décroissante"""
        for i, l in enumerate(lst):
            if listener.priority > l.priority:
                lst.insert(i, listener)
                return
        lst.append(listener)

    def _compute_mouse(self, x: float, y: float) -> None:
        """Calcule la position de la souris"""
        lx, ly = self._window.window_to_screen(x, y)
        self._mouse_x = lx - self._window.screen.half_width
        self._mouse_y = ly - self._window.screen.half_height
        hw, hh = self._window.screen.half_width, self._window.screen.half_height
        self._mouse_out = not (-hw <= self._mouse_x <= hw and -hh <= self._mouse_y <= hh)
    
# ======================================== LISTENER ========================================
class _Listener:
    """Représente un listener d'entrée utilisateur"""
    __slots__ = (
        "callback",
        "args", "kwargs",
        "up",
        "condition",
        "once",
        "repeat",
        "priority",
        "give_key",
        "exclude",
        "keys",
        "_enabled",
        "_active",
        "_remove_fn",
    )

    def __init__(
            self,
            callback: Callable,
            args: list,
            kwargs: dict,
            priority: int,
            remove_fn: Callable,
            *,
            up: bool = False,
            condition: Callable = None,
            once: bool = False,
            repeat: bool = False,
            give_key: bool = False,
            exclude: set = None,
            keys: set = None,
        ):
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self.priority = priority
        self.up = up
        self.condition = condition
        self.once = once
        self.repeat = repeat
        self.give_key = give_key
        self.exclude = exclude or set()
        self.keys = keys or set()
        self._enabled = True
        self._active = True
        self._remove_fn = remove_fn

    # ======================================== PREDICATES ========================================
    def is_enabled(self) -> bool:
        """Renvoie True si le listener est activé"""
        return self._enabled

    def is_active(self) -> bool:
        """Renvoie True si le listener est encore actif"""
        return self._active
    
    # ======================================== STATE ========================================
    def enable(self) -> None:
        """Active le listener"""
        self._enabled = True
    
    def disable(self) -> None:
        """Désactive le listener"""
        self._enabled = False

    def invalidate(self) -> None:
        """Désactive et désinscrit ce listener"""
        if self._active:
            self._active = False
            self._remove_fn(self)

    # ======================================== HELPERS ========================================
    def _fire(self, event_id: int = None) -> None:
        """Appelle le callback avec les arguments enregistrés"""
        kw = dict(self.kwargs)
        if self.give_key and event_id is not None:
            kw["key"] = event_id
        self.callback(*self.args, **kw)
        if self.once:
            self.invalidate()