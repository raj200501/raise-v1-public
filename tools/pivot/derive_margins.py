#!/usr/bin/env python3
"""Derive the 0006 margins from the banked readings. Arithmetic only; no model is re-run.

Why this is a separate script. tools/pivot/run_topk.py banks the readings but not the differences
between them, which is an omission in that script - 0003's run_study.py banks its margins directly.
The frozen reader computes the same differences internally, but it CANNOT be edited to emit them:
its sha256 is sealed into the preregistration chain, and changing it would fail prereg.py verify,
which is the point of freezing it.

So the margins are derived here instead: a shipped, deterministic, re-runnable script over values
that are already banked. That places them in this repository's `arithmetic-verifiable` class - they
follow by subtraction from a banked artifact - rather than letting them be typed into prose where
the outbound-copy gate would rightly refuse them.

Exit codes: 0 written; 2 the source artifact is missing.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "artifacts", "pivot", "deflate_topk.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "deflate_topk_margins.json")

PAIRS = [
    ("top5_margin_frozen", "top5_accuracy", "best_trivial_baseline_top5",
     "top-5 accuracy minus the best PREREGISTERED baseline's top-5"),
    ("top5_margin_expanded", "top5_accuracy", "best_baseline_expanded_top5",
     "top-5 accuracy minus the best baseline's top-5 over ALL baselines, deep trees included"),
    ("selective_margin", "selective_top_decile_accuracy",
     "baseline_selective_top_decile_accuracy",
     "accuracy on the model's own most-confident decile minus the best baseline's accuracy on its "
     "own most-confident decile, taking the maximum over ALL baselines"),
]


FROZEN_SET = ["majority", "stratified", "depth3_tree", "logistic"]


def main() -> int:
    if not os.path.exists(SRC):
        print(f"derive_margins: {os.path.relpath(SRC, REPO)} absent", file=sys.stderr)
        return 2
    d = json.load(open(SRC, encoding="utf-8"))
    out = {"schema": "raise-v1/deflate_topk_margins/1",
           "preregistration": "0006-deflate-operational-output",
           "derivation": "each value is a - b over fields of artifacts/pivot/deflate_topk.json; "
                         "no model is re-run and no new measurement is made",
           "bar": 0.05, "margins": {}}
    for name, a, b, why in PAIRS:
        out["margins"][name] = {
            "value": round(float(d[a]) - float(d[b]), 4),
            "minuend": {"field": a, "value": d[a]},
            "subtrahend": {"field": b, "value": d[b]},
            "clears_bar": bool(round(float(d[a]) - float(d[b]), 4) >= 0.05),
            "meaning": why,
        }
    # The counterfactual: what the selective margin WOULD have been under the looser reading of
    # "the best trivial baseline" - best of the FROZEN set only, rather than the maximum over all
    # baselines. The strict reading was fixed and drand-anchored before the run; this records the
    # size of the concession that was declined, so the choice is auditable rather than asserted.
    bl = d["baseline_selective_top_decile"]
    frozen_best = max((k for k in bl if k in FROZEN_SET), key=lambda k: bl[k])
    out["margins"]["selective_margin_under_looser_frozen_set_reading"] = {
        "value": round(float(d["selective_top_decile_accuracy"]) - float(bl[frozen_best]), 4),
        "minuend": {"field": "selective_top_decile_accuracy",
                    "value": d["selective_top_decile_accuracy"]},
        "subtrahend": {"field": f"baseline_selective_top_decile.{frozen_best}",
                       "value": bl[frozen_best]},
        "clears_bar": True,
        "meaning": ("NOT the reading used. Recorded so the declined concession is auditable: this is "
                    "the margin the study would have claimed had 'best trivial baseline' been read "
                    "as best-of-frozen-set instead of maximum-over-all-baselines."),
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    for k, v in out["margins"].items():
        print(f"  {k:<22} {v['value']:+.4f}   {'clears' if v['clears_bar'] else 'BELOW'} 0.05")
    print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


CARVE_SRC = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation.json")
CARVE_OUT = os.path.join(REPO, "artifacts", "pivot", "carve_margins.json")

CARVE_PAIRS = [
    ("within_margin_frozen", "within_top1", "within_best_trivial_baseline",
     "top-1 at the shorter carve minus that corpus's best PREREGISTERED baseline"),
    ("within_margin_expanded", "within_top1", "within_best_baseline_expanded",
     "top-1 at the shorter carve minus its best baseline over ALL baselines"),
    ("transfer_margin", "transfer_top1", "within_best_trivial_baseline",
     "a model trained at the LONGER carve, evaluated on the shorter corpus, minus that corpus's "
     "own best baseline"),
    ("carve_size_cost_at_matched_rung", "within_top1_at_matched_rung",
     "reference_matched_rung_top1",
     "the same training volume at 1024 versus at 4096 - what the shorter window costs, holding "
     "data volume fixed"),
]


CARVE2048_SRC = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation_2048.json")
CARVE2048_OUT = os.path.join(REPO, "artifacts", "pivot", "carve_margins_2048.json")

CARVE2048_PAIRS = CARVE_PAIRS[:3] + [
    ("within_margin_expanded_gutenberg_excluded", "within_top1_non_gutenberg",
     "within_best_baseline_expanded_non_gutenberg",
     "top-1 at 2048 minus its best baseline over ALL baselines, both scored on the evaluation rows "
     "whose source family is not gutenberg - the rows the chunk-id disjointness guarantee covers"),
    ("transfer_margin_gutenberg_excluded", "transfer_top1_non_gutenberg",
     "within_best_trivial_baseline_non_gutenberg",
     "the 4096-trained model on 2048-byte fragments minus corpus C's own best preregistered "
     "baseline, both on the non-gutenberg rows"),
    ("carve_size_cost_at_matched_rung", "within_top1_at_matched_rung",
     "reference_matched_rung_top1",
     "the same training volume at 2048 versus at 4096 - what the shorter window costs, holding "
     "data volume fixed"),
    ("carve_size_gain_over_1024_at_matched_rung", "within_top1_at_matched_rung",
     "carve1024_matched_rung_top1",
     "the same training volume at 2048 versus at 1024 (the banked 0007 matched-rung accuracy) - "
     "what the longer window buys back, holding data volume fixed"),
]


def carve_margins(src=CARVE_SRC, out_path=CARVE_OUT, prereg="0007-carve-size-generalisation",
                  pairs=CARVE_PAIRS, extra=None) -> int:
    """0007's margins (and, with the 2048 arguments, 0011's), same arithmetic-only derivation."""
    if not os.path.exists(src):
        return 2
    d = json.load(open(src, encoding="utf-8"))
    # The matched-rung accuracy is inside the rungs list rather than a top-level field.
    matched = next((r["accuracy"] for r in d.get("rungs", [])
                    if r["n_units"] == d.get("matched_rung")), None)
    d = dict(d, within_top1_at_matched_rung=matched, **(extra or {}))
    out = {"schema": "raise-v1/carve_margins/1",
           "preregistration": prereg,
           "derivation": f"each value is a - b over fields of {os.path.relpath(src, REPO)}; "
                         "no model is re-run and no new measurement is made",
           "bar": 0.05, "margins": {}}
    for name, a_, b_, why in pairs:
        if d.get(a_) is None or d.get(b_) is None:
            continue
        v = round(float(d[a_]) - float(d[b_]), 4)
        out["margins"][name] = {"value": v, "minuend": {"field": a_, "value": d[a_]},
                                "subtrahend": {"field": b_, "value": d[b_]},
                                "clears_bar": bool(v >= 0.05),
                                "distance_to_bar": round(0.05 - v, 4),
                                "meaning": why}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
    for k, v in out["margins"].items():
        print(f"  {k:<44} {v['value']:+.4f}   {'clears' if v['clears_bar'] else 'BELOW'} 0.05")
    print(f"wrote {os.path.relpath(out_path, REPO)}")
    return 0


def carve2048_margins() -> int:
    """0011's margins: the 0007 pairs plus the gutenberg-excluded readings in both arms and the
    matched-rung comparison against BOTH banked sizes (4096 from deflate_curve.json via the
    artifact's reference_matched_rung_top1; 1024 from carve_generalisation.json's rungs)."""
    if not os.path.exists(CARVE_SRC):
        return 2
    c1024 = json.load(open(CARVE_SRC, encoding="utf-8"))
    m1024 = next((r["accuracy"] for r in c1024.get("rungs", [])
                  if r["n_units"] == c1024.get("matched_rung")), None)
    return carve_margins(CARVE2048_SRC, CARVE2048_OUT, "0011-carve-2048-boundary", CARVE2048_PAIRS,
                         extra={"carve1024_matched_rung_top1": m1024})


ABL = os.path.join(REPO, "artifacts", "pivot", "feature_ablation.json")


def ablation_ratios() -> int:
    """Bank the 1024/4096 accuracy ratio per feature subset, in place, from banked accuracies.

    These were first computed ad hoc to write prose, and the outbound gate refused the prose because
    a ratio that exists only in a shell one-liner traces to nothing. Some of the ratios did happen to
    match unrelated banked values, which is exactly the coincidence that must not be leaned on.
    """
    if not os.path.exists(ABL):
        return 2
    d = json.load(open(ABL, encoding="utf-8"))
    a_, b_ = d["by_carve"].get("4096"), d["by_carve"].get("1024")
    if not a_ or not b_:
        return 2
    ratios = {k: round(b_[k]["accuracy"] / a_[k]["accuracy"], 4) for k in a_ if k in b_}
    d["ratio_1024_over_4096"] = ratios
    d["ratio_spread"] = round(max(ratios.values()) - min(ratios.values()), 4)
    d["ratio_min"] = min(ratios.values())
    d["ratio_max"] = max(ratios.values())
    d["ratio_derivation"] = ("each ratio is by_carve.1024.<subset>.accuracy divided by "
                             "by_carve.4096.<subset>.accuracy; arithmetic only, nothing re-run")
    with open(ABL, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"  ablation ratios {d['ratio_min']}..{d['ratio_max']}, spread {d['ratio_spread']}")
    return 0


if __name__ == "__main__":
    rc = main()
    carve_margins()
    carve2048_margins()
    ablation_ratios()
    raise SystemExit(rc)
