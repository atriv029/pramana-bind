"""EXPLORATORY post-hoc replay of the Experiment 1 extractions with individual reasons switched off.
No model call. The extractions are the recorded ones; only the decision rule changes. This isolates a rule effect.
It is NOT a held-out test of any revised method: the rules were chosen after seeing Experiment 1's errors."""
import json, sys
from collections import Counter
from pathlib import Path

from pramana_bind.bind import conclude, decide
from pramana_bind.extract import parse
from pramana_bind.schema import Source

run = Path("eval/runs/test-haiku")
items = [json.loads(l) for l in open("eval/data/test.jsonl")]
calls = {(r["tag"]["item"], r["tag"]["run"]): r["text"] for r in map(json.loads, open(run / "calls.jsonl"))
         if r.get("ok") and r["tag"]["system"] == "extract"}
VARIANTS = {"as_run (guard off)": set(), "minus qualification_omitted": {"qualification_omitted"},
            "minus narrower_subject": {"narrower_subject"}, "minus quantifier/modality checks": {"quantifier_inflated", "modality_inflated"},
            "minus all three": {"qualification_omitted", "narrower_subject", "quantifier_inflated", "modality_inflated"}}
out = {"note": __doc__.strip(), "n": len(items), "variants": {}}
for name, off in VARIANTS.items():
    fs = tp = 0; flips = []
    for it in items:
        sts = []
        for k in range(3):
            av, _, _ = conclude(parse(calls[(it["id"], k)]), (), Source(), {"T": it["source_text"]}, guard=False)
            n = av.nigamana
            s = n.status.value
            if s == "not_established" and n.reasons and set(n.reasons) <= off:
                s = "supported"
            sts.append(s)
        pred = decide(sts)
        if it["label"] == "supported":
            tp += pred == "supported"
        else:
            fs += pred == "supported"
            if pred == "supported":
                flips.append(it["id"])
    out["variants"][name] = {"false_support": [fs, 68], "supported_recall": [tp, 49], "unsupported_items_accepted": flips}
    print(f"{name:34s} false-support {fs}/68  recall {tp}/49  {flips}")
Path("experiments/exp1/diagnostic_replay.json").write_text(json.dumps(out, indent=1))
