#!/usr/bin/env python3
"""Measure the OPERATIONAL output of the carved-DEFLATE model. Governed by preregistration 0006.

Same corpus, same seed, same grouped split, same four rungs as 0003. Nothing is re-manufactured and
nothing is re-split, so every number here is directly comparable to the top-1 numbers 0003 published.
What changes is what is READ off the model:

  1. ranked candidate lists      top-1 / top-3 / top-5, for the model AND for every baseline
  2. abstention                  accuracy on each classifier's OWN most-confident decile
  3. does usability scale        the top-5 slope across the same four rungs
  4. the null control            shuffled labels; top-5 must fall to the 5/26 chance level

Interpretation choices recorded and drand-anchored BEFORE this ran:
artifacts/pivot/topk_prereg_interpretation.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import CONFIG_NAMES, N_CONFIGS  # noqa: E402
from npzmap import fill_f32, fill_f64, npz_memmap  # noqa: E402
from run_study import _rss_gb, make_model  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KS = (1, 3, 5)


def proba_chunked(model, Xe32, chunk=50000):
    """predict_proba over a float32 evaluation block, widened one chunk at a time."""
    return np.concatenate([model.predict_proba(np.asarray(Xe32[i:i + chunk], dtype=np.float64))
                           for i in range(0, len(Xe32), chunk)])


def topk_hits(proba, classes, ye, k):
    """Per-example 0/1: is the true label among the model's top k? Kept per-example for the bootstrap."""
    k = min(k, proba.shape[1])
    idx = np.argpartition(-proba, k - 1, axis=1)[:, :k]
    return (classes[idx] == ye[:, None]).any(axis=1).astype(np.int8)


def selective_decile(proba, classes, ye, frac=0.10):
    """Accuracy on the most-confident `frac` of the evaluation set.

    Ranking is by DESCENDING maximum class probability with ties broken by ASCENDING evaluation
    index — deterministic, label-independent, and identical for every model and baseline. For a
    constant classifier this yields the first tenth of the evaluation set in stored order, so a
    classifier with no confidence signal gets no benefit from selection. That choice was recorded
    and anchored before this ran; see artifacts/pivot/topk_prereg_interpretation.json.
    """
    conf = proba.max(axis=1)
    order = np.lexsort((np.arange(len(conf)), -conf))
    sel = order[:max(1, int(len(conf) * frac))]
    pred = classes[proba[sel].argmax(axis=1)]
    return round(float((pred == ye[sel]).mean()), 4), int(len(sel))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--carve", type=int, default=4096)
    ap.add_argument("--rungs", type=int, nargs="*", default=[1000, 10000, 100000, 800000])
    ap.add_argument("--eval-frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--model", default="hgb")
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "deflate_topk.json"))
    args = ap.parse_args()

    print(f"[1/5] mapping {os.path.relpath(args.cache, REPO)} in place", flush=True)
    X = npz_memmap(args.cache, "X")
    with np.load(args.cache) as z:
        y = np.asarray(z["y"]); g = np.asarray(z["g"])
    ncols = X.shape[1]

    # Identical split to 0003: same seed, same shuffle order, same grouping.
    rng = np.random.default_rng(args.seed)
    groups = np.unique(g); rng.shuffle(groups)
    ev_groups = set(groups[:max(1, int(len(groups) * args.eval_frac))].tolist())
    is_ev = np.fromiter((int(v) in ev_groups for v in g), bool, len(g))
    tr = np.nonzero(~is_ev)[0]; rng.shuffle(tr)
    tr = tr[:min(len(tr), max(args.rungs))]
    ev = np.nonzero(is_ev)[0]
    Xe = fill_f32(np.empty((len(ev), ncols), np.float32), X, ev, ncols)
    ye = np.asarray(y[is_ev])
    Xtr = fill_f64(np.empty((len(tr), ncols), np.float64), X, tr, ncols)
    ytr = np.asarray(y[tr])
    del X
    print(f"      train {len(ytr)} / eval {len(ye)}, RSS {_rss_gb():.2f} GB", flush=True)

    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier

    FROZEN_SET = ["majority", "stratified", "depth3_tree", "logistic"]
    nb = len(ytr)
    print(f"[2/5] baselines, each scored on its OWN predict_proba and its OWN decile "
          f"(trained on {nb})", flush=True)
    bl_topk, bl_sel = {}, {}
    for nm, clf in [("majority", DummyClassifier(strategy="most_frequent")),
                    ("stratified", DummyClassifier(strategy="stratified", random_state=0)),
                    ("best_single_feat", DecisionTreeClassifier(max_depth=1, random_state=0)),
                    ("depth3_tree", DecisionTreeClassifier(max_depth=3, random_state=0)),
                    ("depth8_tree", DecisionTreeClassifier(max_depth=8, random_state=0)),
                    ("depth16_tree", DecisionTreeClassifier(max_depth=16, random_state=0)),
                    ("logistic", LogisticRegression(max_iter=400))]:
        t = time.perf_counter()
        clf.fit(Xtr[:nb], ytr[:nb])
        pr = proba_chunked(clf, Xe)
        cls = np.asarray(clf.classes_)
        bl_topk[nm] = {f"top{k}": round(float(topk_hits(pr, cls, ye, k).mean()), 4) for k in KS}
        bl_sel[nm] = selective_decile(pr, cls, ye)[0]
        del pr
        print(f"      {nm:<18} top1 {bl_topk[nm]['top1']:.4f}  top3 {bl_topk[nm]['top3']:.4f}  "
              f"top5 {bl_topk[nm]['top5']:.4f}  decile {bl_sel[nm]:.4f}  "
              f"({time.perf_counter()-t:.0f}s, RSS {_rss_gb():.2f} GB)", flush=True)

    frozen5 = {k: v["top5"] for k, v in bl_topk.items() if k in FROZEN_SET}
    fname = max(frozen5, key=frozen5.get)
    all5 = {k: v["top5"] for k, v in bl_topk.items()}
    ename = max(all5, key=all5.get)
    # STRICTEST available reading, fixed before the run: the max over ALL baselines.
    sname = max(bl_sel, key=bl_sel.get)
    print(f"      frozen-set best top5:   {fname} {frozen5[fname]:.4f}", flush=True)
    print(f"      expanded-set best top5: {ename} {all5[ename]:.4f}", flush=True)
    print(f"      best baseline decile:   {sname} {bl_sel[sname]:.4f}  (max over ALL baselines)",
          flush=True)

    print("[3/5] rungs", flush=True)
    rungs, per_ex_top5, model_sel, top1s, top3s, top5s = [], [], None, None, None, None
    for r in args.rungs:
        t = time.perf_counter()
        m = make_model(args.seed, args.model)
        k = max(1, int(r * 0.9))
        m.fit(Xtr[:k], ytr[:k], X_val=Xtr[k:r], y_val=ytr[k:r])
        pr = proba_chunked(m, Xe)
        cls = np.asarray(m.classes_)
        hits = {kk: topk_hits(pr, cls, ye, kk) for kk in KS}
        acc = {f"top{kk}": round(float(hits[kk].mean()), 4) for kk in KS}
        rungs.append({"n_units": int(r), **acc,
                      "train_seconds": round(time.perf_counter() - t, 1)})
        per_ex_top5.append({"n_units": int(r), "per_example": hits[5].tolist()})
        if r == max(args.rungs):
            model_sel, n_sel = selective_decile(pr, cls, ye)
            top1s, top3s, top5s = acc["top1"], acc["top3"], acc["top5"]
        del pr
        print(f"      rung {r:>8}: top1 {acc['top1']:.4f}  top3 {acc['top3']:.4f}  "
              f"top5 {acc['top5']:.4f}   ({rungs[-1]['train_seconds']}s, "
              f"RSS {_rss_gb():.2f} GB)", flush=True)

    print("[4/5] null control: labels shuffled, identical pipeline", flush=True)
    nn = min(len(ytr), 20000)
    y_sh = ytr[:nn].copy(); rng.shuffle(y_sh)
    m0 = make_model(args.seed, args.model)
    k0 = max(1, int(nn * 0.9))
    m0.fit(Xtr[:k0], y_sh[:k0], X_val=Xtr[k0:nn], y_val=y_sh[k0:nn])
    pr0 = proba_chunked(m0, Xe)
    null5 = round(float(topk_hits(pr0, np.asarray(m0.classes_), ye, 5).mean()), 4)
    del pr0
    print(f"      shuffled-label top5 {null5:.4f}  vs 5/26 chance {5/N_CONFIGS:.4f}", flush=True)

    print("[5/5] top-5 slope", flush=True)
    sys.path.insert(0, os.path.join(REPO, "tools"))
    from scaling import fit as fit_curve
    fit = fit_curve(per_ex_top5, n_boot=2000, seed=args.seed, groups=np.asarray(g[ev]))

    out = {
        "schema": "raise-v1/deflate_topk/1",
        "preregistration": "0006-deflate-operational-output",
        "task": ("the operational output of the carved-DEFLATE model: a ranked candidate list and a "
                 "confidence that supports abstention"),
        "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
        "chance_top1": round(1.0 / N_CONFIGS, 6), "chance_top5": round(5.0 / N_CONFIGS, 6),
        "carve_bytes": args.carve, "seed": args.seed, "model_class": args.model,
        "split_is_grouped_by_source": True,
        "n_eval_fragments": int(len(ye)), "n_train_fragments": int(len(ytr)),
        "baselines_trained_on_n": int(nb),
        "baseline_topk": bl_topk,
        "baseline_selective_top_decile": bl_sel,
        "selective_decile_n": int(n_sel),
        "top1_accuracy": top1s, "top3_accuracy": top3s, "top5_accuracy": top5s,
        "best_trivial_baseline_top5": frozen5[fname], "best_trivial_baseline_top5_name": fname,
        "best_baseline_expanded_top5": all5[ename], "best_baseline_expanded_top5_name": ename,
        "selective_top_decile_accuracy": model_sel,
        "baseline_selective_top_decile_accuracy": bl_sel[sname],
        "baseline_selective_top_decile_name": sname,
        "baseline_selective_reading": ("MAXIMUM over ALL baselines, frozen and expanded alike - the "
                                       "strictest available reading of 0006's wording, fixed before "
                                       "the run in artifacts/pivot/topk_prereg_interpretation.json"),
        "shuffled_label_top5_accuracy": null5,
        "rungs": rungs, "n_rungs": len(rungs),
        "decades_spanned": fit["orders_of_magnitude_spanned"],
        "top5_slope": fit["primary_fit"]["slope"],
        "top5_slope_ci95_low": fit["primary_fit"]["slope_ci95"][0],
        "top5_slope_ci95_high": fit["primary_fit"]["slope_ci95"][1],
        "top5_slope_ci95_unit": fit["bootstrap_unit"],
        "top5_slope_r2": fit["primary_fit"]["r2"],
        "top5_permutation_p": fit["permutation_test"]["p_value"],
        "establishes_a_buyer": False,
        "cost": {"train_seconds_per_rung": [r["train_seconds"] for r in rungs],
                 "cpu_cores": 4, "gpu": "none"},
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
    scores_out = os.path.join(REPO, "artifacts", "pivot", "topk_rung_scores.json")
    with open(scores_out, "w") as fh:
        json.dump({"schema": "raise-v1/rung_scores/1",
                   "metric": "top-5 hit on a shared held-out evaluation set, grouped by source chunk",
                   "eval_chunk_ids": np.asarray(g[ev]).tolist(),
                   "rungs": per_ex_top5}, fh)
    print(f"wrote {os.path.relpath(scores_out, REPO)}  (banked so the interval can be re-derived "
          f"at the cluster level - the audit found fragment-level intervals anti-conservative)")
    print(f"\nwrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
