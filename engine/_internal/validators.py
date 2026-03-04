# ======================================== IMPORTS ========================================
from typing import Any, Iterable

# ======================================== CHECKERS ========================================
def expect(value: object, types: Any | Iterable[Any]):
    """
    Vérifie la correspondance des types

    Args:
        value(object): valeur à vérifier
        types(Any|Iterable[Any]): types valides
    """
    if not isinstance(types, (tuple, list, set)):
        types = (types,)