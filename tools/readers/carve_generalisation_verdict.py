#!/usr/bin/env python3
"""Frozen reader for preregistration 0007 — does the carved-DEFLATE result survive a shorter carve?

Written and committed BEFORE the shorter-carve corpus was manufactured and before any model was
trained on it.

WHY THIS EXISTS. Everything in 0003 and 0006 is measured at ONE carve size, 4096 bytes. A forensic
analyst — the only buyer type for which a carved fragment is genuinely the operational setting —
gets whatever the carve yields, and file-carving works in disk clusters that are frequently
smaller. If the result collapses at a shorter window, the one setting where this task is real stops
being real, and that matters more than any further gain at 4096.

TWO QUESTIONS, and they have different consequences:

  WITHIN-SIZE   Train and evaluate at the shorter carve. Is the information still there at all?
  TRANSFER      Take a model trained at 4096 and evaluate it on the shorter carve, at a MATCHED
                training rung so the comparison is about carve size and not about data volume.

THE BAR (frozen). Every within-size clause, then the transfer clause:

  scope            n_rungs >= 4 and decades_spanned >= 2.0
  within margin    within_top1 - within_best_trivial_baseline           >= 0.05
  within margin    within_top1 - within_best_baseline_expanded          >= 0.05   (deep trees too)
  within slope     within_slope_ci95_low > 0
  split            within_split_is_grouped_by_source is True
  null control     within_shuffled_label_accuracy <= chance + 0.02
  transfer margin  transfer_top1 - within_best_trivial_baseline         >= 0.05

VERDICTS, and what each one means — stated here, before the data, so the middle outcome cannot be
spun in either direction afterwards:

  CARVE_FAILS           a within-size clause fails. The information is not recoverable at the
                        shorter carve, and the forensic setting is narrower than 0006 implies.
  CARVE_SIZE_SPECIFIC   within-size passes, transfer fails. This is NOT a failure of the
                        label-factory thesis: the manufacturer is free, so one model per carve size
                        costs another compression pass and nothing else. It IS a failure of the
                        "one model reads a whole disk image" story, and anyone quoting the 4096
                        numbers at a different window would be quoting them wrongly.
  CARVE_ROBUST          both pass. One model spans carve sizes.

Anti-shield clauses (frozen):
  - The two corpora share NO source chunks. The chunk index is the generator seed, so overlapping
    indices would mean a transfer model evaluated on source bytes it had already trained on. The
    shorter-carve corpus is built at an offset past the first corpus's entire range.
  - The transfer arm is compared at a MATCHED training rung. Comparing a top rung against a smaller
    one would confound carve size with data volume.
  - The transfer arm is scored against the SHORTER corpus's own trivial baselines. A transfer number
    that beats nothing local is not evidence of transfer.
  - A missing field reads as failure. Absence is never a pass.
  - This reader cannot revise 0003 or 0006. Those verdicts stand whatever this one says.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation_verdict.json")

MIN_RUNGS = 4
MIN_DECADES = 2.0
MARGIN = 0.05
NULL_TOLERANCE = 0.02


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0007: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0007: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    g = d.get

    def num(key):
        v = g(key)
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    within: list[str] = []
    n_rungs = g("n_rungs")
    if not isinstance(n_rungs, int) or n_rungs < MIN_RUNGS:
        within.append(f"scope: n_rungs={n_rungs!r}, need >= {MIN_RUNGS}")
    dec = num("decades_spanned")
    if dec is None or dec < MIN_DECADES:
        within.append(f"scope: decades_spanned={g('decades_spanned')!r}, need >= {MIN_DECADES}")

    top1 = num("within_top1")
    base = num("within_best_trivial_baseline")
    exp = num("within_best_baseline_expanded")
    if top1 is None or base is None:
        within.append("within margin: within_top1 or within_best_trivial_baseline missing")
    elif top1 - base < MARGIN:
        within.append(f"within margin (frozen set): {top1} - {base} = {round(top1 - base, 4)} "
                      f"is below the preregistered {MARGIN}")
    if top1 is None or exp is None:
        within.append("within margin (expanded): within_top1 or within_best_baseline_expanded missing")
    elif top1 - exp < MARGIN:
        within.append(f"within margin (expanded set): {top1} - {exp} = {round(top1 - exp, 4)} "
                      f"is below the preregistered {MARGIN}")

    lo = num("within_slope_ci95_low")
    if lo is None:
        within.append("within slope: within_slope_ci95_low missing")
    elif lo <= 0:
        within.append(f"within slope: within_slope_ci95_low={lo} does not exceed 0")

    if g("within_split_is_grouped_by_source") is not True:
        within.append("split: within_split_is_grouped_by_source is not True")

    nul, chance = num("within_shuffled_label_accuracy"), num("chance_accuracy")
    if nul is None or chance is None:
        within.append("null control: within_shuffled_label_accuracy or chance_accuracy missing")
    elif nul > chance + NULL_TOLERANCE:
        within.append(f"null control: shuffled labels reached {nul}, above chance {chance} + "
                      f"{NULL_TOLERANCE}")

    transfer: list[str] = []
    tt = num("transfer_top1")
    if tt is None or base is None:
        transfer.append("transfer margin: transfer_top1 or within_best_trivial_baseline missing")
    elif tt - base < MARGIN:
        transfer.append(f"transfer margin: {tt} - {base} = {round(tt - base, 4)} is below the "
                        f"preregistered {MARGIN} — a model trained at the longer carve does not "
                        f"beat the shorter corpus's own dumb rules")
    if g("corpora_share_source_chunks") is not False:
        transfer.append("transfer: corpora_share_source_chunks is not False — the transfer model may "
                        "have trained on source bytes present in this evaluation set")

    if within:
        verdict, meaning = "CARVE_FAILS", (
            "The information is not recoverable at the shorter carve. The forensic setting is "
            "narrower than the 4096 numbers imply.")
    elif transfer:
        verdict, meaning = "CARVE_SIZE_SPECIFIC", (
            "Within-size passes; transfer does not. This is NOT a failure of the label-factory "
            "thesis — the manufacturer is free, so one model per carve size costs another "
            "compression pass and nothing else. It IS a failure of the 'one model reads a whole "
            "disk image' story, and quoting the 4096 numbers at a different window would be "
            "quoting them wrongly.")
    else:
        verdict, meaning = "CARVE_ROBUST", "One model spans carve sizes."

    result = {
        "schema": "raise-v1/carve_generalisation_verdict/1",
        "preregistration": "0007-carve-size-generalisation",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict,
        "meaning": meaning,
        "within_size_failed_clauses": within,
        "transfer_failed_clauses": transfer,
        "establishes_a_buyer": False,
        "read": {k: g(k) for k in
                 ("carve_bytes", "reference_carve_bytes", "matched_rung", "n_rungs",
                  "decades_spanned", "within_top1", "within_best_trivial_baseline",
                  "within_best_trivial_baseline_name", "within_best_baseline_expanded",
                  "within_best_baseline_expanded_name", "within_slope", "within_slope_ci95_low",
                  "transfer_top1", "reference_matched_rung_top1", "chance_accuracy",
                  "within_shuffled_label_accuracy", "within_split_is_grouped_by_source",
                  "corpora_share_source_chunks", "n_classes")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0007 — carve-size generalisation")
    for k, v in result["read"].items():
        print(f"  {k:<34} {v}")
    for label, fails in (("WITHIN-SIZE", within), ("TRANSFER", transfer)):
        if fails:
            print(f"\n  {label} FAILED CLAUSES ({len(fails)}):")
            for f in fails:
                print(f"    · {f}")
    print(f"\n  VERDICT: {verdict}")
    print(f"  {meaning}")
    print("  This does not establish a buyer, and was never capable of doing so.")
    print(f"  wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
