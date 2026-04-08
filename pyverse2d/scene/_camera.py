# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive, clamped, not_in, over
from ..math import Point, Vector
from ..math.easing import EasingFunc, is_easing
from ..abc import Request

from numbers import Real
from dataclasses import dataclass
from typing import ClassVar, Type, Protocol

# ======================================== PROTOCOL ========================================
class Followable(Protocol):
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...

# ======================================== REQUEST ========================================
@dataclass(slots=True)
class TransitionRequest(Request):
    """Requête de transition"""
    start: Point
    end: Point
    duration: float
    elapsed: float
    easing: EasingFunc | None

@dataclass(frozen=True, slots=True)
class FollowRequest(Request):
    """Requête de transition"""
    target: Followable
    offset: Vector
    smoothing: float
    max_speed: float

# ======================================== CAMERA ========================================
class Camera:
    """Définit un point de vue

    Args:
        position: position de la caméra
        view_width: largeur de vision (en unités)
        view_height: hauteur de vision (en unités)
        zoom: facteur de zoom
        rotation: angle de rotation en degrés
    """
    __slots__ = (
        "_position", "_view_width", "_view_height",
        "_zoom", "_rotation",
        "_transition", "_follow",
    )

    TransitionRequest: ClassVar[Type[TransitionRequest]] = TransitionRequest
    FollowRequest: ClassVar[Type[FollowRequest]] = FollowRequest

    def __init__(
            self,
            position: Point = (0.0, 0.0),
            view_width: Real | None = None,
            view_height: Real | None = None,
            zoom: Real = 1.0,
            rotation: Real = 0.0,
        ):
        # Vision
        self._position: Point = Point(position)
        self._view_width: float = over(float(expect(view_width, Real)), 0, include=False) if view_width is not None else None
        self._view_height: float = over(float(expect(view_height, Real)), 0, include=False) if view_height is not None else None

        # Transformation
        self._zoom: float = over(float(expect(zoom, Real)), 0, include=False)
        self._rotation: float = float(expect(rotation, Real))

        # Etat
        self._transition: TransitionRequest = None
        self._follow: FollowRequest = None

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position de la vision

        La position peut être un objet ``Point`` ou un tuple ``(x, y)``.
        """
        return self._position
    
    @position.setter
    def position(self, value: Point) -> None:
        self._position.x = value[0]
        self._position.y = value[1]

    @property
    def x(self) -> float:
        """Coordonnée horizontale
        
        La coordonnée doit être un ``Réel``.
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real) -> None:
        self._position.x = value

    @property
    def y(self) -> float:
        """Coordonnée verticale.
        
        La coordonnée doit être un ``Réel``.
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real) -> None:
        self._position.y = value

    @property
    def view_width(self) -> float:
        """Largeur de vision (en unités)

        La largeur doit être un ``Réel`` positif non nul.
        Mettre à None pour correspondre automatiquement à la largeur du viewport.
        """
        return self._view_width
    
    @view_width.setter
    def view_width(self, value: Real | None) -> None:
        self._view_width = over(float(expect(value, Real)), 0, include=False) if value is not None else None

    @property
    def view_height(self) -> float:
        """Hauteur de vision (en unités)
        
        La hauteur doit être un ``Réel`` positif non nul.
        Mettre à None pour correspondre automatiquement à la hauteur du viewport.
        """
        return self._view_height
    
    @view_height.setter
    def view_height(self, value: Real | None) -> None:
        self._view_height = over(float(expect(value, Real)), 0, include=False) if value is not None else None

    @property
    def zoom(self) -> float:
        """Facteur de zoom
        
        Le facteur doit être un ``Réel`` positif non nul.
        """
        return self._zoom
    
    @zoom.setter
    def zoom(self, value: Real):
        self._zoom = over(float(expect(value, Real)), 0, include=False)

    @property
    def rotation(self) -> float:
        """Angle de rotation

        La rotation se fait en ``degrés`` dans le sens trigonométrique ``(CCW)``.
        """
        return self._rotation
    
    @rotation.setter
    def rotation(self, value: Real) -> None:
        self._rotation = float(expect(value, Real))

    # ======================================== PREDICATES ========================================
    def is_following(self) -> bool:
        """Vérifie que le caméra soit en mode suivi"""
        return self._follow is not None
    
    def in_transition(self) -> bool:
        """Vérifie que la caméra soit en transition"""
        return self._transition is not None
    
    # ======================================== POSITION ========================================
    def move(self, vector: Vector) -> None:
        """Applique une translation vectorielle

        Args:
            vector: vecteur de translation
        """
        self._position.x += vector[0]
        self._position.y += vector[1]

    def goto(
            self,
            position: Point,
            duration: Real = 0.0,
            easing: EasingFunc = None,
        ) -> None:
        """Se déplace jusqu'à une position donnée

        Args:
            position: position cible
            duration: durée de transition
            easing: fonction de progression
        """
        if self.is_following():
            self.unfollow()
        start = self._position.copy()
        end = Point(position)
        duration = positive(float(expect(duration, Real)))
        elapsed = 0.0
        if easing is not None and not is_easing(easing): raise ValueError("easing must be an EasingFunc from pyverse2d.math.easing")
        self._transition = self.TransitionRequest(start, end, duration, elapsed, easing)

    def stop_transition(self) -> None:
        """Met fin à la transition"""
        if self._transition is None:
            return
        self._transition = None

    def follow(
            self,
            target: Followable,
            offset: Vector = (0.0, 0.0),
            smoothing: Real = 0.0,
            max_speed: Real = None,
        ) -> None:
        """Suit un Followable

        Args:
            entity: entité à suivre
            smoothing: facteur de retard relatif [0, 1[
            max_speed: vitesse maximale de déplacement en u/s
        """
        if self.in_transition():
            self.stop_transition()
        offset = Vector(offset)
        not_in(clamped(float(expect(smoothing, Real))), 1)
        if max_speed is not None: positive(not_null(float(expect(max_speed, Real))))
        self._follow = self.FollowRequest(target, offset, smoothing, max_speed)

    def unfollow(self) -> None:
        """Détache la camera de l'entité suivie"""
        if self._follow is None:
            return
        self._follow = None

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        if self.in_transition():
            self._update_transition(dt)
        elif self.is_following():
            self._update_follow(dt)

    def _update_transition(self, dt: float) -> None:
        """Actualise la transition"""
        tr = self._transition
        tr.elapsed += dt
    
        if tr.elapsed >= tr.duration:
            self._go(tr.end.x, tr.end.y)
            return self.stop_transition()
    
        t = tr.elapsed / tr.duration
        if tr.easing is not None:
            t = tr.easing(t)
    
        self._go(*_step_position(tr.start.x, tr.start.y, tr.end.x, tr.end.y, t))

    def _update_follow(self, dt: float) -> None:
        """Actualise le suivi"""
        target = self._follow.target
        offset = self._follow.offset
        target_x, target_y = target.x + offset.x, target.y + offset.y
    
        t = 1 - self._follow.smoothing ** dt
        x, y = _step_position(self._position.x, self._position.y, target_x, target_y, t)
        if self._follow.max_speed is not None:
            dx = x - self._position.x
            dy = y - self._position.y
            max_dist = self._follow.max_speed * dt
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist > max_dist:
                scale = max_dist / dist
                x = self._position.x + dx * scale
                y = self._position.y + dy * scale
        self._go(x, y)

    # ======================================== RESOLVE ========================================
    def resolve(self, viewport_width: int, viewport_height: int) -> tuple[float, float, float, float, float, float]:
        """Renvoie le frustum ``(x, y, width, height, rotation)`` dans l'espace monde

        Args:
            viewport_width: largeur du viewport
            viewport_height: hauteur du viewport
        """
        # Dimensions
        if self._view_width is None and self._view_height is None:
            width  = viewport_width
            height = viewport_height
        elif self._view_width is None:
            height = self._view_height
            width  = height * (viewport_width / viewport_height)
        elif self._view_height is None:
            width  = self._view_width
            height = width * (viewport_height / viewport_width)
        else:
            width  = self._view_width
            height = self._view_height

        return (
            self._position.x,
            self._position.y,
            width ,
            height,
            self._zoom,
            self._rotation,
        )
    
    # ======================================== INTERNALS ========================================
    def _go(self, x: float, y: float) -> None:
        """Déplacement instantanné"""
        self._position.x = x
        self._position.y = y

# ======================================== HELPERS ========================================
def _step_position(start_x: float, start_y: float, end_x: float, end_y: float, t: float) -> tuple[float, float]:
    """Renvoie la position intermédiaire entre deux points

    Args:
        start_x: coordonnée x de la position initiale
        start_y: coordonnée y de la position initiale
        end_x: coordonnée x de la position finale
        end_y: coordonnée y de la position finale
        t: facteur de progression
    """
    x = start_x + (end_x - start_x) * t
    y = start_y + (end_y - start_y) * t
    return (x, y)