# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.window.mouse
from pyglet.window import Window as PygletWindow

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .._rendering import Window

# ======================================== GESTIONNAIRE ========================================
class InputsManager:
    """Gestionnaire des entrées utilisateur"""
    __slots__ = (
        "_listeners",
        "_step", "_pressed", "_released_this_frame",
        "_any_listeners", "_all_listeners", "_triggered_combos",
        "_mouse_x", "_mouse_y",
        "_scroll_dx", "_scroll_dy",
    )
    MOUSELEFT = pyglet.window.mouse.LEFT
    MOUSERIGHT = pyglet.window.mouse.RIGHT
    MOUSEMIDDLE = pyglet.window.mouse.MIDDLE

    def __init__(self):
        self._listeners: dict = {}
        self._step: list = []
        self._pressed: dict = {}
        self._released_this_frame: list = []
        self._any_listeners: list = []
        self._all_listeners: list = []
        self._triggered_combos: set = set()
        self._mouse_x: float = 0.0
        self._mouse_y: float = 0.0
        self._scroll_dx: float = 0.0
        self._scroll_dy: float = 0.0

    # ======================================== BIND WINDOW ========================================
    def bind(self, window: Window):
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
    def _on_press(self, event_id: int):
        """Traite une pression"""
        self._step.append(event_id)

        to_remove = []
        for listener in self._listeners.get(event_id, []):
            if listener["up"]:
                continue
            if listener["repeat"]:
                continue
            if listener["condition"] and not listener["condition"]():
                continue
            kw = dict(listener["kwargs"])
            if listener["give_key"]:
                kw["key"] = event_id
            listener["callback"](*listener["args"], **kw)
            if listener["once"]:
                to_remove.append(listener)

        for l in to_remove:
            self._listeners[event_id].remove(l)
        if event_id in self._listeners and not self._listeners[event_id]:
            del self._listeners[event_id]

        to_remove = []
        for listener in self._any_listeners:
            if event_id in listener["exclude"]:
                continue
            if listener["condition"] and not listener["condition"]():
                continue
            kw = dict(listener["kwargs"])
            if listener["give_key"]:
                kw["key"] = event_id
            listener["callback"](*listener["args"], **kw)
            if listener["once"]:
                to_remove.append(listener)

        for l in to_remove:
            if l in self._any_listeners:
                self._any_listeners.remove(l)

    def _on_release(self, event_id: int):
        """Traite un relâchement"""
        self._pressed[event_id] = False
        self._released_this_frame.append(event_id)

        to_remove = []
        for listener in self._listeners.get(event_id, []):
            if not listener["up"]:
                continue
            if listener["condition"] and not listener["condition"]():
                continue
            kw = dict(listener["kwargs"])
            if listener["give_key"]:
                kw["key"] = event_id
            listener["callback"](*listener["args"], **kw)
            if listener["once"]:
                to_remove.append(listener)

        for l in to_remove:
            self._listeners[event_id].remove(l)
        if event_id in self._listeners and not self._listeners[event_id]:
            del self._listeners[event_id]

    # ======================================== LISTENERS SIMPLES ========================================
    def add_listener(
            self,
            event_id: int,
            callback: callable,
            args: list = None,
            kwargs: dict = None,
            up: bool = False,
            condition: callable = None,
            once: bool = False,
            repeat: bool = False,
            priority: int = 0,
            give_key: bool = False
        ):
        """
        Ajoute un listener sur une entrée utilisateur

        Args:
            event_id(int): identifiant de l'événement
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

        listener = {
            "callback": callback,
            "up": up,
            "condition": condition,
            "once": once,
            "repeat": repeat,
            "priority": priority,
            "give_key": give_key,
            "args": args,
            "kwargs": kwargs,
        }

        if event_id not in self._listeners:
            self._listeners[event_id] = [listener]
            return

        for i, l in enumerate(self._listeners[event_id]):
            if priority > l["priority"]:
                self._listeners[event_id].insert(i, listener)
                return

        self._listeners[event_id].append(listener)

    def remove_listener(self, event_id: int, callback: callable):
        """
        Supprime un listener sur une entrée

        Args:
            event_id(int): identifiant de l'événement
            callback(callable): callback à supprimer
        """
        if event_id in self._listeners:
            self._listeners[event_id] = [
                l for l in self._listeners[event_id]
                if l["callback"] != callback
            ]
            if not self._listeners[event_id]:
                del self._listeners[event_id]

    # ======================================== WHEN ANY ========================================
    def when_any(
            self,
            callback: callable,
            exclude: list = None,
            args: list = None,
            kwargs: dict = None,
            once: bool = False, 
            condition: callable = None,
            priority: int = 0,
            give_key: bool = False
        ):
        """
        Déclenche le callback sur n'importe quelle pression sauf les exclusions

        Args:
            callback(callable): fonction à appeler
            exclude(list): event_id à exclure
            args(list): arguments positionnels
            kwargs(dict): arguments nommés
            once(bool): supprime après première activation
            condition(callable): condition booléenne
            priority(int): priorité d'exécution
            give_key(bool): passe event_id en paramètre key
        """
        if exclude is None: exclude = []
        if args is None: args = []
        if kwargs is None: kwargs = {}

        listener = {
            "callback": callback,
            "exclude": set(exclude),
            "args": args,
            "kwargs": kwargs,
            "once": once,
            "condition": condition,
            "priority": priority,
            "give_key": give_key,
        }

        for i, l in enumerate(self._any_listeners):
            if priority > l["priority"]:
                self._any_listeners.insert(i, listener)
                return

        self._any_listeners.append(listener)

    # ======================================== WHEN ALL ========================================
    def when_all(
            self,
            keys: list,
            callback: callable,
            args: list = None,
            kwargs: dict = None,
            once: bool = False,
            condition: callable = None,
            repeat: bool = False,
            priority: int = 0
        ):
        """
        Déclenche le callback quand toutes les touches sont pressées simultanément

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

        listener = {
            "keys": set(keys),
            "callback": callback,
            "args": args,
            "kwargs": kwargs,
            "once": once,
            "condition": condition,
            "repeat": repeat,
            "priority": priority,
        }

        for i, l in enumerate(self._all_listeners):
            if priority > l["priority"]:
                self._all_listeners.insert(i, listener)
                return

        self._all_listeners.append(listener)

    # ======================================== SUPPRESSION GLOBALE ========================================
    def remove_callback(self, callback: callable):
        """
        Supprime un callback de tous les types de listeners

        Args:
            callback(callable): callback à supprimer partout
        """
        for event_id in list(self._listeners.keys()):
            self._listeners[event_id] = [
                l for l in self._listeners[event_id]
                if l["callback"] != callback
            ]
            if not self._listeners[event_id]:
                del self._listeners[event_id]

        self._any_listeners = [l for l in self._any_listeners if l["callback"] != callback]
        self._all_listeners = [l for l in self._all_listeners if l["callback"] != callback]

    # ======================================== CHECK PRESSED ========================================
    def flush(self):
        """
        À appeler une fois par frame — traite les repeat, combos et nettoie les états
        """
        for event_id, listeners in self._listeners.items():
            if not self._is_currently_pressed(event_id):
                continue
            for listener in listeners:
                if not listener["repeat"]:
                    continue
                if listener["condition"] and not listener["condition"]():
                    continue
                kw = dict(listener["kwargs"])
                if listener["give_key"]:
                    kw["key"] = event_id
                listener["callback"](*listener["args"], **kw)

        to_remove = []
        for listener in self._all_listeners:
            if not all(self._is_currently_pressed(k) for k in listener["keys"]):
                continue
            if listener["condition"] and not listener["condition"]():
                continue

            combo_key = frozenset(listener["keys"])

            if listener["repeat"]:
                listener["callback"](*listener["args"], **listener["kwargs"])
                if listener["once"]:
                    to_remove.append(listener)
            else:
                if combo_key not in self._triggered_combos:
                    listener["callback"](*listener["args"], **listener["kwargs"])
                    self._triggered_combos.add(combo_key)
                    if listener["once"]:
                        to_remove.append(listener)

        active_combos = set()
        for listener in self._all_listeners:
            if all(self._is_currently_pressed(k) for k in listener["keys"]):
                active_combos.add(frozenset(listener["keys"]))
        self._triggered_combos = self._triggered_combos & active_combos

        for l in to_remove:
            self._all_listeners.remove(l)

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