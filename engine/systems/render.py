# ======================================== IMPORTS ========================================
from .._internal import expect
from ..core import System
from ..rendering import Camera, Viewport

# ======================================== SYSTEM ========================================
class RenderSystem(System):
    """Système gérant le rendu"""
    def __init__(self, camera: Camera = None, viewport: Viewport = None):
        """
        Args:
            camera(Camera, optional): caméra active
            viewport(Viewport, optional): viewport actif
        """
        super().__init__()
        self._camera = camera
        self._viewport = viewport

    # ======================================== UPDATE ========================================
    def update(self):
        """Actualisation du système"""
        pass
    
    # ======================================== GETTERS ========================================
    def get_camera(self) -> Camera | None:
        """Renvoie la caméra active"""
        return self._camera
    
    def get_viewport(self) -> Viewport | None:
        """Renvoie le viewport actif"""
        return self._viewport

    # ======================================== SETTERS ========================================
    def set_camera(self, camera: Camera | None):
        """Fixe la caméra active"""
        self._camera = expect(camera, (Camera, None))
    
    def set_viewport(self, viewport: Viewport | None):
        """Fixe le viewport actif"""
        self._viewport = expect(viewport, (Viewport, None))
        if self._viewport is not None:
            self._viewport._bind(self)