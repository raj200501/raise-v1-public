#!/usr/bin/env python3
"""Fill the PENDING rows of tools/pivot/DATASET_CARD.md from the banked artifacts. Nothing else.

The card promises, in its own header, that "none of them will be filled in by hand - they come
from the banked artifacts or they stay PENDING". This is that promise made mechanical: each row
has a function that reads specific JSON keys, and a row whose keys are absent is LEFT at PENDING
rather than guessed. Run it again after any re-measurement; it is idempotent.

Exit codes: 0 written; 2 no artifact to read (the card is left exactly as it was).
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARD = os.path.join(REPO, "tools", "pivot", "DATASET_CARD.md")
CURVE = os.path.join(REPO, "artifacts", "pivot", "deflate_curve.json")
VERDICT = os.path.join(REPO, "artifacts", "pivot", "deflate_verdict.json")

# Mirrors tools/readers/pivot_deflate_curve.py. The reader stays the authority; this is a renderer.
NULL_TOLERANCE = 0.02


def _load(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def rows(c, v):
    """label -> rendered cell, or None to leave the row at PENDING."""
    out = {}
    if isinstance(c.get("n_fragments"), int):
        out["Fragments"] = (f"{c['n_fragments']:,} "
                            f"({c.get('n_train_fragments', 0):,} train / "
                            f"{c.get('n_eval_fragments', 0):,} eval, grouped by source chunk)")
    nul, ch = c.get("shuffled_label_accuracy"), c.get("chance_accuracy")
    if isinstance(nul, (int, float)) and isinstance(ch, (int, float)):
        # The pass/fail word is DERIVED from the same tolerance the frozen reader applies, never
        # written in. A hardcoded "passes" here would keep reading "passes" on a run where the null
        # control had failed, which is the exact class of small untruth this repository exists to
        # not accumulate.
        out["Null control (shuffled labels)"] = (
            f"{nul} vs chance {ch} — "
            f"{'passes' if nul <= ch + NULL_TOLERANCE else 'FAILS'} "
            f"(tolerance {NULL_TOLERANCE})")
    if isinstance(c.get("best_trivial_baseline"), (int, float)):
        cell = (f"frozen set: {c.get('best_trivial_baseline_name')} "
                f"{c['best_trivial_baseline']}")
        if isinstance(c.get("best_baseline_expanded"), (int, float)):
            cell += (f"; expanded set: {c.get('best_baseline_expanded_name')} "
                     f"{c['best_baseline_expanded']}")
        out["Best trivial baseline"] = cell
    if all(isinstance(c.get(k), (int, float)) for k in ("slope", "slope_ci95_low", "slope_ci95_high")):
        out["Scaling slope, 95% interval"] = (
            f"{c['slope']:+.4f} accuracy/decade, 95% CI "
            f"[{c['slope_ci95_low']:+.4f}, {c['slope_ci95_high']:+.4f}] over "
            f"{c.get('decades_spanned')} decades")
    if v.get("verdict"):
        cell = f"**{v['verdict']}**"
        if v.get("failed_clauses"):
            cell += f" — {len(v['failed_clauses'])} failed clause(s), listed in VERDICT.md"
        out["Verdict from the frozen reader"] = cell
    return out


def main() -> int:
    c, v = _load(CURVE), _load(VERDICT)
    if not c and not v:
        print("no banked artifact; DATASET_CARD.md left unchanged", file=sys.stderr)
        return 2
    text = open(CARD, encoding="utf-8").read()
    filled, left = 0, []
    for label, cell in rows(c, v).items():
        pat = re.compile(rf"^\|\s*{re.escape(label)}\s*\|\s*(.*?)\s*\|$", re.M)
        if not pat.search(text):
            print(f"  !! no row labelled {label!r} in the card", file=sys.stderr)
            continue
        text = pat.sub(lambda m: f"| {label} | {cell} |", text, count=1)
        filled += 1
    for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*PENDING\s*\|$", text, re.M):
        left.append(m.group(1))
    open(CARD, "w", encoding="utf-8").write(text)
    print(f"DATASET_CARD.md: {filled} row(s) filled from artifacts, {len(left)} still PENDING"
          + (f" ({', '.join(left)})" if left else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
