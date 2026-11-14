"""Regression cross-check on closed worlds (no ``unknown`` cells).

R1-R8 must agree with the pre-existing ``nyaya_validity.derive_verdict`` and,
where the prabhasa-nyaya ``score`` binary is built, with the Lean deciders.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from pravrudhi.application.nyaya_gold import build_gold_set
from pravrudhi.application.nyaya_gold_score import SCORE_BIN_ENV, _run_lean_scorer, lean_source_commit
from pravrudhi.application.nyaya_validity import derive_verdict

from .schema import Cell, Defeater, Quote, Verdict
from .verdict import derive_ow
from .world import World3

#: derive_verdict's name for R7
CLOSED_NAME = {Verdict.uncorroborated: "aprasiddha"}


def closed_to_world3(world: dict[str, Any], paksa: str, props: tuple[str, ...]) -> World3:
    """A closed world as a World3: every (locus, prop) cell is present or absent."""
    w = World3(paksa=paksa, paksa_located=paksa in world)
    for locus, held in world.items():
        for prop in props:
            w.cells[(locus, prop)] = Cell.present if prop in held else Cell.absent
    return w


def _located(text: str) -> Quote:
    return Quote(quote=text, source_id="constructed", located=True)


def item_to_world3(item: dict[str, Any]) -> World3:
    """A gold item, with its extra premise (if any) expressed as a defeater:
    a pratyaksa observation outranks the inference (badhita); an independently
    valid counter-inference to a different sadhya has equal rank (satpratipaksa)."""
    w = closed_to_world3(item["world"], item["paksa"], (item["hetu"], item["sadhya"]))
    obs = item.get("defeating_source", {}).get("observation")
    if obs and obs["polarity"] == "absent" and obs["locus"] == item["paksa"] and obs["prop"] == item["sadhya"]:
        w.defeaters.append(Defeater(quote=_located("observation"), authority_rank=w.cited_rank + 1))
    ci = item.get("counter_inference")
    if ci and ci["sadhya"] != item["sadhya"]:
        cw = {l: frozenset(p) for l, p in ci["world"].items()}
        ok = derive_verdict(cw, ci["paksa"], ci["sadhya"], ci["hetu"]) == "valid"
        w.defeaters.append(Defeater(quote=_located("counter-inference"), authority_rank=w.cited_rank,
                                    conclusion="incompatible", inference_valid=ok))
    return w


def _name(v: Verdict) -> str:
    return CLOSED_NAME.get(v, v.value)


def crosscheck_closed(per_class: int = 100, seed: int = 0,
                      score_bin: Optional[Path] = None) -> dict[str, Any]:
    items = build_gold_set(per_class, seed)
    n = len(items)
    agree_dv = agree_gold = 0
    ours: dict[str, str] = {}
    disagreements: list[dict[str, str]] = []
    for it in items:
        # (a) base inference, no extra premise, against derive_verdict
        base = closed_to_world3(it["world"], it["paksa"], (it["hetu"], it["sadhya"]))
        mine = _name(derive_ow(base, sadhya=it["sadhya"], hetu=it["hetu"])[0])
        dv = derive_verdict({l: frozenset(p) for l, p in it["world"].items()},
                            it["paksa"], it["sadhya"], it["hetu"])
        agree_dv += mine == dv
        if mine != dv:
            disagreements.append({"id": it["id"], "against": "derive_verdict", "ours": mine, "theirs": dv})
        # (b) full item, with its defeater, against the gold label
        full = _name(derive_ow(item_to_world3(it), sadhya=it["sadhya"], hetu=it["hetu"])[0])
        ours[it["id"]] = full
        agree_gold += full == it["expected"]
        if full != it["expected"]:
            disagreements.append({"id": it["id"], "against": "gold", "ours": full, "theirs": it["expected"]})

    lean: dict[str, Any] = {"ran": False, "reason": "score binary not available"}
    bin_path = score_bin or (Path(os.environ[SCORE_BIN_ENV]) if os.environ.get(SCORE_BIN_ENV) else None)
    if bin_path is not None and Path(bin_path).exists():
        lv = _run_lean_scorer(items, Path(bin_path))
        k = sum(1 for it in items if lv.get(it["id"]) == ours[it["id"]])
        lean = {"ran": True, "agree": k, "n": n, "binary_commit": lean_source_commit(Path(bin_path))}
        disagreements += [{"id": it["id"], "against": "lean", "ours": ours[it["id"]], "theirs": lv.get(it["id"], "")}
                          for it in items if lv.get(it["id"]) != ours[it["id"]]]
    return {
        "n": n, "per_class": per_class, "seed": seed,
        "derive_verdict": {"agree": agree_dv, "n": n},
        "gold_label": {"agree": agree_gold, "n": n},
        "lean": lean,
        "disagreements": disagreements,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(crosscheck_closed(), indent=1))
