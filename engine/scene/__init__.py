# ======================================== IMPORTS ========================================
from .._internal import expect
from .._flag import StackMode

from ._world_layer import WorldLayer
from ._scene import Scene

# ======================================== STATE ========================================
_stack: list[tuple[Scene, StackMode]] = []

# ======================================== GETTERS ========================================
def get_current() -> Scene | None:
    """Renvoie la scene active"""
    return _stack[-1][0] if _stack else None

# ======================================== TRANSITIONS ========================================
def load(scene: Scene):
    """Remplace toute la stack par une scene"""
    global _stack
    for s, _ in reversed(_stack):
        s.on_stop()
    _stack.clear()
    _stack.append((expect(scene, Scene), StackMode.PAUSE))
    scene.on_start()

def switch(scene: Scene):
    """Remplace la scene active par une autre"""
    if _stack:
        _stack[-1][0].on_stop()
        _stack.pop()
    _stack.append((expect(scene, Scene), StackMode.PAUSE))
    scene.on_start()

def push(scene: Scene, mode: StackMode = StackMode.PAUSE):
    """Empile une scene par dessus l'active"""
    if _stack:
        below = _stack[-1][0]
        if mode == StackMode.PAUSE:
            below.on_stop()
        elif mode == StackMode.SUSPEND:
            below.suspend()
    _stack.append((expect(scene, Scene), mode))
    scene.on_start()

def pop():
    """Dépile la scene active et reprend la précédente"""
    if _stack:
        _stack[-1][0].on_stop()
        _stack.pop()
    if _stack:
        _stack[-1][0].on_start()

# ======================================== LOOP ========================================
def update(dt: float):
    for scene, mode in _stack:
        if mode != StackMode.PAUSE:
            scene.update(dt)

def draw():
    for scene, _ in _stack:
        scene.draw()

# ======================================== EXPORTS ========================================
__all__ = [
    "WorldLayer",
    "Scene",
    "StackMode",

    "get_current",
    "load",
    "switch",
    "push",
    "pop",
    "update",
    "draw"
]