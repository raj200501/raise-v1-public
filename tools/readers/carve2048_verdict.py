#!/usr/bin/env python3
"""Frozen reader for preregistration 0011 — where, between 1024 and 4096 bytes, does the carved-DEFLATE
result stop holding?

Written and committed BEFORE the 2048-byte corpus was manufactured and before any model was trained
on it.

WHY THIS EXISTS. The record holds exactly two carve sizes. At 4096 the task clears its bar
(0003, CURVE_ESTABLISHED); at 1024 it ties a dumb rule (0007, CARVE_FAILS). "Valid only at a
4096-byte window" is therefore a two-point statement with an unmeasured boundary somewhere in a
factor of four. This run measures the geometric midpoint, 2048, under the 0007 protocol, and
locates the boundary — of the bar clearing at this protocol's top rung — to a factor of two. It
is the carve-size question the milestone map files under M3, run ahead of M4 at the size that
bounds the record's own scope statement rather than at a buyer-reported size, for the reasons the
preregistration states in its own words.

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
  transfer margin  transfer_top1_non_gutenberg - within_best_trivial_baseline_non_gutenberg
                                                                                     >= 0.05

The gutenberg-excluded clauses are new and are there because the audit of 2026-08-31 found that
the gutenberg family draws its chunks from one shared byte pool, so "disjoint source chunks" is a
guarantee about the seven synthetic families only. Those clauses bind BOTH arms' margins to the
rows the guarantee actually covers — the transfer arm especially, since a 4096-trained model has
seen gutenberg-adjacent bytes whatever the chunk ids say. It is a STRICTER bar than 0007's,
chosen knowing that in 0003 excluding gutenberg widened the margins — a clause that could only
help the result would be a shield, and these can fail on their own.

The within_slope interval is the CLUSTER-bootstrap interval over held-out source chunks
(tools/scaling.py, groups=chunk ids), which the measurement script computes directly; 0007's
artifact carried a fragment-level interval that was replaced after the audit. A number that is
not finite (NaN, inf) is treated exactly like a missing one.

VERDICTS, stated here before the data. Validity comes first, because a run that is not valid
says nothing about the boundary and must not be allowed to say something by accident:

  VOID                  a validity clause fails — wrong scope (carve, reference, rungs, decades),
                        a non-grouped split, a null control above tolerance, or any field the
                        reader needs missing or non-finite. No boundary is bracketed. This is
                        NOT a negative result about the task; it is no result.
  CARVE_FAILS           valid run; a within-size margin or slope clause fails. The boundary lies
                        in (2048, 4096]: the task holds at 4096 and at no shorter window this
                        repository has measured.
  CARVE_SIZE_SPECIFIC   valid run; within-size passes, a transfer margin clause fails (either
                        reading). The boundary lies in (1024, 2048]; one model per carve size,
                        one more compression pass each.
  CARVE_ROBUST          both pass. One model spans 4096 -> 2048.

Anti-shield clauses (frozen):
  - Disjointness is a validity condition, not a transfer result. The script MEASURES it (the
    count of chunk ids shared with corpus A, and the smallest chunk id present) rather than
    echoing its command line; the reader requires zero shared and that smallest id past BOTH
    earlier corpora (>= 75000), and a corpus that fails either is VOID — it was not the
    preregistered corpus.
  - The run's sealed parameters are checked, not assumed: preregistration stamp, seed, the rung
    ladder, the chunk count, the matched rung, the number of corpus-A rows the transfer model
    was actually trained on, and the number of rows the baselines were trained on. Each is banked
    by the script from what it did, and any mismatch is VOID.
  - The transfer arm is compared at a MATCHED training rung and scored against corpus C's OWN
    baselines.
  - A missing or non-finite field reads as VOID. Absence is never a pass, and never a fail.
  - This reader cannot revise 0003, 0006 or 0007. Those verdicts stand whatever this one says.
  - No outcome here establishes a buyer. `establishes_a_buyer` is emitted False unconditionally.

Exit codes: 0 verdict emitted; 2 artifact missing or malformed.
"""
from __future__ import annotations

import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACT = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation_2048.json")
OUT = os.path.join(REPO, "artifacts", "pivot", "carve_generalisation_2048_verdict.json")

PREREG = "0011-carve-2048-boundary"
CARVE = 2048
REFERENCE_CARVE = 4096
MIN_OFFSET = 75000
SEED = 20260825
LADDER = [1000, 10000, 100000, 500000]
N_SOURCE_CHUNKS = 25000
MATCHED_RUNG = 100000
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

    void: list[str] = []          # validity: the run says nothing
    within: list[str] = []        # measured within-size clauses
    transfer: list[str] = []      # measured transfer clauses, plus disjointness

    def num(key):
        """A finite number, or None. NaN and inf are treated exactly like absence."""
        v = g(key)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return v if math.isfinite(v) else None

    def need(*keys):
        missing = [k for k in keys if num(k) is None]
        for k in missing:
            void.append(f"field: {k} is missing or not a finite number")
        return not missing

    # The run's parameters are sealed in the preregistration; each is banked by the script and
    # checked here, so a run under other parameters is VOID rather than silently read.
    if g("preregistration") != PREREG:
        void.append(f"scope: preregistration={g('preregistration')!r}, this reader is frozen for "
                    f"{PREREG}")
    if g("carve_bytes") != CARVE:
        void.append(f"scope: carve_bytes={g('carve_bytes')!r}, this reader is frozen for {CARVE}")
    if g("reference_carve_bytes") != REFERENCE_CARVE:
        void.append(f"scope: reference_carve_bytes={g('reference_carve_bytes')!r}, "
                    f"need {REFERENCE_CARVE}")
    if g("seed") != SEED:
        void.append(f"scope: seed={g('seed')!r}, the preregistered seed is {SEED}")
    if g("n_source_chunks") != N_SOURCE_CHUNKS:
        void.append(f"scope: n_source_chunks={g('n_source_chunks')!r}, the preregistered corpus "
                    f"has {N_SOURCE_CHUNKS}")
    ladder = [r.get("n_units") if isinstance(r, dict) else None for r in (g("rungs") or [])]
    if ladder != LADDER:
        void.append(f"scope: rung ladder {ladder!r} is not the preregistered {LADDER}")
    n_rungs = g("n_rungs")
    if isinstance(n_rungs, bool) or not isinstance(n_rungs, int) or n_rungs < MIN_RUNGS:
        void.append(f"scope: n_rungs={n_rungs!r}, need >= {MIN_RUNGS}")
    if need("decades_spanned") and num("decades_spanned") < MIN_DECADES:
        void.append(f"scope: decades_spanned={g('decades_spanned')!r}, need >= {MIN_DECADES}")
    if g("within_baselines_trained_on_n") != LADDER[-1]:
        void.append(f"scope: within_baselines_trained_on_n={g('within_baselines_trained_on_n')!r}, "
                    f"the baselines must be trained on the top rung's {LADDER[-1]} rows")
    if g("matched_rung") != MATCHED_RUNG:
        void.append(f"scope: matched_rung={g('matched_rung')!r}, the preregistered matched rung "
                    f"is {MATCHED_RUNG}")
    if g("transfer_n_train") != MATCHED_RUNG:
        void.append(f"scope: transfer_n_train={g('transfer_n_train')!r}, the transfer model must "
                    f"be trained on exactly {MATCHED_RUNG} corpus-A rows (measured, not echoed)")

    if g("within_split_is_grouped_by_source") is not True:
        void.append("split: within_split_is_grouped_by_source is not True")

    if need("within_shuffled_label_accuracy", "chance_accuracy"):
        nul, chance = num("within_shuffled_label_accuracy"), num("chance_accuracy")
        if nul > chance + NULL_TOLERANCE:
            void.append(f"null control: shuffled labels reached {nul}, above chance {chance} + "
                        f"{NULL_TOLERANCE} — the pipeline leaks and the run measures nothing")

    if need("within_top1", "within_best_trivial_baseline"):
        top1, base = num("within_top1"), num("within_best_trivial_baseline")
        if top1 - base < MARGIN:
            within.append(f"within margin (frozen set): {top1} - {base} = {round(top1 - base, 4)} "
                          f"is below the preregistered {MARGIN}")
    if need("within_top1", "within_best_baseline_expanded"):
        top1, exp = num("within_top1"), num("within_best_baseline_expanded")
        if top1 - exp < MARGIN:
            within.append(f"within margin (expanded set): {top1} - {exp} = {round(top1 - exp, 4)} "
                          f"is below the preregistered {MARGIN}")
    if need("within_top1_non_gutenberg", "within_best_baseline_expanded_non_gutenberg"):
        top1_ng = num("within_top1_non_gutenberg")
        exp_ng = num("within_best_baseline_expanded_non_gutenberg")
        if top1_ng - exp_ng < MARGIN:
            within.append(f"within margin (expanded set, gutenberg excluded): {top1_ng} - {exp_ng} "
                          f"= {round(top1_ng - exp_ng, 4)} is below the preregistered {MARGIN}")
    if need("within_slope_ci95_low") and num("within_slope_ci95_low") <= 0:
        within.append(f"within slope: within_slope_ci95_low={num('within_slope_ci95_low')} "
                      f"does not exceed 0")

    if need("transfer_top1", "within_best_trivial_baseline"):
        tt, base = num("transfer_top1"), num("within_best_trivial_baseline")
        if tt - base < MARGIN:
            transfer.append(f"transfer margin: {tt} - {base} = {round(tt - base, 4)} is below the "
                            f"preregistered {MARGIN} — a model trained at the longer carve does "
                            f"not beat the shorter corpus's own dumb rules")
    if need("transfer_top1_non_gutenberg", "within_best_trivial_baseline_non_gutenberg"):
        tt_ng = num("transfer_top1_non_gutenberg")
        base_ng = num("within_best_trivial_baseline_non_gutenberg")
        if tt_ng - base_ng < MARGIN:
            transfer.append(f"transfer margin (gutenberg excluded): {tt_ng} - {base_ng} = "
                            f"{round(tt_ng - base_ng, 4)} is below the preregistered {MARGIN}")
    # Disjointness is a validity condition, not a transfer result: a corpus that overlaps an
    # earlier one was not the preregistered corpus, so the whole run is VOID, not "transfer fails".
    if g("corpora_share_source_chunks") is not False:
        void.append("disjointness: corpora_share_source_chunks is not False — the transfer model may "
                    "have trained on source bytes present in this evaluation set")
    if g("n_shared_source_chunks") != 0:
        void.append(f"disjointness: n_shared_source_chunks={g('n_shared_source_chunks')!r}, "
                    f"must be exactly 0 (measured from both corpora's chunk ids)")
    if need("corpus_b_chunk_offset") and num("corpus_b_chunk_offset") < MIN_OFFSET:
        void.append(f"disjointness: corpus_b_chunk_offset={g('corpus_b_chunk_offset')!r} is not "
                    f">= {MIN_OFFSET}; the corpus is not past BOTH earlier corpora's chunk "
                    f"ranges, whatever the disjointness flag says")

    if void:
        verdict, meaning = "VOID", (
            "A validity clause fails. This run brackets no boundary and is not a negative result "
            "about the task; it is no result. Fix the run and re-read, or file it as NOT RUN.")
        boundary = "not bracketed by this run"
    elif within:
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
        "validity_failed_clauses": void,
        "within_size_failed_clauses": within,
        "transfer_failed_clauses": transfer,
        "establishes_a_buyer": False,
        "read": {k: g(k) for k in
                 ("preregistration", "carve_bytes", "carve_bytes_source", "reference_carve_bytes",
                  "seed", "n_source_chunks", "rungs_requested", "within_baselines_trained_on_n",
                  "matched_rung", "transfer_n_train", "within_matched_rung_top1",
                  "n_rungs", "decades_spanned", "within_top1", "within_best_trivial_baseline",
                  "within_best_trivial_baseline_name", "within_best_baseline_expanded",
                  "within_best_baseline_expanded_name", "within_top1_non_gutenberg",
                  "within_best_trivial_baseline_non_gutenberg",
                  "within_best_baseline_expanded_non_gutenberg",
                  "within_best_baseline_expanded_non_gutenberg_name", "within_slope",
                  "within_slope_ci95_low", "within_slope_ci95_note", "transfer_top1",
                  "transfer_top1_non_gutenberg", "reference_matched_rung_top1",
                  "chance_accuracy", "within_shuffled_label_accuracy",
                  "within_split_is_grouped_by_source", "corpora_share_source_chunks",
                  "n_shared_source_chunks", "corpus_b_chunk_offset", "corpus_b_chunk_id_max",
                  "n_classes")},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("READER 0011 — carve-size boundary at 2048")
    for k, v in result["read"].items():
        print(f"  {k:<48} {v}")
    for label, fails in (("VALIDITY", void), ("WITHIN-SIZE", within), ("TRANSFER", transfer)):
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
