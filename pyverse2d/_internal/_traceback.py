# ======================================== IMPORTS ========================================
import sys
from traceback import TracebackException
from pathlib import Path

# ======================================== CONSTANTS ========================================
_ENGINE_ROOT = Path(__file__).resolve().parent.parent

# ======================================== EXCPECT HOOK ========================================
def excepthook(exc_type: type[BaseException], exc: BaseException, tb: TracebackException):
    """Hook d'exception"""
    if not _is_engine_related(tb):
        return sys.__excepthook__(exc_type, exc, tb)

    print("Traceback (most recent call last):")

    filtered = []
    while tb:
        if not _should_hide(tb):
            filtered.append(tb)
        tb = tb.tb_next

    for tb in filtered:
        frame = tb.tb_frame
        code = frame.f_code

        print(
            f'  File "{code.co_filename}", '
            f'line {tb.tb_lineno}, '
            f'in {code.co_name}'
        )

    print(f"{exc_type.__name__}: {exc}")

def install():
    """Configuration du hook"""
    sys.excepthook = excepthook

# ======================================== INTERNALS ========================================
def _is_engine_related(tb: TracebackException) -> bool:
    """Vérification que l'erreur est relative à l'engine"""
    while tb:
        filename = Path(tb.tb_frame.f_code.co_filename)
        try:
            filename.relative_to(_ENGINE_ROOT)
            return True
        except ValueError:
            pass
        tb = tb.tb_next
    return False

def _should_hide(tb: TracebackException) -> bool:
    """Tri des frames"""
    frame = tb.tb_frame
    if frame.f_locals.get("__tracebackhide__"):
        return True
    filename = frame.f_code.co_filename.replace("\\", "/")
    return "/_internal/" in filename

# ======================================== EXPORTS ========================================
__all__ = [
    "excepthook",
    "install",
]