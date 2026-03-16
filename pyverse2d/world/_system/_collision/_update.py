# ======================================== IMPORTS ========================================
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from ...._internal import Pipeline
from ....math import Vector
from ..._world import World
from ..._component import Transform, Collider, GroundSensor
from ._registry import dispatch, Contact, world_center
from ._spatial_hash import SpatialHash
from ._resolve import CachedContact, resolve
from ._warm_start import warm_start
from ._constants import _EXTRA_ITER_THRESHOLD, _EXTRA_ITER

# ======================================== CONTEXTE ========================================
@dataclass
class UpdateContext:
    """Contexte partagé entre les étapes du update"""
    world: World
    dt: float
    hash: SpatialHash | None
    cache: dict
    iterations: int
    entities: list = field(default_factory=list)
    pairs: list = field(default_factory=list)
    active_contacts: list = field(default_factory=list)
    active_keys: set = field(default_factory=set)
    max_depth: float = 0.0

    @staticmethod
    def build(world: World, dt: float, hash: SpatialHash | None, cache: dict, iterations: int) -> UpdateContext:
        """Construit le contexte update"""
        return UpdateContext(world=world, dt=dt, hash=hash, cache=cache, iterations=iterations)

# ======================================== PIPELINE ========================================
update_pipeline = Pipeline("update")

@update_pipeline.step
def _query_entities(ctx: UpdateContext):
    """Récupération des entités avec Collider et Transform"""
    ctx.entities = ctx.world.query(Collider, Transform)

@update_pipeline.step
def _reset_sensors(ctx: UpdateContext):
    """Reset du GroundSensor avant détection"""
    for entity in ctx.entities:
        if entity.has(GroundSensor):
            gs = entity.get(GroundSensor)
            gs._grounded = False
            gs._ground_normal = None

@update_pipeline.step
def _broadphase(ctx: UpdateContext):
    """Broadphase : génération des paires candidates"""
    if ctx.hash is not None:
        if ctx.hash._cell_size is None:
            ctx.hash.calibrate(ctx.entities)
        ctx.hash.update_dynamic(ctx.entities)
        ctx.pairs = ctx.hash.get_pairs()
    else:
        n = len(ctx.entities)
        ctx.pairs = [(ctx.entities[i], ctx.entities[j]) for i in range(n) for j in range(i + 1, n)]

@update_pipeline.step
def _narrowphase(ctx: UpdateContext):
    """Narrowphase : détection, lissage des normales, warm start"""
    for a, b in ctx.pairs:
        col_a: Collider = a.get(Collider)
        col_b: Collider = b.get(Collider)
        if not col_a.is_active() or not col_b.is_active():
            continue
        if not col_a.collides_with(col_b):
            continue
        contact = _detect(col_a, a.get(Transform), col_b, b.get(Transform))
        if contact is None:
            continue
        if col_a.is_trigger() or col_b.is_trigger():
            continue
        # Gestion du cache de contacts persistants
        ia, ib = id(a), id(b)
        key = (ia, ib) if ia < ib else (ib, ia)
        ctx.active_keys.add(key)
        if key not in ctx.cache:
            ctx.cache[key] = CachedContact()
        cached = ctx.cache[key]
        # Lissage de la normale entre frames
        nx, ny = contact.normal.x, contact.normal.y
        if cached.normal is not None:
            pnx, pny = cached.normal
            dot = nx * pnx + ny * pny
            if dot > 0.95:
                mix = 0.7
                mnx = nx * mix + pnx * (1.0 - mix)
                mny = ny * mix + pny * (1.0 - mix)
                n_len = sqrt(mnx * mnx + mny * mny) or 1.0
                nx, ny = mnx / n_len, mny / n_len
            elif dot < 0:
                # Normale inversée : reset des impulsions accumulées
                cached.jn = 0.0
                cached.jt = 0.0
        cached.normal = (nx, ny)
        contact = Contact(Vector(nx, ny), contact.depth)
        # Actualisation du GroundSensor selon la normale du contact
        _update_ground_sensor(a, b, nx, ny)
        if contact.depth > ctx.max_depth:
            ctx.max_depth = contact.depth
        ctx.active_contacts.append((a, b, contact, cached))
        # Application du warm start
        warm_start(a, b, contact, cached)

@update_pipeline.step
def _cleanup_cache(ctx: UpdateContext):
    """Nettoyage des contacts inactifs"""
    for key in list(ctx.cache):
        if key not in ctx.active_keys:
            del ctx.cache[key]

@update_pipeline.step
def _solve(ctx: UpdateContext):
    """Résolution itérative des contacts"""
    iterations = ctx.iterations
    if ctx.max_depth > _EXTRA_ITER_THRESHOLD:
        iterations += _EXTRA_ITER
    for _ in range(iterations):
        for a, b, contact, cached in ctx.active_contacts:
            resolve(a, b, contact, cached, ctx.dt)

# ======================================== HELPERS ========================================
def _detect(col_a: Collider, tr_a: Transform, col_b: Collider, tr_b: Transform) -> Contact | None:
    """Broadphase AABB puis dispatch narrowphase"""
    cx_a, cy_a = world_center(col_a.shape, tr_a, col_a.offset)
    cx_b, cy_b = world_center(col_b.shape, tr_b, col_b.offset)
    ax_min, ay_min, ax_max, ay_max = col_a.shape.world_bounding_box(cx_a, cy_a, tr_a.scale, tr_a.rotation)
    bx_min, by_min, bx_max, by_max = col_b.shape.world_bounding_box(cx_b, cy_b, tr_b.scale, tr_b.rotation)
    if ax_min > bx_max or bx_min > ax_max or ay_min > by_max or by_min > ay_max:
        return None
    return dispatch(col_a.shape, cx_a, cy_a, tr_a.scale, tr_a.rotation,
                    col_b.shape, cx_b, cy_b, tr_b.scale, tr_b.rotation)

def _update_ground_sensor(a, b, nx: float, ny: float):
    """Actualisation du GroundSensor selon la normale du contact"""
    if ny > 0 and a.has(GroundSensor):
        gs = a.get(GroundSensor)
        if ny >= gs._threshold:
            gs._grounded = True
            gs._ground_normal = Vector(nx, ny)
    if ny < 0 and b.has(GroundSensor):
        gs = b.get(GroundSensor)
        if -ny >= gs._threshold:
            gs._grounded = True
            gs._ground_normal = Vector(-nx, -ny)