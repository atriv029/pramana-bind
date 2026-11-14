# Demo script (3–5 minutes)

Everything shown is **recorded**: `demo/viewer.html` is built from certificates made from the model replies saved
during the held-out evaluation. Say so on screen at the start. Nothing in this demo is a live model call, and no
baseline mistake is staged: on this evaluation the baselines made no false acceptances, so none is shown.

| Time | Screen | Say |
|---|---|---|
| 0:00–0:30 | Title card, then `demo/viewer.html` list | "A citation can point to a real source that does not say what the claim says. We asked whether a quote-grounded, rule-based pipeline catches that better than just asking a model. Short answer: it did not. What it does give you is a record anyone can re-check. These are recorded results." |
| 0:30–1:10 | Item 1, *Supported* (Governor, Article 156) | "The model proposes a quote; a string matcher finds it at these offsets; the rules say supported. Two panels: left is the conclusion, which rests on the model's reading. Right is integrity and replay, which is mechanical. They are never merged." |
| 1:10–1:50 | Item 2, *Not established* (Article 133, condition omitted) | "The claim says an appeal lies from any civil judgment. The model quoted the certification condition the claim leaves out. The reason is in plain language; the Nyāya term is secondary." Then item 3 (Article 30, 'every citizen'): "narrower subject". |
| 1:50–2:30 | Item 5, *Unresolved* | "The source could not be located. No model is called, and the status is unresolved. Not finding a source is no evidence about the citation." |
| 2:30–3:20 | Item 4, *Contradicted*, marked unstable | "This one is wrong. The claim is supported: it says 'no appeal lies', and so does the source. The model filed the source's negative sentence as a denial of the claim in two of three runs. Every integrity check still passes, because integrity is not correctness. This is the pipeline's known failure on negatively phrased claims." |
| 3:20–4:10 | Terminal: `demo/tamper_transcript.txt` commands, run live against `demo/ledger` | "Audit with the signer's key, obtained separately: passes. Change two words in one ledger line: fails at that sequence number. Audit without a trusted key: fails, because a key shipped in the bundle cannot vouch for itself." |
| 4:10–4:50 | Figure 1 from the report | "Held-out, 117 items, same model for everything. No system accepted an unsupported citation. The pipeline recovered 29 of 49 supported claims; a single direct question recovered 43. Grounding changed nothing because the model never misquoted. Labels are AI-drafted and still need human review." |

Commands for the terminal segment (run from `demo/`):

```bash
python -m pramana_bind audit ledger/ledger.jsonl --pubkey "$(cat ledger/signer.pub)"
```

```bash
cp -r ledger /tmp/tampered && sed -i '3s/High Court/Low Court/' /tmp/tampered/ledger.jsonl && python -m pramana_bind audit /tmp/tampered/ledger.jsonl --pubkey "$(cat ledger/signer.pub)"
```

```bash
python -m pramana_bind audit ledger/ledger.jsonl
```

In the demo the public key sits next to the ledger for convenience. In real use it must come from somewhere else.
