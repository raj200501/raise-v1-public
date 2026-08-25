#!/usr/bin/env python3
"""Frozen reader for preregistration 0003 — the carved-DEFLATE scaling curve.

Written and committed BEFORE the corpus was manufactured and before any model was trained.

WHAT IS BEING TESTED. Given a carved window from the MIDDLE of a DEFLATE stream — no header, no
stream start, no plaintext — recover the encoder implementation and level that produced it. The
label factory is free and unbounded: compress any bytes under every (implementation, level) and
the label is the configuration you used. The question is whether quality rises with the VOLUME of
manufactured data, and the answer is a slope.

THE BAR (frozen). The study PASSES if and only if ALL of the following hold:

  scope         n_rungs >= 4 and decades_spanned >= 2.0
  slope         slope_ci95_low > 0            (paired bootstrap over evaluation examples)
  margin        top_rung_accuracy - best_trivial_baseline >= 0.05
  split         split_is_grouped_by_source is True
  null control  shuffled_label_accuracy <= chance_accuracy + 0.02

Anti-shield clauses (frozen):
  - The SPLIT clause is not optional and not a detail. A random split over fragments carved from
    the same source bytes measures content memorisation, not encoder identification. Round 2 of the
    archived trial killed a candidate on exactly this: random-split accuracy 0.4873 collapsing to
    0.1531 once whole groups were held out. If the split is not grouped by source, the study FAILS
    however good every other number is.
  - The NULL CONTROL is not optional. Shuffle the labels, retrain, and the same pipeline must fall
    to chance. If it does not, the pipeline is reading something other than the label and no other
    number from it means anything.
  - A MISSING field reads as failure. Absence is never a pass.
  - Failing any single clause fails the study. There is no aggregate score and no discretion.
  - A rising slope that fails the margin clause is reported as a rising slope that fails the margin
    clause. It is not reported as a success with a caveat.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "deflate_curve.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "deflate_verdict.json")

MIN_RUNGS = 4
MIN_DECADES = 2.0
MARGIN = 0.05
NULL_TOLERANCE = 0.02


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0003: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0003: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    fails: list[str] = []
    g = d.get

    n_rungs = g("n_rungs")
    if not isinstance(n_rungs, int) or n_rungs < MIN_RUNGS:
        fails.append(f"scope: n_rungs={n_rungs!r}, need >= {MIN_RUNGS}")
    dec = g("decades_spanned")
    if not isinstance(dec, (int, float)) or dec < MIN_DECADES:
        fails.append(f"scope: decades_spanned={dec!r}, need >= {MIN_DECADES}")

    lo = g("slope_ci95_low")
    if not isinstance(lo, (int, float)):
        fails.append("slope: slope_ci95_low missing")
    elif lo <= 0:
        fails.append(f"slope: slope_ci95_low={lo} does not exceed 0 — the curve is not established "
                     f"as rising")

    top, base = g("top_rung_accuracy"), g("best_trivial_baseline")
    if not isinstance(top, (int, float)) or not isinstance(base, (int, float)):
        fails.append("margin: top_rung_accuracy or best_trivial_baseline missing")
    else:
        m = top - base
        if m < MARGIN:
            fails.append(f"margin: {top} - {base} = {round(m, 4)} is below the preregistered {MARGIN}")

    if g("split_is_grouped_by_source") is not True:
        fails.append("split: split_is_grouped_by_source is not True — a random split measures "
                     "content memorisation, not encoder identification")

    nul, chance = g("shuffled_label_accuracy"), g("chance_accuracy")
    if not isinstance(nul, (int, float)) or not isinstance(chance, (int, float)):
        fails.append("null control: shuffled_label_accuracy or chance_accuracy missing")
    elif nul > chance + NULL_TOLERANCE:
        fails.append(f"null control: shuffled labels reached {nul}, above chance {chance} + "
                     f"{NULL_TOLERANCE} — the pipeline is reading something other than the label")

    verdict = "CURVE_ESTABLISHED" if not fails else "CURVE_NOT_ESTABLISHED"
    result = {
        "schema": "raise-v1/pivot_deflate_verdict/1",
        "preregistration": "0003-pivot-deflate-curve",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict,
        "failed_clauses": fails,
        "read": {k: g(k) for k in
                 ("n_rungs", "decades_spanned", "slope", "slope_ci95_low", "slope_ci95_high",
                  "top_rung_accuracy", "best_trivial_baseline", "chance_accuracy",
                  "shuffled_label_accuracy", "split_is_grouped_by_source", "n_classes")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0003 — carved-DEFLATE scaling curve")
    for k, v in result["read"].items():
        print(f"  {k:<28} {v}")
    if fails:
        print(f"\n  FAILED CLAUSES ({len(fails)}):")
        for f in fails:
            print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
