# ======================================== IMPORTS ========================================
from .._internal import expect
from ..ecs import World
from .._rendering import Renderer
from ..system import RenderSystem
from ..abc import Layer

# ======================================== LAYER ========================================
class WorldLayer(Layer):
    """
    Layer contenant un World

    Args:
        world(World, optional): monde assigné
    """
    def __init__(self, world: World = None):
        self._world: World | None = expect(world, (World, None))
    
    # ======================================== GETTERS ========================================
    @property
    def world(self) -> World | None:
        """Renvoie le monde assigné"""
        return self._world

    # ======================================== SETTERS ========================================
    @world.setter
    def world(self, value: World | None):
        """Fixe le monde assigné"""
        self._world = expect(value, (World, None))

    # ======================================== CYCLE DE VIE ========================================
    def on_start(self):
        """Activation du layer"""
        ...

    def on_stop(self):
        """Désactivation du layer"""
        ...

    # ======================================== LOOP ========================================
    def update(self, dt: float):
        """Actualisation du layer"""
        if self._world is not None:
            self._world.update(dt)

    def draw(self, renderer: Renderer):
        """Affichage du layer"""
        if self._world is not None and self._world.has_system(RenderSystem):
            self._world.get_system(RenderSystem).draw(renderer)