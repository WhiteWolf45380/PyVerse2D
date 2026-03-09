# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import expect
from ..core import MathObject

from numbers import Real
from typing import Iterator
from math import acos

# ======================================== OBJET ========================================
class Vector(MathObject):
    """Objet mathématique 2D abstrait : Vecteur"""
    __slots__ = ("_x", "_y")
    PRECISION = 9
    def __init__(
            self,
            x: Real,
            y: Real
        ):
        """
        Args:
            x(Real): composante x
            y(Real): composante y
        """
        super().__init__()
        self._x: float = round(float(expect(x, Real)), self.PRECISION)
        self._y: float = round(float(expect(y, Real)), self.PRECISION)
    
    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du vecteur"""
        return f"Vector({self._x}, {self._y})"
    
    def __iter__(self) -> Iterator[float]:
        """Renvoie les composantes dans un itérateur"""
        yield self._x
        yield self._y
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du vecteur"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[float]:
        """Renvoie le vecteur sous forme de tuple"""
        return (self._x, self._y)
    
    def to_list(self) -> list[float]:
        """Renvoie le vecteur sous forme de liste"""
        return [self._x, self._y]

    # ======================================== GETTERS ========================================
    def __getitem__(self, i: int) -> float:
        """Renvoie une composante du vecteur"""
        return (self._x, self._y)[expect(i, (int))]
    
    @property
    def x(self) -> float:
        """Renvoie la composante horizontale du vecteur"""
        return self._x
    
    @property
    def y(self) -> float:
        """Renvoie la composante verticale du vecteur"""
        return self._y
    
    def __len__(self) -> int:
        """Renvoie la dimension du vecteur"""
        return 2
    
    @property
    def norm(self) -> float:
        """Renvoie la norme du vecteur"""
        return (self._x**2 + self._y**2)**0.5
    
    def __abs__(self) -> float:
        """Renvoie la norme du vecteur"""
        return self.norm
    
    @property
    def normalized(self) -> Vector:
        """Renvoie le vecteur normalisé"""
        if self.is_null():
            raise ZeroDivisionError("Cannot normalize null vector")
        return self / self.norm

    # ======================================== SETTERS ========================================
    def __setitem__(self, i: int, value: Real):
        """Fixe une composante du vecteur"""
        setattr(self, ("x", "y")[expect(i, int)], round(float(expect(value, Real)), self.PRECISION))
    
    @x.setter
    def x(self, value: Real):
        """Fixe la composante x du vecteur"""
        self._x = round(float(expect(value, Real)), self.PRECISION)
    
    @y.setter
    def y(self, value: Real):
        """Fixe la composante y du vecteur"""
        self._y = round(float(expect(value, Real)), self.PRECISION)

    @norm.setter
    def norm(self, value: Real):
        """Fixe la norme du vecteur"""
        self._x, self._y = float(expect(value, Real)) * self.normalized

    # ======================================== OPERATIONS ========================================
    def __add__(self, other: Vector) -> Vector:
        """Somme de vecteurs"""
        if isinstance(other, Vector):
            return Vector(self._x + other._x, self._y + other._y)
        return NotImplemented
    
    def __sub__(self, other: Vector) -> Vector:
        """Différence de vecteurs"""
        if isinstance(other, Vector):
            return Vector(self._x - other._x, self._y - other._y)
        return NotImplemented
    
    def __mul__(self, other: Real) -> Vector:
        """Multiplication par un scalaire"""
        if isinstance(other, Real):
            return Vector(self._x * float(other), self._y * float(other))
        return NotImplemented
    
    def __rmul__(self, other: Real) -> Vector:
        """Multiplicaiton par un scalaire (inversée)"""
        if isinstance(other, Real):
            return Vector(self._x * float(other), self._y * float(other))
        return NotImplemented
    
    def __truediv__(self, other: Real) -> Vector:
        """Division par un scalaire"""
        if isinstance(other, Real):
            if other == 0:
                raise ZeroDivisionError("Cannot divide by zero")
            return Vector(self._x / float(other), self._y / float(other))
        if isinstance(other, Vector):
            return other.__rtruediv__(self)
        return NotImplemented
    
    def __rtruediv__(self, other: Vector) -> float:
        """Rapport scalaire entre deux vecteurs colinéaires"""
        if isinstance(other, Vector):
            if self.is_null():
                raise ZeroDivisionError("Cannot divide by null vector")
            if not self.is_collinear(other):
                raise RuntimeError("Cannot divide by a non-collinear vector")
            if self._x != 0:
                return other._x / self._x
            elif self._y != 0:
                return other._y / self._y
        return NotImplemented
    
    def __matmul__(self, other: Vector) -> float:
        """Produit scalaire"""
        if isinstance(other, Vector):
            return self._dot(other)
        return NotImplemented
    
    def __xor__(self, other: Vector) -> float:
        """Produit vectoriel"""
        if isinstance(other, Vector):
            return self._cross(other)
        return NotImplemented
    
    def __pos__(self) -> Vector:
        """Renvoie une copie du vecteur"""
        return self.copy()
    
    def __neg__(self) -> Vector:
        """Renvoie le vecteur opposé"""
        return Vector(-self._x, -self._y)
    
    # ======================================== COMPARATORS ========================================
    def __eq__(self, other: Vector) -> bool:
        """Vérifie la correspondance de deux vecteurs"""
        if isinstance(other, Vector):
            return self._x == other._x and self._y == other._y
        return False
    
    # ======================================== PREDICATES ========================================
    def is_null(self) -> bool:
        """Vérifie que le vecteur soit nul"""
        return self._x == 0 and self._y == 0
    
    def __bool__(self) -> bool:
        """Vérifie que le vecteur ne soit pas nul"""
        return not self.is_null()
    
    def is_orthogonal(self, vector: Vector) -> bool:
        """
        Vérifie l'orthogonalité avec un autre vecteur

        Args:
            vector(Vector): vecteur à tester
        """
        return self._is_orthogonal(expect(vector, Vector))
    
    def is_collinear(self, vector: Vector) -> bool:
        """
        Vérifie la colinéarité avec un autre vecteur

        Args:
            vector(Vector): vecteur à tester
        """
        return self._is_collinear(expect(vector, Vector))
    
    # ======================================== PUBLIC METHODS ========================================
    def copy(self) -> Vector:
        """Renvoie une copie"""
        return Vector(self._x, self._y)
    
    def normalize(self):
        """Normalise le vecteur"""
        self.norm = 1.0
    
    def dot(self, vector: Vector) -> float:
        """
        Renvoie le produit scalaire avec un autre vecteur

        Args:
            vector(Vector): second vecteur
        """
        return self._dot(expect(vector, Vector))
    
    def cross(self, vector: Vector) -> float:
        """
        Renvoie le produit vectoriel avec un autre vecteur

        Args:
            vector(Vector): second vecteur
        """
        return self._cross(expect(vector, Vector))
    
    def angle_with(self, vector: Vector) -> float:
        """
        Renvoie l'angle avec un autre vecteur en radians

        Args:
            vector(Vector): second vecteur
        """
        expect(vector, Vector)
        if self.is_null() or vector.is_null():
            raise ValueError("Cannot compute angle with null vector")
        return self._angle_with(vector)
    
    def projection(self, vector: Vector) -> Vector:
        """
        Renvoie le projeté vectoriel sur le vecteur donné

        Args:
            vector(Vector): vecteur de projeté
        """
        expect(vector, Vector)
        if vector.is_null():
            raise ValueError("Cannot project on null vector")
        return self._projection(vector)
    
    def distance(self, vector: Vector) -> float:
        """
        Renvoie la distance euclidienne à un autre vecteur

        Args:
            vector(Vector): vecteur cible
        """
        return self._distance(expect(vector, Vector))

    # ======================================== INTERNAL METHODS ========================================
    def _is_orthogonal(self, vector: Vector) -> bool:
        """Vérifie l'orthogonalité"""
        return self._dot(vector) == 0
    
    def _is_collinear(self, vector: Vector) -> bool:
        """Vérifie la colinéarité"""
        return self._cross(vector) == 0
    
    def _dot(self, vector: Vector) -> float:
        """Produit scalaire"""
        return self._x * vector._x + self._y * vector._y
    
    def _cross(self, vector: Vector) -> float:
        """Produit vectoriel"""
        return self._x * vector._y - self._y * vector._x
    
    def _angle_with(self, vector: Vector) -> float:
        """Distance angulaire"""
        return acos(max(-1.0, min(1.0, self._dot(vector) / (self.norm * vector.norm))))
    
    def _projection(self, vector: Vector) -> Vector:
        """Projeté vectoriel"""
        return (self._dot(vector) / vector._dot(vector)) * vector
    
    def _distance(self, vector: Vector) -> float:
        """Distance euclidienne"""
        return (self - vector).norm