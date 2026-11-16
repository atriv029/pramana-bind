# Human review of Experiment 1 labels (post-evaluation)

Generated from `experiments/human_review/RESULTS.json` by `experiments/human_review/analyze.py`.

## What was reviewed and by whom
- **Reviewer:** R1, the project author. One reviewer; this is a single-author review, not an independent one.
- **Sample:** 30 of the 117 held-out Experiment 1 items, drawn by fixed seed before review (13 originally
  labelled supported, 17 not), from 19 source passages.
- **Timing:** after both evaluations. It is not part of the prospective freeze, and no prompt or rule was changed in response to it.
- **Concealed in the review packet:** original labels, subtypes, rationales, evidence highlights, item identifiers and all system predictions.
  Review ids are hashes.
- **Author's confirmed statement:** “The project author completed a post-evaluation review of 30 held-out items using the blind packet. The
  reviewer did not see any proposed labels before or during labeling.”
- **Other exposure, as far as the artifacts show:** the blind packet contained no system predictions. The author had seen aggregate results. None of
  the 30 reviewed items appears with a system outcome in the earlier Experiment 1 demo viewer. No further statement about exposure to item-level
  predictions has been confirmed, and none is made.
- **AI assistance:** an assistant explained the CSV format and corrected punctuation in an example row. No evidence of AI involvement in the
  labels or reasons; the reasons are preserved verbatim as submitted.

## File validation
- Archived upload: `experiments/human_review/reviewer_R1_original_upload.csv` (sha256 `c2d0740b7bc7794b77b27c70abb7239087d4b69dc92fc49a978d501280ffeae1`), never modified.
- Parsed with a CSV parser: 30 rows; 30 expected ids; missing 0; unexpected 0;
  duplicates 0; invalid labels 0; empty reasons 0.
- Reviewer identifiers: {'R1': 30}. Normalisations applied in the derived import: 0
  (the leading spaces and the “Deputy's Speaker's” wording seen in an earlier draft are not present in the uploaded version).
- Timestamps: every row carries `2026-11-16T03:04:26Z`. This is one session time entered by the reviewer, not a measured per-item time.
- Label counts: {'not_established': 8, 'supported': 13, 'contradicted': 9}. Ambiguous: 0.

## Agreement with the original labels
- **Binary (supported vs not): 30/30** (Wilson 95% [0.886, 1]; Cohen's κ 1.0). Transitions: {'not_supported -> contradicted': 9, 'not_supported -> not_established': 8, 'supported -> supported': 13}.
- **Three-way: 22/30** (κ 0.59). The original labels were binary; the original three-way value is derived post hoc from the
  item author's subtype (“contradicted” subtype → contradicted; any other unsupported subtype → not established). All 8
  disagreements are between *contradicted* and *not established*; none crosses the supported boundary.

| Item | Original (derived) | Reviewer | Reviewer's reason (verbatim) |
|---|---|---|---|
| `test-stat-COI-Article96-2` | contradicted | not_established | The speaker itself carries the rights to speaking or taking part in proceedings, as it is the Deputy Speaker whose rights are limited. |
| `test-avt-496-0` | contradicted | not_established | There is no specification of free lawyers, there is simply an expanded access of them, but no guarantee they're free. |
| `test-stat-COI-Article193-3` | not_established | contradicted | The claim uses quite ambiguous language of whether the person knows their qualification status, while the source text explicitly claims that they do know regardless. |
| `test-avt-48-2` | not_established | contradicted | Though the global case recovery rate is approx. 68%, the rate specific to the USA is roughly 40%, thereby contradicting the claim. |
| `test-stat-BNSS-Section81-1` | not_established | contradicted | The claim says it can never be executed, but the source text shows a clear contradiction where the executing officer has the authority to execute the warrant, and the local police can assist. |
| `test-stat-COI-Article23-1` | not_established | contradicted | There is nothing in the article, as said in source context, that can prevent the State from imposing compulsory service for the following reasons. |
| `test-stat-BNSS-Section39-2` | contradicted | not_established | There is no evidence that it may be up to 7 days, and the source context addresses the issue of twenty-four hours for bond or bail, not necessarily identity. |
| `test-avt-245-0` | contradicted | not_established | The source context does not reference this case whatsoever and claims such instances are misleading. |

With one reviewer this is agreement with the original labels. Inter-reviewer reliability needs a second human reviewer and is not reported.

## System scores on exactly these 30 items
| System | FS, original labels | Recall, original labels | FS, reviewer labels | Recall, reviewer labels | Full 117 items, original labels (FS · recall) |
|---|---|---|---|---|---|
| direct_1 | 0/17 | 12/13 | 0/17 | 12/13 | 0/68 · 43/49 |
| direct_3 | 0/17 | 13/13 | 0/17 | 13/13 | 0/68 · 45/49 |
| taxonomy_1 | 0/17 | 11/13 | 0/17 | 11/13 | 0/68 · 37/49 |
| taxonomy_3 | 0/17 | 11/13 | 0/17 | 11/13 | 0/68 · 37/49 |
| pipeline_noguard | 0/17 | 8/13 | 0/17 | 8/13 | 0/68 · 29/49 |
| pipeline | 0/17 | 7/13 | 0/17 | 7/13 | 0/68 · 24/49 |
| pipeline_noground | 0/17 | 8/13 | 0/17 | 8/13 | 0/68 · 29/49 |

Because the binary labels agree on all 30 items, every system's binary score is identical under both label sets. The 87 unreviewed items remain
AI-drafted and unreviewed. The review covers none of the label disputes that turn on omitted exceptions unless listed above; it does not settle them.
