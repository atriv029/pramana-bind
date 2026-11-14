"""Free-text decomposition: claim + cited passage -> five-member tuple.

This is the only step that calls a model. Its output is testimony (agama):
nothing here is trusted until ``ground`` locates each quote. ``ask_fn`` is any
``prompt -> text`` callable, so the extractor model is the caller's choice.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable, Optional

from pydantic import ValidationError

from .schema import (HETU, SADHYA, Avayava, Fact, Hetu, Locus, Modality, Polarity,
                     Pratijna, Quantifier, Quote, Udaharana)

AskFn = Callable[[str], str]

PROMPT = """You are decomposing a claim and the source it cites into a structured inference. \
You do not judge whether the citation supports the claim. You only report what the SOURCE TEXT says, \
and every report must carry a quote copied character-for-character from the SOURCE TEXT. \
A quote that is not an exact substring of the source will be discarded by a string matcher, \
so never paraphrase, never join separate passages, and never quote the claim itself. \
Choose quotes long enough to occur only once in the source.

Definitions
- paksa (p): the subject the claim is about.
- sadhya (S): what the claim asserts of p.
- quantifier: all | most | some | one. modality: certain | probable | possible.
- hetu (H): the reason the source is cited for, i.e. the property of p, stated in the source, that is supposed to establish S.
- upanaya: a quote showing whether the source says H holds of p. polarity "present" if the source asserts it, \
"absent" if the source denies it. scope "part" if the source asserts H only of a narrower subject than p \
(for example the claim says "adults" and the source says "men aged 40-60"); otherwise "full". \
Use null if the source has no such passage.
- loci: every case, group, example, exception or condition in the source (including p itself, with id "p") \
about which the source says whether H or S holds. For each, list facts with prop "H" or "S", \
polarity "present" or "absent", and a quote. An exception or counterexample where H holds but S does not \
is a locus with H present and S absent. Report these even though they cut against the claim. \
Do not invent loci the source does not mention.

Return one JSON object and nothing else:
{"pratijna": {"paksa": str, "sadhya": str, "quantifier": str, "modality": str, "paksa_quote": str|null},
 "hetu": str,
 "vyapti": "wherever H, S" written out for this H and S,
 "upanaya": {"polarity": "present"|"absent", "scope": "full"|"part", "quote": str} | null,
 "loci": [{"id": "p"|"L1"|"L2"..., "label": str,
           "facts": [{"prop": "H"|"S", "polarity": "present"|"absent", "quote": str}]}]}

CLAIM
<<<{claim}>>>

CITATION AS WRITTEN
<<<{citation}>>>

SOURCE TEXT
<<<{source}>>>
"""

PROMPT_SHA256 = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()


@dataclass
class Extraction:
    avayava: Optional[Avayava]
    raw: str
    error: Optional[str] = None


def render_prompt(claim: str, source_text: str, citation: str = "") -> str:
    return PROMPT.replace("{claim}", claim).replace("{citation}", citation).replace("{source}", source_text)


def _json_object(text: str) -> dict:
    i, j = text.find("{"), text.rfind("}")
    if i == -1 or j <= i:
        raise ValueError("no JSON object in reply")
    obj = json.loads(text[i:j + 1])
    if not isinstance(obj, dict):
        raise ValueError("reply is not a JSON object")
    return obj


def parse(raw: str) -> Avayava:
    """Parse one extractor reply. Offsets or 'located' flags in the reply are
    ignored: a model is never asked to count characters."""
    o = _json_object(raw)
    pj = o["pratijna"]
    mention = pj.get("paksa_quote")
    up = o.get("upanaya")
    loci = []
    for l in o.get("loci") or []:
        facts = [
            Fact(prop={"H": HETU, "S": SADHYA}[f["prop"]], polarity=Polarity(f["polarity"]), quote=f["quote"])
            for f in l.get("facts") or [] if f.get("quote")
        ]
        loci.append(Locus(id=str(l["id"]), label=str(l.get("label", "")), facts=facts))
    return Avayava(
        pratijna=Pratijna(
            paksa=pj["paksa"], sadhya=pj["sadhya"],
            quantifier=Quantifier(pj.get("quantifier", "all")),
            modality=Modality(pj.get("modality", "certain")),
            paksa_mention=Quote(quote=mention) if mention else None,
        ),
        hetu=Hetu(text=o.get("hetu") or ""),
        udaharana=Udaharana(vyapti=o.get("vyapti") or "", loci=loci),
        upanaya=Fact(prop=HETU, polarity=Polarity(up["polarity"]), quote=up["quote"],
                     scope=up.get("scope", "full")) if up and up.get("quote") else None,
    )


def decompose(claim: str, source_text: str, ask_fn: AskFn, n_runs: int = 3,
              citation: str = "") -> list[Extraction]:
    """Run the extractor ``n_runs`` times. A reply that does not parse is kept
    as a failed run (it counts against extraction stability)."""
    prompt = render_prompt(claim, source_text, citation)
    out: list[Extraction] = []
    for _ in range(n_runs):
        raw = ask_fn(prompt)
        try:
            out.append(Extraction(parse(raw), raw))
        except (ValueError, KeyError, TypeError, ValidationError) as e:
            out.append(Extraction(None, raw, f"{type(e).__name__}: {e}"))
    return out
