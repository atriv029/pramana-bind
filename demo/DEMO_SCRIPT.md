# Demonstration script (3–5 minutes)

Everything shown is a **recorded** result: `demo/viewer_exp2.html` is built from certificates in `demo/ledger_exp2/`, which were made from model
replies recorded during the frozen evaluation and decided by rule version N1/3.2. Say so at the start. No live model call is made and no baseline
error is staged. Open the viewer in a browser; run the three commands from the `demo/` folder.

## Demonstration A: evidence change and claim-part localisation (about 2 minutes)
| Step | Action | Expected on screen | Say |
|---|---|---|---|
| A1 | Open `viewer_exp2.html`; item 1 is selected | **Supported**. Two claim parts; evidence “approval rating of 90 %” bound to part 1 and “based on 320 reviews” bound to part 2, both *affirms · necessarily implies*; reference label SUPPORTS | “One claim, two parts: rating above 85%, fewer than 322 reviews. The model files a quote against each part. The program finds each quote and applies a fixed rule.” |
| A2 | Click item 2 | **Contradicted**. Same claim. Part 1 still supported; part 2 *denies* with “based on 323 reviews”; reason “part 2: a located passage states the opposite”; reference label REFUTES | “Only one figure in the source changed, 320 to 323. Only part 2 flips, and the record says which part and which words.” |
| A3 | Point to the two panels | Left: Support. Right: Integrity and replay, with `part_references` and `quote_offsets` rows | “Left is a reading by a model. Right is mechanical. They are never merged into one badge.” |
| A4 | Mention the defect | — | “Under our first rule version these two quotes were attached to the wrong parts. The verdict was right; the explanation was not. Every integrity check passed. We found it by reading this record.” |

Artifacts: items `vitaminc:5ede072ec9e77c00084d23f2_1` and `_2`; ledger sequence 1 and 2.

## Demonstration B: qualification and audit (about 2 minutes)
| Step | Action | Expected on screen | Say |
|---|---|---|---|
| B1 | Click item 3 (“Pink was born on September 8, 1979”) | **Not established**, reason “conditional on something the claim leaves out”; reference label SUPPORTS; review status “diagnosed as unnecessary by an AI-assisted reading; not human-reviewed” | “The source says exactly this. The model filed the stage name as a necessary condition, and the rule obeyed.” |
| B2 | Expand “Counterfactual: qualifier check switched off” | → **Supported**; note that it is a separate, unsigned output | “Switching the check off fixes this one. The signed record is untouched; the counterfactual is computed beside it.” |
| B3 | Click item 4 (the BPT3C citation) and expand the counterfactual | **Not established** with enforcement; **Supported** without; reference label Incorrect | “Here the check is right: the source limits which batches receive gradients. Switch it off and a wrong citation is accepted. Across four benchmarks the check costs 37 correct acceptances and prevents 6 false ones.” |
| B4 | Click item 5 (ContractNLI) | **Supported**; reference label NotMentioned; integrity all pass | “A reading the benchmark disagrees with. Integrity still passes. Integrity is not correctness.” |
| B5 | Terminal, command 1 | Every line PASS; “INTEGRITY AND REPLAY CHECKS PASSED”; “This does not assert that the extracted interpretation of the source is correct.” | “Audit with the signer's key, held separately.” |
| B6 | Terminal, command 2 | `FAIL hash_chain seq 2 this_hash mismatch`, `AUDIT FAILED` | “On a copy, change ‘323 reviews’ to ‘320 reviews’ inside the ledger. The audit fails at that entry.” |
| B7 | Terminal, command 3 | `FAIL signature … no trusted public key supplied` | “Without a key from outside the bundle, the signature proves nothing, so it fails.” |

```bash
python -m pramana_bind audit ledger_exp2/ledger.jsonl --pubkey "$(cat ledger_exp2/signer.pub)"
```

```bash
cp -r ledger_exp2 /tmp/tampered && sed -i '3s/323 reviews/320 reviews/' /tmp/tampered/ledger.jsonl && python -m pramana_bind audit /tmp/tampered/ledger.jsonl --pubkey "$(cat ledger_exp2/signer.pub)"
```

```bash
python -m pramana_bind audit ledger_exp2/ledger.jsonl
```

Expected output of all three is recorded in `demo/tamper_transcript_exp2.txt`. In this demo the public key sits beside the ledger for convenience;
in real use it must come from somewhere else. The private signing key is not in the bundle.

## Closing line (15 seconds), over Figure 2 of the report
“Four public benchmarks, one model. The typed record accepts fewer unsupported claims and misses more supported ones than asking directly, and we see no
clear advantage over generic structure. What it gives you is a decision someone else can replay and challenge, field by field.”

The earlier Experiment 1 viewer (`demo/viewer.html`, rule schema 2) is kept for the record.
