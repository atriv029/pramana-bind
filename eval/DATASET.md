# Dataset and annotation

## Task
Passage-level citation support. Each item is a claim, a citation string and one source passage. The label says
whether **that passage alone** supports the claim: same subject, scope, strength, conditions and time frame.
Binary primary label: `supported` / `not_supported`. Unsupported items carry an optional subtype
(contradicted, missing_evidence, scope_inflation, exception_omitted, misbinding, temporal). Subtypes are the item
author's description of why the item is unsupported; they were not independently annotated and are used only
descriptively.

## Files
| File | Items | Families | Supported / not | Use |
|---|---|---|---|---|
| data/dev.jsonl | 21 | 8 | 9 / 12 | development (prompt and operating-point decisions) |
| data/test.jsonl | 117 | 36 | 49 / 68 | held-out |
| data/attack_dev.jsonl | 7 | 7 | 1 / 6 | attack development |
| data/attack_test.jsonl | 23 | 21 | 4 / 19 | held-out fixed attacks |

A family is one source passage. All claims written against the same passage share a family, and no family appears
in both a development and a held-out file. Built by `scripts/build_dataset.py` and `scripts/build_attacks.py`;
every evidence span is asserted to be a substring of its source at build time.

## Slices
**Statutory (72 held-out items, 17 passages).** Passages are sections of the Bharatiya Nyaya Sanhita, Bharatiya
Nagarik Suraksha Sanhita, Bharatiya Sakshya Adhiniyam and articles of the Constitution of India, taken verbatim
from the statute corpus shipped with `pravrudhi` 0.6.34 (pre-existing). Passages were sampled at random (seed 11)
from sections of 350-1100 characters containing an exception or negation cue, then chosen by the author.
The task is **support by the supplied excerpt only**. No item asserts what the law currently is, whether a provision
is in force, or which of two provisions prevails; no supersession or repeal items are included, because that would
need item-specific authoritative evidence and qualified legal review, which were not available.

**AVeriTeC-derived (45 held-out items, 19 passages).** Each passage is one *extractive evidence answer* from the
AVeriTeC development set (Schlichtkrull et al., 2023; CC BY-NC 4.0; `data/dev.json` at the commit in INVENTORY.md).
AVeriTeC labels claims against a whole set of question-answer evidence. That claim-level verdict is **not** our
label: one passage rarely settles the claim. For each passage the author wrote a passage-level label for the
original AVeriTeC claim where that was clear, and added one or two new claims that the passage does or does not
support. `averitec.claim_level_label` is kept as metadata only. Candidates were sampled at random (seed 5) from
extractive answers of 260-750 characters; passages where support depended on outside knowledge were dropped
(for example a passage giving a 1960 figure for a claim about "independence").

**Attack (constructed).** Short sources written by the author to aim one named attack at the verifiers. They are
not real documents and say so in `source_locator`.

No separate paltering slice was built. Items where every quoted sentence is true but the claim does not follow
(scope, exception, misbinding) are present in both slices with the implied claim written out explicitly; nothing
here measures what readers infer from an unstated implication.

## Who labelled, and what that does and does not support
All claims written for this dataset, all labels, rationales and evidence spans were drafted by an AI assistant
(Claude, a larger model than the one evaluated) reading the passages, before any system was run on the held-out
files. Labels were never taken from, or adjusted to, any system's output.

**No human has reviewed these labels at the time of the reported results.** `review.status` is `pending` on
every item. The review packet in `review/` contains no system predictions; `second_reviewer_ids.txt` marks 49
harder held-out items for a second reviewer, with a blind sheet that hides the proposed label.
`scripts/apply_review.py` computes agreement and Cohen's kappa from the filled sheet. Until that is done:
- the labels are a single AI annotator's, and share a model family with the evaluated systems, which could favour
  those systems where the annotator and the model make the same reading error;
- no inter-annotator agreement can be reported, and none is.

## Per-item fields
`id`, `family`, `slice`, `split`, `claim`, `citation`, `source_text`, `source_sha256`, `source_locator`,
`retrieval`, `label`, `subtype`, `evidence_spans` (character offsets into `source_text`), `rationale`,
`task_note`, `drafting`, `review` {status, reviewer_1, reviewer_2, adjudication}, and for AVeriTeC-derived items
`averitec` {claim_index, claim_level_label, claim_is_original}.

## Licence
AVeriTeC-derived items inherit CC BY-NC 4.0. Statutory text is Indian legislation as shipped in the pravrudhi corpus.
