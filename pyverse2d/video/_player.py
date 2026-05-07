# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import over, expect
from ..math import Point

from ._video import Video

from numbers import Real

# ======================================== PLAYER ========================================
class VideoPlayer:
    """Lecteur vidéo monde"""
    __slots__ = (
        "_position", "_width", "_height",
        "_playing", "_paused",
        "_video",
    )

    def __init__(self, position: Point, width: int, height: int):
        # Transtypage et vérifications
        position = Point(position)
        width = int(width)
        height = int(height)

        if __debug__:
            over(width, 0, include=False)
            over(height, 0, include=False)

        # Attributs publiques
        self._position: Point = position
        self._width: int = width
        self._height: int = height

        # Attributs internes
        self._playing: bool = False
        self._paused: bool = False

        # Context
        self._video: Video = None

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position
        
        La position peut être un objet ``Point`` ou n'importe quel tuple ``(x, y)``.
        """
        return self._position
    
    @position.setter
    def position(self, value: Point) -> None:
        self._position.x, self._position.y = value

    @property
    def x(self) -> float:
        """Position horizontale"""
        return self._position.x
    
    @x.setter
    def x(self, value: Real) -> None:
        self._position.x = value

    @property
    def y(self) -> float:
        """Position verticale"""
        return self._y
    
    @y.setter
    def y(self, value: float) -> None:
        self._position.y = value

    @property
    def width(self) -> int:
        """Largeur du lecteur
        
        La largeur doit être un ``int`` positif non nul.
        """
        return self._width
    
    @width.setter
    def width(self, value: int) -> None:
        value = int(value)
        if __debug__:
            over(value, 0, include=False)
        return value
    
    @property
    def height(self) -> int:
        """Hauteur du lecteur
        
        La hauteur doit être un ``int`` positif non nul.
        """
        return self._height
    
    @height.setter
    def height(self, value: int) -> None:
        value = int(value)
        if __debug__:
            over(value, 0, include=False)
        return value
    
    # ======================================== PREDICATES ========================================
    def is_playing(self) -> bool:
        """Vérifie que le lecteur soit en cours de lecture"""
        return self._playing
    
    def is_paused(self) -> bool:
        """Vérifie que le lecteur soit en pause"""
        return self._paused
    
    # ======================================== INTERFACE ========================================
    def load(self, video: Video) -> None:
        """Charge une vidéo
        
        Args:
            video: ``Video`` à charger
        """
        if __debug__:
            expect(video, Video)
        self._video = video

    def play(self, video : Video | None = None) -> None:
        """Lance la lecture d'une vidéo
        
        Args:
            video: ``Video`` à lancer *(par défaut la vidéo chargée)*
        """
        if __debug__:
            expect(video, (Video, None))
        self._video: Video = video or self._video
        self._playing = True

    def pause(self) -> None:
        """Met le lecture en pause"""
        self._paused = True

    def unpause(self) -> None:
        """Reprend la lecture"""
        self._paused = False

    def stop(self) -> None:
        """Arrête la lecture"""
        self._playing = False

    def clear(self) -> None:
        """Nettoie le contexte courant"""
        self._video = None
    
    # ======================================== INTERNALS ========================================