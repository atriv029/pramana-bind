# Dataset manifest (retrieved 2026-11-15)

Raw files are cached unchanged in `data_cache/` (not committed). `fetch_datasets.sh` re-downloads them at the pinned
revisions. No remote dataset code was executed; all files are static JSON/JSONL/TSV. Adapted samples are in
`experiments/exp2/data/` with their own checksums in `ADAPT_REPORT.json`.

| Dataset | Original URL | Pinned revision | Licence (where verified) | Splits found (rows; labels) |
|---|---|---|---|---|
| ContractNLI | https://stanfordnlp.github.io/contract-nli/ (Download Dataset → resources/contract-nli.zip on the gh-pages branch of github.com/stanfordnlp/contract-nli) | gh-pages `eced6528` | CC BY 4.0 (`LICENSE` in the archive). The archive also has a `TERMS` file: using the data signifies agreement to those terms, which point to CC BY 4.0. **No separate acceptance was made on your behalf; please read TERMS.** | train 423 docs / 7,191 pairs; dev 61 / 1,037; test 123 / 2,091 (total 607 docs, 10,319 pairs, 17 hypotheses) |
| VitaminC | https://huggingface.co/datasets/tals/vitaminc | `be6febb7` | CC BY-SA 3.0 (dataset card, `LICENSE`) | dev 63,054 rows / 18,836 cases; test 55,197 / 16,487; train not downloaded (not needed) |
| SciCiteVal | https://huggingface.co/datasets/birdie0111/SciCiteVal | `d0bcba16` | CC BY 4.0 (dataset card) | experiment_dataset.tsv 1,034 rows (302 Correct, 302 Incorrect, 430 Unrelated), single split; Qasa_annotated.tsv 1,399 rows. Columns as found: Citation_context, Cited_content, Label, Twist_category. No id column: joined to QASA by exact text, 3 Correct/Incorrect rows and all Unrelated rows do not join |
| AttributionBench | https://huggingface.co/datasets/osunlp/AttributionBench (also github.com/OSU-NLP-Group/AttributionBench) | `62569e64`, configuration subset_balanced | Apache-2.0 (dataset card); constituent datasets have their own licences, not individually checked | dev 1,198; test 1,610; test_ood 1,686 (HAGRID 1,088, BEGIN 436, AttrScore-GenSearch 162), balanced labels |
| AVeriTeC (Experiment 1) | https://github.com/MichSchli/AVeriTeC | `7c62d1e` | CC BY-NC 4.0 | dev.json 500 claims |

Raw-file checksums (sha256):
```
e03fc77bbf8b53e2976a250e81d8a294bc3d5e5fb014521e477dee9340d6287b  contract-nli/contract-nli.zip
dbceb356cd6203b35b27be94a5fa85e499a81c34c42c89ad53060b39f0257ba5  contract-nli/contract-nli/train.json
310af7d661d2ab50ee3700169cef524c75f39fb296bbf5a515c229eb0f42e68e  contract-nli/contract-nli/dev.json
460267b56052a2dc5aead98eb35eadef9e6734d5723d37b4a9790e410f812387  contract-nli/contract-nli/test.json
544934677f5d133873e6d38f4557f8966f4efa5d3d70874ffe6913f2091b86b5  tals/vitaminc/dev.jsonl
7ad1808dbc30c62e0a1427a53022d0dfaff668a1fde3c4b612a2d266edd753ad  tals/vitaminc/test.jsonl
01e9ab2337cafb3fa1c590311cd082a7628a3e239fbcd0ad2757a0e9aaa71b40  birdie0111/SciCiteVal/experiment_dataset.tsv
fd1e95b14dcc3487a86672e2a00179d7c138a6a50af8c87b7000d9a29a3fae63  birdie0111/SciCiteVal/Qasa_annotated.tsv
a744d1f84e621015f7a7e1941c3fb3f0838be767645dfb2ec784efd3133ab7d6  osunlp/AttributionBench/dev_all_subset_balanced.jsonl
c2ff75dd4ea5cf12d86166ead66a96b42d5001a36daf02ff71303ef3317715a8  osunlp/AttributionBench/test_all_subset_balanced.jsonl
90d8f5363cec90197f80b3e896dad17e091a108a5bf282c3d515d48c9a01a934  osunlp/AttributionBench/test_ood_all_subset_balanced.jsonl
```

Not retrieved (optional in the handoff; out of time): FOLIO, ProofWriter, SciFact, ERASER, ALCE.
Redistribution: the repository commits only the adapted evaluation samples (a few hundred items per dataset, with
attribution and licence reference per item) and the adapters; VitaminC items carry CC BY-SA 3.0.
