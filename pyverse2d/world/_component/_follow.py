# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._internal import expect, clamped, over, positive
from ...abc import Component
from ...math import Vector

from typing import TYPE_CHECKING, Iterator
from numbers import Real

if TYPE_CHECKING:
    from .._entity import Entity

# ======================================== COMPONENT ========================================
class Follow(Component):
    """``Component`` gérant le suivi

    Ce composant est manipulé par ``SteeringSystem``.

    Args:
        entity: ``Entité`` à suivre
        offset: ``Vecteur`` de décalage par rapport à la cible
        force: force d'attraction en Newtons
        smoothing: facteur de retard relatif [0, 1[
        radius_min: borne intérieure de la zone acceptable — en dessous, force répulsive.
                    Doit être inférieur ou égal à radius_max.
        radius_max: borne extérieure de la zone acceptable — au delà, force attractive.
                    0 = pile sur la cible.
        dot_min: composante alignée minimale acceptable par rapport à l'offset [-1, 1].
                 1 = exactement dans la direction de l'offset, -1 = direction opposée.
        cross_min: composante latérale minimale acceptable par rapport à l'offset [-1, 1].
                   0 = aligné, -1 = 90° à droite.
        cross_max: composante latérale maximale acceptable par rapport à l'offset [-1, 1].
                   0 = aligné, 1 = 90° à gauche.
        axis_x: activer le suivi horizontal
        axis_y: activer le suivi vertical
        noise_amplitude: amplitude du bruit de déplacement en unités monde. 0 = pas de bruit
        noise_frequency: fréquence du bruit en Hz — plus élevé = mouvement plus rapide
    """
    __slots__ = (
        "_entity", "_offset",
        "_force", "_smoothing",
        "_radius_min", "_radius_max",
        "_dot_min", "_cross_min", "_cross_max",
        "_axis_x", "_axis_y",
        "_noise_amplitude", "_noise_frequency",
        "_noise_t",
    )
    requires = ("Transform",)

    def __init__(
            self,
            entity: Entity,
            offset: Vector = (0.0, 0.0),
            force: Real = 5000.0,
            smoothing: Real = 0.0,
            radius_min: Real = 0.0,
            radius_max: Real = 0.0,
            dot_min: Real = -1.0,
            cross_min: Real = -1.0,
            cross_max: Real = 1.0,
            axis_x: bool = True,
            axis_y: bool = True,
            noise_amplitude: Real = 0.0,
            noise_frequency: Real = 1.0,
        ):
        from .._entity import Entity
        self._entity: Entity = expect(entity, Entity)
        self._offset: Vector = Vector(offset)
        self._force: float = over(float(expect(force, Real)), 0.0, include=False)
        self._smoothing: float = clamped(float(expect(smoothing, Real)), include_max=False)
        r_min = abs(float(expect(radius_min, Real)))
        r_max = abs(float(expect(radius_max, Real)))
        self._radius_min: float = r_min
        self._radius_max: float = r_max
        self._dot_min: float = float(clamped(expect(dot_min, Real)))
        self._cross_min: float = float(clamped(expect(cross_min, Real)))
        self._cross_max: float = float(clamped(expect(cross_max, Real)))
        self._axis_x: bool = expect(axis_x, bool)
        self._axis_y: bool = expect(axis_y, bool)
        self._noise_amplitude: float = abs(float(expect(noise_amplitude, Real)))
        self._noise_frequency: float = over(float(expect(noise_frequency, Real)), 0.0, include=False)
        self._noise_t: float = 0.0

        assert r_min > r_max, ValueError(f"radius_min ({r_min}) doit être inférieur ou égal à radius_max ({r_max})")
        assert self._entity.has("Transform"), ValueError(f"Entity {self._entity.id}... has no Transform component")

    # ======================================== CONVERSIONS ========================================
    def __repr__(self) -> str:
        """Renvoie une représentation du composant"""
        return f"Follow(entity={self._entity.id[:8]}..., offset={self._offset}, force={self._force})"

    def __iter__(self) -> Iterator:
        """Renvoie les attributs dans un itérateur"""
        return iter(self.get_attributes())

    def __hash__(self) -> int:
        """Renvoie le hash du composant"""
        return hash(self.get_attributes())

    def get_attributes(self) -> tuple:
        """Renvoie les attributs du composant"""
        return (
            self._entity, self._offset,
            self._force, self._smoothing,
            self._radius_min, self._radius_max,
            self._dot_min, self._cross_min, self._cross_max,
            self._axis_x, self._axis_y,
            self._noise_amplitude, self._noise_frequency,
        )

    # ======================================== PROPERTIES ========================================
    @property
    def entity(self) -> Entity:
        """Entité à suivre

        L'entité doit être un objet ``Entity`` avec un composant ``Transform``.
        """
        return self._entity

    @entity.setter
    def entity(self, value: Entity) -> None:
        from .._entity import Entity
        self._entity = expect(value, Entity)
        if not self._entity.has("Transform"):
            raise ValueError(f"Entity {self._entity.id}... has no Transform component")

    @property
    def offset(self) -> Vector:
        """Décalage par rapport à la cible

        Le décalage peut être un objet ``Vector`` ou un tuple ``(vx, vy)``.
        """
        return self._offset

    @offset.setter
    def offset(self, value: Vector) -> None:
        self._offset = Vector(value)

    @property
    def force(self) -> float:
        """Force d'attraction

        La force doit être un ``Réel`` positif non nul.
        L'unité est le Newton.
        """
        return self._force

    @force.setter
    def force(self, value: Real) -> None:
        self._force = over(float(expect(value, Real)), 0.0, include=False)

    @property
    def smoothing(self) -> float:
        """Facteur de retard

        Le facteur doit être un ``Réel`` compris dans l'intervalle [0, 1[.
        Plus la valeur est élevée, plus le suivi est progressif.
        """
        return self._smoothing

    @smoothing.setter
    def smoothing(self, value: Real) -> None:
        self._smoothing = clamped(float(expect(value, Real)), include_max=False)

    @property
    def radius_min(self) -> float:
        """Borne intérieure de la zone acceptable

        En dessous de cette distance, une force répulsive est appliquée pour
        ramener l'entité dans la zone. Doit être inférieur ou égal à radius_max.
        """
        return self._radius_min

    @radius_min.setter
    def radius_min(self, value: Real) -> None:
        r = abs(float(expect(value, Real)))
        if r > self._radius_max:
            raise ValueError(f"radius_min ({r}) doit être inférieur ou égal à radius_max ({self._radius_max})")
        self._radius_min = r

    @property
    def radius_max(self) -> float:
        """Borne extérieure de la zone acceptable

        Au delà de cette distance, une force attractive est appliquée.
        0 = pile sur la cible. Doit être supérieur ou égal à radius_min.
        """
        return self._radius_max

    @radius_max.setter
    def radius_max(self, value: Real) -> None:
        r = abs(float(expect(value, Real)))
        if r < self._radius_min:
            raise ValueError(f"radius_max ({r}) doit être supérieur ou égal à radius_min ({self._radius_min})")
        self._radius_max = r

    @property
    def dot_min(self) -> float:
        """Composante alignée minimale acceptable

        Défini l'angle minimal acceptable par rapport à la direction de l'offset.
        1 = exactement dans la direction de l'offset, -1 = direction opposée.
        """
        return self._dot_min

    @dot_min.setter
    def dot_min(self, value: Real) -> None:
        self._dot_min = float(clamped(expect(value, Real)))

    @property
    def cross_min(self) -> float:
        """Composante latérale minimale acceptable

        Défini la déviation latérale minimale acceptable par rapport à l'offset.
        0 = aligné, -1 = 90° à droite.
        """
        return self._cross_min

    @cross_min.setter
    def cross_min(self, value: Real) -> None:
        self._cross_min = float(clamped(expect(value, Real)))

    @property
    def cross_max(self) -> float:
        """Composante latérale maximale acceptable

        Défini la déviation latérale maximale acceptable par rapport à l'offset.
        0 = aligné, 1 = 90° à gauche.
        """
        return self._cross_max

    @cross_max.setter
    def cross_max(self, value: Real) -> None:
        self._cross_max = float(clamped(expect(value, Real)))

    @property
    def axis_x(self) -> bool:
        """Suivi horizontal actif

        Si False, l'entité ne suit pas la cible horizontalement.
        """
        return self._axis_x

    @axis_x.setter
    def axis_x(self, value: bool) -> None:
        self._axis_x = expect(value, bool)

    @property
    def axis_y(self) -> bool:
        """Suivi vertical actif

        Si False, l'entité ne suit pas la cible verticalement.
        """
        return self._axis_y

    @axis_y.setter
    def axis_y(self, value: bool) -> None:
        self._axis_y = expect(value, bool)

    @property
    def noise_amplitude(self) -> float:
        """Amplitude du bruit de déplacement

        Défini l'amplitude maximale du bruit organique appliqué à l'offset cible.
        0 = pas de bruit, exprimé en unités monde.
        """
        return self._noise_amplitude

    @noise_amplitude.setter
    def noise_amplitude(self, value: Real) -> None:
        self._noise_amplitude = abs(float(expect(value, Real)))

    @property
    def noise_frequency(self) -> float:
        """Fréquence du bruit

        Défini la vitesse d'évolution du bruit organique.
        Plus la valeur est élevée, plus le mouvement est rapide.
        L'unité est le Hz.
        """
        return self._noise_frequency

    @noise_frequency.setter
    def noise_frequency(self, value: Real) -> None:
        self._noise_frequency = over(float(expect(value, Real)), 0.0, include=False)