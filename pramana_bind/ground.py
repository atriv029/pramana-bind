"""Grounding: every quote the extractor proposed is located by
``pravrudhi.application.nyaya_quote.locate_quote`` (pre-existing), which
computes the offsets itself and never repairs a quote.

Unlocated facts are kept with ``located=False`` rather than deleted, so the G
sub-score has its denominator and the certificate shows what was refused and
why. ``build_world`` ignores them: a fact without a located quote does not
enter the world.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Iterable

from pravrudhi.application.nyaya_quote import locate_quote

from .schema import Avayava, Defeater, Quote


def ground_quote(q: Quote, texts: Mapping[str, str]) -> tuple[Quote, str]:
    """Return a copy with system offsets (or cleared ones) and the locator's reason."""
    loc = locate_quote(texts, fact_id=q.source_id, quote=q.quote)
    upd = (
        {"located": True, "start": loc.start, "end": loc.end, "offsets_source": "system"}
        if loc.valid
        else {"located": False, "start": None, "end": None, "offsets_source": None}
    )
    return q.model_copy(update=upd), loc.reason


def ground(avayava: Avayava, texts: Mapping[str, str]) -> tuple[Avayava, dict[str, str]]:
    """Ground every quote in the avayava. Returns (grounded copy, {path: reason})."""
    av = avayava.model_copy(deep=True)
    reasons: dict[str, str] = {}
    if av.pratijna.paksa_mention is not None:
        av.pratijna.paksa_mention, reasons["pratijna.paksa_mention"] = ground_quote(
            av.pratijna.paksa_mention, texts)
    if av.upanaya is not None:
        av.upanaya, reasons["upanaya"] = ground_quote(av.upanaya, texts)
    for locus in av.udaharana.loci:
        for i, f in enumerate(locus.facts):
            locus.facts[i], reasons[f"udaharana.{locus.id}.{i}"] = ground_quote(f, texts)
    return av, reasons


def ground_defeaters(defeaters: Iterable[Defeater], texts: Mapping[str, str]
                     ) -> tuple[list[Defeater], dict[str, str]]:
    out, reasons = [], {}
    for i, d in enumerate(defeaters):
        q, reasons[f"defeaters.{i}"] = ground_quote(d.quote, texts)
        out.append(d.model_copy(update={"quote": q}))
    return out, reasons
