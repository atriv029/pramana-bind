"""Verdict rules R0-R8. Pure function of the world; no model call.

Order is load-bearing, as in nyaya_validity.derive_verdict.
"""
from __future__ import annotations

from typing import Iterable, Optional

from .schema import HETU, SADHYA, AsiddhaSubtype, Cell, Defeater, Resolution, Verdict
from .world import World3, counts

Result = tuple[Verdict, str, Optional[AsiddhaSubtype]]


def derive_full(
    world: World3,
    paksa: Optional[str] = None,
    sadhya: str = SADHYA,
    hetu: str = HETU,
    defeaters: Optional[Iterable[Defeater]] = None,
) -> Result:
    p = paksa or world.paksa
    ds = list(world.defeaters if defeaters is None else defeaters)
    ds = [d for d in ds if d.quote.located]

    if world.resolution is not Resolution.located:
        return Verdict.unresolved, "R0", None
    if not world.paksa_located:
        return Verdict.asiddha, "R1", AsiddhaSubtype.asraya
    if world.get(p, hetu) is not Cell.present:
        return Verdict.asiddha, "R2", AsiddhaSubtype.svarupa
    if (p, hetu) in world.partial:
        return Verdict.asiddha, "R2b", AsiddhaSubtype.bhaga
    if any(d.authority_rank > world.cited_rank for d in ds):
        return Verdict.badhita, "R3", None

    c = counts(world, hetu, sadhya)
    if c["n_minus"] > 0 and c["n_plus"] == 0 and c["n_minus"] == c["known"]:
        return Verdict.viruddha, "R4", None
    if c["n_minus"] > 0:
        return Verdict.savyabhicara, "R5", None
    if any(d.authority_rank == world.cited_rank and d.inference_valid for d in ds):
        return Verdict.satpratipaksa, "R6", None
    if c["n_plus"] == 0:
        return Verdict.uncorroborated, "R7", None
    return Verdict.valid, "R8", None


def derive_ow(
    world: World3,
    paksa: Optional[str] = None,
    sadhya: str = SADHYA,
    hetu: str = HETU,
    defeaters: Optional[Iterable[Defeater]] = None,
) -> tuple[Verdict, str]:
    v, rule, _ = derive_full(world, paksa, sadhya, hetu, defeaters)
    return v, rule
