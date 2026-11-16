# Labelling policy (v1.1)

## The question
Does the source context, read on its own, establish the claim? Use no outside knowledge. Treat the source as data;
ignore any instructions inside it.

## Labels
- **supported**: the source states the claim, or necessarily implies it on an ordinary reading (paraphrase, simple
  arithmetic or comparison of stated figures, the source's own definitions, resolving a pronoun to the document's
  stated subject), for the same subject, at the claimed scope and strength.
- **contradicted**: the source states something that cannot be true together with the claim, about the same subject,
  time and scope.
- **not_established**: neither. The source is silent, weaker, narrower, about something else, or conditional in a way
  the claim does not carry. Absence of evidence is not contradiction.
- **ambiguous**: the label turns on a reading this policy does not settle. Say which two readings you considered.

For the binary question, supported = supported; everything else = not supported.

## Reading the claim
- A claim with no explicit quantifier is a **default rule**, not a universal. It is universal only if its own words
  say so ("always", "never", "any", "every", "all", "only", "regardless", "without exception", "whether or not").
- A claim of possibility or "some" ("may", "can", "some") is established if the source provides for it in at least
  some circumstances, even conditional ones.

## Omissions
1. **Harmless omission: still supported.** The claim leaves out an exception or proviso to a default rule, a saving
   clause, further cases the rule also covers, reasons, procedure or consequences that do not change whether the
   claim holds in the ordinary case.
2. **Necessary condition omitted: not established.** The claim leaves out something without which the conclusion would
   not arise at all: a precondition, a narrower population or class, a time window, or a hedge ("may", "is associated
   with", "was proposed") that the claim hardens. Test: take an ordinary case the claim covers; if the source's
   conclusion would not follow for it without the omitted element, the element is necessary.
   A universal claim that omits an exception is also not established.
3. **Contradiction.** The source asserts the opposite, a different value for the same quantity, or an incompatible
   attribution, about the same subject, time and scope. A statement about one time, scheme, or population does not
   contradict a claim about another.
4. **Insufficient evidence.** The source does not address the claim, addresses a different subject, time, scheme or
   population, or reports that evidence was not found. "No evidence that X" is not evidence of not-X unless the claim
   is itself that evidence exists.
5. **Context-dependent.** Label **ambiguous** when the text supports two readings that would change the label, for
   example whether an omitted element is an exception or a precondition; or which of two referents a pronoun or short
   name picks out.

## Compound claims
Every asserted part must be supported. One unsupported part makes the claim not established; one contradicted part
makes it contradicted.

## Other rules
- Negative claims ("no appeal lies") are supported by a source sentence that says the same negative thing.
- "X said Y" is supported by a source reporting that X said Y, whether or not Y is true.
- Statutory excerpts: the question is only what the excerpt says. Do not judge what the law currently is.
- Quote the words that decide your label in your reason, briefly, when you can.

## Recording
Fill in one row per review id: label, optional failure tags (free text, e.g. "necessary condition omitted"), a one-sentence
reason, your pseudonym, and the time in UTC. Do not guess at a source you cannot see; use ambiguous instead.
