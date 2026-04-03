# ======================================== IMPORTS ========================================
from __future__ import annotations
from typing import Callable

# ======================================== TOOL ========================================
class Processor:
    """
    Exécute une séquence de fonctions sur un contexte

    Args:
        name(str): nom de la pipeline pour le debug
    """
    def __init__(self, name: str = ""):
        self._name: str = name
        self._steps: list[Callable] = []

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        return f"Pipeline(name={self._name!r}, steps={[s.__name__ for s in self._steps]})"

    def __len__(self) -> int:
        return len(self._steps)

    # ======================================== DECORATEUR ========================================
    def step(self, fn: Callable) -> Callable:
        """
        Enregistre une fonction comme étape de la pipeline

        Args:
            fn(callable): fonction à enregistrer, prend un contexte en argument
        """
        self._steps.append(fn)
        return fn

    # ======================================== EXECUTION ========================================
    def run(self, ctx) -> None:
        """
        Exécute toutes les étapes séquentiellement sur le contexte

        Args:
            ctx: contexte partagé entre les étapes
        """
        for step in self._steps:
            if step(ctx) is False:
                return
            
    def __call__(self, ctx) -> None:
        """
        Exécute toutes les étapes séquentiellement sur le contexte

        Args:
            ctx: contexte partagé entre les étapes
        """
        self.run(ctx)