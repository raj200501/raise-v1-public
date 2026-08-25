#!/usr/bin/env python3
"""Manufacture the corpus, then measure the scaling curve. Governed by preregistration 0003.

Pipeline, in the order the preregistration requires:
  1. manufacture fragments (label = the (implementation, level) that produced the stream)
  2. split GROUPED BY SOURCE CHUNK, so no source bytes straddle train and evaluation
  3. measure the trivial baselines FIRST, before any learned number is believed
  4. train one fixed model class at every rung
  5. run the NULL CONTROL: shuffle labels, retrain, confirm it falls to chance
  6. write artifacts/pivot/deflate_curve.json for the frozen reader

The model class is held identical across rungs. Changing capacity between rungs would make the
slope a statement about the model rather than about the data.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import Counter
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import CONFIG_NAMES, FAMILIES, N_CONFIGS, chunk_fragments, load_real  # noqa: E402
from features import N_FEATURES, features_many  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_REAL = None


def _init(src_dir):
    global _REAL
    _REAL = load_real(src_dir)


def _one(args):
    idx, family, chunk_size, carve_len = args
    frags, labels, _ = chunk_fragments(idx, family, _REAL, chunk_size, carve_len)
    if not frags:
        return np.empty((0, N_FEATURES), np.float32), np.empty(0, np.int16), np.empty(0, np.int32)
    return (features_many(frags),
            np.asarray(labels, dtype=np.int16),
            np.full(len(labels), idx, dtype=np.int32))


def build(n_chunks, chunk_size, carve_len, src_dir, procs, ncols=0):
    """Preallocated so peak memory is one copy of the corpus, not two.

    A vstack at a million rows briefly holds both the list of blocks and the result, which is the
    difference between fitting in 15 GB and not.
    """
    tasks = [(i, FAMILIES[i % len(FAMILIES)], chunk_size, carve_len) for i in range(n_chunks)]
    ncols = ncols or N_FEATURES
    cap = n_chunks * N_CONFIGS
    X = np.empty((cap, ncols), dtype=np.float32)
    Y = np.empty(cap, dtype=np.int16)
    G = np.empty(cap, dtype=np.int32)
    n = 0
    t0 = time.perf_counter()
    with Pool(procs, initializer=_init, initargs=(src_dir,)) as pool:
        for k, (x, y, g) in enumerate(pool.imap_unordered(_one, tasks, chunksize=8), 1):
            m = len(y)
            if m:
                X[n:n + m] = x[:, :ncols]; Y[n:n + m] = y; G[n:n + m] = g
                n += m
            if k % 2000 == 0:
                print(f"    {k}/{n_chunks} chunks, {n} fragments, "
                      f"{time.perf_counter()-t0:.0f}s", flush=True)
    return X[:n], Y[:n], G[:n], round(time.perf_counter() - t0, 1)


def make_model(seed, kind="mlp"):
    """One fixed model class for every rung and for the null control.

    Which class is used was chosen ONCE on pilot data, before the scaled run, and then held fixed.
    That choice is recorded in the artifact as `model_class` so it cannot be quietly revisited.
    """
    if kind == "hgb":
        from sklearn.ensemble import HistGradientBoostingClassifier
        # early_stopping is OFF, and that is a memory decision, not a modelling one. With it on,
        # sklearn calls train_test_split(X, y) inside fit(), which materialises a full extra copy of
        # the training pool - 5.19 GB at the top rung. Two runs were OOM-killed at exactly that
        # point, both at anon-rss 13.9 GB. Turning it off removes the copy. It is applied to EVERY
        # rung and to the null control, so the model class stays identical across the curve and no
        # rung is advantaged.
        return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.15,
                                              max_leaf_nodes=63, early_stopping=False,
                                              random_state=seed)
    if kind == "extratrees":
        from sklearn.ensemble import ExtraTreesClassifier
        return ExtraTreesClassifier(n_estimators=300, n_jobs=-1, min_samples_leaf=2,
                                    random_state=seed)
    if kind == "rf":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=300, n_jobs=-1, min_samples_leaf=2,
                                      random_state=seed)
    from sklearn.neural_network import MLPClassifier
    return MLPClassifier(hidden_layer_sizes=(384, 192), alpha=1e-4, batch_size=512,
                         learning_rate_init=2e-3, max_iter=60, early_stopping=True,
                         n_iter_no_change=6, validation_fraction=0.1, random_state=seed)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chunks", type=int, default=2000)
    ap.add_argument("--chunk-size", type=int, default=32768)
    ap.add_argument("--carve", type=int, default=2048)
    ap.add_argument("--rungs", type=int, nargs="*", default=[500, 5000, 50000])
    ap.add_argument("--eval-frac", type=float, default=0.2)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--src", default=os.path.join(REPO, "data", "pivot", "src"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "deflate_curve.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot",
                                                         "deflate_rung_scores.json"))
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--cache", default=None, help="npz path to cache/reuse the manufactured features")
    ap.add_argument("--model", default="mlp", choices=["mlp", "hgb", "extratrees", "rf"])
    ap.add_argument("--feature-cols", type=int, default=0,
                    help="use only the first N feature columns (0 = all). Columns 0..552 are the "
                         "v1 set; v2 and v3 append to it and both were measured to earn nothing.")
    args = ap.parse_args()

    if args.cache and os.path.exists(args.cache):
        print(f"[1/5] reusing cached corpus {args.cache} (memory-mapped)", flush=True)
        z = np.load(args.cache, mmap_mode="r")
        X, y, g, build_s = z["X"], z["y"], z["g"], float(z["build_s"])
        y = np.asarray(y); g = np.asarray(g)
        mmapped = True
    else:
        print(f"[1/5] manufacturing from {args.chunks} source chunks "
              f"({args.chunk_size}B each, carving {args.carve}B)...", flush=True)
        X, y, g, build_s = build(args.chunks, args.chunk_size, args.carve, args.src, args.procs,
                                 args.feature_cols)
        mmapped = False
        if args.cache:
            os.makedirs(os.path.dirname(os.path.abspath(args.cache)), exist_ok=True)
            np.savez(args.cache, X=X, y=y, g=g, build_s=build_s)
            print(f"      cached to {args.cache}", flush=True)
    print(f"      {len(y)} fragments, {X.shape[1]} features, {build_s}s", flush=True)

    rng = np.random.default_rng(args.seed)
    groups = np.unique(g); rng.shuffle(groups)
    n_ev = max(1, int(len(groups) * args.eval_frac))
    ev_groups = set(groups[:n_ev].tolist())
    is_ev = np.fromiter((int(v) in ev_groups for v in g), bool, len(g))
    # Materialise the evaluation set and a REORDERED training pool exactly once, so that each rung
    # is a contiguous VIEW rather than a fresh fancy-index copy. The first attempt at this run was
    # OOM-killed at the 1M rung (anon-rss 13.9 GB) because the full corpus and a 4.4 GB training
    # copy were resident simultaneously. Memory-mapping the cache keeps the source out of anon
    # memory entirely.
    tr = np.nonzero(~is_ev)[0]
    rng.shuffle(tr)
    ncols = args.feature_cols or X.shape[1]
    Xe = np.ascontiguousarray(X[np.nonzero(is_ev)[0]][:, :ncols])
    ye = y[is_ev]
    Xtr = np.ascontiguousarray(X[tr][:, :ncols])
    ytr = y[tr]
    if mmapped:
        del X, z
    import gc as _gc
    _gc.collect()
    print(f"      materialised: train {Xtr.nbytes/1e9:.2f} GB, eval {Xe.nbytes/1e9:.2f} GB, "
          f"{ncols} feature columns", flush=True)
    chance = 1.0 / N_CONFIGS
    print(f"[2/5] grouped split: {len(tr)} train / {len(ye)} eval, "
          f"{len(ev_groups)} held-out source chunks, chance={chance:.4f}", flush=True)

    print("[3/5] trivial baselines (measured before any learned number)...", flush=True)
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.tree import DecisionTreeClassifier
    # The baselines are trained on the SAME maximum training data as the top rung. Beating a
    # data-starved baseline would flatter the result, so the baseline is not starved.
    top_rung = max([r for r in args.rungs if r <= len(tr)], default=len(tr))
    nb = min(len(ytr), top_rung)
    print(f"      (baselines trained on {nb} fragments - the same as the top rung)", flush=True)
    baselines = {}
    for nm, clf in [("majority", DummyClassifier(strategy="most_frequent")),
                    ("stratified", DummyClassifier(strategy="stratified", random_state=0)),
                    ("best_single_feat", DecisionTreeClassifier(max_depth=1, random_state=0)),
                    ("depth3_tree", DecisionTreeClassifier(max_depth=3, random_state=0)),
                    ("depth8_tree", DecisionTreeClassifier(max_depth=8, random_state=0)),
                    ("depth16_tree", DecisionTreeClassifier(max_depth=16, random_state=0)),
                    ("logistic", LogisticRegression(max_iter=400))]:
        t = time.perf_counter()
        clf.fit(Xtr[:nb], ytr[:nb])
        baselines[nm] = round(float(accuracy_score(ye, clf.predict(Xe))), 4)
        print(f"      {nm:<18} {baselines[nm]:.4f}   ({time.perf_counter()-t:.0f}s)", flush=True)
    # The frozen baseline set (preregistration 0003) is: majority, label-prior sampling,
    # length/ratio-only (NOT COMPUTABLE here - see artifacts/pivot/prereg_interpretation.json),
    # depth-3 tree, logistic regression. `best_trivial_baseline` takes the best of THAT set,
    # because that is what was frozen. The deeper trees added during piloting are reported
    # separately as the expanded, stricter reading.
    FROZEN_SET = ["majority", "stratified", "depth3_tree", "logistic"]
    frozen = {k: v for k, v in baselines.items() if k in FROZEN_SET}
    best_name = max(frozen, key=frozen.get)
    best_val = frozen[best_name]
    exp_name = max(baselines, key=baselines.get)
    exp_val = baselines[exp_name]
    print(f"      frozen-set best:   {best_name} {best_val:.4f}", flush=True)
    print(f"      expanded-set best: {exp_name} {exp_val:.4f}  (stricter reading)", flush=True)

    print("[4/5] rungs (one fixed model class throughout)...", flush=True)
    rungs, per_ex, skipped, costs = [], [], [], []
    for r in args.rungs:
        if r > len(ytr):
            skipped.append(r); print(f"      rung {r}: SKIPPED, only {len(ytr)} training fragments")
            continue
        t = time.perf_counter()
        m = make_model(args.seed, args.model).fit(Xtr[:r], ytr[:r])
        correct = (m.predict(Xe) == ye).astype(np.int8)
        acc = float(correct.mean())
        secs = round(time.perf_counter() - t, 1)
        rungs.append({"n_units": int(r), "accuracy": round(acc, 4), "train_seconds": secs})
        per_ex.append({"n_units": int(r), "per_example": correct.tolist()})
        costs.append(secs)
        print(f"      rung {r:>8}: accuracy {acc:.4f}   ({secs}s)", flush=True)

    print("[5/5] null control: labels shuffled, identical pipeline...", flush=True)
    nn = min(len(ytr), max(args.rungs[0], 20000))
    y_sh = ytr[:nn].copy(); rng.shuffle(y_sh)
    t = time.perf_counter()
    m0 = make_model(args.seed, args.model).fit(Xtr[:nn], y_sh)
    null_acc = round(float((m0.predict(Xe) == ye).mean()), 4)
    print(f"      shuffled-label accuracy {null_acc:.4f}  vs chance {chance:.4f}   "
          f"({time.perf_counter()-t:.0f}s)", flush=True)

    with open(args.scores_out, "w") as fh:
        json.dump({"schema": "raise-v1/rung_scores/1",
                   "metric": "accuracy on a shared held-out evaluation set, grouped by source chunk",
                   "rungs": per_ex}, fh)

    fit = None
    if len(rungs) >= 4:
        sys.path.insert(0, os.path.join(REPO, "tools"))
        from scaling import fit as fit_curve
        fit = fit_curve([{"n_units": r["n_units"], "per_example": p["per_example"]}
                         for r, p in zip(rungs, per_ex)], n_boot=2000, seed=args.seed)

    out = {
        "schema": "raise-v1/pivot_deflate_curve/1",
        "tag": args.tag,
        "preregistration": "0003-pivot-deflate-curve",
        "task": "recover the (implementation, level) that produced a carved DEFLATE fragment",
        "student_input": f"{args.carve} bytes carved from the middle of the stream. No header, no "
                         f"stream start, no plaintext, and NOT the stream length.",
        "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
        "chance_accuracy": round(chance, 6),
        "content_families": FAMILIES,
        "n_source_chunks": args.chunks, "chunk_size_bytes": args.chunk_size,
        "carve_bytes": args.carve, "n_fragments": int(len(y)),
        "feature_set": (f"first {args.feature_cols} columns" if args.feature_cols else "all"),
        "n_features": int(Xtr.shape[1]), "seed": args.seed, "model_class": args.model,
        "split_is_grouped_by_source": True,
        "n_eval_fragments": int(len(ye)), "n_train_fragments": int(len(ytr)),
        "n_heldout_source_chunks": int(len(ev_groups)),
        "trivial_baselines": baselines,
        "best_trivial_baseline_name": best_name, "best_trivial_baseline": best_val,
        "frozen_baseline_set": ["majority", "stratified", "depth3_tree", "logistic"],
        "length_ratio_baseline": "NOT COMPUTABLE - fragments are fixed-length and the ratio needs "
                                 "the plaintext; it degenerates to the majority baseline, which is "
                                 "measured. See artifacts/pivot/prereg_interpretation.json.",
        "best_baseline_expanded_name": exp_name, "best_baseline_expanded": exp_val,
        "baselines_trained_on_n": int(nb),
        "rungs": rungs, "rungs_skipped": skipped,
        "n_rungs": len(rungs),
        "top_rung_accuracy": rungs[-1]["accuracy"] if rungs else None,
        "shuffled_label_accuracy": null_acc,
        "free_decoder_arm": "UNAVAILABLE BY CONSTRUCTION. Law L3(i)'s re-run-and-compare attack "
                            "requires re-running the compressor on the plaintext. A carved fragment "
                            "does not contain the plaintext, so the zero-training decoder that beat "
                            "every learned model on SAT solvers cannot be built here.",
        "cost": {"build_seconds": build_s, "train_seconds_per_rung": costs,
                 "cpu_cores": args.procs, "gpu": "none"},
    }
    if rungs:
        out["margin_over_frozen_baseline"] = round(rungs[-1]["accuracy"] - best_val, 4)
        out["margin_over_expanded_baseline"] = round(rungs[-1]["accuracy"] - exp_val, 4)
    if fit:
        out["decades_spanned"] = fit["orders_of_magnitude_spanned"]
        out["slope"] = fit["primary_fit"]["slope"]
        out["slope_ci95_low"] = fit["primary_fit"]["slope_ci95"][0]
        out["slope_ci95_high"] = fit["primary_fit"]["slope_ci95"][1]
        out["slope_r2"] = fit["primary_fit"]["r2"]
        out["permutation_p"] = fit["permutation_test"]["p_value"]
    else:
        out["decades_spanned"] = (round(float(np.log10(rungs[-1]["n_units"] / rungs[0]["n_units"])), 4)
                                  if len(rungs) >= 2 else 0.0)
        out["note_no_fit"] = (f"{len(rungs)} rung(s); tools/scaling.py requires >= 4 and refuses "
                              f"fewer. No slope was fitted.")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"\nbest trivial baseline: {best_name} {best_val:.4f} | chance {chance:.4f}")
    if rungs:
        print(f"top rung {rungs[-1]['accuracy']:.4f} | margin over baseline "
              f"{rungs[-1]['accuracy']-best_val:+.4f} (prereg needs >= 0.05)")
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
