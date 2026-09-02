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
  disjointness     n_shared_source_chunks == 0, corpora_share_source_chunks is False, and the
                   MEASURED chunk-id range is exactly 75000..99999 (past corpus A's 0..49999 and
                   corpus B's 50000..74999; exact, so the corpus cannot be redrawn at another
                   offset and re-read)
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
    echoing its command line; the reader requires zero shared and the measured chunk-id range
    to be exactly 75000..99999, and a corpus that fails either is VOID — it was not the
    preregistered corpus, and it cannot be redrawn at another offset and re-read.
  - The corpus is tied to its inputs: the script hashes the ten source files it read and the
    label and chunk-id arrays of corpus A it trained the transfer model on, and the reader
    compares them with the banked manifest hashes. The transfer model must also reproduce
    corpus A's banked matched-rung accuracy on corpus A's own evaluation set (within 0.01),
    so a transfer failure cannot be a retraining failure in disguise.
  - Margins are compared after rounding the difference to 6 decimals, so a margin the artifact
    prints as 0.0500 reads as 0.0500, not as a binary-float artefact on either side of the bar.
  - The run's sealed parameters are checked, not assumed: preregistration stamp, seed, the rung
    ladder, the chunk count, the matched rung, the number of corpus-A rows the transfer model
    was actually trained on, and the number of rows the baselines were trained on. Each is banked
    by the script from what it did, and any mismatch is VOID.
  - The transfer arm is compared at a MATCHED training rung and scored against corpus C's OWN
    baselines.
  - A missing or non-finite field reads as VOID. Absence is never a pass, and never a fail.
  - This reader cannot revise 0003, 0006 or 0007. Those verdicts stand whatever this one says.
  - No outcome here establishes a buyer. `establishes_a_buyer` is emitted False unconditionally.

The preregistered invocation, stated so no default can substitute a banked 0007 path:

  python3 tools/pivot/run_carve.py --carve 2048 --chunks 25000 --chunk-offset 75000 \
      --cache data/pivot/carve_c2048.npz \
      --out artifacts/pivot/carve_generalisation_2048.json \
      --scores-out artifacts/pivot/carve_rung_scores_2048.json \
      --preregistration 0011-carve-2048-boundary

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
CARVE_SOURCE = "cache metadata written at build time"
REFERENCE_CARVE = 4096
OFFSET = 75000                 # exact, not a lower bound: the corpus is 75000..99999 and nothing else
CHUNK_ID_MAX = 99999
CHUNK_SIZE = 32768
EVAL_FRAC = 0.2
N_EVAL_CHUNKS = 5000           # 25000 chunks x 0.2, the cluster count the slope interval must be over
BOOTSTRAP_RESAMPLES = 2000
TRANSFER_SELF_TOLERANCE = 0.01  # the transfer model must reproduce corpus A's banked matched-rung top-1
SEED = 20260825
# sha256 of the ten Project Gutenberg sources the corpora are built from, as banked in
# artifacts/pivot/corpus_manifest.json (sources_sha256). The script hashes the files it read.
SOURCES_SHA256 = {
    "pg11.txt": "a3a27f8edbf7fcd9b8ba8435494440e24952deaa3e2f2d65192d4cb7ca403754",
    "pg1342.txt": "a5666f87abf2cbfdaa27ea8c73bd284da9649b9a2ab27b4e6c8f6aeab1bd1c88",
    "pg1661.txt": "b9c105a5c0cf9fcb37c7d0211658851ed56074519c9455d15e20f04c0c5a3174",
    "pg1952.txt": "0604e2f8ab0a7acf9a7e1ea647e59eafcae7ed5d75c5cc985772c032d8655acb",
    "pg2600.txt": "e4bcf9042609b62c7de72a6f1b311f54c412943a9d641b7efcf79a464b5f31c8",
    "pg2701.txt": "0670d7bb10b99d05f095a28942801aa74d4921d1b34dbdc76900e2c4c2bd2189",
    "pg5200.txt": "6b023bfbb6c951841325554a588b6d88a8cf5d117d52fd3ffb2790c1089caf77",
    "pg74.txt": "fe74f3e43a7c0a0d0189b40ce966ce73795559b63076ccc0ea2e8ba2b9a9b213",
    "pg84.txt": "06c37d2c52d208d3d81eb12c3b10b5edbd7728b73554325ddceadbe2fb427e77",
    "pg98.txt": "e3dfeb67feb904ac0f73a35204a175c58248422c2be8556802cb8820d958d67c",
}
# sha256 of corpus A's label and chunk-id arrays, as banked in corpus_manifest.json for
# data/pivot/full_c4096.npz; the script hashes the arrays it actually loaded.
REFERENCE_Y_SHA256 = "2b70426881e569f303c400b8dc2b3cb69f30dbe2e36a93dff56df54df9acf093"
REFERENCE_G_SHA256 = "eda31b7cfa24640dff694c00e62849537490c9572966a5247d1f5127800e4df9"
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

    def margin(a, b):
        """The artifact banks accuracies rounded to 4 decimals; their difference is rounded to
        6 before comparison so that a margin printed as 0.0500 cannot read as 0.04999999."""
        return round(a - b, 6)

    def below(a, b):
        return margin(a, b) < MARGIN - 1e-9

    # The run's parameters are sealed in the preregistration; each is banked by the script and
    # checked here, so a run under other parameters is VOID rather than silently read.
    if g("preregistration") != PREREG:
        void.append(f"scope: preregistration={g('preregistration')!r}, this reader is frozen for "
                    f"{PREREG}")
    if g("carve_bytes") != CARVE:
        void.append(f"scope: carve_bytes={g('carve_bytes')!r}, this reader is frozen for {CARVE}")
    if g("carve_bytes_source") != CARVE_SOURCE:
        void.append(f"scope: carve_bytes_source={g('carve_bytes_source')!r}; carve_bytes must come "
                    f"from the corpus cache's build metadata, not from a command line")
    if g("chunk_size") != CHUNK_SIZE:
        void.append(f"scope: chunk_size={g('chunk_size')!r}, the preregistered chunk is {CHUNK_SIZE}")
    if num("eval_frac") != EVAL_FRAC:
        void.append(f"scope: eval_frac={g('eval_frac')!r}, the preregistered fraction is {EVAL_FRAC}")
    src = g("sources_sha256")
    if not isinstance(src, dict) or {k: v for k, v in src.items()} != SOURCES_SHA256:
        void.append("scope: sources_sha256 does not equal the banked hashes of the ten source files "
                    "(artifacts/pivot/corpus_manifest.json); the corpus was not built from the "
                    "banked source bytes, or the hashes were not banked")
    if g("reference_y_sha256") != REFERENCE_Y_SHA256 or g("reference_g_sha256") != REFERENCE_G_SHA256:
        void.append("scope: reference_y_sha256/reference_g_sha256 do not equal the banked hashes of "
                    "corpus A's arrays; the transfer model was not trained on the banked 4096 corpus")
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
    if need("transfer_model_top1_on_reference_eval", "reference_matched_rung_top1"):
        own, banked = num("transfer_model_top1_on_reference_eval"), num("reference_matched_rung_top1")
        if abs(own - banked) > TRANSFER_SELF_TOLERANCE:
            void.append(f"transfer model: scores {own} on corpus A's own evaluation set against the "
                        f"banked {banked} at the same rung; it did not reproduce the model it is "
                        f"supposed to be, so a transfer failure would be a retraining failure")
    if g("within_slope_bootstrap_unit") != "cluster":
        void.append(f"slope interval: within_slope_bootstrap_unit={g('within_slope_bootstrap_unit')!r}, "
                    f"the interval the clause gates on must be the cluster bootstrap")
    if g("within_slope_n_clusters") != N_EVAL_CHUNKS:
        void.append(f"slope interval: within_slope_n_clusters={g('within_slope_n_clusters')!r}, "
                    f"must be the {N_EVAL_CHUNKS} held-out source chunks")
    if g("within_slope_bootstrap_resamples") != BOOTSTRAP_RESAMPLES:
        void.append(f"slope interval: within_slope_bootstrap_resamples="
                    f"{g('within_slope_bootstrap_resamples')!r}, preregistered {BOOTSTRAP_RESAMPLES}")

    if g("within_split_is_grouped_by_source") is not True:
        void.append("split: within_split_is_grouped_by_source is not True")

    if need("within_shuffled_label_accuracy", "chance_accuracy"):
        nul, chance = num("within_shuffled_label_accuracy"), num("chance_accuracy")
        if nul > chance + NULL_TOLERANCE:
            void.append(f"null control: shuffled labels reached {nul}, above chance {chance} + "
                        f"{NULL_TOLERANCE} — the pipeline leaks and the run measures nothing")

    if need("within_top1", "within_best_trivial_baseline"):
        top1, base = num("within_top1"), num("within_best_trivial_baseline")
        if below(top1, base):
            within.append(f"within margin (frozen set): {top1} - {base} = {margin(top1, base)} "
                          f"is below the preregistered {MARGIN}")
    if need("within_top1", "within_best_baseline_expanded"):
        top1, exp = num("within_top1"), num("within_best_baseline_expanded")
        if below(top1, exp):
            within.append(f"within margin (expanded set): {top1} - {exp} = {margin(top1, exp)} "
                          f"is below the preregistered {MARGIN}")
    if need("within_top1_non_gutenberg", "within_best_baseline_expanded_non_gutenberg"):
        top1_ng = num("within_top1_non_gutenberg")
        exp_ng = num("within_best_baseline_expanded_non_gutenberg")
        if below(top1_ng, exp_ng):
            within.append(f"within margin (expanded set, gutenberg excluded): {top1_ng} - {exp_ng} "
                          f"= {margin(top1_ng, exp_ng)} is below the preregistered {MARGIN}")
    if need("within_slope_ci95_low") and num("within_slope_ci95_low") <= 0:
        within.append(f"within slope: within_slope_ci95_low={num('within_slope_ci95_low')} "
                      f"does not exceed 0")

    if need("transfer_top1", "within_best_trivial_baseline"):
        tt, base = num("transfer_top1"), num("within_best_trivial_baseline")
        if below(tt, base):
            transfer.append(f"transfer margin: {tt} - {base} = {margin(tt, base)} is below the "
                            f"preregistered {MARGIN} — a model trained at the longer carve does "
                            f"not beat the shorter corpus's own dumb rules")
    if need("transfer_top1_non_gutenberg", "within_best_trivial_baseline_non_gutenberg"):
        tt_ng = num("transfer_top1_non_gutenberg")
        base_ng = num("within_best_trivial_baseline_non_gutenberg")
        if below(tt_ng, base_ng):
            transfer.append(f"transfer margin (gutenberg excluded): {tt_ng} - {base_ng} = "
                            f"{margin(tt_ng, base_ng)} is below the preregistered {MARGIN}")
    # Disjointness is a validity condition, not a transfer result: a corpus that overlaps an
    # earlier one was not the preregistered corpus, so the whole run is VOID, not "transfer fails".
    if g("corpora_share_source_chunks") is not False:
        void.append("disjointness: corpora_share_source_chunks is not False — the transfer model may "
                    "have trained on source bytes present in this evaluation set")
    if g("n_shared_source_chunks") != 0:
        void.append(f"disjointness: n_shared_source_chunks={g('n_shared_source_chunks')!r}, "
                    f"must be exactly 0 (measured from both corpora's chunk ids)")
    if g("corpus_b_chunk_offset") != OFFSET or g("corpus_b_chunk_id_max") != CHUNK_ID_MAX:
        void.append(f"disjointness: measured chunk-id range "
                    f"{g('corpus_b_chunk_offset')!r}..{g('corpus_b_chunk_id_max')!r} is not the "
                    f"preregistered {OFFSET}..{CHUNK_ID_MAX}; the corpus is either not past BOTH "
                    f"earlier corpora or is a different draw than the one sealed here, whatever "
                    f"the disjointness flag says")

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
                         "CARVE_FAILS) and 4096 (0003, CURVE_ESTABLISHED), each under its own "
                         "measured protocol: 4096 cleared its bar at an 800000-fragment top rung, "
                         "1024 and 2048 are measured at a 500000-fragment top rung. The bracket is "
                         "a statement about where the bar clears under those protocols, not a "
                         "claim that 4096 was measured at 500000; the like-for-like size comparison "
                         "is within_matched_rung_top1 at the 100000 rung. This reader reads only "
                         "its own artifact and revises neither earlier verdict.",
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
                  "chunk_size", "eval_frac", "transfer_model_top1_on_reference_eval",
                  "within_slope_bootstrap_unit", "within_slope_n_clusters",
                  "within_slope_bootstrap_resamples", "n_classes")},
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
