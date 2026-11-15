# Annotation policy v1.1 (passage-level citation support)

Written 2026-11-15, after Experiment 1, without consulting any system's prediction on any item. It replaces the
informal rule used when the Experiment 1 labels were drafted. A reviewer applies it with only the claim, the
allowed source context and any stated dates in front of them.

## The question
Does the allowed source context, read on its own, establish the claim? Use no outside knowledge.

## Labels
- **supported** — the source states, or directly and necessarily implies, what the claim says, for the same
  subject, at the claimed scope and strength, under conditions the claim does not misstate.
- **contradicted** — the source states something that cannot be true together with the claim.
- **not_established** — neither. The source is silent, weaker, narrower, about something else, or conditional in a
  way the claim does not carry.
- **ambiguous** — the label turns on a reading the policy does not settle. Record the two readings. Ambiguous items
  are never dropped: they are counted and reported in a sensitivity analysis under each reading.

Binary projection (used where a dataset has only two labels): supported vs. everything else.

## How generic statements are read
A claim without an explicit quantifier ("A tenant may terminate on thirty days' notice") is read as a **default
rule**, not as a universal with no exceptions. A claim is read as **universal** only when its own words say so:
"always", "never", "any", "every", "all", "in all cases", "only", "can never", "regardless", "without exception",
"whether or not", or an equivalent. This reading is fixed. It does not depend on which answer any system gave.

**v1.1 additions (2026-11-15, from development data on external benchmarks, before any external evaluation item was run).**
"Necessarily implies" includes paraphrase, simple arithmetic or comparison of stated figures, the source's own
definitions, and resolving a pronoun to the document's stated subject. A claim of possibility or of "some"
("may", "can", "some") is established if the source provides for it in at least some circumstances, even
conditional ones: an existential claim needs one witness.

## Omissions: five cases
1. **Faithful summary, harmless omission → supported.** The claim leaves out detail that does not change whether
   the conclusion holds in the ordinary case: an *exception* carved out of a default rule (a proviso, a saving
   clause, "unless", "except"), further cases to which the rule also applies, reasons, consequences, procedure.
   A default-rule claim that omits an exception is still supported. *Example:* "Facts the parties agree to admit
   need not be proved" for a section that adds "provided the Court may still require proof".
2. **Omitted necessary condition → not_established.** The claim leaves out something without which the conclusion
   does not arise at all in the source: a precondition ("if the High Court certifies"), a restriction of who or
   what is covered (a narrower population, class, place, offence), a time window, or a hedge ("may", "is
   associated with", "was proposed") that the claim hardens. Test: take an ordinary case the claim covers; if the
   source's conclusion would not follow for it without the omitted element, the element is necessary.
   A **universal** claim that omits an exception also falls here, because the exception defeats the universal.
3. **Contradiction → contradicted.** The source asserts the opposite, a different value for the same quantity, or
   an incompatible attribution, *about the same subject, time and scope as the claim*. A statement about the
   present does not contradict a claim about the future; a statement about scheme A does not contradict a claim
   about scheme B. Those are case 4.
4. **Insufficient evidence → not_established.** The source does not address the claim, addresses a different
   subject, time, scheme or population, or reports that evidence was not found. "No evidence that X" is not
   evidence of not-X, unless the claim itself is that evidence exists.
5. **Context-dependent → ambiguous.** The reading depends on whether an omitted element is an exception or a
   precondition and the text supports both; or on which of two referents a pronoun or short name picks out; or on
   whether a compound claim's parts are all meant to be asserted. Record both readings.

## Further rules
- Compound claims: every asserted part must be supported. One unsupported part makes the claim not_established;
  one contradicted part makes it contradicted.
- Negative claims ("no appeal lies") are supported by a source sentence that says the same negative thing.
- Quotation and attribution: "X said Y" is supported by a source reporting that X said Y, whether or not Y is true.
- Statutory excerpts: the question is only what the excerpt says. Nothing here decides current law.
- Evidence spans are a reviewer aid recorded after the label. More than one span can be sufficient.

## Failure tags (optional, multiple allowed, for unsupported items)
missing_premise · wrong_entity · scope_extension · polarity_inversion · necessary_condition_omitted ·
exception_omitted_from_universal · unsupported_causality · conflicting_evidence · temporal_mismatch ·
strength_inflation · insufficient_evidence. These describe why the *source fails the claim*. They are operational
English tags. No one-to-one mapping to classical Nyāya terms is asserted; where the software shows a Sanskrit term
beside a tag it is a gloss, pending scholarly review.

## Record kept per item
original label; each reviewer's independent label, tags and note; adjudicated label and reason; reviewer
pseudonym; timestamp; policy version (`1.1`). Reviewers must not see system predictions, proposed labels,
highlights or rationales in the first pass. A model is never recorded as a human reviewer.

## Items already flagged for adjudication (by an AI-assisted reading; not replacement labels)
Label disputes: `test-stat-BSA-Section53-0`, `test-stat-COI-Article133-1`, `test-stat-COI-Article179-0`,
`test-avt-437-1`, `dev-stat-BNS-Section205-0`. Subtype disputes: `test-avt-360-0`, `test-avt-60-0`,
`test-avt-402-1`. Under this policy several of the first group look like case 1 (default rule, exception omitted),
but that is for the human reviewer to decide.
