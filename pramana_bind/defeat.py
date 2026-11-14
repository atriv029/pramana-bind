"""Counter-source retrieval. BM25 (pre-existing ``nyaya.Corpus``) finds
candidates; a model proposes a denying quote; the quote is then located
mechanically like any other. Authority rank is a table, not a model opinion.
"""
from __future__ import annotations

import json
from typing import Optional

from pravrudhi.application.nyaya import Corpus

from .extract import AskFn, _json_object
from .schema import Defeater, Pratijna, Quote

#: Larger outranks smaller. The Constitution over statute; the 2023 codes
#: (in force 1 July 2024) over the IPC they replaced. Adjust before freezing.
STATUTE_RANK = {"COI": 3, "BNS": 2, "BNSS": 2, "BSA": 2, "IPC": 1}
DEFAULT_RANK = 0

DEFEAT_PROMPT = """Below is a claim and one other legal text. Decide only whether the TEXT states something \
that cannot be true together with the claim: it denies the claim ("not_S") or asserts something incompatible \
of the same subject ("incompatible"). Silence is not denial. If it does, copy the denying passage \
character-for-character from the TEXT.

Return one JSON object and nothing else:
{"denies": true|false, "conclusion": "not_S"|"incompatible"|null, "quote": str|null}

CLAIM: {paksa} -- {sadhya}

TEXT [{doc_id}]
<<<{text}>>>
"""


def rank_of(doc_id: str) -> int:
    return STATUTE_RANK.get(doc_id.split("/", 1)[0], DEFAULT_RANK)


def find_defeaters(pratijna: Pratijna, corpus: Corpus, ask_fn: AskFn,
                   cited_id: Optional[str] = None, k: int = 4
                   ) -> tuple[list[Defeater], dict[str, str]]:
    """Returns (ungrounded defeaters, {source_id: text}). Pass both to ``bind``."""
    defeaters: list[Defeater] = []
    texts: dict[str, str] = {}
    for doc, score in corpus.retrieve(f"{pratijna.paksa} {pratijna.sadhya}", k=k + 1):
        if doc.id == cited_id or len(defeaters) >= k:
            continue
        prompt = (DEFEAT_PROMPT.replace("{paksa}", pratijna.paksa).replace("{sadhya}", pratijna.sadhya)
                  .replace("{doc_id}", doc.id).replace("{text}", doc.text))
        try:
            o = _json_object(ask_fn(prompt))
        except (ValueError, json.JSONDecodeError):
            continue
        if not o.get("denies") or not o.get("quote"):
            continue
        texts[doc.id] = doc.text
        defeaters.append(Defeater(
            quote=Quote(quote=o["quote"], source_id=doc.id),
            authority_rank=rank_of(doc.id),
            conclusion=o.get("conclusion") if o.get("conclusion") in ("not_S", "incompatible") else "not_S",
            source={"locator": doc.id, "act": doc.act, "section": doc.section, "bm25": score},
        ))
    return defeaters, texts
