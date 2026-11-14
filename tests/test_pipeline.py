import json

import pytest
from fastapi.testclient import TestClient

from pramana_bind import certificate as c
from pramana_bind.__main__ import main
from pramana_bind.api import create_app
from pramana_bind.bind import ExtractionError, bind
from pramana_bind.schema import Defeater, Quote, Source

SRC = ("Whoever commits theft shall be punished with imprisonment of either description for a term which may "
       "extend to three years. Theft in a dwelling house shall be punished with imprisonment which may extend "
       "to seven years. Nothing in this section applies to a child under seven years of age, who shall not be punished.")
CLAIM = "Everyone who commits theft is punished with up to three years."

REPLY = {
    "pratijna": {"paksa": "anyone who commits theft", "sadhya": "punished with up to three years",
                 "quantifier": "all", "modality": "certain", "paksa_quote": "Whoever commits theft"},
    "hetu": "commits theft", "vyapti": "wherever theft, up to three years",
    "upanaya": {"polarity": "present", "scope": "full", "quote": "Whoever commits theft shall be punished"},
    "loci": [
        {"id": "L1", "label": "theft in a dwelling", "facts": [
            {"prop": "H", "polarity": "present", "quote": "Theft in a dwelling house"},
            {"prop": "S", "polarity": "absent", "quote": "may extend to seven years"}]},
        {"id": "L2", "label": "ordinary theft", "facts": [
            {"prop": "H", "polarity": "present", "quote": "commits theft shall"},
            {"prop": "S", "polarity": "present", "quote": "may extend to three years"},
            {"prop": "S", "polarity": "present", "quote": "this quote is not in the source"}]},
    ],
}


def ask_const(reply):
    return lambda prompt: "Here you go:\n" + json.dumps(reply)


def test_bind_savyabhicara_end_to_end():
    body, texts = bind(CLAIM, SRC, ask_const(REPLY), citation_raw="s. 379", model="fake")
    nig = body["avayava"]["nigamana"]
    assert (nig["verdict"], nig["rule"]) == ("savyabhicara", "R5")
    assert nig["pbs"]["G"] == pytest.approx(5 / 6) and nig["pbs"]["V"] == pytest.approx(0.2)
    assert body["extraction"]["verdict_agreement"] == 1.0 and not body["extraction"]["unstable"]
    assert body["ground_reasons"]["udaharana.L2.2"] == "quote_not_found"
    up = body["avayava"]["upanaya"]
    assert SRC[up["start"]:up["end"]] == up["quote"] and up["offsets_source"] == "system"
    assert body["id"] == c.cert_id(body) and list(texts) == [body["source"]["text_sha256"]]


def test_unlocated_source_is_unresolved_without_model_call():
    def boom(_):
        raise AssertionError("model must not be called")
    body, texts = bind(CLAIM, None, boom)
    assert body["avayava"]["nigamana"]["verdict"] == "unresolved" and texts == {}


def test_instability_and_failed_runs():
    valid = json.loads(json.dumps(REPLY)); valid["loci"] = valid["loci"][1:]
    replies = iter([json.dumps(REPLY), json.dumps(valid), "no json here"])
    body, _ = bind(CLAIM, SRC, lambda p: next(replies))
    ex = body["extraction"]
    assert ex["run_verdicts"] == ["savyabhicara", "valid", "extraction_failed"]
    assert ex["unstable"] and ex["verdict_agreement"] == pytest.approx(1 / 3)
    with pytest.raises(ExtractionError):
        bind(CLAIM, SRC, lambda p: "garbage")


def test_defeater_outranks():
    valid = json.loads(json.dumps(REPLY)); valid["loci"] = valid["loci"][1:]
    d = Defeater(quote=Quote(quote="is repealed", source_id="BNS/x"), authority_rank=2)
    body, texts = bind(CLAIM, SRC, ask_const(valid), source=Source(authority_rank=1),
                       defeaters=[d], counter_texts={"BNS/x": "The earlier provision is repealed."})
    assert body["avayava"]["nigamana"]["rule"] == "R3" and len(texts) == 2
    assert body["avayava"]["nigamana"]["pbs"]["value"] == 0.0


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "ledger.jsonl"
    w = c.open_ledger(path)
    for cite in ("s. 379", "section 379 IPC"):
        body, texts = bind(CLAIM, SRC, ask_const(REPLY), n_runs=1, citation_raw=cite)
        cert = c.emit(body, w, texts)
    pub = c.generate_key(tmp_path / "k.key")
    c.sign_head(path, c.load_key(tmp_path / "k.key"))
    return path, pub, cert


def test_audit_passes_and_cli(ledger, capsys):
    path, pub, cert = ledger
    rep = c.audit(path, pub)
    assert rep.ok and rep.n_certificates == 2 and rep.n_events == 3
    assert {s.step for s in rep.steps} == {"hash_chain", "signature", "certificate_id", "source_hashes",
                                           "quote_offsets", "verdict", "pbs"}
    assert main(["audit", str(path), "--pubkey", pub]) == 0
    assert "AUDIT PASSED" in capsys.readouterr().out
    found = c.find_certificate(path, cert["id"])
    assert found["seq"] == 2 and found["proof"]["this_hash"] == found["this_hash"]


def test_one_character_edit_fails_at_that_seq(ledger):
    path, pub, _ = ledger
    lines = path.read_text().splitlines()
    lines[1] = lines[1].replace("savyabhicara", "savyabhicarb", 1)
    path.write_text("\n".join(lines) + "\n")
    rep = c.audit(path, pub)
    assert not rep.ok and rep.steps[0].step == "hash_chain" and rep.steps[0].seq == 1


def test_wrong_key_and_unsigned_tail(ledger, tmp_path):
    path, pub, _ = ledger
    other = c.generate_key(tmp_path / "other.key")
    sig = [s for s in c.audit(path, other).steps if s.step == "signature"][0]
    assert not sig.ok and "different key" in sig.detail
    body, texts = bind(CLAIM, SRC, ask_const(REPLY), n_runs=1)
    c.emit(body, c.open_ledger(path), texts)
    sig = [s for s in c.audit(path, pub).steps if s.step == "signature"][0]
    assert not sig.ok and "chain head is seq 3" in sig.detail


def _rewrite_cert(tmp_path, mutate):
    """A forger who recomputes the id and the whole chain still fails the audit."""
    path = tmp_path / "forged.jsonl"
    body, texts = bind(CLAIM, SRC, ask_const(REPLY), n_runs=1)
    mutate(body)
    body["id"] = c.cert_id(body)
    c.emit(body, c.open_ledger(path), texts)
    return {s.step: s for s in c.audit(path).steps}


def test_forged_verdict_is_caught(tmp_path):
    def m(b):
        b["avayava"]["nigamana"].update(verdict="valid", rule="R8")
    steps = _rewrite_cert(tmp_path, m)
    assert steps["hash_chain"].ok and steps["certificate_id"].ok and not steps["verdict"].ok


def test_forged_quote_and_offsets_are_caught(tmp_path):
    def m(b):
        f = b["avayava"]["udaharana"]["loci"][1]["facts"][2]
        f.update(located=True, start=0, end=10, offsets_source="system")
    steps = _rewrite_cert(tmp_path, m)
    assert not steps["quote_offsets"].ok


def test_swapped_source_text_is_caught(ledger):
    path, pub, cert = ledger
    f = c.sources_dir(path) / f"{cert['source']['text_sha256']}.txt"
    f.write_text(SRC.replace("three", "four"))
    steps = {s.step: s for s in c.audit(path, pub).steps}
    assert not steps["source_hashes"].ok and not steps["quote_offsets"].ok


def test_api(tmp_path):
    path = tmp_path / "ledger.jsonl"
    client = TestClient(create_app(path, ask_const(REPLY), model="fake"))
    assert client.post("/api/pramana/audit").status_code == 404
    r = client.post("/api/pramana/bind", json={"claim": CLAIM, "source_text": SRC, "citation_raw": "s. 379"})
    assert r.status_code == 200 and r.json()["avayava"]["nigamana"]["verdict"] == "savyabhicara"
    cid = r.json()["id"]
    assert client.get(f"/api/pramana/cert/{cid}").json()["seq"] == 1
    assert client.get("/api/pramana/cert/urn:pramana:cert:nope").status_code == 404
    rep = client.post("/api/pramana/audit").json()
    assert not rep["ok"] and [s for s in rep["steps"] if not s["ok"]][0]["step"] == "signature"
