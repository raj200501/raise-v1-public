#!/usr/bin/env python3
"""Frozen reader for preregistration 0005 - the EphemErr A2 test.

WHAT IS BEING TESTED. From a GPS broadcast navigation record alone - what every receiver on Earth
already holds - predict whether that record's signal-in-space ranging error will exceed a high
threshold at a future epoch. The label is manufactured by propagating the record and differencing
it against the precise post-processed orbit and clock, which are reconstructed days later from a
global tracking network the receiver has no access to.

WHY A2 IS THE WHOLE QUESTION. Five candidates across rounds 1-3 died because a rule anyone could
write by hand already owned the label, and none of them expected it. Round 2 flagged the URA/SISA
index as the likely dominant baseline here - it is the operator's own error bound and it ships FREE
inside the student's input. Pipeline validation then measured URA's rank correlation with SISRE at
-0.077, essentially nothing, and identified a DIFFERENT dominant baseline that round 2 never named:
satellite identity. Both are in the frozen baseline set below.

THE BAR (frozen). The A2 gate PASSES if and only if ALL hold:

  auc_margin       learned_auc - best_baseline_auc >= 0.05
  split            split_is_temporal is True - train on earlier days, test on strictly later ones
  null_control     shuffled_label_auc <= 0.55
  scope            n_test_epochs >= 20000 and n_satellites >= 20

Anti-shield clauses (frozen):
  - The baseline set is FROZEN here and is not a formality: global mean, PER-SATELLITE historical
    mean, URA index alone, and per-satellite mean combined with age-of-data. `best_baseline_auc` is
    the maximum over that set. Adding a stronger baseline later is allowed and must be reported
    SEPARATELY; it may not replace this set, and it may not be dropped if it wins.
  - A TEMPORAL split is required. A random split over epochs lets the model see the same satellite
    on the same day and measures memorisation of a slowly varying state, not prediction. This is
    the direct analogue of the grouped-split clause that caught a 0.4873 -> 0.1531 collapse in the
    archived trial.
  - A MISSING field reads as failure. Absence is never a pass.
  - Failing any single clause fails the gate. No aggregate score, no discretion.
  - Passing A2 does NOT make EphemErr viable. It clears ONE gate. The scaling curve, G4 under the
    effort lens, and the buyer all remain untested.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "ephemerr", "a2_result.json")
OUT = os.path.join(REPO, "artifacts", "ephemerr", "a2_verdict.json")
MARGIN = 0.05
NULL_MAX = 0.55
MIN_TEST = 20000
MIN_SATS = 20


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0005: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              "  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0005: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    f, g = [], d.get
    learned, base = g("learned_auc"), g("best_baseline_auc")
    if not isinstance(learned, (int, float)) or not isinstance(base, (int, float)):
        f.append("learned_auc or best_baseline_auc missing")
    else:
        m = learned - base
        if m < MARGIN:
            f.append(f"auc_margin: {learned} - {base} = {round(m, 4)} is below the frozen {MARGIN}")
    if g("split_is_temporal") is not True:
        f.append("split_is_temporal is not True - a random split measures memorisation of a slowly "
                 "varying state, not prediction")
    nul = g("shuffled_label_auc")
    if not isinstance(nul, (int, float)):
        f.append("shuffled_label_auc missing")
    elif nul > NULL_MAX:
        f.append(f"null control: shuffled labels reached AUC {nul}, above {NULL_MAX}")
    n = g("n_test_epochs")
    if not isinstance(n, int) or n < MIN_TEST:
        f.append(f"scope: n_test_epochs={n!r}, need >= {MIN_TEST}")
    s = g("n_satellites")
    if not isinstance(s, int) or s < MIN_SATS:
        f.append(f"scope: n_satellites={s!r}, need >= {MIN_SATS}")

    verdict = "A2_PASSED" if not f else "A2_FAILED"
    res = {"schema": "raise-v1/ephemerr_a2_verdict/1",
           "preregistration": "0005-ephemerr-a2",
           "source_artifact": os.path.relpath(ARTIFACT, REPO),
           "verdict": verdict, "failed_clauses": f,
           "read": {k: g(k) for k in ("learned_auc", "best_baseline_auc", "best_baseline_name",
                                      "baseline_aucs", "shuffled_label_auc", "split_is_temporal",
                                      "n_test_epochs", "n_satellites", "positive_rate")},
           "what_passing_means": "Clears ONE gate. The scaling curve, G4 under the effort lens and "
                                 "the buyer all remain untested."}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("READER 0005 - EphemErr A2")
    for k, v in res["read"].items():
        print(f"  {k:<22} {v}")
    if f:
        print(f"\n  FAILED CLAUSES ({len(f)}):")
        for x in f:
            print(f"    · {x}")
    print(f"\n  VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
