# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive, clamped, not_in
from ..math import Point, Vector
from ..abc import Request
from ..world import Entity, Transform

from pyglet.math import Mat4, Vec3
from numbers import Real
from dataclasses import dataclass
from typing import Callable, ClassVar, Type

# ======================================== ALIAS ========================================
EasingFunc = Callable[[float], float]

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
    entity: Entity
    smoothing: float

# ======================================== CAMERA ========================================
class Camera:
    """
    Définit le point de vue dans le monde

    Args:
        position(Point): position de la caméra
        zoom (Real): facteur de zoom
    """
    __slots__ = (
        "_position", "_offset", "_zoom",
        "_transition", "_follow",
        "_final_position",
    )

    TransitionRequest: ClassVar[Type[TransitionRequest]] = TransitionRequest
    FollowRequest: ClassVar[Type[FollowRequest]] = FollowRequest

    def __init__(self, position: Point = (0.0, 0.0), zoom: Real = 1.0):
        # Transform
        self._position: Point = Point(position)
        self._offset: Vector = Vector(0.0, 0.0)
        self._zoom: float = float(positive(not_null(expect(zoom, Real))))

        # Etat
        self._transition: TransitionRequest = None
        self._follow: FollowRequest = None

        # Paramètres flottants
        self._final_position: Point = self._position

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position brute

        La position peut être un objet ``Point`` ou un tuple ``(x, y)``
        """
        return self._position
    
    @position.setter
    def position(self, value: Point):
        self._position = Point(value)
        self._compute_final_position()

    @property
    def x(self) -> float:
        """Position brute horizontale
        
        La coordonnée doit être un ``Réel``
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real):
        self._position._x = value
        self._compute_final_position()

    @property
    def y(self) -> float:
        """Position brute verticale
        
        La coordonnée doit être un ``Réel``
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real):
        self._position._y = value
        self._compute_final_position()

    @property
    def offset(self) -> Vector:
        """Vecteur de décalage par rapport à la position

        Le vecteur peut être un objet ``Vector`` ou un tuple ``(vx, vy)``
        """
        return self._offset
    
    @offset.setter
    def offset(self, value: Vector) -> None:
        self._offset = Vector(value)
        self._compute_final_position()
    
    @property
    def offset_x(self) -> float:
        """Décalage horizontal par rapport à la position
        
        La composante doit être un ``Réel``
        """
        return self._offset.x
    
    @offset_x.setter
    def offset_x(self, value: Real) -> None:
        self._offset._x = value
        self._compute_final_position()
    
    @property
    def offset_y(self) -> float:
        """Décalage vertical par rapport à la position
        
        La composante doit être un ``Réel``
        """
        return self._offset.y
    
    @offset_y.setter
    def offset_y(self, value: Real) -> None:
        self._offset_y = value
        self._compute_final_position()

    @property
    def zoom(self) -> float:
        """Facteur de zoom
        
        Le facteur doit être un ``Réel`` positif non nul
        """
        return self._zoom
    
    @zoom.setter
    def zoom(self, value: Real):
        self._zoom = positive(not_null(float(expect(value, Real))))

    @property
    def final_position(self) -> Point:
        """Renvoie la position finale"""
        return self._final_position

    @property
    def final_x(self) -> float:
        """position horizontale finale"""
        return self._final_position.x
    
    @property
    def final_y(self) -> float:
        """position verticale finale"""
        return self._final_position.y

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
        self._position += Vector(vector)
        self._compute_final_position()

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
        start = self._position
        end = Point(position)
        duration = positive(float(expect(duration, Real)))
        elapsed = 0.0
        easing = callable(easing) if easing is not None else None
        self._transition = self.TransitionRequest(start, end, duration, elapsed, easing)

    def stop_transition(self) -> None:
        """Met fin à la transition"""
        if self._transition is None:
            return
        self._transition = None

    def follow(
            self,
            entity: Entity,
            smoothing: Real,
        ) -> None:
        """
        Suit le Transform d'une entité

        Args:
            entity: entité à suivre
            smoothing: facteur de retard relatif [0, 1[
        """
        if not expect(entity, Entity).has(Transform):
            raise ValueError(f"Entity {entity.id[:8]}... has no Transform component")
        if self.in_transition():
            self.stop_transition()
        smoothing = not_in(clamped(float(expect(smoothing, Real))), 1)
        self._follow = FollowRequest(entity, smoothing)

    def unfollow(self) -> None:
        """Détache la camera de l'entité suivie"""
        if self._follow is None:
            return
        self._position = self._follow.entity.transform.position.copy()
        self._follow = None

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        if self.in_transition():
            self._update_transition(dt)
        if self.is_following():
            self._update_follow(dt)

    # ======================================== RENDER ========================================
    def view_matrix(self) -> Mat4:
        """Produit la matrice de vue à appliquer à l'écran"""
        fx, fy = self.final_position
        translate = Mat4.from_translation(Vec3(-fx, -fy, 0))
        scale = Mat4.from_scale(Vec3(self._zoom, self._zoom, 1))
        return translate @ scale
    
    def zoom_matrix(self) -> Mat4:
        """Produit uniquement la matrice de zoom à appliquer à l'écran"""
        return Mat4.from_scale(Vec3(self._zoom, self._zoom, 1))

    # ======================================== INTERNALS ========================================
    def _update_transtion(self, dt: float) -> None:
        """Actualise la transition"""
        tr = self._transition
        tr.elapsed += dt
        if tr.elapsed >= tr.duration:
            self._go(tr.end.x, tr.end.y)
            self._transition = None
            return
        t = tr.elapsed / tr.duration
        if tr.easing is not None:
            t = tr.easing(t)
        self._go(_step_position(tr.start.x, tr.start.y, tr.end.x, tr.end.y, t))

    def _update_follow(self, dt: float) -> None:
        """Actualise le suivi"""
        entity = self._follow.entity
        if not entity.is_active() or not entity.has(Transform):
            self._follow = None
            return
        target = entity.transform.position
        t = 1 - self._follow.smoothing ** dt
        self._go(_step_position(self._position.x, self._position.y, target.x, target.y, t))

    def _go(self, x: float, y: float) -> None:
        """Déplacement instantanné optimisé"""
        self._position.x, self._position.y = x, y

    def _compute_final_position(self) -> None:
        """Calcul la position finale"""
        self._final_position.x = self._position.x + self._offset.x
        self._final_position.y = self._position.y + self._offset.y

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