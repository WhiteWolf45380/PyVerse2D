# ======================================== IMPORTS ========================================
from types import UnionType
from typing import Tuple, get_args, get_origin

# ======================================== TYPE CHECK ========================================
def expect(value: object, types: type | Tuple[type, ...]):
    """
    Vérifie la valeur contre un type supporté :
        T                   type simple
        (T1, T2, T3)        multi-types
        T1 | T2             union
        list[T]             liste typée
        set[T]              set typé
        tuple[T]            tuple broadcast
        tuple[T1, T2, T3]   tuple positionnel
        dict[K, V]          dictionnaire typé

    Args:
        value(object): valeur à vérifier
        types(type|Tuple[type, ...]): types à vérifier

    Returns:
        value(object): si valide
    
    Raises:
        TypeError: si la valeur n'est pas conforme
    """
    # (T1, T2, T3)
    if isinstance(types, tuple):
        types = tuple(type(None) if t is None else t for t in types)
        if not isinstance(value, types):
            readable = " | ".join(t.__name__ for t in types)
            raise TypeError(f"expected ({readable}), got ({type(value).__name__})")
        return value

    # T
    origin = get_origin(types)
    if origin is None:
        types = type(None) if types is None else types
        if not isinstance(value, types):
            raise TypeError(f"expected ({types.__name__}), got ({type(value).__name__})")
        return value
    
    # T1 |T2
    args = get_args(types)
    if origin is UnionType:
        for t in args:
            try:
                return expect(value, t)
            except TypeError:
                continue
        readable = " | ".join(t.__name__ for t in args)
        raise TypeError(f"expected ({readable}), got ({type(value).__name__})")

    # list[T] / set[T]
    if origin in (list, set):
        if not isinstance(value, origin):
            raise TypeError(f"expected ({origin.__name__}), got ({type(value).__name__})")
        inner = args[0]
        if get_origin(inner) is None:
            for i, v in enumerate(value):
                if not isinstance(v, inner):
                    raise TypeError(f"at index {i}: expected ({inner.__name__}), got ({type(v).__name__})")
        else:
            for i, v in enumerate(value):
                try:
                    expect(v, inner)
                except TypeError as e:
                    raise TypeError(f"at index {i}: {e}") from e
        return value

    # tuple[T] / tuple[T1, T2, T3]
    if origin is tuple:
        if not isinstance(value, tuple):
            raise TypeError(f"expected (tuple), got ({type(value).__name__})")
        if len(args) == 1:
            inner = args[0]
            if get_origin(inner) is None:
                for i, v in enumerate(value):
                    if not isinstance(v, inner):
                        raise TypeError(f"at index {i}: expected ({inner.__name__}), got ({type(v).__name__})")
            else:
                for i, v in enumerate(value):
                    try:
                        expect(v, inner)
                    except TypeError as e:
                        raise TypeError(f"at index {i}: {e}") from e
        else:
            if len(value) != len(args):
                raise TypeError(f"expected (tuple) of len {len(args)}, got {len(value)}")
            for i, (v, t) in enumerate(zip(value, args)):
                if get_origin(t) is None:
                    if not isinstance(v, t):
                        raise TypeError(f"at index {i}: expected ({t.__name__}), got ({type(v).__name__})")
                else:
                    try:
                        expect(v, t)
                    except TypeError as e:
                        raise TypeError(f"at index {i}: {e}") from e
        return value

    # dict[K, V]
    if origin is dict:
        if not isinstance(value, dict):
            raise TypeError(f"expected (dict), got ({type(value).__name__})")
        kt, vt = args
        kt_simple = get_origin(kt) is None
        vt_simple = get_origin(vt) is None
        for k, v in value.items():
            if kt_simple:
                if not isinstance(k, kt):
                    raise TypeError(f"at key {k!r}: invalid key: expected ({kt.__name__}), got ({type(k).__name__})")
            else:
                try:
                    expect(k, kt)
                except TypeError as e:
                    raise TypeError(f"at key {k!r}: invalid key: {e}") from e
            if vt_simple:
                if not isinstance(v, vt):
                    raise TypeError(f"at key {k!r}: expected ({vt.__name__}), got ({type(v).__name__})")
            else:
                try:
                    expect(v, vt)
                except TypeError as e:
                    raise TypeError(f"at key {k!r}: {e}") from e
        return value

    raise TypeError(f"unsupported type annotation: {types!r}")