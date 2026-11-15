# Experiment 2 protocol (frozen 2026-11-15T06:31:36Z, before any call on an evaluation file)

## Questions
Primary: does explicitly representing the subject, reason, scope, conditions and counter-evidence of an inference
improve citation-support decisions and error localisation, compared with a matched direct judge and a generic
structured verifier? Secondary: which errors arise in extraction, which in the decision procedure, and which survive
a successful integrity audit?

## Systems (one model, claude-haiku-5-5 via headless Claude Code, default sampling; identical claim, source and
task note for every system; one call per item unless stated)
- **B0** direct three-way judge. **T** the same judge given the failure taxonomy.
- **B1** generic structured verifier: claim parts; per part, quoted evidence with relation / same_entity / same_scope;
  quoted missing conditions; quotes grounded by exact match; fixed decision rule (`decide_b1`).
- **N1** revised method (schema 3, rules N1/3.1): parts with polarity, quantifier, modality; quoted evidence with stance
  relative to the claim as written, basis (states / necessarily implies / suggests), subject match; typed qualifiers
  (necessary condition, scope, temporal, exception, uncertainty, incidental) with the claim aspect they change;
  quotes grounded; fixed decision rule (`decide_n1`).
- Rule-only ablations computed from the SAME N1 reply: **N1_noqual** (qualifiers ignored), **N1_noground** (quotes
  accepted unchecked).
- Stability / budget subset: the first 40 items of each evaluation file additionally get two more B0 calls and two
  more N1 calls; B0x3 and N1x3 are majority votes. Reported separately; token and cost budgets are published.
B1 and N1 differ in what is represented, not in terminology: N1's prompt uses English labels throughout, so no
separate "English rendering" arm exists. Where B1 and N1 decide alike, that is reported as such.

## Data (fixed by experiments/exp2/adapt.py, seed 20261115, before any prediction)
| File | Items | Families | sha256 |
|---|---|---|---|
| contractnli_eval.jsonl | 204 | 12 | 1e21ba8dac8b36c393df2f908684576883ab9852303eaf876c8437f492f52268 |
| vitaminc_eval.jsonl | 240 | 70 | 7625fdf268030ce0dd7504c292daba15cc4a416f75de80a2febfe8c9ea411f46 |
| scicite_eval.jsonl | 160 | 17 | 2497b1ba00636aa47e8d1aad89c0f17b5a6253c612dfbafae5f9d1a5fd68b6a8 |
| attributionbench_eval.jsonl | 150 | 143 | 1e8f538f26ddd5c5bf1f7077d13c664d889f77e8e06b184095712efbf3dbb43e |

- ContractNLI: 12 whole test documents x 17 hypotheses, full document in the prompt, no truncation, no gold spans shown.
  Only 17 recurring hypotheses exist; items are not independent question types.
- VitaminC: 70 complete contrast groups (case_id) from the test split, three labels preserved.
- SciCiteVal: 60 Correct, 60 Incorrect, 40 Unrelated in whole QASA-paper families; **no SciCiteVal item was used in
  development**. Correct-vs-Incorrect is the headline for this dataset; Unrelated is reported separately.
- AttributionBench: 150 out-of-distribution test items, proportional by constituent, whole reference bundle as source.
Development used only: ContractNLI dev (3 documents), VitaminC dev (20 groups), AttributionBench dev (40 items).

## Prompts and rules
- prompt B0: sha256 07a0fac6e5e5d089fcb264c59da2743ef7b01f35ee7cd27b676576aae5fc5be0
- prompt T: sha256 1f500f0a57287ad2998ea24c15b147924d13de3a61564c4176a5460299e437b1
- prompt B1: sha256 fc00f5a674abe0814c5cefc4d7b82fdedd57b0fbc17cb87fe62e8e9909aa2200
- prompt N1: sha256 278fb34128c1d747e23981ee6b97563ba41297ea25f5e6faba036304e17d1ef5
- rules: N1/3.1 B1/1.0
- experiments/exp2/score.py sha256 540b867bf61ca6866a6c095a3a3a8dd3506d9e07dd12ca24b613d5b74de7ed95

## Metrics
Per dataset, never pooled into one headline. Primary: false-support rate and supported-claim recall (binary
projection: supported vs. everything else). Where gold has three labels (ContractNLI, VitaminC): three-way accuracy
and macro-F1. Also: support precision, failed/malformed outputs (kept in the denominator as wrong), quote-location
rate, cost and latency, VitaminC joint correctness within contrast groups, SciCiteVal acceptance by distortion tag,
AttributionBench by constituent. Uncertainty: Wilson intervals (descriptive; items within a family are correlated) and
family-cluster bootstrap intervals for paired differences N1 minus each other system. Five comparisons per dataset
are made and not adjusted; a single interval excluding zero is treated as suggestive.
**Primary datasets:** ContractNLI and VitaminC. **Primary comparisons:** N1 vs B0 and N1 vs B1 on three-way accuracy.

## Hypotheses (either direction is reportable)
H1 N1's three-way accuracy is at least B0's on the primary datasets. H2 N1's is higher than B1's.
H3 Ignoring qualifiers (N1_noqual) raises false support. H4 Disabling grounding changes few outcomes (Experiment 1
found none). Development results (40 items each) had N1 roughly level with B0 and T, so no advantage is presumed.

## Development disclosed
dev1 (policy v1.0, direct-assertion-only rule): all systems over-conservative. dev2: policy v1.1 (ordinary inference
counts; possibility claims need one witness), per-benchmark task note, evidence "basis" field. dev3: one wording change
to B1's prompt for parity. Runs kept in experiments/exp2/runs/dev*.

## Caching and retries
A successful (system, item, run) call is never re-issued. Transport errors are retried twice within a call and
re-issued on a later invocation. Malformed answers are kept and scored as failures.
