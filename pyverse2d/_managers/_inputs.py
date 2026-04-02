# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._flag import Key
from ..abc import Manager

from ._context import ContextManager

from pyglet.window import Window as PygletWindow

from typing import TYPE_CHECKING, Any, Callable, ClassVar
if TYPE_CHECKING:
    from .._rendering import Window

# ======================================== GESTIONNAIRE ========================================
class InputsManager(Manager):
    """Gestionnaire des entrées utilisateur"""
    __slots__ = (
        "_ctx",
        "_listeners",
        "_step", "_pressed", "_released_this_frame",
        "_any_listeners", "_all_listeners", "_triggered_combos",
        "_mouse_x", "_mouse_y",
        "_scroll_dx", "_scroll_dy",
    )
    Listener: ClassVar[type[Listener]] = Listener

    def __init__(self, context_manager: ContextManager):
        # Contexte de managers
        self._ctx: ContextManager = context_manager

        # Listeners
        self._listeners: dict[int, list[Listener]] = {}
        self._any_listeners: list[Listener] = []
        self._all_listeners: list[Listener] = []

        # Events
        self._step: list = []
        self._pressed: dict = {}
        self._released_this_frame: list = []
        self._triggered_combos: set = set()

        # Paramètres dynamiques
        self._mouse_x: float = 0.0
        self._mouse_y: float = 0.0
        self._scroll_dx: float = 0.0
        self._scroll_dy: float = 0.0

    # ======================================== BIND WINDOW ========================================
    def bind(self, window: Window) -> None:
        """
        Lie le gestionnaire à une fenêtre pyglet

        Args:
            window: fenêtre à assigner
        """
        pyglet_window: PygletWindow = window.native

        @pyglet_window.event
        def on_key_press(symbol, modifiers):
            self._on_press(symbol)

        @pyglet_window.event
        def on_key_release(symbol, modifiers):
            self._on_release(symbol)

        @pyglet_window.event
        def on_mouse_press(x, y, button, modifiers):
            self._mouse_x = x
            self._mouse_y = y
            self._on_press(button)

        @pyglet_window.event
        def on_mouse_release(x, y, button, modifiers):
            self._mouse_x = x
            self._mouse_y = y
            self._on_release(button)

        @pyglet_window.event
        def on_mouse_motion(x, y, dx, dy):
            self._mouse_x = x
            self._mouse_y = y

        @pyglet_window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self._mouse_x = x
            self._mouse_y = y

        @pyglet_window.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):
            self._scroll_dx = scroll_x
            self._scroll_dy = scroll_y

    # ======================================== PRESS / RELEASE ========================================
    def _on_press(self, event_id: int) -> None:
        """Traite une pression"""
        self._step.append(event_id)

        for listener in list(self._listeners.get(event_id, [])):
            if not listener.active:
                continue
            if listener.up:
                continue
            if listener.repeat:
                continue
            if listener.condition and not listener.condition():
                continue
            listener._fire(event_id)

        for listener in list(self._any_listeners):
            if not listener.active:
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
            if not listener.active:
                continue
            if not listener.up:
                continue
            if listener.condition and not listener.condition():
                continue
            listener._fire(event_id)

    # ======================================== HELPERS D'INSERTION ========================================
    def _insert_by_priority(self, lst: list, listener: Listener) -> None:
        """Insère un listener dans une liste triée par priorité décroissante"""
        for i, l in enumerate(lst):
            if listener.priority > l.priority:
                lst.insert(i, listener)
                return
        lst.append(listener)

    # ======================================== LISTENERS SIMPLES ========================================
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
        ) -> Listener:
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

        def _remove(l: Listener):
            lst = self._listeners.get(key)
            if lst and l in lst:
                lst.remove(l)
                if not lst:
                    del self._listeners[key]

        listener = Listener(
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

    # ======================================== WHEN ANY ========================================
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
        ) -> Listener:
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

        def _remove(l: Listener):
            if l in self._any_listeners:
                self._any_listeners.remove(l)

        listener = Listener(
            callback, args, kwargs, priority, _remove,
            once=once, condition=condition,
            give_key=give_key, exclude=set(exclude),
        )

        self._insert_by_priority(self._any_listeners, listener)
        return listener

    # ======================================== WHEN ALL ========================================
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
        ) -> Listener:
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

        def _remove(l: Listener):
            if l in self._all_listeners:
                self._all_listeners.remove(l)

        listener = Listener(callback, args, kwargs, priority, _remove, once=once, condition=condition, repeat=repeat, keys=set(keys))
        self._insert_by_priority(self._all_listeners, listener)
        return listener

    # ======================================== SUPPRESSION GLOBALE ========================================
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
                if not listener.active:
                    continue
                if not listener.repeat:
                    continue
                if listener.condition and not listener.condition():
                    continue
                listener._fire(event_id)

        # Combos (when_all)
        for listener in list(self._all_listeners):
            if not listener.active:
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

    # ======================================== INTERROGATION ========================================
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

    # ======================================== SOURIS ========================================
    @property
    def mouse_x(self) -> float:
        """Renvoie la position X de la souris"""
        return self._mouse_x

    @property
    def mouse_y(self) -> float:
        """Renvoie la position Y de la souris"""
        return self._mouse_y

    @property
    def mouse_pos(self) -> tuple[float, float]:
        """Renvoie la position de la souris"""
        return self._mouse_x, self._mouse_y

    @property
    def scroll_x(self) -> float:
        """Renvoie le défilement horizontal de la molette cette frame"""
        return self._scroll_dx

    @property
    def scroll_y(self) -> float:
        """Renvoie le défilement vertical de la molette cette frame"""
        return self._scroll_dy
    
    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        self.flush()
    
# ======================================== LISTENER ========================================
class Listener:
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
        self._active = True
        self._remove_fn = remove_fn

    def invalidate(self) -> None:
        """Désactive et désinscrit ce listener"""
        if self._active:
            self._active = False
            self._remove_fn(self)

    @property
    def active(self) -> bool:
        """Renvoie True si le listener est encore actif"""
        return self._active

    def _fire(self, event_id: int = None) -> None:
        """Appelle le callback avec les arguments enregistrés"""
        kw = dict(self.kwargs)
        if self.give_key and event_id is not None:
            kw["key"] = event_id
        self.callback(*self.args, **kw)
        if self.once:
            self.invalidate()