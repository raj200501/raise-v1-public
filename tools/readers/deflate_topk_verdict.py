#!/usr/bin/env python3
"""Frozen reader for preregistration 0006 — is the carved-DEFLATE output operationally usable?

Written and committed BEFORE any top-k or confidence number existed on this corpus.

WHY THIS EXISTS. Preregistration 0003 is already decided: the curve is established and top-1 at the
top rung is 0.2395. Top-1 is the wrong reading for the only buyer type where a CARVED fragment is
genuinely the operational setting. A forensic analyst facing 26 candidate encoders wants a
shortlist, and wants to know when to ignore the tool. This asks whether the model produces those.

It does NOT establish a buyer. Clearing every clause below would not establish one.

THE BAR (frozen). OUTPUT_USABLE if and only if ALL of the following hold:

  scope             n_rungs >= 4 and decades_spanned >= 2.0
  top5 margin       top5_accuracy - best_trivial_baseline_top5        >= 0.05
  top5 margin (exp) top5_accuracy - best_baseline_expanded_top5       >= 0.05
  selective margin  selective_top_decile_accuracy
                      - baseline_selective_top_decile_accuracy        >= 0.05
  selective floor   selective_top_decile_accuracy                     >= 0.50
  top5 slope        top5_slope_ci95_low > 0
  null control      shuffled_label_top5_accuracy <= 0.2123   (5/26 chance + 0.02)

Anti-shield clauses (frozen):
  - BOTH top-5 margins are clauses. 0003 reported the frozen and expanded baseline sets voluntarily;
    here the expanded one binds. Ranking 5 of 26 is a far easier task than picking 1, so the model's
    advantage may not survive it — that is the most likely honest failure and it is not a footnote.
  - Baselines are scored on their OWN predict_proba and their OWN most-confident decile. Comparing a
    model's shortlist against a baseline's single guess would be rigged.
  - The NULL CONTROL matters MORE here than in 0003, not less: a top-5 metric is five times easier to
    satisfy by luck than top-1.
  - If the top-5 clauses pass and the selective clauses fail, that is reported as a usable shortlist
    with UNUSABLE CONFIDENCE. It is not a success with a caveat.
  - A missing field reads as failure. Absence is never a pass.
  - Failing any single clause fails the study. No aggregate score, no discretion.
  - This reader cannot revise or reinterpret 0003. That verdict stands whatever this one says.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "deflate_topk.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "deflate_topk_verdict.json")

MIN_RUNGS = 4
MIN_DECADES = 2.0
MARGIN = 0.05
SELECTIVE_FLOOR = 0.50
NULL_TOP5_MAX = 0.2123


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0006: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0006: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    fails: list[str] = []
    g = d.get

    def num(key):
        v = g(key)
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    n_rungs = g("n_rungs")
    if not isinstance(n_rungs, int) or n_rungs < MIN_RUNGS:
        fails.append(f"scope: n_rungs={n_rungs!r}, need >= {MIN_RUNGS}")
    dec = num("decades_spanned")
    if dec is None or dec < MIN_DECADES:
        fails.append(f"scope: decades_spanned={g('decades_spanned')!r}, need >= {MIN_DECADES}")

    top5 = num("top5_accuracy")
    for key, label in (("best_trivial_baseline_top5", "top5 margin (frozen set)"),
                       ("best_baseline_expanded_top5", "top5 margin (expanded set)")):
        base = num(key)
        if top5 is None or base is None:
            fails.append(f"{label}: top5_accuracy or {key} missing")
        elif top5 - base < MARGIN:
            fails.append(f"{label}: {top5} - {base} = {round(top5 - base, 4)} is below the "
                         f"preregistered {MARGIN}")

    sel, bsel = num("selective_top_decile_accuracy"), num("baseline_selective_top_decile_accuracy")
    if sel is None or bsel is None:
        fails.append("selective margin: selective_top_decile_accuracy or its baseline is missing")
    elif sel - bsel < MARGIN:
        fails.append(f"selective margin: {sel} - {bsel} = {round(sel - bsel, 4)} is below the "
                     f"preregistered {MARGIN}")
    if sel is None:
        fails.append("selective floor: selective_top_decile_accuracy missing")
    elif sel < SELECTIVE_FLOOR:
        fails.append(f"selective floor: {sel} is below the preregistered {SELECTIVE_FLOOR} — on the "
                     f"tenth of fragments it is surest about, the tool is wrong more often than right")

    lo = num("top5_slope_ci95_low")
    if lo is None:
        fails.append("top5 slope: top5_slope_ci95_low missing")
    elif lo <= 0:
        fails.append(f"top5 slope: top5_slope_ci95_low={lo} does not exceed 0")

    if g("split_is_grouped_by_source") is not True:
        fails.append("split: split_is_grouped_by_source is not True")

    nul = num("shuffled_label_top5_accuracy")
    if nul is None:
        fails.append("null control: shuffled_label_top5_accuracy missing")
    elif nul > NULL_TOP5_MAX:
        fails.append(f"null control: shuffled labels reached top-5 {nul}, above the {NULL_TOP5_MAX} "
                     f"chance-plus-tolerance level — a top-5 metric is five times easier to satisfy "
                     f"by luck and this pipeline is reading something other than the label")

    verdict = "OUTPUT_USABLE" if not fails else "OUTPUT_NOT_USABLE"
    # Named in advance so the most likely partial outcome cannot be spun as a success with a caveat.
    shortlist_ok = not any(f.startswith("top5 margin") or f.startswith("top5 slope") for f in fails)
    confidence_ok = not any(f.startswith("selective") for f in fails)
    if verdict == "OUTPUT_NOT_USABLE" and shortlist_ok and not confidence_ok:
        shape = "USABLE SHORTLIST, UNUSABLE CONFIDENCE"
    elif verdict == "OUTPUT_NOT_USABLE" and confidence_ok and not shortlist_ok:
        shape = "USABLE CONFIDENCE, SHORTLIST NO BETTER THAN A DUMB RULE"
    elif verdict == "OUTPUT_NOT_USABLE":
        shape = "NEITHER HALF USABLE"
    else:
        shape = "BOTH HALVES USABLE"

    result = {
        "schema": "raise-v1/deflate_topk_verdict/1",
        "preregistration": "0006-deflate-operational-output",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict,
        "shape": shape,
        "failed_clauses": fails,
        "establishes_a_buyer": False,
        "read": {k: g(k) for k in
                 ("n_rungs", "decades_spanned", "top1_accuracy", "top3_accuracy", "top5_accuracy",
                  "best_trivial_baseline_top5", "best_trivial_baseline_top5_name",
                  "best_baseline_expanded_top5", "best_baseline_expanded_top5_name",
                  "selective_top_decile_accuracy", "baseline_selective_top_decile_accuracy",
                  "top5_slope", "top5_slope_ci95_low", "top5_slope_ci95_high",
                  "shuffled_label_top5_accuracy", "split_is_grouped_by_source", "n_classes")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0006 — carved-DEFLATE operational output")
    for k, v in result["read"].items():
        print(f"  {k:<38} {v}")
    if fails:
        print(f"\n  FAILED CLAUSES ({len(fails)}):")
        for f in fails:
            print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}   [{shape}]")
    print("  This does not establish a buyer, and was never capable of doing so.")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
