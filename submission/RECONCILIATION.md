# Reconciliation of totals

Generated from `submission/metrics_master.json` (built by `experiments/reconcile.py` from raw call logs, records and ledgers).

## Calls and cost, by scope
| Scope | Successful calls | Failed call records | Cost (USD) |
|---|---|---|---|
| exp1_development (21 items; prompt v2 then v3; baselines copied into the v3 folder are counted once, in v2) | 189 | 0 | 0.13 |
| exp1_development_extract_v3 | 63 | 0 | 0.08 |
| exp1_attack_development (7 items) | 63 | 0 | 0.03 |
| exp1_heldout (117 items) | 1053 | 170 | 0.8 |
| exp1_attack_heldout (23 items) | 207 | 207 | 0.11 |
| exp2_development (dev1, dev2, dev3) | 1000 | 0 | 1.44 |
| exp3_second_model | 168 | 0 | 2.01 |
| exp2_heldout_main (754 items x 4 prompts, run 0) | 3016 | 0 | 3.92 |
| exp2_heldout_repeats (40 items x 4 datasets x 2 prompts x 2 extra runs) | 640 |  | 0.66 |

- **Experiment 2 held-out evaluation: 3656 calls, $4.58** (3,016 main calls = 754 items × 4 prompts, plus 640 repeat
  calls on the 40-item stability subsets). **With the 1000 development-pilot calls: 4656 calls, $6.02.**
  The earlier report counted held-out calls only; the earlier status message added development. Both were right for their scope; neither said which.
- Failed call records are account usage-limit errors (Experiment 1 held-out and attack runs, and the second-model run); each failed call was re-issued
  once the limit reset, except in the second-model run, which was stopped. No Experiment 2 call failed.

## Quotations (Experiment 2 held-out, run 0)
| System | Located | Proposed | Items with a refused quote | Items whose outcome changes if grounding is off |
|---|---|---|---|---|
| N1 | 2531 | 2540 | 8 | 0 |
| B1 | 1876 | 1880 | 4 | 0 |

- The earlier report's **2,531 / 2,540** is the N1 total and is correct. The status message's “2,856 / 2,865” cannot be reproduced from any artifact
  and was an error in that message; N1 and B1 together are 4407 / 4420.
- **The verbatim check did fire:** it refused 9 N1 quotes (not found, or found more than once) on
  8 items and 4 B1 quotes. What is true is narrower:
  **no refusal changed any final decision.** Earlier wording that the check “never fired” was wrong and is corrected everywhere.
- Experiment 1: 319 / 319 quotes located in the representative runs.

## Items, records and certificates
- 754 evaluation items → 753 parsed N1 records → 753 certificates under each rule version.
- The one item without a certificate is `scicite:row152`: its N1 reply was not a parseable JSON object. It is scored as a failure and
  stays in every denominator. There is **no de-duplication** and no many-to-one mapping; certificate ids are content hashes that include the item id.
- `submission/COVERAGE_MANIFEST.json` lists every item with its record status, part numbering, both certificate ids and ledger sequence number.

## The part-binding defect and what changed after the fix
The extractor numbers claim parts from 1 in every recorded record ({'one_based': 753}). Rules N1/3.1 and B1/1.0 read references as zero-based and sent
an out-of-range reference to the first part, so in all 272 multi-part N1 records evidence was attached to the wrong part. Overall
verdicts were mostly unaffected because every part must be supported, but the per-part explanation was wrong. Rules N1/3.2 and B1/1.1 resolve the
numbering per record, report invalid references (4 records) instead of moving them, and store the binding.
Frozen extractions were replayed with no model call; original results are kept in `experiments/exp2/` (tag `exp2-frozen`), corrected ones in `experiments/exp2b/`.

| Dataset | System | Before (FS · recall) | After (FS · recall) | Items whose status changed |
|---|---|---|---|---|
| contractnli | B1 | 10/118 · 26/86 | 10/118 · 26/86 | 0 |
| contractnli | N1 | 10/118 · 34/86 | 10/118 · 34/86 | 0 |
| contractnli | N1_noqual | 10/118 · 47/86 | 10/118 · 47/86 | 0 |
| vitaminc | B1 | 4/120 · 86/120 | 4/120 · 86/120 | 0 |
| vitaminc | N1 | 4/120 · 87/120 | 4/120 · 87/120 | 0 |
| vitaminc | N1_noqual | 5/120 · 92/120 | 5/120 · 92/120 | 0 |
| scicite | B1 | 6/100 · 16/60 | 6/100 · 16/60 | 0 |
| scicite | N1 | 5/100 · 19/60 | 5/100 · 18/60 | 4 |
| scicite | N1_noqual | 7/100 · 28/60 | 7/100 · 29/60 | 2 |
| attributionbench | B1 | 13/64 · 50/86 | 13/64 · 50/86 | 0 |
| attributionbench | N1 | 10/64 · 50/86 | 10/64 · 49/86 | 1 |
| attributionbench | N1_noqual | 13/64 · 57/86 | 13/64 · 57/86 | 0 |

N1 items whose stated reasons changed: contractnli 8, vitaminc 19, scicite 79, attributionbench 47 (of 754). B0 and T are unaffected.

## Qualifier ablation, recomputed from paired outputs (rules N1/3.2)
| Dataset | Supported items regained | Unsupported items admitted | Acceptances lost | Changes among non-support statuses |
|---|---|---|---|---|
| contractnli | 13 | 0 | 0 | 0 |
| vitaminc | 5 | 1 | 0 | 0 |
| scicite | 11 | 2 | 0 | 0 |
| attributionbench | 8 | 3 | 0 | 0 |

43 items change in total; the change is monotonic (every change is not-established → supported). Under the superseded rules the
SciCiteVal and AttributionBench rows were 9/2 and 7/3. All 43 cases, with claim, context, extraction, qualifier text, offsets and both
verdicts, are in `submission/QUALIFIER_TRANSITIONS.json`. The human-corrected-extraction diagnostic is **pending**: no human-corrected records exist.

## Second model
426 calls to `claude-sonnet-5-5` ($5.42) completed VitaminC and AttributionBench subsamples; the run then stopped on an account
usage limit. Not completed: {'scicite': '152 of 228 calls succeeded before the limit; not scored', 'contractnli': '16 of 204 calls; not scored', 'taxonomy judge': 'omitted by protocol'}.
