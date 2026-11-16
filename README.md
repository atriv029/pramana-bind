# Pramāna-Bind

**Auditable evidence commitments and the cost of qualification in citation verification.**

Aaina Trivedi (Independent Researcher). Built for the Apart Research AI × Epistemics Research Sprint, 13–15 November 2026, Track 2 (trust infrastructure).

A citation can point to a real, relevant source that does not support the claim attached to it. Pramāṇa-Bind is a citation verifier in which a language model must commit to an explicit record (which quoted passage bears on which part of a claim, and which conditions qualify it), a program applies a fixed, versioned rule to that record, and the result is saved as a signed certificate that anyone can replay without a model. The record is motivated by the Nyāya analysis of inference: subject, property claimed, reason, the relation that warrants the step, and conditions that defeat it.

- **Report:** [`submission/report.pdf`](submission/report.pdf)
- **Interactive demo (one file, works offline):** [`demo/Pramana_Bind_demo.html`](demo/Pramana_Bind_demo.html). Download it and open it in a browser.
- **Every number traced to a file:** [`submission/CLAIMS.md`](submission/CLAIMS.md)

## What we found

The project asks two questions.

**1. Which rule changes what the verifier accepts?** On 754 items from four public benchmarks, with one model and everything else held fixed:

| | Unsupported claims accepted | Supported claims recovered |
|---|---|---|
| Direct judge (ask the model) | 40 of 402 | 218 of 352 |
| Typed verifier (this project) | 29 of 402 | 188 of 352 |

The typed verifier is more cautious. One rule explains most of the gap: holding the model's extracted records fixed and switching off qualifier enforcement regained 37 supported claims and admitted 6 unsupported ones (43 verdicts changed, all in the same direction). We detected no clear advantage over a generic structured verifier that uses entities, polarity, scope and conditions without the Nyāya-motivated typing. Verbatim quote checking refused 9 of 2,540 quotations and changed no decision.

**2. What can an auditor establish from a replayable certificate?** That a decision is reproducible and unaltered. A part-numbering error in our own registered rule attached evidence to the wrong claim part: it changed 5 of 754 final verdicts and 153 part-level explanations, and every affected certificate passed its audit, because replay executed the same faulty rule. The error was found by a person reading one record against its source. It is fixed under new rule versions, and both versions are kept.

Supporting material, with its limits stated: a single-author review of 30 of our own 117 Experiment 1 items agreed with their binary support labels on 30 of 30 (22 of 30 three-way); a partial second-model run completed two of four subsamples and showed the same cautious pattern. See [`submission/LIMITATIONS.md`](submission/LIMITATIONS.md).

## How it works

```
claim + source ──► model extraction ──► quote location ──► decision rule ──► signed certificate ──► audit / replay
                   (one call; the      (exact string      (fixed, versioned;  (hash-chained ledger,   (no model call;
                    only model step)    match; computed    pure function)      Ed25519 on the head)    recomputes every
                                        offsets)                                                       derived field)
```

1. **Extraction (model).** The model splits the claim into asserted parts, each with polarity, quantifier and modality. For each part it quotes passages and labels each with a *stance* toward the part (affirms, denies, weaker, unrelated), a *basis* (states, necessarily implies, merely suggests) and a *subject match* (same, broader, narrower, different). It also quotes *qualifiers* and types them (necessary condition, scope restriction, temporal restriction, exception, uncertainty qualifier, incidental detail).
2. **Quote location (program).** Each quotation must occur exactly once in the source (exact match, else whitespace-collapsed). Nothing is repaired; a quote found zero or several times is refused.
3. **Decision rule (program).** A part is supported if a located passage affirms it by statement or necessary implication about the same or a broader subject, none denies it, and no unstated blocking qualifier applies. Denial gives *contradicted*. Passages on both sides give *not established* with both kept. Every part must be supported.
4. **Certificate and audit (program).** The decision is appended to a hash-chained ledger whose head is signed. An audit discards every derived field and recomputes it. Certificates replay only under their own rule version.

### Nyāya concern → implemented field

| Nyāya concern | Field | What it does not capture |
|---|---|---|
| Subject (*pakṣa*) | claim subject; `subject_match` per passage | The match is the model's label |
| Property claimed (*sādhya*) | claim parts with polarity, quantifier, modality | The split and strength are the model's reading |
| Reason (*hetu*) | quoted passage with `stance` | A quotation is not automatically a sufficient reason |
| Warranting relation (*vyāpti*) | `basis`: states / necessarily implies / suggests | A label, not a demonstrated relation |
| Unstated condition (*upādhi*) | typed, quoted qualifiers | Only conditions the source states and the model notices |
| Defeat, counterbalance | denying passages; conflict flag | Only within the supplied context; nothing is retrieved |

The Sanskrit terms are glosses on the fields. They are not evidence that a decision is correct.

### What is checked and what is not

| Property | Status |
|---|---|
| The quotation occurs in the supplied source | checked |
| The source text is the one the certificate was built from | checked (SHA-256) |
| Evidence is bound to the stated claim part | checked (rules N1/3.2) |
| The decision follows from the record | checked (rule replay) |
| The record is unchanged since signing | checked, given a key obtained outside the bundle |
| The ledger has not been rolled back | only against a checkpoint the auditor already holds |
| The quotation means what it is filed as | **not checked** (model assignment) |
| The quotation is about the claim's subject, scope and time | **not checked** (model assignment) |
| A qualifier is necessary rather than incidental | **not checked** (model assignment) |
| No contrary evidence exists elsewhere | **not checked** |

"Audit passed" means the integrity and replay checks passed. It never means the reading is true.

## Repository layout

| Path | Contents |
|---|---|
| `pramana_bind/` | The library. `v3.py`: current record schema, prompts, decision rules (N1/3.2, B1/1.1), part binding, versioned audit. `schema.py`, `extract.py`, `ground.py`, `world.py`, `verdict.py`, `status.py`, `bind.py`: the first (Experiment 1) pipeline. `certificate.py`: ledger, signing, audit. `baselines.py`, `models.py`: comparison judges and the model adapter. `__main__.py`: command line. |
| `tests/` | 83 tests: rules, part binding, audit and tamper cases, and three known-limit tests that assert wrong behaviour on purpose. |
| `eval/` | Experiment 1: items and labels, frozen protocol, runner, scorer, raw model replies, predictions, signed ledgers. |
| `experiments/exp1/` | Manifest of Experiment 1, exploratory rule replay, stage-level error table. |
| `experiments/exp2/` | Experiment 2 as registered: protocol, annotation policy, dataset manifest, fetch and adapter scripts, adapted samples, runner, scorer, raw replies, ledger (rules N1/3.1). |
| `experiments/exp2b/` | The same frozen replies decided by the corrected rules; before/after table; ledger (rules N1/3.2). |
| `experiments/exp3/` | Partial second-model run: protocol, seeded subsample, results. |
| `experiments/human_review/` | Archived review upload, import and analysis script, results. |
| `experiments/reconcile.py` | Rebuilds `submission/metrics_master.json`, the coverage map and the paired qualifier cases from raw artifacts. |
| `submission/` | Report (`report.pdf`), editable source (`report_source.html`), generator (`build_report.py`), `CLAIMS.md`, `HUMAN_REVIEW.md`, `RECONCILIATION.md`, `LIMITATIONS.md`, figures with their data and scripts, fonts, per-item predictions, coverage map. |
| `demo/` | Interactive demo, its builder and offline test (`interactive/`), hosted-ready copy and walkthroughs (`hosting/`), earlier certificate viewers. |
| `review_blind_v2/` | Blind review packet, blank sheets and labelling policy (no answer key). |
| `docs/` | `AUDIT.md`: what an audit establishes. `HISTORY.md`: mapping of commit identifiers cited in sprint documents. |
| `INVENTORY.md`, `SUBMIT.md` | Module-by-module inventory; submission sheet. |

## Install

Python 3.13. The library imports two pre-existing packages, `pravrudhi` and `pravrudhi_kernel` (quote locator, hash-chained ledger), from https://github.com/AxisMeru/pravrudhi.

```bash
git clone https://github.com/AxisMeru/pravrudhi ../pravrudhi
```

```bash
uv venv && uv pip install -r requirements.lock && uv pip install -e ../pravrudhi/pravrudhi_kernel -e ../pravrudhi -e '.[dev]'
```

## Reproduce the results (no model access needed)

Every prediction is recomputed from the recorded model replies.

```bash
.venv/bin/pytest -q
```

```bash
for d in contractnli vitaminc scicite attributionbench; do .venv/bin/python experiments/exp2/score.py experiments/exp2b/runs/eval-$d; done
```

```bash
.venv/bin/python eval/scripts/score.py eval/runs/test-haiku
```

```bash
.venv/bin/python experiments/reconcile.py
```

```bash
.venv/bin/python experiments/human_review/analyze.py
```

`experiments/human_review/analyze.py` needs the private review key, which is not in this repository; its outputs are committed.

Audit a ledger (integrity and replay; prints that it does not assert the reading is correct):

```bash
.venv/bin/python -m pramana_bind audit experiments/exp2b/ledger/ledger.jsonl --pubkey "$(cat experiments/exp2b/ledger/signer.pub)"
```

Rebuild figures, report and demo:

```bash
.venv/bin/python submission/figure_scripts/make_figures.py && .venv/bin/python submission/figure_scripts/make_diagrams.py
```

```bash
.venv/bin/python submission/build_report.py
```

```bash
.venv/bin/python demo/interactive/extract_data.py && .venv/bin/python demo/interactive/build.py && node demo/interactive/test_demo.js "$PWD/demo/Pramana_Bind_demo.html"
```

The diagram and PDF steps use headless Chromium through Playwright. `build_report.py` writes `submission/report.html`; print it to PDF (US Letter) to obtain `report.pdf`.

To re-query a model instead of replaying, delete a run's `calls.jsonl` and run `experiments/exp2/run.py`; this needs the `claude` command-line tool signed in. To re-download the benchmark releases at their pinned revisions, run `experiments/exp2/fetch_datasets.sh`.

## The interactive demo

`demo/Pramana_Bind_demo.html` is self-contained (data and fonts inside the file; no network, no API key, no model call).

1. **Change one number.** A real VitaminC pair: the source says 320 or 323 reviews; the claim says fewer than 322. Only the review-count part flips. A switch shows the original part-binding bug beside the corrected rule.
2. **Switch a rule off.** Toggle qualifier enforcement on a correct claim the rule blocks and on a wrong citation it blocks, next to the benchmark-wide trade-off.
3. **What a passing audit certifies.** The original certificate passes audit with evidence on the wrong part; a deliberately modified copy fails.

Model readings are recorded. Quote location, part binding, verdicts and the source hash are recomputed in the browser. Hash-chain and signature results are recorded command-line output. See `demo/hosting/WALKTHROUGH.md` for a 60-second walkthrough and a recording script, and `demo/hosting/README.md` for hosting.

## Data and licences

| Dataset | Use | Licence |
|---|---|---|
| ContractNLI (Koreeda and Manning, 2021) | 12 test contracts × 17 hypotheses | CC BY 4.0; the release also ships terms of use |
| VitaminC (Schuster et al., 2021) | 70 contrast groups | CC BY-SA 3.0 |
| SciCiteVal (Liu et al., 2026) | 160 items | CC BY 4.0 |
| AttributionBench (Li et al., 2024) | 150 out-of-distribution items | Apache-2.0; constituents vary |
| AVeriTeC (Schlichtkrull et al., 2023) | evidence passages in Experiment 1 | CC BY-NC 4.0 |

Only the adapted evaluation samples are committed, each item carrying its licence reference. Full releases are fetched by script and are not redistributed here. Pinned revisions and checksums: `experiments/exp2/DATASETS.md`.

## Pre-existing versus sprint work

- **Pre-existing, imported unchanged:** `pravrudhi` 0.6.34 and `pravrudhi_kernel` 0.1.0 (quote locator, statute corpus, constructed symbolic gold set, hash-chained ledger, canonical JSON), and the public datasets.
- **Written during the sprint:** everything in this repository.

## Limitations in brief

One primary model. Modest samples with wide intervals and unadjusted comparisons. Stance, basis, subject match and qualifier type are unchecked model assignments. Experiment 1 labels were drafted by an AI assistant; 30 of 117 were reviewed by the author. Qualifier-mechanism diagnoses are AI-assisted. The corrected rules were applied after the registered freeze, and both versions are reported. The second-model run is partial and from the same vendor. No retrieval of counter-evidence, no formal verification, no study of whether people catch more errors with these records. Full list: `submission/LIMITATIONS.md`.

## AI assistance

Author conceived and framed the project, defined the research questions, and directed each stage. The author and an AI coding assistant both contributed to the code. The assistant drafted the Experiment 1 items and initial labels, ran the experiments, generated the figures, and drafted the report under the author’s direction. The author conducted the human label review and reviewed the analysis and manuscript. Appendix D provides further details.

## History

The commit history was rewritten once before publication to set the author identity and remove a committed review answer key; commit dates are preserved. `docs/HISTORY.md` maps the commit identifiers cited in sprint documents to the ones in this repository.

## Citation

Trivedi, A. (2026). *Pramāṇa-Bind: Auditable Evidence Commitments and the Cost of Qualification in Citation Verification.* AI × Epistemics Research Sprint, Apart Research.
