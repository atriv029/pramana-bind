# What "audit passed" means

`python -m pramana_bind audit LEDGER --pubkey KEY` reports **integrity and replay** checks. A pass means every
check below passed. It does **not** mean the extracted reading of the source is true.

## Five properties, kept apart
| # | Property | Checked by | Mechanical? |
|---|---|---|---|
| 1 | The quotation occurs in the supplied source | `locate_quote` (exact, else whitespace-collapsed; one occurrence only) | yes |
| 2 | The quotation supports the proposition it is filed under | nobody | **no: model testimony** |
| 3 | The proposition is about the right subject, scope, time, strength | compared mechanically, but from labels the extractor supplied (scope full/part, source quantifier and modality, omitted conditions); optional keyword guard | **partly** |
| 4 | The conclusion follows under the stated rules | `derive_full` (R0-R8) and `support_status`, pure functions | yes |
| 5 | The certificate is unchanged since its trusted checkpoint | hash chain + Ed25519 over the chain head | yes, given a trusted key |

`tests/test_semantic_boundary.py` holds a counterexample for each gap. Tests named `test_LIMIT_*` assert behaviour
that is wrong as a judgement of support (an exact quote filed with inverted polarity; a correct quote attached to the
wrong entity; correlation filed as causation) and are kept so that the limit is stated in code.

## What the audit recomputes
Nothing derived is read from the certificate and believed. For each certificate the auditor:
1. recomputes the certificate id from the canonical (JCS) body;
2. checks schema and rules versions against the auditor's own;
3. loads each source text by its recorded sha256 and re-hashes it;
4. discards the stored `located`, offsets, match mode and context flags of every quote and re-locates every quote;
5. rebuilds the three-valued world from those re-located quotes (the world is never stored);
6. re-derives verdict, rule, support status, reasons and PBS and compares them with the certificate;
7. checks that the item-level status follows from the recorded per-run statuses by the fixed decision rule.

What is taken as given: the extractor's quotes and how it filed them, and the recorded statuses of the two
non-representative extraction runs (their tuples are not stored, so they are recorded, not replayable).

Recorded for each certificate: source hashes and per-quote match mode; system-computed offsets; extractor model id,
prompt hash, number of runs, grounding and guard settings; rule and schema versions; ledger sequence number, previous
hash and own hash; and, beside the ledger, the signed head (sequence number, head hash, signature).

## The signature and whose key it is
The chain head is signed with Ed25519. The auditor must supply the signer's public key **from somewhere other than
the bundle being audited**. The signature file carries a copy of the public key for convenience, but the audit never
uses it: anyone who can rewrite the ledger can also re-sign it and ship their own key, so a key that arrives with the
bundle gives no assurance about who signed. Without `--pubkey` the signature step fails.

## The rollback boundary
A local signed hash chain shows that a ledger is internally consistent and was signed by the key holder at that head.
It does not show that the ledger is the *latest* one. An older copy, correctly signed at its own head, passes.
To detect rollback or a fork the auditor needs a head they saw earlier: `--checkpoint SEQ:HASH` fails if the ledger
is shorter than, or disagrees with, that point. This is not a transparency log: there is no public append-only
record, no consistency proof between heads, and no third-party witness. The signer can still show different ledgers
to different people who do not compare notes.

## Tamper tests that run in CI (`tests/test_pipeline.py`)
One-character edit; reordered events; a deleted middle event; truncation; a key substituted by a re-signing attacker;
no key supplied; an unsigned tail; rollback with and without a checkpoint; a swapped source text; and, for a forger
who recomputes the id and rebuilds the whole chain: a changed verdict, status, item-level status, score, quote
offsets, `located` flag, or context flag.
