"""Schema-3 decision rules on FROZEN structured records (fixtures, not model output), including the
field-level interventions: change one extracted field, hold the rest, check the derivation moves as expected."""
import copy

import pytest

from pramana_bind import certificate as c
from pramana_bind.v3 import decide_b1, decide_n1, make_body_v3

SRC = ("No appeal shall lie from the order of a single Judge. An appeal lies if the High Court certifies the case. "
       "A tenant may terminate on thirty days notice, unless the lease is for a fixed term. "
       "Men aged 40 to 60 showed lower blood pressure. The drug may reduce symptoms.")


def rec(parts=None, evidence=(), qualifiers=(), path="direct_assertion"):
    return {"claim": {"subject": "s", "parts": parts or [{"predicate": "p", "polarity": "affirmative",
            "quantifier": "unspecified", "universal_wording": False, "modality": "certain", "time": None}]},
            "evidence": list(evidence), "qualifiers": list(qualifiers), "inference_path": path}


def ev(quote, stance="affirms", role="bears_on_part", subj="same", part=0, basis="states"):
    return {"part": part, "role": role, "stance": stance, "basis": basis, "subject_match": subj, "quote": quote}


def q(quote, relation, changed="predicate", stated=False, part=0):
    return {"part": part, "relation": relation, "claim_part_changed": changed, "stated_in_claim": stated,
            "text": "", "quote": quote}


A = ev("An appeal lies if the High Court certifies the case")


def st(r, **kw):
    d = decide_n1(r, SRC, **kw)
    return d["status"], d["reasons"]


def test_negative_claim_affirmed_by_negative_sentence():
    r = rec(parts=[{"predicate": "no appeal lies from a single Judge", "polarity": "negative"}],
            evidence=[ev("No appeal shall lie from the order of a single Judge")])
    assert st(r) == ("supported", [])


def test_typed_qualifiers_block_or_not():
    lease = ev("A tenant may terminate on thirty days notice")
    exc = "unless the lease is for a fixed term"
    assert st(rec(evidence=[lease], qualifiers=[q(exc, "exception")])) == ("supported", [])          # default rule
    uni = rec(parts=[{"predicate": "p", "universal_wording": True}], evidence=[lease], qualifiers=[q(exc, "exception")])
    assert st(uni) == ("not_established", ["exception_omitted_from_universal"])
    cond = "if the High Court certifies the case"
    assert st(rec(evidence=[A], qualifiers=[q(cond, "necessary_condition")])) == ("not_established", ["necessary_condition_omitted"])
    assert st(rec(evidence=[A], qualifiers=[q(cond, "necessary_condition", stated=True)])) == ("supported", [])
    assert st(rec(evidence=[A], qualifiers=[q(cond, "incidental_detail")])) == ("supported", [])
    assert st(rec(evidence=[A], qualifiers=[q("not in the source", "necessary_condition")])) == ("supported", [])  # unlocated
    assert st(rec(evidence=[A], qualifiers=[q(cond, "necessary_condition")]), use_qualifiers=False)[0] == "supported"


def test_scope_strength_entity_and_inference_paths():
    assert st(rec(evidence=[ev("Men aged 40 to 60 showed lower blood pressure", subj="narrower")])) == ("not_established", ["scope_extension"])
    assert st(rec(evidence=[ev("The drug may reduce symptoms", stance="weaker")])) == ("not_established", ["strength_inflation"])
    assert st(rec(evidence=[ev("The drug may reduce symptoms", subj="different")])) == ("not_established", ["wrong_entity"])
    assert st(rec(evidence=[ev("The drug may reduce symptoms", basis="suggests")], path="induction")) == ("not_established", ["inferred_only"])
    assert st(rec(evidence=[ev("The drug may reduce symptoms", basis="necessarily_implies")], path="deduction")) == ("supported", [])
    poss = [{"predicate": "p", "modality": "possible"}]   # a possibility claim needs one witness
    assert st(rec(parts=poss, evidence=[A], qualifiers=[q("if the High Court certifies the case", "necessary_condition")])) == ("supported", [])
    assert st(rec(parts=poss, evidence=[ev("Men aged 40 to 60 showed lower blood pressure", subj="narrower")])) == ("supported", [])
    assert st(rec()) == ("not_established", ["insufficient_evidence"])


def test_conflict_keeps_both_sides_and_denial_contradicts():
    both = rec(evidence=[A, ev("No appeal shall lie from the order of a single Judge", stance="denies")])
    d = decide_n1(both, SRC)
    assert d["status"] == "not_established" and d["conflict"] and d["parts"][0]["n_affirm"] == 1 == d["parts"][0]["n_deny"]
    assert st(rec(evidence=[ev("The drug may reduce symptoms", stance="denies")])) == ("contradicted", ["source_denies"])


def test_every_part_needs_its_own_evidence():
    two = rec(parts=[{"predicate": "a"}, {"predicate": "b"}], evidence=[ev("The drug may reduce symptoms", part=0)])
    assert st(two) == ("not_established", ["part1:insufficient_evidence"])


def test_grounding_and_no_self_asserted_location():
    fake = dict(ev("The drug cures everything"), located=True, start=0, end=5)
    assert st(rec(evidence=[fake]))[0] == "not_established"
    assert st(rec(evidence=[fake]), grounding=False)[0] == "supported"


@pytest.mark.parametrize("field,value,expect", [
    ("stance", "denies", "contradicted"),          # decisive field: outcome must move
    ("stance", "weaker", "not_established"),
    ("subject_match", "narrower", "not_established"),
    ("subject_match", "broader", "supported"),     # still covers the subject
    ("basis", "suggests", "not_established"),
    ("basis", "necessarily_implies", "supported"),
    ("role", "counterexample", "not_established"),
])
def test_single_field_intervention(field, value, expect):
    base = rec(evidence=[A])
    assert st(base)[0] == "supported"
    r = copy.deepcopy(base); r["evidence"][0][field] = value
    assert st(r)[0] == expect


def test_irrelevant_field_control():
    base = rec(evidence=[A]); r = copy.deepcopy(base)
    r["claim"]["subject"] = "something else entirely"; r["evidence"][0]["note"] = "x"; r["inference_path"] = "none"
    assert st(r) == st(base)


def test_b1_rules():
    e = {"part": 0, "relation": "entails", "same_entity": True, "same_scope": True, "quote": "The drug may reduce symptoms"}
    assert decide_b1({"claim_parts": ["x"], "evidence": [e]}, SRC)["status"] == "supported"
    assert decide_b1({"claim_parts": ["x"], "evidence": [dict(e, same_scope=False)]}, SRC)["reasons"] == ["scope_or_entity_mismatch"]
    assert decide_b1({"claim_parts": ["x"], "evidence": [dict(e, relation="contradicts")]}, SRC)["status"] == "contradicted"
    m = {"part": 0, "text": "", "quote": "if the High Court certifies the case"}
    assert decide_b1({"claim_parts": ["x"], "evidence": [e], "missing_conditions": [m]}, SRC)["reasons"] == ["missing_condition"]


def test_versioned_audit_dispatch(tmp_path):
    r = rec(evidence=[A], qualifiers=[q("if the High Court certifies the case", "necessary_condition")])
    body = make_body_v3("claim", SRC, r, decide_n1(r, SRC), model="fixture")
    path = tmp_path / "l.jsonl"; w = c.open_ledger(path)
    import hashlib
    c.emit(body, w, {hashlib.sha256(SRC.encode()).hexdigest(): SRC})
    forged = copy.deepcopy(body); forged["derived"]["status"] = "supported"; forged["derived"]["reasons"] = []
    forged["status"] = "supported"; forged["id"] = c.cert_id(forged); c.emit(forged, w, {})
    pub = c.generate_key(tmp_path / "k.key"); c.sign_head(path, c.load_key(tmp_path / "k.key"))
    rep = c.audit(path, pub)
    by = {}
    for s in rep.steps:
        by.setdefault(s.seq, {})[s.step] = s.ok
    assert all(by[1].values()) and by[2]["status"] is False and by[2]["decision"] is False and by[2]["certificate_id"]


# ---- part binding (regression for the defect found on vitaminc:5ede072ec9e77c00084d23f2_2) ---------------------
from pramana_bind.v3 import resolve_part_refs

TWO = [{"predicate": "rating above 85%"}, {"predicate": "fewer than 322 reviews"}]
SRC2 = "The film holds an approval rating of 90 % , based on 323 reviews ."


def test_one_based_references_bind_to_the_right_part():
    r = rec(parts=TWO, evidence=[ev("approval rating of 90 %", part=1), ev("based on 323 reviews", stance="denies", part=2)])
    d = decide_n1(r, SRC2)
    assert d["part_numbering"] == "one_based" and d["evidence_part_index"] == [0, 1]
    assert [p["status"] for p in d["parts"]] == ["supported", "contradicted"]      # rating affirmed, review count denied
    assert d["reasons"] == ["part1:source_denies"] and d["status"] == "contradicted"
    legacy = decide_n1(r, SRC2, legacy_part_index=True)                            # the defect, preserved for replay
    assert [p["status"] for p in legacy["parts"]] == ["contradicted", "supported"] and legacy["rules_version"] == "N1/3.1"


def test_zero_based_references_still_work():
    r = rec(parts=TWO, evidence=[ev("approval rating of 90 %", part=0), ev("based on 323 reviews", stance="denies", part=1)])
    d = decide_n1(r, SRC2)
    assert d["part_numbering"] == "zero_based" and [p["status"] for p in d["parts"]] == ["supported", "contradicted"]


def test_invalid_reference_is_reported_not_moved_to_part_zero():
    r = rec(parts=TWO, evidence=[ev("approval rating of 90 %", part=1), ev("based on 323 reviews", part=7)])
    d = decide_n1(r, SRC2)
    assert d["evidence_part_index"] == [0, None] and d["invalid_part_references"] == 1
    assert [p["status"] for p in d["parts"]] == ["supported", "not_established"]


def test_resolve_part_refs_cases():
    assert resolve_part_refs([1, 2, 2], 2) == ([0, 1, 1], "one_based")
    assert resolve_part_refs([0, 1], 2) == ([0, 1], "zero_based")
    assert resolve_part_refs([1, 1], 3) == ([0, 0], "one_based")          # no 0 anywhere: one-based
    assert resolve_part_refs([None, "1", True, 3], 2)[0] == [None, None, None, None]
    assert resolve_part_refs([None, 1], 1)[0] == [0, 0]                    # single part: missing ref means that part


def test_qualifier_binds_to_its_own_part_and_conflict_is_per_part():
    cond = q("if the High Court certifies the case", "necessary_condition", part=2)
    r = rec(parts=[{"predicate": "a"}, {"predicate": "b"}], evidence=[ev("The drug may reduce symptoms", part=1), dict(A, part=2)],
            qualifiers=[cond])
    d = decide_n1(r, SRC)
    assert [p["status"] for p in d["parts"]] == ["supported", "not_established"] and d["reasons"] == ["part1:necessary_condition_omitted"]
    # affirm on one part and deny on another is NOT a conflict; on the same part it is
    r2 = rec(parts=[{"predicate": "a"}, {"predicate": "b"}], evidence=[dict(A, part=1), ev("The drug may reduce symptoms", stance="denies", part=2)])
    assert decide_n1(r2, SRC)["conflict"] is False and decide_n1(r2, SRC)["status"] == "contradicted"
    r3 = rec(parts=[{"predicate": "a"}, {"predicate": "b"}], evidence=[dict(A, part=1), ev("The drug may reduce symptoms", stance="denies", part=1)])
    assert decide_n1(r3, SRC)["conflict"] is True


def test_b1_one_based_binding():
    e1 = {"part": 1, "relation": "entails", "same_entity": True, "same_scope": True, "quote": "approval rating of 90 %"}
    e2 = {"part": 2, "relation": "contradicts", "same_entity": True, "same_scope": True, "quote": "based on 323 reviews"}
    d = decide_b1({"claim_parts": ["a", "b"], "evidence": [e1, e2]}, SRC2)
    assert [p["status"] for p in d["parts"]] == ["supported", "contradicted"]


def test_superseded_certificate_replays_under_its_own_rules(tmp_path):
    import hashlib
    r = rec(parts=TWO, evidence=[ev("approval rating of 90 %", part=1), ev("based on 323 reviews", stance="denies", part=2)])
    old = make_body_v3("claim", SRC2, r, decide_n1(r, SRC2, legacy_part_index=True), model="fixture")
    new = make_body_v3("claim", SRC2, r, decide_n1(r, SRC2), model="fixture")
    assert old["checks"]["rules_version"] == "N1/3.1" and new["checks"]["rules_version"] == "N1/3.2" and old["id"] != new["id"]
    path = tmp_path / "l.jsonl"; w = c.open_ledger(path)
    c.emit(old, w, {hashlib.sha256(SRC2.encode()).hexdigest(): SRC2}); c.emit(new, w, {})
    pub = c.generate_key(tmp_path / "k.key"); c.sign_head(path, c.load_key(tmp_path / "k.key"))
    rep = c.audit(path, pub)
    assert rep.ok and any("superseded" in s.detail for s in rep.steps) and any(s.step == "part_references" for s in rep.steps)
