# Analysis protocol for the held-out evaluation (prospective registration)

Frozen on 2026-11-14T08:58:38Z, in the commit that adds this file, before any system was run on
`test.jsonl` or `attack_test.jsonl`. Earlier development experiments are disclosed in section 6.

## 1. Question
Can a Nyaya-inspired, quote-grounded pipeline reduce false acceptance of unsupported citations while keeping
useful coverage, and make its remaining errors independently inspectable?

## 2. Frozen inputs
| File | sha256 |
|---|---|
| eval/data/test.jsonl (117 items, 36 source families, 49 supported / 68 not supported) | 60e418634ad9f51a3d3cc7a9277dc5ccc353fcd56c21a9b3ab35ad90b2a374cc |
| eval/data/attack_test.jsonl (23 constructed items, 4 supported controls) | 8cacbf89052cbfd1ec1a806a8b1dd9c88a081add4aec75322083a99b235a676f |
| eval/data/dev.jsonl (21 items, development only) | 93e2b155e0c200744dffdbe0f095fac5b33485b26fdbf1c0b4a17c0fe502cc62 |
| eval/data/attack_dev.jsonl (7 items, development only) | 209745eafeb140e59820b210d18af199457b271149a061bb0bd00d2be2766af6 |
| extractor prompt (pramana_bind/extract.py PROMPT) | 98cb5f7ca0eb0e317bf4cac5536973344a61b9ef578ec99481fb93b653162b65 |
| direct-judge prompt | 7ccd237e59cbf4599192bb54574e7376177cde8ba78602d825b69d41a850d0bc |
| taxonomy-judge prompt | 38f276b2056fa719903022e6bd2f320988cabdbb19f2491aebbf25b15c30f3e6 |
| eval/scripts/score.py | 5d49588dcab485a89dae3aa164d1cd886729a32d9c3568a06224495157e0bf00 |

Gold labels are passage-level: does the supplied passage support the claim. They were drafted by an AI assistant
from the passages before any system ran on these files, and are not derived from any system's output.
Human review is pending at freeze time; if review changes labels, results are reported on BOTH the frozen labels
and the reviewed labels, and the changes are listed.

## 3. Systems (one model for all: claude-haiku-5-5 through headless Claude Code; default sampling)
All systems receive the same claim, citation string and source text. No system receives retrieved counter-sources.
1. direct_1: one direct support judgement.
2. direct_3: three direct judgements, "supported" iff a strict majority (call budget matched to the pipeline).
3. taxonomy_1 / taxonomy_3: an LLM judge given the same failure definitions the pipeline uses, 1 and 3 calls.
4. **pipeline_noguard (PRIMARY)**: 3 extractions -> quote grounding -> world -> rules -> status;
   "supported" iff a strict majority of the 3 runs is supported. Lexical context guard OFF.
5. pipeline: the same with the lexical context guard ON (secondary).
6. pipeline_noground: the same extractions with quote grounding disabled (every quote accepted unchecked).
Systems 4-6 are computed from the SAME three extraction replies, so they differ only in the named component.

Operating point: the guard is OFF in the primary system because on development data it rejected supported items
(1 of 9) without removing any false acceptance (0 of 12 either way). This was decided on development data only.

## 4. Metrics
Primary: false-support rate = unsupported gold items predicted supported / all unsupported gold items;
supported-claim recall = supported gold items predicted supported / all supported gold items.
A lower false-support rate is not reported as an improvement if recall is materially lower; both are always shown together.
Also: precision of support decisions; coverage / abstention (unresolved or failed); confusion tables including
unresolved and failed outputs; parse-failure and call-failure rates; quote-location rate; agreement across the
three runs (reported as stability, not confidence); latency, tokens, cost; breakdown by slice and failure subtype.
Malformed replies and failed calls stay in the denominator as non-supported predictions.
Uncertainty: Wilson 95% intervals per rate (these treat items as independent, which related items from one
source are not); paired differences against the primary system by bootstrap over source FAMILIES; exact McNemar
on accuracy, stated with its independence assumption.

## 5. Hypotheses, stated so that either outcome is reportable
H1. pipeline_noguard has a lower false-support rate than direct_1 at recall not more than 10 points lower.
H2. pipeline_noguard has a lower false-support rate than taxonomy_3 (does the symbolic step add anything beyond
    a better prompt?). Failure of H2 is a finding, not a failed project.
H3. Disabling grounding raises the false-support rate.
With 68 unsupported and 49 supported items, a rate near 10% has a 95% interval of roughly +/-7 to 9 points;
differences smaller than that are not reported as findings. Per-subtype cells are descriptive only.

## 6. Development disclosed
- 21 development items and 7 attack-development items (different source families from the test files).
- Extractor prompt v2 (run kept in eval/runs/dev-haiku-promptv2): recall 1/9 because the extractor listed
  harmless detail as "omitted conditions". Prompt v3 narrowed that definition: recall 8/9, false support 0/12.
- The guard's "provided that" rule and the status layer were written during development.
- The direct judge made no error on development data (0/12 false support, 9/9 recall); the test set may be
  similarly easy for it. That would be reported as such.

## 7. Not claimed
PBS is an uncalibrated heuristic and is not used for any outcome metric. No Lean verification is claimed
(the Lean binary was not available). Audit results concern integrity and replay, not truth of the extraction.
