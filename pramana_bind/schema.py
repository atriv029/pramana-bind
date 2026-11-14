"""Data model for a claim-citation pair decomposed into the five-member inference.

Everything here that carries a quote is model testimony (agama) until
``located`` is set by the grounding step. Only located quotes enter the world.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = "2"
RULES_VERSION = "R0-R8+status/2"

HETU = "H"
SADHYA = "S"
PAKSA = "p"


class Polarity(str, Enum):
    present = "present"
    absent = "absent"


class Cell(str, Enum):
    present = "present"
    absent = "absent"
    unknown = "unknown"


class Quantifier(str, Enum):
    all = "all"
    most = "most"
    some = "some"
    one = "one"


class Modality(str, Enum):
    certain = "certain"
    probable = "probable"
    possible = "possible"


class Verdict(str, Enum):
    valid = "valid"
    unresolved = "unresolved"  # R0: not a fallacy; no evidence either way
    asiddha = "asiddha"
    badhita = "badhita"
    viruddha = "viruddha"
    savyabhicara = "savyabhicara"
    satpratipaksa = "satpratipaksa"
    uncorroborated = "uncorroborated"  # aprasiddha


class SupportStatus(str, Enum):
    """The reader-facing outcome. Distinct from the Nyaya verdict: 'valid' under
    the finite-world rules (R8) is NOT by itself 'supported'."""

    supported = "supported"
    not_established = "not_established"
    contradicted = "contradicted"
    unresolved = "unresolved"


class AsiddhaSubtype(str, Enum):
    asraya = "asraya"  # R1: the subject is not identifiable in the source
    svarupa = "svarupa"  # R2: the source does not put H at p
    bhaga = "bhaga"  # R2b: H holds only of a proper part of p


class Resolution(str, Enum):
    located = "located"
    not_located = "not_located"
    ambiguous = "ambiguous"


class Quote(BaseModel):
    """A verbatim span proposed by the extractor. Offsets are never taken from
    the model: grounding computes them and sets ``offsets_source='system'``."""

    quote: str
    source_id: str = "T"  # "T" is the cited source; others are counter-sources
    start: Optional[int] = None
    end: Optional[int] = None
    offsets_source: Optional[Literal["system"]] = None
    located: bool = False
    # Derived by grounding, never by the model:
    match: Optional[Literal["exact", "whitespace_collapsed", "ungrounded"]] = None
    flags: list[str] = Field(default_factory=list)  # quote-context cues, see ground.py


class Fact(Quote):
    prop: str  # HETU, SADHYA, or a free property name
    polarity: Polarity
    # 'part' = the quote asserts the property of a proper part of the locus
    # (R2b). This is extractor testimony; the quote is checked, the scope
    # judgement is not.
    scope: Literal["full", "part"] = "full"
    weight: float = 1.0  # w_i in the G sub-score
    # Strength of the SOURCE statement as the extractor reads it (testimony).
    # Compared mechanically with the claim's quantifier/modality.
    quantifier: Optional[Quantifier] = None
    modality: Optional[Modality] = None


class Condition(Quote):
    """A qualification the source attaches to the statement that the claim
    leaves out (time limit, precondition, exception). Extractor testimony;
    only the quote is checked."""

    kind: Literal["temporal", "condition", "exception", "other"] = "other"
    text: str = ""


class Locus(BaseModel):
    id: str
    label: str = ""
    facts: list[Fact] = Field(default_factory=list)


class Pratijna(BaseModel):
    paksa: str
    sadhya: str
    quantifier: Quantifier = Quantifier.all
    modality: Modality = Modality.certain
    # A span of T that identifies the subject. R1 fires when neither this nor
    # any fact about p is located in T.
    paksa_mention: Optional[Quote] = None


class Hetu(BaseModel):
    text: str


class Udaharana(BaseModel):
    vyapti: str = ""
    loci: list[Locus] = Field(default_factory=list)


class Nigamana(BaseModel):
    verdict: Verdict
    subtype: Optional[AsiddhaSubtype] = None
    rule: str
    status: SupportStatus = SupportStatus.unresolved
    reasons: list[str] = Field(default_factory=list)
    pbs: dict[str, float] = Field(default_factory=dict)


class Avayava(BaseModel):
    pratijna: Pratijna
    hetu: Hetu
    udaharana: Udaharana = Field(default_factory=Udaharana)
    upanaya: Optional[Fact] = None  # "H holds of p, in this source"
    conditions: list[Condition] = Field(default_factory=list)
    nigamana: Optional[Nigamana] = None  # derived, never extracted


class Source(BaseModel):
    locator: str = ""
    retrieved_at: Optional[str] = None
    text_sha256: Optional[str] = None
    resolution: Resolution = Resolution.located
    authority_rank: int = 0  # larger = more authoritative


class Defeater(BaseModel):
    """A counter-source that concludes not-S (or an incompatible S') of p.

    ``kind`` is what the retriever/extractor proposed. The verdict ignores it
    and decides badhita vs satpratipaksa from ``authority_rank`` alone.
    """

    quote: Quote
    authority_rank: int
    conclusion: Literal["not_S", "incompatible"] = "not_S"
    inference_valid: bool = True  # R6 needs an independently valid inference
    kind: Optional[Literal["satpratipaksa", "badhita"]] = None
    source: dict = Field(default_factory=dict)
