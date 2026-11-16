# Limitations (summary for reviewers)

1. **Reading is unchecked.** Stance, basis ("necessarily implies"), subject match and qualifier type are model assignments. The program checks only
   that quotations occur, that references are valid, and that the decision follows from the record. Three tests (`test_LIMIT_*`) assert that inverted
   polarity, a wrong-entity quote and correlation read as causation are accepted if filed that way.
2. **No clear advantage over generic structure was detected.** The design cannot show equivalence; intervals are wide.
3. **Qualifier enforcement costs more correct acceptances than the false ones it prevents** (37 vs 6 across four datasets). Mechanism diagnoses are
   AI-assisted and not human-reviewed. The human-corrected-record diagnostic is pending.
4. **A part-binding defect existed in the registered rule.** It was found after the freeze, fixed under new rule versions and replayed. Verdicts changed on
   5 of 754 items; per-part explanations on 153. Both versions are kept. Every affected certificate had passed audit.
5. **Labels.** Experiment 2 uses benchmark labels with uncorrected noise. Experiment 1 labels are AI-drafted; 30 of 117 were reviewed by the project
   author alone, after the evaluations, having seen aggregate results. No inter-reviewer reliability exists.
6. **Models.** One primary model. The second-model run is from the same vendor, on a subsample, and completed two of four datasets before an account
   usage limit. The taxonomy judge was not run on the second model.
7. **Samples.** 754 external items; ContractNLI has 12 documents and 17 recurring hypotheses; comparisons are unadjusted for multiplicity.
8. **Audit scope.** A local signed hash chain; rollback is detectable only against a checkpoint the auditor already holds. No public log, no retrieval of
   counter-evidence, no judgement of source authority, no Lean or solver verification.
9. **Not measured:** whether people detect or localise errors better with the record than with a one-line rationale.
10. **Template.** The report follows the official template's section structure but is rendered from HTML, not produced in the Google Doc.
