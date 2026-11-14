# Pramāṇa-Bind

Typed, replayable citation verdicts from Nyāya inference structure.
The model proposes; string matching and set theory dispose.

## Disclosure: what is sprint work and what is not

| Piece | Status |
|---|---|
| `pravrudhi` engine: `nyaya_quote.locate_quote`, `nyaya_validity.derive_verdict`, `nyaya_gold`, `nyaya_gold_score`, `nyaya.Corpus` and the statute corpus | **Pre-existing** (before 13 Nov 2026), imported as a dependency |
| `pravrudhi_kernel.ledger` (hash-chained JSONL, JCS, verify) | **Pre-existing**, imported |
| `prabhasa-nyaya` Lean deciders | **Pre-existing**, external binary; see "Lean" below |
| Everything in this repository | **New during the sprint** |

## Install and test

```bash
uv venv && uv pip install -e /path/to/pravrudhi-main/pravrudhi_kernel -e /path/to/pravrudhi-main -e '.[dev]'
```

```bash
.venv/bin/pytest -q
```

## Commands (none calls a model)

```bash
python -m pramana_bind crosscheck          # R1-R8 vs derive_verdict (and Lean if PRABHASA_NYAYA_SCORE_BIN is set)
python -m pramana_bind keygen signer.key   # prints the public key
python -m pramana_bind sign ledger.jsonl signer.key
python -m pramana_bind audit ledger.jsonl --pubkey <base64>
```

## What is and is not checked

- **Derived, replayable:** quote location and offsets, the three-valued world, the verdict (R0-R8), PBS, the hash chain, the head signature. `audit` recomputes all of these.
- **Model testimony (agama), not checked:** which subject, reason and loci the extractor chose; whether a located quote really asserts or denies the property it is filed under; the `scope: part` judgement behind asiddha/bhāga. Extraction stability across runs is reported for this reason.
- **Lean:** the Lean deciders work on closed worlds. They are exercised by `crosscheck`, not per certificate, and only when the `score` binary is present. A certificate's `checks.lean.ran` is `false` otherwise.
