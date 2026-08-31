#!/usr/bin/env python3
"""Which feature families carry the signal, at 4096 and at 1024?

DIAGNOSTIC, NOT A CLAIM. Preregistration 0007 returned CARVE_FAILS and established - because A1 had
already measured the input - that the failure at a 1024-byte window is a MODELLING failure rather
than an information failure. That makes "which part of the representation dies" a question with an
answer, and this finds it.

Nothing here is preregistered and nothing here may be reported as a result. If it points at a fix,
that fix needs its own preregistration, frozen before it is measured, exactly as 0006 and 0007 were.
Its output is banked into the engineering log, not into a verdict.

Both corpora are held at the SAME training rung so the comparison is about the representation and
not about data volume.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from npzmap import fill_f32, npz_memmap  # noqa: E402
from run_study import make_model, predict_chunked  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Column layout of features.py v3, read off its concatenate() call and its constants.
FAMILIES = {
    "byte_hist":    (0, 256),
    "pair_hash":    (256, 512),
    "bit_runs":     (512, 536),
    "scalars":      (536, 553),
    "align_stats":  (553, 593),
    "stored_block": (593, 596),
    "align_hist":   (596, 1108),
}
SUBSETS = {
    "all":                 list(FAMILIES),
    "byte_hist_only":      ["byte_hist"],
    "v1_no_alignment":     ["byte_hist", "pair_hash", "bit_runs", "scalars"],
    "align_hist_only":     ["align_hist"],
    "alignment_only":      ["align_stats", "stored_block", "align_hist"],
    "drop_align_hist":     ["byte_hist", "pair_hash", "bit_runs", "scalars", "align_stats",
                            "stored_block"],
}


def cols(names):
    idx = []
    for n in names:
        lo, hi = FAMILIES[n]
        idx.extend(range(lo, hi))
    return np.array(idx, dtype=np.int64)


def load(cache, seed, eval_frac, rung):
    X = npz_memmap(cache, "X")
    with np.load(cache) as z:
        y = np.asarray(z["y"]); g = np.asarray(z["g"])
    ncols = X.shape[1]
    rng = np.random.default_rng(seed)
    groups = np.unique(g); rng.shuffle(groups)
    ev_groups = set(groups[:max(1, int(len(groups) * eval_frac))].tolist())
    is_ev = np.fromiter((int(v) in ev_groups for v in g), bool, len(g))
    tr = np.nonzero(~is_ev)[0]; rng.shuffle(tr); tr = tr[:rung]
    ev = np.nonzero(is_ev)[0]
    Xe = fill_f32(np.empty((len(ev), ncols), np.float32), X, ev, ncols)
    Xt = fill_f32(np.empty((len(tr), ncols), np.float32), X, tr, ncols)
    return Xt, np.asarray(y[tr]), Xe, np.asarray(y[is_ev])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--eval-frac", type=float, default=0.2)
    args = ap.parse_args()

    corpora = [("4096", os.path.join(REPO, "data", "pivot", "full_c4096.npz")),
               ("1024", os.path.join(REPO, "data", "pivot", "carve_c1024.npz"))]
    out = {"schema": "raise-v1/feature_ablation/1",
           "status": ("DIAGNOSTIC ONLY. Not preregistered, not a result, and not quotable as one. "
                      "Any fix it suggests needs its own preregistration frozen before measurement."),
           "rung": args.rung, "seed": args.seed,
           "families": {k: list(v) for k, v in FAMILIES.items()}, "by_carve": {}}
    for carve, cache in corpora:
        if not os.path.exists(cache):
            print(f"skipping {carve}: {cache} absent"); continue
        Xt, yt, Xe, ye = load(cache, args.seed, args.eval_frac, args.rung)
        print(f"\n=== carve {carve}: {len(yt)} train / {len(ye)} eval ===", flush=True)
        res = {}
        for name, fams in SUBSETS.items():
            c = cols(fams)
            t = time.perf_counter()
            Xtr = np.ascontiguousarray(Xt[:, c], dtype=np.float64)
            m = make_model(args.seed, "hgb")
            k = max(1, int(len(yt) * 0.9))
            m.fit(Xtr[:k], yt[:k], X_val=Xtr[k:], y_val=yt[k:])
            acc = round(float((predict_chunked(m, Xe[:, c]) == ye).mean()), 4)
            del Xtr
            res[name] = {"accuracy": acc, "n_features": int(len(c)),
                         "seconds": round(time.perf_counter() - t, 1)}
            print(f"  {name:<20} {len(c):>5} feats   {acc:.4f}   ({res[name]['seconds']}s)",
                  flush=True)
        out["by_carve"][carve] = res
        del Xt, Xe
        p = os.path.join(REPO, "artifacts", "pivot", "feature_ablation.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")   # write after each corpus
    print("\nwrote artifacts/pivot/feature_ablation.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
