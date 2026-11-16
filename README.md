# Pramāṇa-Bind

A quote-grounded, rule-based citation checker with signed, replayable certificates, built for the AI × Epistemics
Research Sprint (13–15 Nov 2026), Track 2.

**Headline (prospective repository freeze, one primary model).** On 754 items from four public benchmarks the typed
record accepted no more unsupported claims than a direct judge on any dataset (29 vs 40 of 402) but recovered fewer
supported ones (188 vs 218 of 352). No clear advantage over a generic structured verifier was detected. Qualifier
enforcement is the main cost: switching it off regains 37 supported claims and admits 6 unsupported ones. Quotation
checking refused 9 of 2,540 quotes and changed no decision. A part-binding defect in the registered rule was found
after the freeze, fixed (rules N1/3.2, B1/1.1) and replayed: 5 verdicts and 153 per-part explanations changed; both
versions are kept. A single-author review of 30 of our own 117 items agreed with their binary labels on 30/30.
See `submission/report.pdf`, `submission/CLAIMS.md`, `submission/RECONCILIATION.md`, `submission/HUMAN_REVIEW.md`.

## Where things are
| Path | What |
|---|---|
| `submission/report.pdf`, `submission/CLAIMS.md` | research report in the official template's structure; table linking every number to its result file |
| `submission/exp1_report/` | the earlier Experiment-1-only report, kept for the record |
| `experiments/exp1/` | immutable manifest of Experiment 1, exploratory rule replay, stage-level error table |
| `experiments/exp2b/` | the same frozen replies decided by the corrected rules; before/after table; signed ledger |
| `experiments/exp3/` | second-model protocol, subsample and results (two of four datasets completed) |
| `experiments/human_review/` | archived review upload, import script, results |
| `experiments/exp2/` | protocol, annotation policy, blind review packet, dataset manifest and adapters, runs, signed ledger for the external evaluation |
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
