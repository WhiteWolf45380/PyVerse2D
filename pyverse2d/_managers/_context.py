# ======================================== IMPORTS ========================================
from typing import Iterator

# ======================================== CONTEXT ========================================
class ContextManager:
    """Contexte des managers"""
    __slots__ = (
        "time",
        "inputs",
        "ui_manager",
    )

    def __iter__(self) -> Iterator:
        """Itère sur les itérateurs"""
        for manager in self.__slots__:
            yield getattr(self, manager, None)