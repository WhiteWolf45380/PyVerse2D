# ======================================== IMPORTS ========================================
from ..._flag import Key
from ..._managers._inputs import Listener
from ...abc import Behavior

from typing import Callable, Any

# ======================================== BEHAVIOR ========================================
class ClickBehavior(Behavior):
    """Behavior gérant le clique

    Args:
        ...
    """
    __slots__ = ("_down_listeners", "_up_listeners")

    def __init__(self):
        # Initialisation du comportement
        super().__init__("click")

        # Actions
        self._down_listeners: dict[str, Listener] = {}
        self._up_listeners: dict[str, Listener] = {}

    def add(
        self,
        key: Key.MouseInput = Key.MOUSELEFT,
        callback: Callable = None,
        name: str = None,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        when_up: Callable = None,
        condition: Callable = None,
        once: bool = False,
        repeat: bool = False,
        priority: int = 0,
        give_key: bool = False,
    ) -> None:
        """Ajoute une action lors du clique sur le widget

        Args:
            key: ``MouseInput`` à détecter
            callback: ``fonction`` à appeler
            name: identifant associé à l'action
            args: arguments à passer à la fonction
            kwargs: arguments nommés à passer à la fonction
            when_up: ``fonction`` à appeler lors du relâchement
            condition: ``fonction`` de confirmation lors du clique
            once: supprime le listener après éxécution
            repeat: répète l'action tant que le clique est maintenu
            priority: priorité de l'action
            give_key: passe un argument ``key`` à la fonction
        """
        if name in self._down_listeners:
            raise ValueError(f"This bhavior already has a Listener {name}")

        down_listener: Listener = self._inputs.add_listener(
            key = key,
            callback = callback,
            args = args,
            kwargs = kwargs,
            condition = condition,
            once = once,
            repeat = repeat,
            priority = priority,
            give_key = give_key,
        )
        self._down_listeners[name] = down_listener

        if when_up:
            up_listener: Listener = self._inputs.add_listener(
                key = key,
                up = True,
            )
            self._up_listeners[name] = up_listener