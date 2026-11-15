#!/usr/bin/env bash
# Fetch the original releases, pinned, unchanged, into data_cache/ (not committed). No remote code is executed.
set -euo pipefail
C="$(cd "$(dirname "$0")/../.." && pwd)/data_cache"; mkdir -p "$C"
hf() { # repo revision file
  mkdir -p "$C/$1/$(dirname "$3")"; [ -s "$C/$1/$3" ] || curl -sSfL -m 900 -o "$C/$1/$3" "https://huggingface.co/datasets/$1/resolve/$2/$3"; }
VITC=be6febb761b0b2807687e61e0b5282e459df2fa0
for f in dev.jsonl test.jsonl README.md LICENSE; do hf tals/vitaminc $VITC $f; done
SCV=d0bcba167856c634237ee87afc564085ae3417b1
for f in experiment_dataset.tsv Qasa_annotated.tsv README.md; do hf birdie0111/SciCiteVal $SCV $f; done
AB=62569e644f4186606f54f742178a4517431b42e1
for f in dev_all_subset_balanced.jsonl test_all_subset_balanced.jsonl test_ood_all_subset_balanced.jsonl README.md; do hf osunlp/AttributionBench $AB $f; done
# ContractNLI: the official page (stanfordnlp.github.io/contract-nli) is the gh-pages branch of the repo; its
# "Download Dataset" link is resources/contract-nli.zip on that branch.
CNLI=eced6528dd3c1d14d73f9a87df8f7bdbc03126f9
if [ ! -s "$C/contract-nli/contract-nli.zip" ]; then
  mkdir -p "$C/contract-nli"; t=$(mktemp -d)
  git clone -q --depth 1 -b gh-pages https://github.com/stanfordnlp/contract-nli "$t/r"
  test "$(git -C "$t/r" rev-parse HEAD)" = "$CNLI" || echo "WARNING: contract-nli gh-pages moved from pinned $CNLI" >&2
  cp "$t/r/resources/contract-nli.zip" "$C/contract-nli/"; cp "$t/r"/*.html "$C/contract-nli/" 2>/dev/null || true; rm -rf "$t"
fi
(cd "$C/contract-nli" && [ -d contract-nli ] || unzip -q -o contract-nli.zip)
