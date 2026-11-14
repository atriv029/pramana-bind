import json

import pytest
from fastapi.testclient import TestClient
from fixtures import CLAIM, PLAIN, REPLY, SRC, canned

from pramana_bind import certificate as c
from pramana_bind.__main__ import main
from pramana_bind.api import create_app
from pramana_bind.bind import ExtractionError, bind, decide
from pramana_bind.schema import Defeater, Quote, Source


def nig(body):
    return body["avayava"]["nigamana"]


def test_bind_exception_in_source_end_to_end():
    body, texts = bind(CLAIM, SRC, canned(REPLY), citation_raw="s. 379", model="fixture")
    n = nig(body)
    assert (n["verdict"], n["rule"], n["status"], n["reasons"]) == (
        "savyabhicara", "R5", "not_established", ["exception_in_source"])
    assert body["status"] == "not_established"
    assert body["extraction"]["status_agreement"] == 1.0 and not body["extraction"]["unstable"]
    assert body["ground_reasons"]["udaharana.L1.2"] == "quote_not_found"
    f = body["avayava"]["udaharana"]["loci"][0]["facts"][0]
    assert SRC[f["start"]:f["end"]] == f["quote"] and f["offsets_source"] == "system" and f["match"] == "exact"
    assert body["id"] == c.cert_id(body) and list(texts) == [body["source"]["text_sha256"]]


def test_unlocated_source_is_unresolved_without_model_call():
    def boom(_):
        raise AssertionError("model must not be called")
    body, texts = bind(CLAIM, None, boom)
    assert nig(body)["status"] == "unresolved" == body["status"] and texts == {}


def test_decision_rule():
    assert decide(["supported", "supported", "not_established"]) == "supported"
    assert decide(["supported", "not_established", "extraction_failed"]) == "not_established"
    assert decide(["supported", "contradicted", "not_established"]) == "not_established"  # tie
    assert decide(["contradicted", "contradicted", "supported"]) == "contradicted"
    assert decide(["supported", "extraction_failed", "extraction_failed"]) == "not_established"
    assert decide(["extraction_failed"] * 3) == "extraction_failed"


def test_instability_and_failed_runs():
    replies = iter([json.dumps(REPLY), json.dumps(PLAIN), "no json here"])
    body, _ = bind(CLAIM, SRC, lambda p: next(replies))
    ex = body["extraction"]
    assert ex["run_statuses"] == ["not_established", "supported", "extraction_failed"]
    assert ex["unstable"] and body["status"] == "not_established"
    with pytest.raises(ExtractionError):
        bind(CLAIM, SRC, lambda p: "garbage")


def test_defeater_outranks():
    dft = Defeater(quote=Quote(quote="is repealed", source_id="X"), authority_rank=2)
    body, texts = bind(CLAIM, SRC, canned(PLAIN), source=Source(authority_rank=1),
                       defeaters=[dft], counter_texts={"X": "The earlier provision is repealed."})
    assert nig(body)["rule"] == "R3" and nig(body)["status"] == "contradicted" and len(texts) == 2


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "ledger.jsonl"
    w = c.open_ledger(path)
    for cite in ("s. 379", "section 379 IPC"):
        body, texts = bind(CLAIM, SRC, canned(REPLY), n_runs=1, citation_raw=cite)
        cert = c.emit(body, w, texts)
    pub = c.generate_key(tmp_path / "k.key")
    c.sign_head(path, c.load_key(tmp_path / "k.key"))
    return path, pub, cert


def failing(rep):
    return {s.step for s in rep.steps if not s.ok}


def test_audit_passes_and_cli(ledger, capsys):
    path, pub, cert = ledger
    rep = c.audit(path, pub)
    assert rep.ok and rep.n_certificates == 2 and rep.n_events == 3
    assert {s.step for s in rep.steps} == {"hash_chain", "signature", "certificate_id", "versions", "source_hashes",
                                           "quote_offsets", "verdict", "status", "pbs", "decision"}
    assert main(["audit", str(path), "--pubkey", pub]) == 0
    out = capsys.readouterr().out
    assert "CHECKS PASSED" in out and "does not assert" in out
    found = c.find_certificate(path, cert["id"])
    assert found["seq"] == 2 and found["proof"]["this_hash"] == found["this_hash"]


def test_one_character_edit_fails_at_that_seq(ledger):
    path, pub, _ = ledger
    lines = path.read_text().splitlines()
    lines[1] = lines[1].replace("savyabhicara", "savyabhicarb", 1)
    path.write_text("\n".join(lines) + "\n")
    rep = c.audit(path, pub)
    assert not rep.ok and rep.steps[0].step == "hash_chain" and rep.steps[0].seq == 1


def test_reordered_and_missing_events(ledger):
    path, pub, _ = ledger
    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], lines[2], lines[1]]) + "\n")
    rep = c.audit(path, pub)
    assert failing(rep) == {"hash_chain"} and rep.steps[0].seq == 1
    path.write_text("\n".join([lines[0], lines[2]]) + "\n")  # middle event removed
    assert c.audit(path, pub).steps[0].seq == 1
    path.write_text("\n".join(lines[:2]) + "\n")  # truncated: chain intact, signature no longer covers head
    assert failing(c.audit(path, pub)) == {"signature"}


def test_key_pinning(ledger, tmp_path):
    path, pub, _ = ledger
    # no trusted key: the bundle's own key cannot vouch for itself
    sig = [s for s in c.audit(path).steps if s.step == "signature"][0]
    assert not sig.ok and "no trusted public key" in sig.detail
    # attacker re-signs with their own key and ships their public key in the bundle
    c.generate_key(tmp_path / "evil.key")
    c.sign_head(path, c.load_key(tmp_path / "evil.key"))
    sig = [s for s in c.audit(path, pub).steps if s.step == "signature"][0]
    assert not sig.ok and "does not verify under the pinned key" in sig.detail


def test_unsigned_tail(ledger):
    path, pub, _ = ledger
    body, texts = bind(CLAIM, SRC, canned(PLAIN), n_runs=1)
    c.emit(body, c.open_ledger(path), texts)
    sig = [s for s in c.audit(path, pub).steps if s.step == "signature"][0]
    assert not sig.ok and "chain head is seq 3" in sig.detail


def test_rollback_needs_a_trusted_checkpoint(ledger, tmp_path):
    """An older, correctly signed ledger passes unless the auditor holds a newer checkpoint."""
    path, pub, cert = ledger
    old = tmp_path / "old"; old.mkdir()
    lines = path.read_text().splitlines()
    (old / "ledger.jsonl").write_text("\n".join(lines[:2]) + "\n")
    (old / "sources").mkdir()
    for f in c.sources_dir(path).iterdir():
        (old / "sources" / f.name).write_bytes(f.read_bytes())
    c.sign_head(old / "ledger.jsonl", c.load_key(tmp_path / "k.key"))  # the signer's own earlier head
    assert c.audit(old / "ledger.jsonl", pub).ok                       # passes: this is the documented boundary
    cp = (cert["seq"], cert["this_hash"])
    assert failing(c.audit(old / "ledger.jsonl", pub, checkpoint=cp)) == {"checkpoint"}
    assert c.audit(path, pub, checkpoint=cp).ok
    assert failing(c.audit(path, pub, checkpoint=(1, "0" * 64))) == {"checkpoint"}


def _forged(tmp_path, mutate, reply=REPLY):
    """A forger who recomputes the certificate id and rebuilds the whole chain."""
    path = tmp_path / "forged.jsonl"
    body, texts = bind(CLAIM, SRC, canned(reply), n_runs=1)
    mutate(body)
    body["id"] = c.cert_id(body)
    c.emit(body, c.open_ledger(path), texts)
    pub = c.generate_key(tmp_path / "f.key")
    c.sign_head(path, c.load_key(tmp_path / "f.key"))
    return failing(c.audit(path, pub))


def test_forged_verdict_status_and_decision_are_caught(tmp_path):
    assert _forged(tmp_path / "a", lambda b: nig(b).update(verdict="valid", rule="R8")) == {"verdict"}
    assert _forged(tmp_path / "b", lambda b: nig(b).update(status="supported", reasons=[])) == {"status"}
    assert _forged(tmp_path / "c", lambda b: b.update(status="supported")) == {"decision"}
    assert _forged(tmp_path / "d", lambda b: nig(b)["pbs"].update(value=0.99)) == {"pbs"}


def test_forged_offsets_located_flag_and_context_flags_are_caught(tmp_path):
    def loc(b):
        b["avayava"]["udaharana"]["loci"][1]["facts"][2].update(
            located=True, start=0, end=10, offsets_source="system", match="exact")
    # un-refusing the refused counter-quote changes nothing else here, so only the quote step fails
    assert _forged(tmp_path / "a", loc) == {"quote_offsets"}

    def shift(b):
        b["avayava"]["udaharana"]["loci"][0]["facts"][0].update(start=1, end=2)
    assert _forged(tmp_path / "b", shift) == {"quote_offsets"}

    def flag(b):
        b["avayava"]["udaharana"]["loci"][0]["facts"][0]["flags"] = ["negation_cue_before_quote"]
    assert _forged(tmp_path / "c", flag) == {"quote_offsets"}


def test_swapped_source_text_is_caught(ledger):
    path, pub, cert = ledger
    f = c.sources_dir(path) / f"{cert['source']['text_sha256']}.txt"
    f.write_text(SRC.replace("three", "four"))
    assert {"source_hashes", "quote_offsets"} <= failing(c.audit(path, pub))


def test_api(tmp_path):
    path = tmp_path / "ledger.jsonl"
    client = TestClient(create_app(path, canned(REPLY), model="fixture"))
    assert client.post("/api/pramana/audit").status_code == 404
    r = client.post("/api/pramana/bind", json={"claim": CLAIM, "source_text": SRC, "citation_raw": "s. 379"})
    assert r.status_code == 200 and r.json()["status"] == "not_established"
    cid = r.json()["id"]
    assert client.get(f"/api/pramana/cert/{cid}").json()["seq"] == 1
    assert client.get("/api/pramana/cert/urn:pramana:cert:nope").status_code == 404
    rep = client.post("/api/pramana/audit").json()
    assert not rep["ok"] and [s for s in rep["steps"] if not s["ok"]][0]["step"] == "signature"
