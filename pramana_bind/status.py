"""Support status: the reader-facing outcome, kept apart from the Nyaya verdict.

Why a separate layer. The verdict rules decide a finite world. In an open
world, "one corroborating example and no observed counterexample" (R8) does
not establish an unrestricted natural-language claim, so R8 is never by itself
'supported'. A citation is 'supported' only when the cited source is on
record -- by a located quote -- as stating S of p, at the claimed strength,
with nothing located that cuts against it.

Everything here is a deterministic function of the grounded tuple. It is
therefore replayable, and it is exactly as right as the extractor's filing of
each quote (which subject, which polarity, which strength). That filing is
testimony and is not checked here.
"""
from __future__ import annotations

from .ground import NEG_FLAG, QUAL_FLAG
from .retreat import M_LADDER, Q_LADDER
from .schema import HETU, SADHYA, Avayava, Cell, Fact, Polarity, SupportStatus, Verdict
from .world import World3, counts

#: plain-language reason -> the Nyaya term it corresponds to (secondary label)
NYAYA_TERM = {
    "source_not_located": "(none: no evidence either way)",
    "subject_not_in_source": "asiddha / asraya",
    "claim_not_stated_in_source": "asiddha / svarupa",
    "finite_rule_pass_only": "anumana only: vyapti not established in an open world",
    "narrower_subject": "asiddha / bhaga",
    "quantifier_inflated": "asiddha / bhaga",
    "modality_inflated": "sadhya stronger than the source's",
    "qualification_omitted": "sopadhika (conditioned) hetu",
    "exception_in_source": "savyabhicara",
    "conflicting_statements": "(source both asserts and denies)",
    "source_denies_claim": "viruddha",
    "reason_proves_opposite": "viruddha",
    "overridden_by_higher_authority": "badhita",
    "contested_by_equal_source": "satpratipaksa",
    NEG_FLAG: "(lexical guard)",
    QUAL_FLAG: "(lexical guard)",
}


def _fact_reasons(f: Fact, av: Avayava, guard: bool) -> list[str]:
    r = []
    if f.scope != "full":
        r.append("narrower_subject")
    cq, cm = av.pratijna.quantifier, av.pratijna.modality
    if f.quantifier is not None and Q_LADDER.index(f.quantifier) > Q_LADDER.index(cq):
        r.append("quantifier_inflated")
    if f.modality is not None and M_LADDER.index(f.modality) > M_LADDER.index(cm):
        r.append("modality_inflated")
    if guard:
        r.extend(fl for fl in f.flags if fl in (NEG_FLAG, QUAL_FLAG))
    return r


def support_status(av: Avayava, world: World3, verdict: Verdict, rule: str,
                   guard: bool = True) -> tuple[SupportStatus, list[str]]:
    p = world.paksa
    if rule == "R0":
        return SupportStatus.unresolved, ["source_not_located"]
    if (p, SADHYA) in world.conflicts:
        return SupportStatus.not_established, ["conflicting_statements"]
    if world.get(p, SADHYA) is Cell.absent:
        return SupportStatus.contradicted, ["source_denies_claim"]
    if rule == "R3":
        return SupportStatus.contradicted, ["overridden_by_higher_authority"]
    if rule == "R4":
        return SupportStatus.contradicted, ["reason_proves_opposite"]
    if not world.paksa_located:
        return SupportStatus.not_established, ["subject_not_in_source"]

    direct = [f for l in av.udaharana.loci if l.id == p for f in l.facts
              if f.prop == SADHYA and f.polarity is Polarity.present and f.located and f.source_id == "T"]
    if not direct:
        reasons = ["claim_not_stated_in_source"] + (["finite_rule_pass_only"] if rule == "R8" else [])
    else:
        reasons = min((_fact_reasons(f, av, guard) for f in direct), key=len)
    if any(c.located for c in av.conditions):
        reasons.append("qualification_omitted")
    if counts(world, HETU, SADHYA)["n_minus"] > 0:
        reasons.append("exception_in_source")
    if any(d.authority_rank == world.cited_rank and d.inference_valid for d in world.defeaters):
        reasons.append("contested_by_equal_source")
    return (SupportStatus.not_established, reasons) if reasons else (SupportStatus.supported, [])
