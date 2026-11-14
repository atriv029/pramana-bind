# Pramāṇa-Bind

A quote-grounded, rule-based citation checker with signed, replayable certificates, built for the AI × Epistemics
Research Sprint (13–15 Nov 2026), Track 2.

**Headline result (held-out, 117 items, one model):** the pipeline did not beat simpler baselines. No system accepted
an unsupported citation (0/68 each). The pipeline recovered 29/49 supported claims; a one-call direct judge 43/49; a
judge prompted with the same failure taxonomy 37/49. Quote grounding changed no outcome. What the pipeline adds is an
audit trail, not accuracy. Labels are AI-drafted and **not yet human-reviewed**. See `submission/report.pdf`.

## Where things are
| Path | What |
|---|---|
| `submission/report.pdf` | research report (6 pages incl. appendices) |
| `INVENTORY.md` | every module: behaviour, tests run, limits, dependency versions |
| `eval/PROTOCOL.md` | analysis protocol frozen before the held-out run |
| `eval/DATASET.md`, `eval/data/` | dataset, annotation and licence notes; dev, test and attack files |
| `eval/review/` | human-review packet (no predictions) and blind second-reviewer sheet |
| `eval/runs/` | raw model replies with tokens, latency, cost; predictions; metrics; signed ledgers |
| `docs/AUDIT.md` | exactly what "audit passed" means and does not mean |
| `demo/` | viewer built from real certificates, demo script, tamper transcript |

## Pre-existing versus sprint work
| Piece | Status |
|---|---|
| `pravrudhi` 0.6.34: `nyaya_quote.locate_quote`, `nyaya_validity.derive_verdict`, `nyaya_gold`, statute corpus | pre-existing, imported |
| `pravrudhi_kernel` 0.1.0: hash-chained ledger, JCS, chain verification | pre-existing, imported |
| AVeriTeC development data | third-party (CC BY-NC 4.0) |
| `prabhasa-nyaya` Lean deciders | pre-existing, **not available, not run** |
| Everything in this repository | written during the sprint |

## Install
```bash
uv venv && uv pip install -r requirements.lock && uv pip install -e /path/to/pravrudhi-main/pravrudhi_kernel -e /path/to/pravrudhi-main -e '.[dev]'
```
Python 3.13. `requirements.lock` pins every third-party package; the two `pravrudhi` packages are installed from the
pre-existing source tree.

## Reproduce without model access
```bash
.venv/bin/pytest -q
```
```bash
.venv/bin/python -m pramana_bind crosscheck
```
```bash
.venv/bin/python eval/scripts/run.py eval/data/test.jsonl eval/runs/test-haiku --model claude-haiku-5-5
```
```bash
.venv/bin/python eval/scripts/score.py eval/runs/test-haiku
```
```bash
.venv/bin/python -m pramana_bind audit eval/runs/test-haiku/ledger.jsonl --pubkey "$(cat eval/runs/test-haiku/signer.pub)"
```
`run.py` re-uses the recorded calls in `calls.jsonl`, so predictions are recomputed from the raw replies with no model
call. To re-query the model, delete `calls.jsonl`; this needs the `claude` CLI signed in.
Note: re-running `run.py` rebuilds and re-signs that run's ledger with a new key if `signer.key` is absent.

## What is checked and what is not
1. A quote occurs in the source: **checked** by string match.
2. The quote means what the model filed it as: **not checked**.
3. Right subject, scope, time, strength: compared mechanically, from labels the model supplied.
4. The outcome follows from the rules: **checked**, pure functions.
5. The certificate is unchanged: **checked**, given a public key obtained separately.

"Audit passed" means 1, 4 and 5 held for the recorded quotes. It never means the reading is true. PBS is an
uncalibrated experimental score, not a probability. Nothing here is Lean-verified.
