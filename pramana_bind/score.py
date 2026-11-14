"""Per-citation binding score PBS = G * V * D in [0, 1].

For ranking and thresholds only; the categorical verdict stays strict.
"""
from __future__ import annotations

from .schema import HETU, SADHYA, Verdict
from .world import World3, counts


def pbs(world: World3, verdict: Verdict, lam: float = 3.0,
        hetu: str = HETU, sadhya: str = SADHYA) -> dict[str, float]:
    if lam < 1:
        raise ValueError("lambda must be >= 1")
    # G (paksadharmata): share of proposed premise facts whose quote located
    g = 0.0
    if world.paksa_located and world.weight_total > 0:
        g = world.weight_located / world.weight_total
    # V (vyapti)
    c = counts(world, hetu, sadhya)
    v = c["n_plus"] / (c["n_plus"] + lam * c["n_minus"] + 1)
    # D (non-defeat), from the located defeaters rather than the final verdict,
    # so an asiddha citation that is also overruled still shows D = 0.
    ds = world.defeaters
    badhita = verdict is Verdict.badhita or any(
        d.authority_rank > world.cited_rank for d in ds)
    satprati = verdict is Verdict.satpratipaksa or any(
        d.authority_rank == world.cited_rank and d.inference_valid for d in ds)
    d = 1.0 - max(0.0, 0.5 * satprati, 1.0 * badhita)
    return {"G": g, "V": v, "D": d, "value": g * v * d}
