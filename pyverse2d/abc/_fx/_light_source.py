# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import Positionnal
from ...math import Vector, Point
from ...math.easing import EasingFunc, is_easing, linear
from ...asset import Color

from abc import ABC
from dataclasses import dataclass
from numbers import Real

# ======================================== REQUEST ========================================
@dataclass(slots=True)
class AttachRequest:
    target: Positionnal
    offset: Vector
    smoothing: float

# ======================================== ABSTRACT CLASS ========================================
class LightSource(ABC):
    """Classe abstraite des sources de lumière

    Args:
        position: position
        color: couleur de la lumière émise
        intensity: intensité lumineuse
        falloff: fonction d'atténuation
        enable: activation initiale de la lumière
    """
    __slots__ = (
        "_position",
        "_color", "_intensity", "_falloff",
        "_enabled",
        "_attach",
    )

    def __init__(
            self,
            position: Point = (0.0, 0.0),
            color: Color = (255, 255, 255),
            intensity: Real = 1.0,
            falloff: EasingFunc = None,
            enabled: bool = True,
        ):
        # Paramètres publiques
        self._position: Point = Point(position)
        self._color: Color = Color(color)
        self._intensity: float = float(intensity)
        self._falloff: EasingFunc = falloff
        self._enabled: bool = enabled

        if __debug__:
            if not 0.0 <= self._intensity <= 1.0: raise ValueError("intensity must be within 0.0 and 1.0")
            if self._falloff is not None and not is_easing(self._falloff): raise ValueError("falloff must be an EasingFunc from pv.math.easing module or None")
            if not isinstance(enabled, bool): raise TypeError(f"enabled must be a boolean, got {type(self._enabled).__name__}")

        # Paramètres internes
        self._attach: AttachRequest | None = None

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position

        La position peut être un objet ``Point`` ou un tuple ``(x, y)``.
        """
        return self._position
    
    @position.setter
    def position(self, value: Point) -> None:
        self._position.x, self._position.y = value

    @property
    def x(self) -> float:
        """Position horizontale

        La coordonnée doit être un ``Réel``.
        """
        return self._position.x
    
    @x.setter
    def x(self, value: Real) -> None:
        self._position.x = value

    @property
    def y(self) -> float:
        """Position verticale

        La coordonnée doit être un ``Réel``.
        """
        return self._position.y
    
    @y.setter
    def y(self, value: Real) -> None:
        self._position.y = value

    @property
    def color(self) -> Color:
        """Couleur de la lumière

        La couleur peut être un objet ``Color`` ou n'importe quel tuple ``(r, g, b)``.
        Le canal alpha n'est pas pris en considération dans la couleur.
        """
        return self._color
    
    @color.setter
    def color(self, value: Color) -> None:
        self._color = Color(value)

    @property
    def intensity(self) -> float:
        """Intensité lumineuse

        L'intensité doit être un ``Réel``compris dans l'intervalle *[0, 1]*.
        Mettre cette propriété à 1.0 pour une intensité maximale.
        """
        return self._intensity
    
    @intensity.setter
    def intensity(self, value: Real) -> None:
        value = float(value)
        assert 0.0 <= value <= 1.0, f"intensity must be within 0.0 and 1.0, got {value}"
        self._intensity = value
    
    @property
    def falloff(self) -> EasingFunc:
        """Fonction d'atténuation

        La fonction doit être une ``EasingFunc``du module math.easing.
        Mettre cette propriété à None pour un éclairage constant.
        """
        return self._falloff
    
    @falloff.setter
    def falloff(self, value: EasingFunc) -> None:
        assert value is None or is_easing(value), "falloff must be an EasingFunc from math.easing module or None"
        self._falloff = value

    @property
    def enabled(self) -> bool:
        """Renvoie l'état d'activation de la lumière

        L'état doit être un booléen.
        """
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        assert isinstance(value, bool), f"enabled must be a boolean, got {type(value).__name__}"
        self._enabled = value

    # ======================================== STATE ========================================
    def enable(self) -> None:
        """Active la lumière"""
        self._enabled = True

    def disable(self) -> None:
        """Désactive la lumière"""
        self._enabled = False

    def toggle(self) -> None:
        """Bascule l'activation de la lumière"""
        self._enabled = not self._enabled

    def is_enabled(self) -> bool:
        """Vérifie l'activation de la lumière"""
        return self._enabled

    # ======================================== ATTACH ========================================
    def attach_to(
            self,
            target: Positionnal,
            offset: Vector = (0.0, 0.0),
            smoothing: Real = 0.0,
        ) -> None:
        """Attache la source lumineuse à un objet positionnel

        Args:
            target: cible d'attache
            offset: décalage par rapport à la cible
            smoothing: facteur de retard *[0, 1[*
        """
        offset = Vector(offset)
        smoothing = float(smoothing)
        assert 0.0 <= smoothing < 1.0, f"smoothing must be within 0.0 and 1.0 excluded"
        self._attach = AttachRequest(target, offset, smoothing)
    
    def detach(self) -> None:
        """Met fin à l'attache de la source lumineuse"""
        self._attach = None

    def is_attached(self) -> bool:
        """Vérifie si la source est attachée"""
        return self._attach is not None
    
    def attach_target(self) -> Positionnal:
        """Renvoie la cible de l'attache"""
        if self._attach is None:
            return None
        return self._attach.target

    # ======================================== LIFE CYCLE ========================================
    def update(self, dt: float) -> None:
        """Actualisation"""
        if self._attach is not None:
            self._update_attach(dt)
        self._update(dt)

    def _update(self, dt: float) -> None:
        """Actualisation personnalisée (à override)"""
        pass

    def _update_attach(self, dt: float) -> None:
        """Actualisation de l'attache"""
        target = self._attach.target
        offset = self._attach.offset
        smoothing = self._attach.smoothing

        # Calcul de la position cible
        target_x, target_y = target.x + offset.x, target.y + offset.y
        t = 1 - smoothing ** dt

        # Calcul de la position intermédiaire
        x = self._position.x + (target_x - self._position.x) * t
        y = self._position.y + (target_y - self._position.y) * t

        # Mise à jour de la position
        self._position.x = x
        self._position.y = y