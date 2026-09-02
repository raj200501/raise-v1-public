#!/usr/bin/env python3
"""Measure carve-size generalisation. Governed by preregistration 0007 (chain seq 7, 40ded1fa).

Two arms:

  WITHIN-SIZE  build corpus B at a shorter carve from source chunks DISJOINT from corpus A, then
               run the same four-rung protocol 0003 used: grouped split, trivial baselines trained
               on the same data as the top rung, null control, slope with a paired bootstrap.
  TRANSFER     train on corpus A at a MATCHED rung and evaluate on corpus B's held-out set. Matched
               so the comparison is about carve size and not data volume; scored against corpus B's
               OWN baselines because a transfer number that beats nothing local is not transfer.

The disjointness is the arm's validity condition, not a nicety: the chunk index IS the generator
seed, so overlapping indices would mean the transfer model is scored on bytes it trained on. This
script asserts it and writes the flag the frozen reader checks.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import CONFIG_NAMES, FAMILIES, N_CONFIGS  # noqa: E402
from npzmap import fill_f32, fill_f64, npz_memmap  # noqa: E402
from run_study import _rss_gb, build, make_model, predict_chunked  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FROZEN_SET = ["majority", "stratified", "depth3_tree", "logistic"]


def grouped_split(y, g, seed, eval_frac, cap):
    rng = np.random.default_rng(seed)
    groups = np.unique(g); rng.shuffle(groups)
    ev_groups = set(groups[:max(1, int(len(groups) * eval_frac))].tolist())
    is_ev = np.fromiter((int(v) in ev_groups for v in g), bool, len(g))
    tr = np.nonzero(~is_ev)[0]; rng.shuffle(tr)
    return np.nonzero(is_ev)[0], tr[:min(len(tr), cap)], rng


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carve", type=int, default=1024)
    ap.add_argument("--chunks", type=int, default=25000)
    ap.add_argument("--chunk-offset", type=int, default=50000)
    ap.add_argument("--chunk-size", type=int, default=32768)
    ap.add_argument("--rungs", type=int, nargs="*", default=[1000, 10000, 100000, 500000])
    ap.add_argument("--matched-rung", type=int, default=100000)
    ap.add_argument("--reference-cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--reference-carve", type=int, default=4096)
    ap.add_argument("--reference-chunks-used", type=int, default=50000)
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "carve_c1024.npz"))
    ap.add_argument("--eval-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--src", default=os.path.join(REPO, "data", "pivot", "src"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot",
                                                  "carve_generalisation.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot",
                                                         "carve_rung_scores.json"))
    ap.add_argument("--preregistration", default="0007-carve-size-generalisation")
    args = ap.parse_args()

    disjoint = args.chunk_offset >= args.reference_chunks_used
    if not disjoint:
        print(f"REFUSING: chunk offset {args.chunk_offset} overlaps the reference corpus's "
              f"0..{args.reference_chunks_used - 1}. The transfer arm would be scored on source "
              f"bytes the model trained on.", file=sys.stderr)
        return 3

    if os.path.exists(args.cache):
        print(f"[1/6] reusing corpus B {os.path.relpath(args.cache, REPO)}", flush=True)
        Xb = npz_memmap(args.cache, "X")
        with np.load(args.cache) as z:
            yb = np.asarray(z["y"]); gb = np.asarray(z["g"]); build_s = float(z["build_s"])
            # A cache built at one carve length silently reused at another would bank a
            # carve_bytes that is an echo of the command line, not a property of the data. Caches
            # written since 0011 carry their build parameters; a legacy cache (0007's) does not,
            # and that is recorded in the artifact rather than papered over.
            if "carve" in z.files:
                cache_carve, cache_off = int(z["carve"]), int(z["chunk_offset"])
                if cache_carve != args.carve or cache_off != args.chunk_offset:
                    print(f"REFUSING: cache was built at carve {cache_carve}, offset {cache_off}; "
                          f"the command line says carve {args.carve}, offset {args.chunk_offset}.",
                          file=sys.stderr)
                    return 3
                carve_source = "cache metadata written at build time"
            else:
                carve_source = ("command line - legacy cache without build metadata; the chunk-id "
                                "range below is measured from the data regardless")
    else:
        print(f"[1/6] manufacturing corpus B: carve {args.carve}, {args.chunks} chunks at "
              f"offset {args.chunk_offset}", flush=True)
        Xb, yb, gb, build_s = build(args.chunks, args.chunk_size, args.carve, args.src,
                                    args.procs, 0, args.chunk_offset)
        os.makedirs(os.path.dirname(args.cache), exist_ok=True)
        np.savez(args.cache, X=Xb, y=yb, g=gb, build_s=build_s, carve=args.carve,
                 chunk_offset=args.chunk_offset, chunk_size=args.chunk_size)
        del Xb
        Xb = npz_memmap(args.cache, "X")
        carve_source = "cache metadata written at build time"
    ncols = Xb.shape[1]
    chunk_id_min, chunk_id_max = int(gb.min()), int(gb.max())
    if chunk_id_min < args.chunk_offset:
        print(f"REFUSING: the corpus contains chunk id {chunk_id_min}, below the stated offset "
              f"{args.chunk_offset}.", file=sys.stderr)
        return 3
    print(f"      {len(yb)} fragments, {ncols} features, {build_s}s; chunk ids "
          f"{chunk_id_min}..{chunk_id_max} (measured from the data)", flush=True)

    ev_b, tr_b, rng = grouped_split(yb, gb, args.seed, args.eval_frac, max(args.rungs))
    # The grouped-split flag is MEASURED: no source chunk may appear on both sides.
    split_is_grouped = bool(np.intersect1d(np.unique(gb[ev_b]), np.unique(gb[tr_b])).size == 0)
    n_source_chunks = int(np.unique(gb).size)
    Xe = fill_f32(np.empty((len(ev_b), ncols), np.float32), Xb, ev_b, ncols)
    ye = np.asarray(yb[ev_b])
    # The gutenberg family draws its chunks from ONE shared byte pool, so "disjoint source chunks"
    # is a guarantee about the seven synthetic families only (CORRECTIONS.md 2026-08-31, defect 2).
    # Every accuracy below is therefore also banked with gutenberg excluded, so a reader can bind a
    # clause to the rows the guarantee actually covers.
    fam_ev = np.array([FAMILIES[int(v) % len(FAMILIES)] for v in gb[ev_b]])
    non_gut = fam_ev != "gutenberg"

    def by_family(correct):
        return {f: round(float(correct[fam_ev == f].mean()), 4) for f in FAMILIES}

    def excl(correct):
        return round(float(correct[non_gut].mean()), 4)
    Xtr = fill_f64(np.empty((len(tr_b), ncols), np.float64), Xb, tr_b, ncols)
    ytr = np.asarray(yb[tr_b])
    del Xb
    chance = 1.0 / N_CONFIGS
    print(f"[2/6] corpus B split: {len(ytr)} train / {len(ye)} eval, chance {chance:.6f}, "
          f"RSS {_rss_gb():.2f} GB", flush=True)

    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier
    nb = len(ytr)
    print(f"[3/6] corpus B trivial baselines (trained on {nb}, same as the top rung)", flush=True)
    baselines, baselines_excl, baselines_fam = {}, {}, {}
    for nm, clf in [("majority", DummyClassifier(strategy="most_frequent")),
                    ("stratified", DummyClassifier(strategy="stratified", random_state=0)),
                    ("best_single_feat", DecisionTreeClassifier(max_depth=1, random_state=0)),
                    ("depth3_tree", DecisionTreeClassifier(max_depth=3, random_state=0)),
                    ("depth8_tree", DecisionTreeClassifier(max_depth=8, random_state=0)),
                    ("depth16_tree", DecisionTreeClassifier(max_depth=16, random_state=0)),
                    ("logistic", LogisticRegression(max_iter=400))]:
        t = time.perf_counter()
        clf.fit(Xtr[:nb], ytr[:nb])
        ok = (predict_chunked(clf, Xe) == ye)
        baselines[nm] = round(float(ok.mean()), 4)
        baselines_excl[nm] = excl(ok); baselines_fam[nm] = by_family(ok)
        print(f"      {nm:<18} {baselines[nm]:.4f}  ({time.perf_counter()-t:.0f}s, "
              f"RSS {_rss_gb():.2f} GB)", flush=True)
    frozen = {k: v for k, v in baselines.items() if k in FROZEN_SET}
    fname = max(frozen, key=frozen.get); ename = max(baselines, key=baselines.get)
    frozen_excl = {k: v for k, v in baselines_excl.items() if k in FROZEN_SET}
    fname_excl = max(frozen_excl, key=frozen_excl.get)
    ename_excl = max(baselines_excl, key=baselines_excl.get)

    print("[4/6] corpus B rungs", flush=True)
    rungs, per_ex = [], []
    for r in args.rungs:
        if r > len(ytr):
            print(f"      rung {r}: SKIPPED, only {len(ytr)} training fragments"); continue
        t = time.perf_counter()
        m = make_model(args.seed, "hgb")
        k = max(1, int(r * 0.9))
        m.fit(Xtr[:k], ytr[:k], X_val=Xtr[k:r], y_val=ytr[k:r])
        correct = (predict_chunked(m, Xe) == ye).astype(np.int8)
        rungs.append({"n_units": int(r), "accuracy": round(float(correct.mean()), 4),
                      "accuracy_non_gutenberg": excl(correct),
                      "per_family": by_family(correct),
                      "train_seconds": round(time.perf_counter() - t, 1)})
        per_ex.append({"n_units": int(r), "per_example": correct.tolist()})
        print(f"      rung {r:>7}: {rungs[-1]['accuracy']:.4f}  "
              f"({rungs[-1]['train_seconds']}s, RSS {_rss_gb():.2f} GB)", flush=True)

    nn = min(len(ytr), 20000)
    y_sh = ytr[:nn].copy(); rng.shuffle(y_sh)
    m0 = make_model(args.seed, "hgb"); k0 = max(1, int(nn * 0.9))
    m0.fit(Xtr[:k0], y_sh[:k0], X_val=Xtr[k0:nn], y_val=y_sh[k0:nn])
    null_acc = round(float((predict_chunked(m0, Xe) == ye).mean()), 4)
    print(f"      null control {null_acc:.4f} vs chance {chance:.4f}", flush=True)
    del Xtr, ytr

    print(f"[5/6] transfer: train on corpus A at the matched rung {args.matched_rung}, "
          f"evaluate on corpus B", flush=True)
    Xa = npz_memmap(args.reference_cache, "X")
    with np.load(args.reference_cache) as z:
        ya = np.asarray(z["y"]); ga = np.asarray(z["g"])
    # Disjointness is MEASURED here, from the two corpora's chunk ids, not echoed from the
    # command line: the flag the reader gates on is the count of shared chunk ids being zero.
    n_shared = int(np.intersect1d(np.unique(gb), np.unique(ga)).size)
    ref_chunk_id_max = int(ga.max())
    print(f"      corpus A chunk ids up to {ref_chunk_id_max}; shared with corpus B: {n_shared}",
          flush=True)
    _, tr_a, _ = grouped_split(ya, ga, args.seed, args.eval_frac, args.matched_rung)
    Xtra = fill_f64(np.empty((len(tr_a), ncols), np.float64), Xa, tr_a, ncols)
    ytra = np.asarray(ya[tr_a])
    del Xa
    t = time.perf_counter()
    ma = make_model(args.seed, "hgb"); ka = max(1, int(len(ytra) * 0.9))
    ma.fit(Xtra[:ka], ytra[:ka], X_val=Xtra[ka:], y_val=ytra[ka:])
    ok_t = (predict_chunked(ma, Xe) == ye)
    transfer = round(float(ok_t.mean()), 4)
    transfer_excl = excl(ok_t); transfer_fam = by_family(ok_t)
    print(f"      transfer top-1 {transfer:.4f}  ({time.perf_counter()-t:.0f}s)", flush=True)
    n_train_a = int(len(ytra))
    del Xtra

    print("[6/6] slope", flush=True)
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from scaling import fit as fit_curve
    # Primary interval: cluster bootstrap over held-out source chunks, the dependence unit the
    # grouped split declares (CORRECTIONS.md 2026-08-31, defect 1). The fragment-level interval is
    # banked beside it, labelled superseded, so the two can be compared but not confused.
    fit = fit_curve(per_ex, n_boot=2000, seed=args.seed, groups=np.asarray(gb[ev_b]))
    fit_frag = fit_curve(per_ex, n_boot=2000, seed=args.seed)

    ref = json.load(open(os.path.join(REPO, "artifacts", "pivot", "deflate_curve.json")))
    ref_matched = next((r["accuracy"] for r in ref["rungs"]
                        if r["n_units"] == args.matched_rung), None)
    out = {
        "schema": "raise-v1/carve_generalisation/1",
        "preregistration": args.preregistration,
        "carve_bytes": args.carve, "carve_bytes_source": carve_source,
        "reference_carve_bytes": args.reference_carve,
        "matched_rung": args.matched_rung,
        "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
        "chance_accuracy": round(chance, 6),
        "corpora_share_source_chunks": n_shared > 0,
        "n_shared_source_chunks": n_shared,
        "corpus_b_chunk_offset": chunk_id_min,
        "corpus_b_chunk_offset_source": "smallest chunk id present in corpus B, measured from its g array",
        "corpus_b_chunk_id_max": chunk_id_max,
        "corpus_a_chunk_id_max": ref_chunk_id_max,
        "corpus_a_chunks_used": args.reference_chunks_used,
        "n_fragments": int(len(yb)), "n_eval_fragments": int(len(ye)),
        "n_source_chunks": n_source_chunks,
        "seed": args.seed,
        "rungs_requested": [int(r) for r in args.rungs],
        "within_baselines_trained_on_n": int(nb),
        "within_matched_rung_top1": next((r["accuracy"] for r in rungs
                                          if r["n_units"] == args.matched_rung), None),
        "transfer_n_train": n_train_a,
        "within_split_is_grouped_by_source": split_is_grouped,
        "within_trivial_baselines": baselines,
        "within_best_trivial_baseline": frozen[fname], "within_best_trivial_baseline_name": fname,
        "within_best_baseline_expanded": baselines[ename],
        "within_best_baseline_expanded_name": ename,
        "within_top1": rungs[-1]["accuracy"] if rungs else None,
        "within_shuffled_label_accuracy": null_acc,
        "transfer_top1": transfer,
        "reference_matched_rung_top1": ref_matched,
        "n_eval_non_gutenberg": int(non_gut.sum()),
        "within_top1_non_gutenberg": rungs[-1]["accuracy_non_gutenberg"] if rungs else None,
        "within_trivial_baselines_non_gutenberg": baselines_excl,
        "within_best_trivial_baseline_non_gutenberg": frozen_excl[fname_excl],
        "within_best_trivial_baseline_non_gutenberg_name": fname_excl,
        "within_best_baseline_expanded_non_gutenberg": baselines_excl[ename_excl],
        "within_best_baseline_expanded_non_gutenberg_name": ename_excl,
        "within_per_family_top_rung": rungs[-1]["per_family"] if rungs else None,
        "within_per_family_baselines": baselines_fam,
        "transfer_top1_non_gutenberg": transfer_excl,
        "transfer_per_family": transfer_fam,
        "rungs": rungs, "n_rungs": len(rungs),
        "decades_spanned": fit["orders_of_magnitude_spanned"],
        "within_slope": fit["primary_fit"]["slope"],
        "within_slope_ci95_low": fit["primary_fit"]["slope_ci95"][0],
        "within_slope_ci95_high": fit["primary_fit"]["slope_ci95"][1],
        "within_slope_ci95_note": (f"cluster bootstrap over {fit['n_clusters']} held-out source "
                                   f"chunks, paired across rungs, {fit['bootstrap_resamples']} "
                                   f"resamples; the fragment-level interval is banked beside it "
                                   f"as superseded"),
        "within_slope_ci95_low_fragment_level_superseded": fit_frag["primary_fit"]["slope_ci95"][0],
        "within_slope_ci95_high_fragment_level_superseded": fit_frag["primary_fit"]["slope_ci95"][1],
        "within_slope_r2": fit["primary_fit"]["r2"],
        "within_permutation_p": fit["permutation_test"]["p_value"],
        "establishes_a_buyer": False,
        "cost": {"build_seconds": build_s,
                 "train_seconds_per_rung": [r["train_seconds"] for r in rungs],
                 "cpu_cores": args.procs, "gpu": "none"},
    }
    scores_out = args.scores_out
    with open(scores_out, "w") as fh:
        json.dump({"schema": "raise-v1/rung_scores/1",
                   "metric": "top-1 on corpus B's held-out evaluation set, grouped by source chunk",
                   "eval_chunk_ids": np.asarray(gb[ev_b]).tolist(),
                   "rungs": per_ex}, fh)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"\nwithin-size top1 {out['within_top1']} | transfer {transfer} | "
          f"corpus B best trivial {frozen[fname]} ({fname})")
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
