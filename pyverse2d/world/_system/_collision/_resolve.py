# ======================================== IMPORTS ========================================
from __future__ import annotations

from dataclasses import dataclass
from math import acos as _acos, degrees as _degrees

from ...._internal import Pipeline
from ....math import Vector
from ..._component import Transform, RigidBody, GroundSensor
from ._constants import (
    _SLOP, _BAUMGARTE, _MAX_CORRECTION, _MAX_MASS_RATIO,
    _RESTITUTION_THRESHOLD, _RESTITUTION_MAX_VEL,
)

# ======================================== CACHED CONTACT ========================================
class CachedContact:
    """
    Impulsions accumulées + normale lissée pour une paire de contacts persistante

    Args:
        jn: impulsion normale accumulée (>= 0)
        jt: impulsion tangentielle accumulée (cône de Coulomb)
        normal: normale lissée entre frames
    """
    __slots__ = ("jn", "jt", "normal")

    def __init__(self):
        self.jn: float = 0.0
        self.jt: float = 0.0
        self.normal: tuple | None = None

# ======================================== CONTEXTE ========================================
@dataclass
class ResolveContext:
    """Contexte partagé entre les étapes du solver"""
    a: object
    b: object
    contact: object
    cached: CachedContact
    dt: float
    has_rb_a: bool = False
    has_rb_b: bool = False
    rb_a: RigidBody | None = None
    rb_b: RigidBody | None = None
    static_a: bool = False
    static_b: bool = False
    inv_a: float = 0.0
    inv_b: float = 0.0
    inv_sum: float = 0.0
    tr_a: Transform | None = None
    tr_b: Transform | None = None
    nx: float = 0.0
    ny: float = 0.0
    tx: float = 0.0
    ty: float = 0.0
    depth: float = 0.0
    rel_vx: float = 0.0
    rel_vy: float = 0.0
    vel_along: float = 0.0
    j_delta_n: float = 0.0
    j_delta_t: float = 0.0

    @staticmethod
    def build(a, b, contact, cached: CachedContact, dt: float) -> ResolveContext | None:
        """Construit le contexte — retourne None si la paire est non résoluble"""
        has_rb_a = a.has(RigidBody)
        has_rb_b = b.has(RigidBody)
        rb_a = a.get(RigidBody) if has_rb_a else None
        rb_b = b.get(RigidBody) if has_rb_b else None
        static_a = (not has_rb_a) or rb_a.is_static()
        static_b = (not has_rb_b) or rb_b.is_static()
        if static_a and static_b:
            return None
        nx, ny = contact.normal.x, contact.normal.y
        depth = contact.depth
        inv_a = inv_b = inv_sum = 0.0
        rel_vx = rel_vy = vel_along = 0.0
        if has_rb_a and has_rb_b:
            inv_a = 0.0 if static_a else 1.0 / rb_a.mass
            inv_b = 0.0 if static_b else 1.0 / rb_b.mass
            inv_sum = inv_a + inv_b
            vax = rb_a.velocity.x + (rb_a._acceleration.x * dt if not static_a else 0.0)
            vay = rb_a.velocity.y + (rb_a._acceleration.y * dt if not static_a else 0.0)
            vbx = rb_b.velocity.x + (rb_b._acceleration.x * dt if not static_b else 0.0)
            vby = rb_b.velocity.y + (rb_b._acceleration.y * dt if not static_b else 0.0)
            rel_vx = vax - vbx
            rel_vy = vay - vby
            vel_along = rel_vx * nx + rel_vy * ny
        return ResolveContext(
            a=a, b=b, contact=contact, cached=cached, dt=dt,
            has_rb_a=has_rb_a, has_rb_b=has_rb_b,
            rb_a=rb_a, rb_b=rb_b,
            static_a=static_a, static_b=static_b,
            inv_a=inv_a, inv_b=inv_b, inv_sum=inv_sum,
            tr_a=a.get(Transform), tr_b=b.get(Transform),
            nx=nx, ny=ny, tx=-ny, ty=nx, depth=depth,
            rel_vx=rel_vx, rel_vy=rel_vy, vel_along=vel_along,
        )

# ======================================== PIPELINE ========================================
resolve_pipeline = Pipeline("resolve")

@resolve_pipeline.step
def _wake(ctx: ResolveContext):
    """Réveil des corps endormis"""
    if ctx.has_rb_a and ctx.rb_a.is_sleeping():
        ctx.rb_a.wake()
    if ctx.has_rb_b and ctx.rb_b.is_sleeping():
        ctx.rb_b.wake()

@resolve_pipeline.step
def _position_only(ctx: ResolveContext):
    """Cas sans RigidBody des deux côtés : correction de position uniquement"""
    if ctx.has_rb_a and ctx.has_rb_b:
        return
    correction = min(max(ctx.depth - _SLOP, 0.0) * _BAUMGARTE, _MAX_CORRECTION)
    if correction > 0:
        if ctx.static_a:
            ctx.tr_b.x -= ctx.nx * correction
            ctx.tr_b.y -= ctx.ny * correction
        else:
            ctx.tr_a.x += ctx.nx * correction
            ctx.tr_a.y += ctx.ny * correction
    return False

@resolve_pipeline.step
def _check_inv_sum(ctx: ResolveContext):
    """Court-circuit si masses infinies des deux côtés"""
    if ctx.inv_sum == 0:
        return False

@resolve_pipeline.step
def _baumgarte(ctx: ResolveContext):
    """Correction de position Baumgarte si les objets se rapprochent"""
    if ctx.vel_along >= 0:
        return
    correction = min(max(ctx.depth - _SLOP, 0.0) * _BAUMGARTE, _MAX_CORRECTION)
    if correction <= 0:
        return
    if ctx.static_a:
        ctx.tr_b.x -= ctx.nx * correction
        ctx.tr_b.y -= ctx.ny * correction
    elif ctx.static_b:
        ctx.tr_a.x += ctx.nx * correction
        ctx.tr_a.y += ctx.ny * correction
    else:
        ra = min(ctx.inv_a / ctx.inv_sum, _MAX_MASS_RATIO)
        rb = min(ctx.inv_b / ctx.inv_sum, _MAX_MASS_RATIO)
        ctx.tr_a.x += ctx.nx * correction * ra
        ctx.tr_a.y += ctx.ny * correction * ra
        ctx.tr_b.x -= ctx.nx * correction * rb
        ctx.tr_b.y -= ctx.ny * correction * rb

@resolve_pipeline.step
def _normal_impulse(ctx: ResolveContext):
    """Calcul et clamping de l'impulsion normale avec restitution"""
    if not ctx.static_a and not ctx.static_b:
        restitution = min(ctx.rb_a.restitution, ctx.rb_b.restitution)
    elif ctx.static_a:
        restitution = ctx.rb_b.restitution
    else:
        restitution = ctx.rb_a.restitution
    if ctx.vel_along < -_RESTITUTION_THRESHOLD:
        # Impact significatif : restitution scalée selon la vitesse
        t = min((-ctx.vel_along - _RESTITUTION_THRESHOLD) / (_RESTITUTION_MAX_VEL - _RESTITUTION_THRESHOLD), 1.0)
        j_delta_n = -(1.0 + restitution * t) * ctx.vel_along / ctx.inv_sum
    elif ctx.vel_along < 0:
        # Approche lente : correction de penetration sans restitution
        bias = _BAUMGARTE * max(ctx.depth - _SLOP, 0.0)
        j_delta_n = -(ctx.vel_along + bias) / ctx.inv_sum
    else:
        # Objet qui s'eloigne : pas d'impulsion
        j_delta_n = 0.0
    # Clamping : pas de traction
    old_jn = ctx.cached.jn
    ctx.cached.jn = max(0.0, old_jn + j_delta_n)
    ctx.j_delta_n = ctx.cached.jn - old_jn

@resolve_pipeline.step
def _friction(ctx: ResolveContext):
    """Calcul de la friction tangentielle avec gestion surfaces verticales et stability_angle"""
    if abs(ctx.ny) < 0.3:
        # Surface verticale : pas de friction tangentielle
        ctx.cached.jt = 0.0
        ctx.j_delta_t = 0.0
        return
    if not ctx.static_a and not ctx.static_b:
        friction_dynamic = (ctx.rb_a.friction + ctx.rb_b.friction) * 0.5
    elif ctx.static_a:
        friction_dynamic = ctx.rb_b.friction
    else:
        friction_dynamic = ctx.rb_a.friction
    # Friction statique selon stability_angle
    surface_angle = _degrees(_acos(min(abs(ctx.ny), 1.0)))
    stability_angle = 75.0
    for entity in (ctx.a, ctx.b):
        if entity.has(GroundSensor):
            stability_angle = entity.get(GroundSensor).stability_angle
            break
    friction_static = 0.0 if surface_angle > stability_angle else friction_dynamic * 1.5
    vel_tan = ctx.rel_vx * ctx.tx + ctx.rel_vy * ctx.ty
    j_delta_t_needed = -vel_tan / ctx.inv_sum
    old_jt = ctx.cached.jt
    # Choix friction statique ou dynamique selon le cone de Coulomb
    if abs(j_delta_t_needed) <= friction_static * ctx.cached.jn:
        ctx.cached.jt = max(-friction_static * ctx.cached.jn, min(friction_static * ctx.cached.jn, old_jt + j_delta_t_needed))
    else:
        ctx.cached.jt = max(-friction_dynamic * ctx.cached.jn, min(friction_dynamic * ctx.cached.jn, old_jt + j_delta_t_needed))
    ctx.j_delta_t = ctx.cached.jt - old_jt

@resolve_pipeline.step
def _apply(ctx: ResolveContext):
    """Application des impulsions normale et tangentielle"""
    ix = ctx.nx * ctx.j_delta_n + ctx.tx * ctx.j_delta_t
    iy = ctx.ny * ctx.j_delta_n + ctx.ty * ctx.j_delta_t
    if not ctx.static_a:
        ctx.rb_a.velocity = Vector(ctx.rb_a.velocity.x + ix * ctx.inv_a, ctx.rb_a.velocity.y + iy * ctx.inv_a)
    if not ctx.static_b:
        ctx.rb_b.velocity = Vector(ctx.rb_b.velocity.x - ix * ctx.inv_b, ctx.rb_b.velocity.y - iy * ctx.inv_b)

# ======================================== FACADE ========================================
def resolve(a, b, contact, cached: CachedContact, dt: float):
    """Sequential Impulse Solver avec vitesse prédictive"""
    ctx = ResolveContext.build(a, b, contact, cached, dt)
    if ctx is None:
        return
    resolve_pipeline.run(ctx)