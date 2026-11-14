"""Three-valued world W : Locus x Property -> {present, absent, unknown}.

Only located quotes write cells. Silence is ``unknown``, not deviation: this
is the open-world departure from nyaya_validity.derive_verdict.

Independence: two loci whose S-evidence is the same span of text are one
observation, not two. Corroboration and deviation are counted over distinct
evidence, and a "locus" that merely re-quotes the subject's own statement is
not a corroborating example.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .schema import (
    HETU,
    PAKSA,
    SADHYA,
    Avayava,
    Cell,
    Defeater,
    Fact,
    Polarity,
    Resolution,
    Source,
)

Span = tuple  # (source_id, start, end) or (source_id, normalised quote) when ungrounded


def span_of(f: Fact) -> Span:
    if f.start is not None:
        return (f.source_id, f.start, f.end)
    return (f.source_id, " ".join(f.quote.split()))


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
    evidence: dict[tuple[str, str], frozenset] = field(default_factory=dict)
    defeaters: list[Defeater] = field(default_factory=list)  # located only
    # G sub-score bookkeeping over the distinct premise facts proposed
    weight_total: float = 0.0
    weight_located: float = 0.0

    def get(self, locus: str, prop: str) -> Cell:
        return self.cells.get((locus, prop), Cell.unknown)

    def loci(self) -> list[str]:
        return sorted({l for l, _ in self.cells})


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
    ev: dict[tuple[str, str], set] = {}
    full_present: set[tuple[str, str]] = set()
    part_present: set[tuple[str, str]] = set()
    counted: set[tuple] = set()
    for locus_id, fact in _premise_facts(avayava, paksa):
        # a fact repeated verbatim (same property, polarity and words) is one fact
        dedupe = (fact.prop, fact.polarity, fact.source_id, " ".join(fact.quote.split()))
        if dedupe not in counted:
            counted.add(dedupe)
            w.weight_total += fact.weight
            if fact.located:
                w.weight_located += fact.weight
        if not fact.located:
            continue
        key = (locus_id, fact.prop)
        seen.setdefault(key, set()).add(fact.polarity)
        ev.setdefault(key, set()).add(span_of(fact))
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
        w.evidence[key] = frozenset(ev[key])
    w.partial = {k for k in part_present - full_present if w.cells.get(k) is Cell.present}

    mention = avayava.pratijna.paksa_mention
    if mention is not None and mention.located and mention.source_id == "T":
        w.paksa_located = True

    w.defeaters = [d for d in defeaters if d.quote.located]
    return w


def counts(w: World3, hetu: str = HETU, sadhya: str = SADHYA) -> dict[str, int]:
    """n_plus (sapaksa), n_minus (deviating), and the number of H-loci whose S
    cell is known -- each counted over DISTINCT S-evidence, so the same passage
    filed under two locus names is one observation. A locus whose S-evidence is
    the subject's own is the subject, not a corroborating example."""
    p_ev = w.evidence.get((w.paksa, sadhya), frozenset())
    groups: dict[tuple, str] = {}  # (cell, evidence) -> representative locus
    for l in w.loci():
        if w.get(l, hetu) is not Cell.present:
            continue
        cell = w.get(l, sadhya)
        if cell is Cell.unknown:
            continue
        e = w.evidence.get((l, sadhya), frozenset())
        is_p = l == w.paksa or (e and e == p_ev)
        key = ("p",) if is_p else (cell, e or l)
        if is_p and l != w.paksa and ("p",) in groups:
            continue
        groups.setdefault(key, l if not is_p else w.paksa)
    n_plus = sum(1 for k in groups if k != ("p",) and k[0] is Cell.present)
    n_minus = sum(1 for k in groups if k != ("p",) and k[0] is Cell.absent)
    p_known = w.get(w.paksa, hetu) is Cell.present and w.get(w.paksa, sadhya) is not Cell.unknown
    if p_known and w.get(w.paksa, sadhya) is Cell.absent:
        n_minus += 1
    return {"n_plus": n_plus, "n_minus": n_minus, "known": n_plus + n_minus + (
        1 if p_known and w.get(w.paksa, sadhya) is Cell.present else 0)}
