"""The pipeline: decompose -> ground -> world -> derive -> status -> certificate body."""
from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Mapping
from typing import Any, Iterable, Optional

from .certificate import make_body
from .extract import PROMPT_SHA256, AskFn, Extraction, decompose
from .ground import ground, ground_defeaters
from .schema import Avayava, Defeater, Hetu, Nigamana, Pratijna, Resolution, Source, SupportStatus
from .score import pbs
from .status import support_status
from .verdict import derive_full
from .world import build_world

FAILED = "extraction_failed"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def conclude(avayava: Avayava, defeaters: Iterable[Defeater], source: Source,
             texts: Mapping[str, str], lam: float = 3.0, *, grounding: bool = True,
             guard: bool = True) -> tuple[Avayava, list[Defeater], dict[str, str]]:
    """Ground, build the world, derive verdict and status. Pure: no model call.
    ``audit`` repeats exactly this from the stored quotes and source texts.

    ``grounding=False`` and ``guard=False`` are ablations."""
    av, reasons = ground(avayava, texts, grounding)
    ds, dreasons = ground_defeaters(defeaters, texts, grounding)
    world = build_world(av, ds, source)
    verdict, rule, subtype = derive_full(world)
    status, why = support_status(av, world, verdict, rule, guard)
    av.nigamana = Nigamana(verdict=verdict, subtype=subtype, rule=rule, status=status, reasons=why,
                           pbs=pbs(world, verdict, lam))
    return av, ds, {**reasons, **dreasons}


def decide(run_statuses: list[str]) -> str:
    """Item-level decision over the extraction runs (fixed before the held-out
    evaluation): 'supported' needs a strict majority of ALL runs, failed runs
    included; otherwise the most common non-supported status, ties going to
    not_established. All runs failed -> extraction_failed."""
    n = len(run_statuses)
    if n and run_statuses.count("supported") * 2 > n:
        return "supported"
    rest = [s for s in run_statuses if s not in ("supported", FAILED)]
    if not rest:
        return FAILED if run_statuses and all(s == FAILED for s in run_statuses) else "not_established"
    tally = Counter(rest)
    top = max(tally.values())
    winners = [s for s in tally if tally[s] == top]
    return winners[0] if len(winners) == 1 else "not_established"


def bind_extractions(claim: str, source_text: str, extractions: list[Extraction], *,
                     citation_raw: str = "", source: Optional[Source] = None,
                     defeaters: Iterable[Defeater] = (), counter_texts: Optional[Mapping[str, str]] = None,
                     lam: float = 3.0, model: str = "", grounding: bool = True, guard: bool = True,
                     document_sha256: Optional[str] = None, claim_span: Optional[tuple[int, int]] = None,
                     ) -> tuple[dict[str, Any], dict[str, str]]:
    """Everything after the model calls. Deterministic given the extractions, so
    ablations can be re-run over the same raw model output."""
    src = (source or Source()).model_copy()
    texts = {"T": source_text, **(counter_texts or {})}
    src.text_sha256 = sha256_text(source_text)
    subject = {"document_sha256": document_sha256, "claim_span": list(claim_span) if claim_span else None,
               "claim_text": claim, "citation_raw": citation_raw}
    runs = []
    for ex in extractions:
        if ex.avayava is None:
            runs.append((FAILED, None))
            continue
        av, ds, reasons = conclude(ex.avayava, defeaters, src, texts, lam, grounding=grounding, guard=guard)
        runs.append((av.nigamana.status.value, (av, ds, reasons)))
    statuses = [s for s, _ in runs]
    final = decide(statuses)
    extraction = {
        "provenance": "agama", "gen_ai.request.model": model, "runs": len(runs),
        "run_statuses": statuses,
        "run_verdicts": [p[0].nigamana.verdict.value if p else FAILED for _, p in runs],
        # stability, not confidence: the share of runs that reached the reported status
        "status_agreement": statuses.count(final) / len(runs) if runs else None,
        "unstable": len(set(statuses)) > 1,
        "decision_rule": "supported iff strict majority of runs; else modal non-supported status",
        "prompt_sha256": PROMPT_SHA256,
        "grounding": grounding, "context_guard": guard,
    }
    if final == FAILED:
        raise ExtractionError([ex.error for ex in extractions])
    rep = next((p for s, p in runs if s == final and p), None) or next(p for _, p in runs if p)
    av, ds, reasons = rep
    extraction["representative_run"] = next(i for i, (_, p) in enumerate(runs) if p is rep)
    if av.nigamana.status.value != final:  # only when the tie rule chose not_established
        extraction["tie_broken_to"] = final
    used = {"T"} | {d.quote.source_id for d in ds}
    hashes = {sid: sha256_text(texts[sid]) for sid in used if sid in texts}
    body = make_body(subject, src, av, ds, hashes, reasons, lam, extraction, final_status=final)
    return body, {h: texts[sid] for sid, h in hashes.items()}


def bind(claim: str, source_text: Optional[str], ask_fn: AskFn, *,
         citation_raw: str = "", source: Optional[Source] = None, n_runs: int = 3, **kw: Any,
         ) -> tuple[dict[str, Any], dict[str, str]]:
    """Returns (certificate body, {sha256: text} for every text it quotes).

    ``source_text=None`` (or a source whose resolution is not 'located') yields
    an ``unresolved`` certificate without calling the model: not finding a
    source is no evidence about the citation either way.
    """
    src = (source or Source()).model_copy()
    if source_text is None and src.resolution is Resolution.located:
        src.resolution = Resolution.not_located
    if src.resolution is not Resolution.located:
        lam = kw.get("lam", 3.0)
        av = Avayava(pratijna=Pratijna(paksa="", sadhya=claim), hetu=Hetu(text=""))
        world = build_world(av, (), src)
        verdict, rule, subtype = derive_full(world)
        status, why = support_status(av, world, verdict, rule)
        av.nigamana = Nigamana(verdict=verdict, subtype=subtype, rule=rule, status=status, reasons=why,
                               pbs=pbs(world, verdict, lam))
        subject = {"document_sha256": kw.get("document_sha256"), "claim_span": None,
                   "claim_text": claim, "citation_raw": citation_raw}
        body = make_body(subject, src, av, [], {}, {}, lam,
                         {"provenance": "agama", "gen_ai.request.model": kw.get("model", ""), "runs": 0,
                          "run_statuses": [], "status_agreement": None, "unstable": False,
                          "prompt_sha256": PROMPT_SHA256, "grounding": True, "context_guard": True},
                         final_status=SupportStatus.unresolved.value)
        return body, {}
    exs = decompose(claim, source_text, ask_fn, n_runs, citation_raw)
    return bind_extractions(claim, source_text, exs, citation_raw=citation_raw, source=src, **kw)


class ExtractionError(RuntimeError):
    """No extractor run returned a parseable tuple."""
