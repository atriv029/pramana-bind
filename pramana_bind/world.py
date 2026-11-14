"""Three-valued world W : Locus x Property -> {present, absent, unknown}.

Only located quotes write cells. Silence is ``unknown``, not deviation: this
is the open-world departure from nyaya_validity.derive_verdict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .schema import (
    HETU,
    PAKSA,
    Avayava,
    Cell,
    Defeater,
    Fact,
    Polarity,
    Resolution,
    Source,
)


@dataclass
class World3:
    cells: dict[tuple[str, str], Cell] = field(default_factory=dict)
    paksa: str = PAKSA
    resolution: Resolution = Resolution.located
    paksa_located: bool = False
    cited_rank: int = 0
    # cells whose only 'present' evidence covers a proper part of the locus
    partial: set[tuple[str, str]] = field(default_factory=set)
    # cells with located quotes on both sides; held at unknown and reported
    conflicts: set[tuple[str, str]] = field(default_factory=set)
    defeaters: list[Defeater] = field(default_factory=list)  # located only
    # G sub-score bookkeeping over the premise facts the extractor proposed
    weight_total: float = 0.0
    weight_located: float = 0.0

    def get(self, locus: str, prop: str) -> Cell:
        return self.cells.get((locus, prop), Cell.unknown)

    def loci(self) -> list[str]:
        return sorted({l for l, _ in self.cells})

    def has_unknown(self, props: Iterable[str]) -> bool:
        return any(self.get(l, p) is Cell.unknown for l in self.loci() for p in props)


def _premise_facts(av: Avayava, paksa: str) -> list[tuple[str, Fact]]:
    out: list[tuple[str, Fact]] = []
    if av.upanaya is not None:
        out.append((paksa, av.upanaya))
    for locus in av.udaharana.loci:
        out.extend((locus.id, f) for f in locus.facts)
    return out


def build_world(
    avayava: Avayava,
    defeaters: Iterable[Defeater] = (),
    source: Optional[Source] = None,
    paksa: str = PAKSA,
) -> World3:
    """Build the world from a *grounded* avayava (``located`` flags set)."""
    src = source or Source()
    w = World3(paksa=paksa, resolution=src.resolution, cited_rank=src.authority_rank)

    seen: dict[tuple[str, str], set[Polarity]] = {}
    full_present: set[tuple[str, str]] = set()
    part_present: set[tuple[str, str]] = set()
    for locus_id, fact in _premise_facts(avayava, paksa):
        w.weight_total += fact.weight
        if not fact.located:
            continue
        w.weight_located += fact.weight
        key = (locus_id, fact.prop)
        seen.setdefault(key, set()).add(fact.polarity)
        if fact.polarity is Polarity.present:
            (part_present if fact.scope == "part" else full_present).add(key)
        if locus_id == paksa and fact.source_id == "T":
            w.paksa_located = True

    for key, pols in seen.items():
        if len(pols) == 2:
            w.conflicts.add(key)
            w.cells[key] = Cell.unknown
        else:
            w.cells[key] = Cell(next(iter(pols)).value)
    w.partial = {k for k in part_present - full_present if w.cells.get(k) is Cell.present}

    mention = avayava.pratijna.paksa_mention
    if mention is not None and mention.located and mention.source_id == "T":
        w.paksa_located = True

    w.defeaters = [d for d in defeaters if d.quote.located]
    return w


def counts(w: World3, hetu: str = HETU, sadhya: str = "S") -> dict[str, int]:
    """n_plus (sapaksa), n_minus (vipaksa where H strays), and the number of
    H-loci whose S cell is known."""
    h_plus = [l for l in w.loci() if w.get(l, hetu) is Cell.present]
    n_plus = sum(1 for l in h_plus if l != w.paksa and w.get(l, sadhya) is Cell.present)
    n_minus = sum(1 for l in h_plus if w.get(l, sadhya) is Cell.absent)
    known = sum(1 for l in h_plus if w.get(l, sadhya) is not Cell.unknown)
    return {"n_plus": n_plus, "n_minus": n_minus, "known": known}
