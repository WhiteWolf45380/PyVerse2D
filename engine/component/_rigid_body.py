# ======================================== IMPORTS ========================================
from .._internal import expect, clamped, positive
from .._core import Component

from numbers import Real
from typing import Iterator

# ======================================== COMPONENT ========================================
class RigidBody(Component):
    """Composant gérant un corps dynamique"""
    __slots__ = ("_mass", "_friction", "_restitution", "_gravity", "_gravity_scale")
    requires = ("Transform",)

    def __init__(
            self,
            mass: Real = 0.0,
            friction: Real = 0.5,
            restitution: Real = 0.0,
            gravity: bool = True,
            gravity_scale: Real = 1.0,
        ):
        """
        Args:
            mass(Real, optional): masse du corps (0 ou inf pour un corps statique)
            friction(float, optional): résistance au glissement
            restitution(float, optional): facteur de rebond
            gravity(bool, optional): soumission à la gravité
            gravity_scale(Real, optional): facteur de gravité
        """
        self._mass: float = float(positive(expect(mass, Real)))
        self._friction: float = float(clamped(expect(friction, Real)))
        self._restitution: float = float(positive(expect(restitution, Real)))
        self._gravity: bool = expect(gravity, bool)
        self._gravity_scale: float = float(expect(gravity_scale, Real))

    # ======================================== CONVERSIONS ========================================
    def __repr__(self):
        """Renvoie une représentation du composant"""
        return f"RigidBody(mass={self._mass}, friction={self._friction}, restitution={self._restitution}, gravity={self._gravity}, gravity_scale={self._gravity_scale})"
    
    def __iter__(self) -> Iterator:
        """Renvoie le composant dans un itérateur"""
        return iter(self.to_tuple())
    
    def __hash__(self) -> int:
        """Renvoie l'entier hashé du composant"""
        return hash(self.to_tuple())
    
    def to_tuple(self) -> tuple[float, float, float, bool, float]:
        """Renvoie le composant sous forme de tuple"""
        return (self._mass, self._friction, self._restitution, self._gravity, self._gravity_scale)
    
    def to_list(self) -> list:
        """Renvoie le composant sous forme de liste"""
        return [self._mass, self._friction, self._restitution, self._gravity, self._gravity_scale]
    
    # ======================================== GETTERS ========================================
    @property
    def mass(self) -> float:
        """Renvoie la masse du corps"""
        return self._mass

    @property
    def friction(self) -> float:
        """Renvoie le facteur de friction du corps"""
        return self._friction
    
    @property
    def restitution(self) -> float:
        """Renvoie le facteur de restitution du corps"""
        return self._restitution
    
    @property
    def gravity_scale(self) -> float:
        """Renvoie le facteur de gravité"""
        return self._gravity_scale

    # ======================================== SETTERS ========================================
    @mass.setter
    def mass(self, value: Real):
        """Fixe la masse du corps"""
        self._mass = float(positive(expect(value, Real)))

    @friction.setter
    def friction(self, value: Real):
        """Fixe le facteur de friction du corps"""
        self._friction = float(clamped(expect(value, Real)))
    
    @restitution.setter
    def restitution(self, value: Real):
        """Fixe le facteur de restitution du corps"""
        self._restitution = float(positive(expect(value, Real)))
    
    @gravity_scale.setter
    def gravity_scale(self, value: Real):
        """Fixe le facteur de gravité"""
        self._gravity_scale = float(expect(value, Real))
    
    # ======================================== PREDICATES ========================================
    def is_static(self) -> bool:
        """Vérifie si le corps est statique"""
        return self._mass == 0 or self._mass == float("inf")
    
    def is_gravitational(self) -> bool:
        """Vérifie la soumission à la gravité"""
        return self._gravity
    
    # ======================================== PUBLIC METHODS ========================================
    def enable_gravity(self):
        """Active la gravité"""
        self._gravity = True
    
    def disable_gravity(self):
        """Désactive la gravité"""
        self._gravity = False