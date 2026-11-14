"""The pipeline: decompose -> ground -> world -> derive -> certificate body."""
from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Mapping
from typing import Any, Iterable, Optional

from .certificate import make_body
from .extract import PROMPT_SHA256, AskFn, decompose
from .ground import ground, ground_defeaters
from .schema import Avayava, Defeater, Nigamana, Resolution, Source
from .score import pbs
from .verdict import derive_full
from .world import build_world

FAILED = "extraction_failed"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def conclude(avayava: Avayava, defeaters: Iterable[Defeater], source: Source,
             texts: Mapping[str, str], lam: float = 3.0
             ) -> tuple[Avayava, list[Defeater], dict[str, str]]:
    """Ground, build the world, derive. Pure: no model call. This is exactly
    what ``audit`` repeats."""
    av, reasons = ground(avayava, texts)
    ds, dreasons = ground_defeaters(defeaters, texts)
    world = build_world(av, ds, source)
    verdict, rule, subtype = derive_full(world)
    av.nigamana = Nigamana(verdict=verdict, subtype=subtype, rule=rule, pbs=pbs(world, verdict, lam))
    return av, ds, {**reasons, **dreasons}


def bind(claim: str, source_text: Optional[str], ask_fn: AskFn, *,
         citation_raw: str = "", source: Optional[Source] = None,
         defeaters: Iterable[Defeater] = (), counter_texts: Optional[Mapping[str, str]] = None,
         n_runs: int = 3, lam: float = 3.0, model: str = "",
         document_sha256: Optional[str] = None, claim_span: Optional[tuple[int, int]] = None,
         ) -> tuple[dict[str, Any], dict[str, str]]:
    """Returns (certificate body, {sha256: text} for every text it quotes).

    ``source_text=None`` (or a source whose resolution is not 'located') yields
    an ``unresolved`` certificate without calling the model: not finding a
    source is no evidence about the citation either way.
    """
    src = (source or Source()).model_copy()
    if source_text is None and src.resolution is Resolution.located:
        src.resolution = Resolution.not_located
    subject = {"document_sha256": document_sha256, "claim_span": list(claim_span) if claim_span else None,
               "claim_text": claim, "citation_raw": citation_raw}

    if src.resolution is not Resolution.located:
        world = build_world(_empty(claim), (), src)
        verdict, rule, subtype = derive_full(world)
        av = _empty(claim)
        av.nigamana = Nigamana(verdict=verdict, subtype=subtype, rule=rule, pbs=pbs(world, verdict, lam))
        body = make_body(subject, src, av, [], {}, {}, lam,
                         {"provenance": "agama", "gen_ai.request.model": model, "runs": 0,
                          "verdict_agreement": None, "unstable": False, "prompt_sha256": PROMPT_SHA256})
        return body, {}

    texts = {"T": source_text, **(counter_texts or {})}
    src.text_sha256 = sha256_text(source_text)
    runs = []
    for ex in decompose(claim, source_text, ask_fn, n_runs, citation_raw):
        if ex.avayava is None:
            runs.append((FAILED, None, ex.error))
            continue
        av, ds, reasons = conclude(ex.avayava, defeaters, src, texts, lam)
        runs.append((av.nigamana.verdict.value, (av, ds, reasons), None))

    tally = Counter(v for v, _, _ in runs)
    # modal verdict; ties broken by first occurrence so the result is order-stable
    modal = max(tally, key=lambda v: (tally[v], -[r[0] for r in runs].index(v)))
    extraction = {
        "provenance": "agama", "gen_ai.request.model": model, "runs": len(runs),
        "run_verdicts": [v for v, _, _ in runs],
        "verdict_agreement": tally[modal] / len(runs),
        "unstable": len(tally) > 1,
        "prompt_sha256": PROMPT_SHA256,
    }
    if modal == FAILED:
        raise ExtractionError([e for _, _, e in runs])
    av, ds, reasons = next(p for v, p, _ in runs if v == modal)
    used = {"T"} | {d.quote.source_id for d in ds}
    hashes = {sid: sha256_text(texts[sid]) for sid in used if sid in texts}
    body = make_body(subject, src, av, ds, hashes, reasons, lam, extraction)
    return body, {h: texts[sid] for sid, h in hashes.items()}


class ExtractionError(RuntimeError):
    """Most extractor runs did not return a parseable tuple."""


def _empty(claim: str) -> Avayava:
    from .schema import Hetu, Pratijna
    return Avayava(pratijna=Pratijna(paksa="", sadhya=claim), hetu=Hetu(text=""))
