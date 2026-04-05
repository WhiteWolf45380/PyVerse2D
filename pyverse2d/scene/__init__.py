# ======================================== IMPORTS ========================================
from .._internal import expect
from .._flag import StackMode, SceneState, CameraMode
from .._rendering._pipeline import Pipeline

from ._camera import Camera
from ._viewport import Viewport
from ._world_layer import WorldLayer
from ._tile_layer import TileLayer
from ._gui_layer import GuiLayer
from ._scene import Scene

from pyverse2d import mouse

# ======================================== STATE ========================================
_stack: list[Scene] = []
_update_states: tuple[SceneState, ...] = (SceneState.RUNNING, SceneState.HIDDEN)
_draw_states: tuple[SceneState, ...] = (SceneState.RUNNING, SceneState.PAUSED)

# ======================================== GETTERS ========================================
def get_current() -> Scene | None:
    """Renvoie la scene active"""
    return _stack[-1] if _stack else None

# ======================================== TRANSITIONS ========================================
def load(scene: Scene):
    """Remplace toute la stack par une scene"""
    _stop_all()
    _stack.clear()
    _stack.append(expect(scene, Scene))
    scene.set_state(SceneState.RUNNING)
    scene.on_start()

def switch(scene: Scene):
    """Remplace la scene active par une autre"""
    if _stack:
        top = _stack[-1]
        top.set_state(SceneState.SLEEPING)
        top.on_stop()
        _stack.pop()
    _stack.append(expect(scene, Scene))
    scene.set_state(SceneState.RUNNING)
    scene.on_start()

def push(scene: Scene):
    """Empile une scene par dessus la scene active"""
    if _stack and scene.stack_mode is not StackMode.OVERLAY:
        top = _stack[-1]
        if scene.stack_mode is StackMode.PAUSE: top.set_state(SceneState.PAUSED)
        elif scene.stack_mode is StackMode.HIDE: top.set_state(SceneState.HIDDEN)
        else:
            top.set_state(SceneState.SLEEPING)
            top.on_stop()
    _stack.append(expect(scene, Scene))
    scene.set_state(SceneState.RUNNING)
    scene.on_start()

def pop():
    """Dépile la scene active et reprend la précédente"""
    if _stack:
        top = _stack[-1]
        top.set_state(SceneState.SLEEPING)
        top.on_stop()
        _stack.pop()
        if _stack:
            new_top = _stack[-1]
            new_top.set_state(SceneState.RUNNING)
            new_top.on_start()
        return top

# ======================================== LOOP ========================================
def update(dt: float):
    """Actualisation des scènes"""
    for scene in reversed(_stack):
        if scene.state in _update_states:
            mouse.set_viewport_origin(scene.viewport.origin)
            scene.update(dt)
    mouse.set_viewport_origin((0, 0))

def draw(pipeline: Pipeline):
    """Affichage des scènes"""
    for scene in _stack:
        if scene.state in _draw_states:
            scene.draw(pipeline)

# ======================================== INTERNALS ========================================
def _stop_all():
    for scene in _stack:
        scene.set_state(SceneState.SLEEPING)
        scene.on_stop()

# ======================================== EXPORTS ========================================
__all__ = [
    "CameraMode",
    "StackMode",
    "SceneState",

    "Camera",
    "Viewport",

    "WorldLayer",
    "TileLayer",
    "GuiLayer",
    "Scene",

    "get_current",
    "load",
    "switch",
    "push",
    "pop",
    "update",
    "draw"
]