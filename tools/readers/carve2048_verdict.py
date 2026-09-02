#!/usr/bin/env python3
"""Frozen reader for preregistration 0011 — where, between 1024 and 4096 bytes, does the carved-DEFLATE
result stop holding?

Written and committed BEFORE the 2048-byte corpus was manufactured and before any model was trained
on it.

WHY THIS EXISTS. The record holds exactly two carve sizes. At 4096 the task clears its bar
(0003, CURVE_ESTABLISHED); at 1024 it ties a dumb rule (0007, CARVE_FAILS). "Valid only at a
4096-byte window" is therefore a two-point statement with an unmeasured boundary somewhere in a
factor of four. This run measures the geometric midpoint, 2048, under the 0007 protocol, and
locates the boundary to a factor of two. It is the M3 carve-size arm of the milestone map, run not
at a buyer-reported size — none is known — but at the size that bounds the record's own scope
statement.

TWO QUESTIONS, as in 0007:

  WITHIN-SIZE   Train and evaluate at 2048. Does the bar clear here?
  TRANSFER      Take a model trained at 4096 and evaluate it on 2048-byte fragments at a MATCHED
                training rung.

THE BAR (frozen). Every within-size clause, then the transfer clause:

  scope            carve_bytes == 2048, reference_carve_bytes == 4096,
                   n_rungs >= 4 and decades_spanned >= 2.0
  within margin    within_top1 - within_best_trivial_baseline                        >= 0.05
  within margin    within_top1 - within_best_baseline_expanded                       >= 0.05
  within margin    within_top1_non_gutenberg - within_best_baseline_expanded_non_gutenberg
                                                                                     >= 0.05
  within slope     within_slope_ci95_low > 0
  split            within_split_is_grouped_by_source is True
  null control     within_shuffled_label_accuracy <= chance + 0.02
  disjointness     corpora_share_source_chunks is False AND corpus_b_chunk_offset >= 75000
                   (past corpus A's 0..49999 AND corpus B's 50000..74999)
  transfer margin  transfer_top1 - within_best_trivial_baseline                      >= 0.05

The gutenberg-excluded clause is new and is there because the audit of 2026-08-31 found that the
gutenberg family draws its chunks from one shared byte pool, so "disjoint source chunks" is a
guarantee about the seven synthetic families only. That clause binds the margin to the rows the
guarantee actually covers. It is a STRICTER bar than 0007's, chosen knowing that in 0003 excluding
gutenberg widened the margins — a clause that could only help the result would be a shield, and
this one can fail on its own.

VERDICTS, stated here before the data:

  CARVE_FAILS           a within-size clause fails. The boundary lies in (2048, 4096]: the task
                        holds at 4096 and at no shorter window this repository has measured.
  CARVE_SIZE_SPECIFIC   within-size passes, transfer fails. The boundary lies in (1024, 2048];
                        one model per carve size, one more compression pass each.
  CARVE_ROBUST          both pass. One model spans 4096 -> 2048.

Anti-shield clauses (frozen):
  - Disjointness is a validity condition on the transfer arm, not a nicety, and here it is
    checked against BOTH earlier corpora by offset, not only by the flag the script sets.
  - The transfer arm is compared at a MATCHED training rung and scored against corpus C's OWN
    baselines.
  - A missing field reads as failure. Absence is never a pass.
  - This reader cannot revise 0003, 0006 or 0007. Those verdicts stand whatever this one says.
  - No outcome here establishes a buyer. `establishes_a_buyer` is emitted False unconditionally.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation_2048.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation_2048_verdict.json")

CARVE = 2048
REFERENCE_CARVE = 4096
MIN_OFFSET = 75000
MIN_RUNGS = 4
MIN_DECADES = 2.0
MARGIN = 0.05
NULL_TOLERANCE = 0.02


def main() -> int:
    if not os.path.exists(ARTIFACT):
        print(f"READER 0011: artifact absent: {os.path.relpath(ARTIFACT, REPO)}\n"
              f"  Absence is not a pass. No verdict emitted.", file=sys.stderr)
        return 2
    try:
        d = json.load(open(ARTIFACT, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"READER 0011: artifact malformed ({type(e).__name__}: {e}).", file=sys.stderr)
        return 2

    g = d.get

    def num(key):
        v = g(key)
        return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

    within: list[str] = []
    if g("carve_bytes") != CARVE:
        within.append(f"scope: carve_bytes={g('carve_bytes')!r}, this reader is frozen for {CARVE}")
    if g("reference_carve_bytes") != REFERENCE_CARVE:
        within.append(f"scope: reference_carve_bytes={g('reference_carve_bytes')!r}, "
                      f"need {REFERENCE_CARVE}")
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

    top1_ng = num("within_top1_non_gutenberg")
    exp_ng = num("within_best_baseline_expanded_non_gutenberg")
    if top1_ng is None or exp_ng is None:
        within.append("within margin (expanded, gutenberg excluded): within_top1_non_gutenberg or "
                      "within_best_baseline_expanded_non_gutenberg missing — the rows the "
                      "disjointness guarantee actually covers were not scored")
    elif top1_ng - exp_ng < MARGIN:
        within.append(f"within margin (expanded set, gutenberg excluded): {top1_ng} - {exp_ng} = "
                      f"{round(top1_ng - exp_ng, 4)} is below the preregistered {MARGIN}")

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
    off = num("corpus_b_chunk_offset")
    if off is None or off < MIN_OFFSET:
        transfer.append(f"transfer: corpus_b_chunk_offset={g('corpus_b_chunk_offset')!r} is not "
                        f">= {MIN_OFFSET}; the corpus is not past BOTH earlier corpora's chunk "
                        f"ranges, whatever the disjointness flag says")

    if within:
        verdict, meaning = "CARVE_FAILS", (
            "A within-size clause fails at 2048. The task holds at 4096 and at no shorter window "
            "this repository has measured; the window boundary for this recipe lies in "
            "(2048, 4096].")
        boundary = "(2048, 4096]"
    elif transfer:
        verdict, meaning = "CARVE_SIZE_SPECIFIC", (
            "Within-size passes at 2048; transfer from 4096 does not. The boundary lies in "
            "(1024, 2048]. One model per carve size costs one more compression pass and nothing "
            "else; the 'one model reads a whole disk image' story still fails.")
        boundary = "(1024, 2048]"
    else:
        verdict, meaning = "CARVE_ROBUST", (
            "Both pass. One model spans 4096 -> 2048; the boundary lies in (1024, 2048].")
        boundary = "(1024, 2048]"

    result = {
        "schema": "raise-v1/carve_generalisation_2048_verdict/1",
        "preregistration": "0011-carve-2048-boundary",
        "source_artifact": os.path.relpath(ARTIFACT, REPO),
        "verdict": verdict,
        "meaning": meaning,
        "boundary_bytes": boundary,
        "boundary_note": "Bracketed by this run together with the banked verdicts at 1024 (0007, "
                         "CARVE_FAILS) and 4096 (0003, CURVE_ESTABLISHED); this reader reads only "
                         "its own artifact and revises neither.",
        "within_size_failed_clauses": within,
        "transfer_failed_clauses": transfer,
        "establishes_a_buyer": False,
        "read": {k: g(k) for k in
                 ("carve_bytes", "reference_carve_bytes", "matched_rung", "n_rungs",
                  "decades_spanned", "within_top1", "within_best_trivial_baseline",
                  "within_best_trivial_baseline_name", "within_best_baseline_expanded",
                  "within_best_baseline_expanded_name", "within_top1_non_gutenberg",
                  "within_best_baseline_expanded_non_gutenberg",
                  "within_best_baseline_expanded_non_gutenberg_name", "within_slope",
                  "within_slope_ci95_low", "transfer_top1", "reference_matched_rung_top1",
                  "chance_accuracy", "within_shuffled_label_accuracy",
                  "within_split_is_grouped_by_source", "corpora_share_source_chunks",
                  "corpus_b_chunk_offset", "n_classes")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0011 — carve-size boundary at 2048")
    for k, v in result["read"].items():
        print(f"  {k:<48} {v}")
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
