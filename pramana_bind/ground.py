"""Grounding: every quote the extractor proposed is located by
``pravrudhi.application.nyaya_quote.locate_quote`` (pre-existing), which
computes the offsets itself and never repairs a quote.

What grounding establishes: the quoted characters occur, once, in the supplied
text. What it does NOT establish: that the quote means what the extractor
filed it under, or that it is about the claimed subject. The context flags
below are a cheap lexical guard against two specific failures (a negation or a
qualifier sitting in the same sentence but outside the quote); they are
heuristics, not semantic checks.

Unlocated facts are kept with ``located=False`` so the certificate shows what
was refused and why. ``build_world`` ignores them.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Iterable

from pravrudhi.application.nyaya_quote import locate_quote

from .schema import Avayava, Defeater, Quote

_BOUNDARY = ".!?;\n"
_NEG = re.compile(r"\b(not|no|never|neither|nor|nothing|none|cannot)\b|n't", re.I)
_QUAL = re.compile(r"\b(unless|except|excepting|provided that|subject to|only if|only when|only where|"
                   r"save as|other than|but not|however|notwithstanding)\b", re.I)

NEG_FLAG = "negation_cue_before_quote"
QUAL_FLAG = "qualifier_cue_outside_quote"


def context_flags(text: str, start: int, end: int) -> list[str]:
    """Lexical cues in the quote's own sentence but outside the quote."""
    s = max(text.rfind(c, 0, start) for c in _BOUNDARY) + 1
    ends = [i for i in (text.find(c, end) for c in _BOUNDARY) if i != -1]
    e = min(ends) if ends else len(text)
    before, after = text[s:start], text[end:e]
    flags = []
    if _NEG.search(before):
        flags.append(NEG_FLAG)
    if _QUAL.search(before) or _QUAL.search(after):
        flags.append(QUAL_FLAG)
    return flags


def ground_quote(q: Quote, texts: Mapping[str, str], grounding: bool = True) -> tuple[Quote, str]:
    """Return a copy with every derived field recomputed, and the locator's reason.

    ``grounding=False`` is the ablation: any non-empty quote is accepted
    unchecked, with no offsets and no context flags."""
    blank = {"located": False, "start": None, "end": None, "offsets_source": None, "match": None, "flags": []}
    if not grounding:
        ok = bool(q.quote and q.quote.strip())
        return q.model_copy(update={**blank, "located": ok, "match": "ungrounded" if ok else None}), \
            "ungrounded" if ok else "empty_quote"
    loc = locate_quote(texts, fact_id=q.source_id, quote=q.quote)
    if not loc.valid:
        return q.model_copy(update=blank), loc.reason
    return q.model_copy(update={
        "located": True, "start": loc.start, "end": loc.end, "offsets_source": "system", "match": loc.match,
        "flags": context_flags(texts[q.source_id], loc.start, loc.end),
    }), loc.reason


def ground(avayava: Avayava, texts: Mapping[str, str], grounding: bool = True
           ) -> tuple[Avayava, dict[str, str]]:
    """Ground every quote in the avayava. Returns (grounded copy, {path: reason})."""
    av = avayava.model_copy(deep=True)
    av.nigamana = None
    reasons: dict[str, str] = {}
    if av.pratijna.paksa_mention is not None:
        av.pratijna.paksa_mention, reasons["pratijna.paksa_mention"] = ground_quote(
            av.pratijna.paksa_mention, texts, grounding)
    if av.upanaya is not None:
        av.upanaya, reasons["upanaya"] = ground_quote(av.upanaya, texts, grounding)
    for locus in av.udaharana.loci:
        for i, f in enumerate(locus.facts):
            locus.facts[i], reasons[f"udaharana.{locus.id}.{i}"] = ground_quote(f, texts, grounding)
    for i, c in enumerate(av.conditions):
        av.conditions[i], reasons[f"conditions.{i}"] = ground_quote(c, texts, grounding)
    return av, reasons


def ground_defeaters(defeaters: Iterable[Defeater], texts: Mapping[str, str], grounding: bool = True
                     ) -> tuple[list[Defeater], dict[str, str]]:
    out, reasons = [], {}
    for i, d in enumerate(defeaters):
        q, reasons[f"defeaters.{i}"] = ground_quote(d.quote, texts, grounding)
        out.append(d.model_copy(update={"quote": q}))
    return out, reasons
