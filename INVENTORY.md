# Implementation inventory

State at 2026-11-14T09:01Z. "Pre-sprint" means it existed before 13 Nov 2026 and is imported, not written here.

## Dependencies (all pre-sprint)
| Dependency | Version / commit | How obtained |
|---|---|---|
| pravrudhi | 0.6.34 (zip upload `pravrudhi-main_1.zip`; no git metadata in the archive, files dated 23 Oct 2026) | installed editable |
| pravrudhi-kernel | 0.1.0 (same archive) | installed editable |
| pravrudhi-app | d2bb849930429412e1038aa384a26ffde2cacd96 (public GitHub, read-only clone) | inspected only; not modified, not used at runtime |
| AVeriTeC | 7c62d1ec8df3fb560d6efe2b85fa191135636f81 (github.com/MichSchli/AVeriTeC, CC BY-NC 4.0) | `data/dev.json` used as a source of claims and evidence passages |
| prabhasa-nyaya Lean `score` binary | **not available** | Lean leg of the cross-check did not run |
| Model | claude-haiku-5-5 via headless Claude Code CLI | see `pramana_bind/models.py` |

## Modules in this repository (all written during the sprint)
| Module | Purpose | Behaviour implemented | Tests run | Known limitations |
|---|---|---|---|---|
| schema.py | data model | five-member tuple, quotes, facts with source-strength labels, omitted conditions, verdict and support-status enums, schema/rules versions | exercised by every test | quantifier, modality, scope, conditions are extractor labels; time is only representable as an "omitted condition" |
| extract.py | the only model step | prompt v3, tolerant JSON parser, n runs; ignores any offsets/flags/verdict a reply carries | test_semantic_boundary (fixtures); dev + held-out runs (live model) | output is testimony; which subject/polarity a quote is filed under is unchecked |
| ground.py | quote location | wraps pre-sprint `locate_quote` (exact, else whitespace-collapsed; ambiguous or missing quotes refused); records match mode; lexical context flags; grounding can be disabled for the ablation | test_ground_crosscheck, test_semantic_boundary | establishes occurrence only; context flags are keyword heuristics |
| world.py | three-valued world | present/absent/unknown; conflicts held at unknown; evidence de-duplicated by span | test_verdict, test_semantic_boundary | — |
| verdict.py | rules R0–R8 | ordered rules, returns verdict, rule id, subtype | test_verdict (each rule and the ordering), cross-check | decides a finite world; R8 "valid" is not support |
| status.py | reader-facing outcome | supported / not_established / contradicted / unresolved with plain-language reasons; "supported" requires a located direct statement | test_semantic_boundary, test_pipeline | a deterministic function of extractor filings |
| score.py | PBS | G·V·D | test_verdict, test_semantic_boundary (sensitivity) | experimental, uncalibrated, sensitive to omitted facts; not used for outcome metrics |
| bind.py | pipeline | conclude (pure), 3-run decision rule, certificate body | test_pipeline | only the representative run's tuple is stored |
| certificate.py | ledger, signature, audit | emit to pre-sprint hash-chained ledger; Ed25519 over chain head; audit replays quotes, flags, verdict, status, score, decision; pinned key; optional checkpoint | test_pipeline (tamper, reorder, deletion, truncation, key substitution, rollback, forged derived fields) | local signed chain, not a transparency log; non-representative runs are recorded, not replayable |
| crosscheck.py | symbolic regression | rules vs `derive_verdict` and gold labels on closed worlds | test_ground_crosscheck | Lean leg not run |
| baselines.py | comparison judges | direct and taxonomy prompts, majority rule | held-out runs | — |
| models.py | model access | headless Claude CLI, raw call log with usage/latency/cost | live runs | no temperature control through this interface |
| retreat.py | Track 1 metric | retreat distance, equivocation, gap | test_retreat (unit only) | **not evaluated**; no Track 1 claim is made |
| defeat.py | counter-source retrieval | BM25 + model-proposed denying quote | **no tests; not used in any reported result** | hard-coded statute rank table must not be read as legal applicability |
| api.py | HTTP routes | bind / cert / audit | test_pipeline::test_api | no auth; demo only |
| viewer/ | certificate viewer | static page built from a real ledger | built from real runs | standalone; not integrated into pravrudhi-app `/citations` |

## Tests and cross-check actually run
```
$ .venv/bin/pytest -q
60 passed, 1 warning in 1.12s

$ .venv/bin/python -m pramana_bind crosscheck --per-class 100     # seed 0
{"n": 600, "per_class": 100, "seed": 0, "derive_verdict": {"agree": 600, "n": 600}, "gold_label": {"agree": 600, "n": 600}, "lean": {"ran": false, "reason": "score binary not available"}}
disagreements: 0
```

What the 600-item cross-check compares, exactly (items from pre-sprint `nyaya_gold.build_gold_set(100, seed=0)`):

1. **Base inference vs `nyaya_validity.derive_verdict`** (600/600). For every item, the world, pakṣa, sādhya and hetu
   are given to both functions with the item's extra premise ignored. `derive_verdict` can return only
   valid / asiddha / viruddha / savyabhicara / aprasiddha. For the 200 badhita and satpratipaksa items the base
   inference is, by construction, valid, and both functions say so; this leg says nothing about defeat.
2. **Full item vs the gold label** (600/600). Here `derive_ow` also receives the item's extra premise, converted by
   `crosscheck.item_to_world3` into a defeater: the constructed observation becomes a higher-ranked defeater (badhita);
   the counter-inference becomes an equal-ranked defeater, marked valid only if `derive_verdict` calls it valid
   (satpratipaksa). The comparison is with the generator's label. `derive_verdict` does not and cannot return
   badhita or satpratipaksa; agreement on those 200 items is agreement with how the gold set was constructed and with
   this module's own conversion, which is a weaker check than legs 1 or 3.
3. **Lean deciders**: not run. No Lean claim is made.

Also: exhaustive agreement on more than 50,000 (paksa, sadhya, hetu) triples with `derive_verdict` on 300 random closed worlds (seed 7), in
`tests/test_ground_crosscheck.py`.

This is symbolic regression agreement on constructed closed worlds. It is not evidence about natural-language support.

## Addendum: Experiment 2 (15 Nov 2026)
| Module / artefact | Purpose | Tests / runs | Known limitations |
|---|---|---|---|
| pramana_bind/v3.py | schema-3 record (N1), generic structured baseline (B1), direct and taxonomy prompts, decision rules, versioned certificate and audit replay | tests/test_v3.py (16 cases on frozen records, incl. single-field interventions and a control); 4,656 live calls | every stance/basis/subject/relation label is model-assigned; time only as a qualifier |
| experiments/exp1/ | immutable manifest (tag `exp1-frozen`), exploratory rule replay, stage-level error table | replay re-derives 29/49, 0/68 exactly | replay and diagnoses are post-hoc, AI-made |
| experiments/exp2/ | pinned fetch script, adapters, protocol, runner, scorer, figures, ledger builder, annotation policy v1.1, blind review packet | all four evaluation runs, 0 failed calls | modest samples; no human review recorded |
| submission/build_report.py | report and claim-to-evidence table generated from result files | run | narrative text is hand-written around generated numbers |

Test summary: 76 tests pass. Of these, 3 (`test_LIMIT_*`) are **known-limit characterisations** that assert wrong
behaviour on purpose (inverted polarity, wrong entity, correlation as causation); 73 are correctness tests.
Model identity: every successful call in both experiments reports `claude-haiku-5-5` as the served model
(`served_models` in each metrics.json); no alias or fallback was observed.
Not done from the handoff: human review and adjudication; independently annotated failure tags; the 2×2
corrected-extraction diagnostic (needs human-corrected records); pipeline-level synthetic interventions beyond
VitaminC's own contrast pairs; human audit study; FOLIO/ProofWriter/SciFact/ERASER; a second model; fine-tuning;
the full-size allocation (754 items evaluated, not ~5,000).

## Addendum: 16 Nov 2026
- **Part-binding defect** in `v3.py` (rules N1/3.1, B1/1.0) fixed as N1/3.2, B1/1.1 (`resolve_part_refs`); old rule kept for replay of old
  certificates; 7 new regression tests. Replay in `experiments/exp2b/`.
- `experiments/reconcile.py` → `submission/metrics_master.json`, `COVERAGE_MANIFEST.json`, `QUALIFIER_TRANSITIONS.json`.
- `experiments/human_review/analyze.py` → `RESULTS.json`, `submission/HUMAN_REVIEW.md`.
- `experiments/exp3/`: second model `claude-sonnet-5-5`, served id verified on all 426 scored calls; stopped by usage limit.
- Tests: 83 pass (80 correctness, 3 known-limit characterisations).
- Figures: `submission/figure_scripts/` (matplotlib for empirical figures; HTML rendered by Chromium for Figures 1 and 5), fonts Source Serif 4,
  Source Sans 3, IBM Plex Mono (SIL OFL, bundled in `submission/fonts/`; obtained from the fontsource npm packages).
