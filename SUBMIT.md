# Submission sheet

Deadline: Monday 16 November 2026, 11:59 UTC (Sunday 15 November 23:59 Anywhere on Earth). Resubmitting under the same title replaces the earlier entry.

## Portal fields
| Portal field | What to enter |
|---|---|
| Project title | Pramāṇa-Bind: Auditable Evidence Commitments and the Cost of Qualification in Citation Verification |
| Project summary | the text under “Paste-ready summary” below |
| PDF report | `Pramana_Bind_report.pdf` |
| Tracks | **Track 2: Trust Infrastructure** (primary). Optionally also Track 1: Model Epistemics & Decision-Making Evals, for the error-mechanism analysis. Leave the others unticked. |
| Interested in publishing | your choice |
| Author | Aaina Trivedi — Independent Researcher |
| Demo link (if the form has a link or “other artifacts” field) | pending: host `index.html` from `Pramana_Bind_demo_hosting.zip` and paste the public link. If the form accepts attachments instead, attach `Pramana_Bind_demo.html`. |
| Code repository link (optional) | https://github.com/atriv029/pramana-bind (use it only if the repository is set to public, so judges can open it) |

The report does not depend on either optional link.

## Paste-ready summary
A citation can point to a real source that does not actually support the claim. We built a checker in which an AI model must write down which quoted
words support which part of a claim, a fixed rule turns that record into a verdict, and the result is saved as a signed certificate anyone can replay.
On 754 claims from four public benchmarks, this checker was more cautious than simply asking the model, not more accurate: it accepted 29 of 402
unsupported claims where asking directly accepted 40, but it recognised only 188 of 352 supported claims where asking directly recognised 218. One
rule explains most of that gap. When we switched off the rule that rejects claims for leaving out a condition, 37 correct claims were accepted again
and 6 wrong ones slipped through. We also learned what a replayable certificate does and does not prove. A numbering mistake in our own rule attached
evidence to the wrong part of the claim on 153 of 754 items while changing only 5 final verdicts, and every one of those certificates passed its
audit, because the audit faithfully re-ran the same mistaken rule. An audit can show a result is reproducible and untampered with. It cannot show
the evidence was read correctly. An interactive demo lets you change the evidence, switch the rule off, and see the audit pass and fail.

(190 words. The 30-item author review and the partial second-model run are in the report, not in this summary.)

## Files
| File | Use |
|---|---|
| `Pramana_Bind_report.pdf` | upload as the report |
| `Pramana_Bind_demo.html` | open locally; attach if the portal allows |
| `Pramana_Bind_demo_hosting.zip` | `index.html` to host, hosting README, walkthrough and recording script |
| `Pramana_Bind_manuscript_and_reproducibility.zip` | editable manuscript source, figure scripts and data, per-item outputs, paired qualifier results, certificate coverage, tests, claim-to-artifact map |

## Numbers used everywhere (from `submission/metrics_master.json` and the corrected per-dataset metrics)
Direct judge 40/402 unsupported accepted, 218/352 supported recovered · typed verifier 29/402 and 188/352 · qualifier enforcement off: +37 supported,
+6 unsupported, 43 changes, all in one direction · part-binding fix: 5 of 754 verdicts, 153 part-level explanations · author review: 30/30 binary,
22/30 three-way.
