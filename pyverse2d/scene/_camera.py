# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect, not_null, positive
from ..math import Point, Vector
from ..world import Entity, Transform

from pyglet.math import Mat4, Vec3
from numbers import Real

# ======================================== CAMERA ========================================
class Camera:
    """
    Définit le point de vue dans le monde

    Args:
        pos(Point): position de la caméra
        zoom (Real): facteur de zoom
    """
    __slots__ = ("_pos", "_following", "_offset", "_zoom")

    def __init__(self, pos: Point = (0.0, 0.0), zoom: Real = 1.0):
        self._pos: Point = Point(pos)
        self._following: Entity | None = None
        self._offset: Vector = Vector(0.0, 0.0)
        self._zoom: float = float(positive(not_null(expect(zoom, Real))))

    # ======================================== GETTERS ========================================
    @property
    def x(self) -> float:
        """Renvoie la position horizontale"""
        return self._pos.x

    @property
    def y(self) -> float:
        """Renvoie la position verticale"""
        return self._pos.y

    @property
    def pos(self) -> Point:
        """Renvoie la position"""
        return self._pos

    @property
    def offset(self) -> Vector:
        """Renvoie le vecteur de décalage à la position"""
        return self._offset
    
    @property
    def final_x(self) -> float:
        """Position horizontale finale"""
        self._check_follow()
        base = self._following.get(Transform).x if self._following else self._pos.x
        return base + self._offset.x
    
    @property
    def final_y(self) -> float:
        """Position verticale finale"""
        self._check_follow()
        base = self._following.get(Transform).y if self._following else self._pos.y
        return base + self._offset.y

    @property
    def final_pos(self) -> Point:
        """Renvoie la position finale"""
        self._check_follow()
        base = self._following.get(Transform).pos if self._following else self._pos
        return base + self._offset

    @property
    def zoom(self) -> float:
        return self._zoom

    # ======================================== SETTERS ========================================
    @x.setter
    def x(self, value: Real):
        self._pos.x = float(expect(value, Real))

    @y.setter
    def y(self, value: Real):
        self._pos.y = float(expect(value, Real))

    @pos.setter
    def pos(self, value: Point):
        self._pos = Point(value)

    @zoom.setter
    def zoom(self, value: Real):
        if float(value) <= 0:
            raise ValueError("Zoom must be greater than 0")
        self._zoom = float(value)

    # ======================================== FOLLOW ========================================
    def follow(self, entity: Entity):
        """
        Suit le Transform d'une entité

        Args:
            entity (Entity): entité à suivre
        """
        if not entity.has(Transform):
            raise ValueError(f"Entity {entity.id[:8]}... has no Transform component")
        self._following = entity

    def unfollow(self):
        """Détache la camera de l'entité suivie"""
        self._following = None

    def _check_follow(self):
        """Unfollow automatique si l'entité est inactive"""
        if self._following is not None and not self._following.is_active():
            self._following = None

    # ======================================== DÉPLACEMENT ========================================
    def move(self, vector: Vector):
        """
        Déplace la position manuelle de la camera

        Args:
            vectorr(Vector): vecteur de translation
        """
        self._pos += Vector(vector)

    # ======================================== RENDU ========================================
    def view_matrix(self) -> Mat4:
        """Produit la matrice de vue à appliquer à l'écran"""
        fx, fy = self.final_pos
        translate = Mat4.from_translation(Vec3(-fx, -fy, 0))
        scale = Mat4.from_scale(Vec3(self._zoom, self._zoom, 1))
        return translate @ scale