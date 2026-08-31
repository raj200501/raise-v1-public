#!/usr/bin/env python3
"""Re-score the 0003 trivial baselines with per-family eval breakdowns. Post-audit derivation.

An adversarial audit established that gutenberg-family source bytes straddle the train/eval
boundary (windows drawn from one shared 7.84 MB pool), so the grouped-split guarantee is false for
that eighth of the corpus. The model's banked per-example scores let its accuracy be restated with
gutenberg excluded; the BASELINES' per-example predictions were never banked, so the margin could
not be restated without refitting them. This refits the same baselines on the same rows with the
same seeds - deterministic, no tuning - and banks per-family and gutenberg-excluded accuracies.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import FAMILIES
from npzmap import fill_f32, fill_f64, npz_memmap
from run_study import predict_chunked

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

X = npz_memmap(os.path.join(REPO, "data/pivot/full_c4096.npz"), "X")
with np.load(os.path.join(REPO, "data/pivot/full_c4096.npz")) as z:
    y = np.asarray(z["y"]); g = np.asarray(z["g"])
rng = np.random.default_rng(20260825)
groups = np.unique(g); rng.shuffle(groups)
ev_groups = set(groups[:max(1, int(len(groups)*0.2))].tolist())
is_ev = np.fromiter((int(v) in ev_groups for v in g), bool, len(g))
tr = np.nonzero(~is_ev)[0]; rng.shuffle(tr); tr = tr[:800000]
ev = np.nonzero(is_ev)[0]
fam_ev = np.array([FAMILIES[int(i) % len(FAMILIES)] for i in g[ev]])
gut = fam_ev == "gutenberg"
ncols = X.shape[1]
Xe = fill_f32(np.empty((len(ev), ncols), np.float32), X, ev, ncols); ye = y[is_ev]
Xtr = fill_f64(np.empty((len(tr), ncols), np.float64), X, tr, ncols); ytr = y[tr]
del X
print(f"refit on {len(ytr)}, score on {len(ye)} ({int(gut.sum())} gutenberg)", flush=True)

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
out = {"schema": "raise-v1/baseline_family_rescore/1",
       "why": __doc__.strip().split("\n\n")[1],
       "n_train": int(len(ytr)), "n_eval": int(len(ye)),
       "n_eval_gutenberg": int(gut.sum()), "baselines": {}}
for nm, clf in [("majority", DummyClassifier(strategy="most_frequent")),
                ("stratified", DummyClassifier(strategy="stratified", random_state=0)),
                ("best_single_feat", DecisionTreeClassifier(max_depth=1, random_state=0)),
                ("depth3_tree", DecisionTreeClassifier(max_depth=3, random_state=0)),
                ("depth8_tree", DecisionTreeClassifier(max_depth=8, random_state=0)),
                ("depth16_tree", DecisionTreeClassifier(max_depth=16, random_state=0)),
                ("logistic", LogisticRegression(max_iter=400))]:
    t = time.perf_counter(); clf.fit(Xtr, ytr)
    pred = predict_chunked(clf, Xe)
    ok = (pred == ye)
    rec = {"full_eval": round(float(ok.mean()), 4),
           "non_gutenberg": round(float(ok[~gut].mean()), 4),
           "gutenberg": round(float(ok[gut].mean()), 4),
           "per_family": {f: round(float(ok[fam_ev == f].mean()), 4) for f in FAMILIES},
           "seconds": round(time.perf_counter() - t, 1)}
    out["baselines"][nm] = rec
    print(f"  {nm:<18} full {rec['full_eval']:.4f}  non-gut {rec['non_gutenberg']:.4f}  "
          f"gut {rec['gutenberg']:.4f}  ({rec['seconds']}s)", flush=True)
    p = os.path.join(REPO, "artifacts/pivot/baseline_family_rescore.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
print("wrote artifacts/pivot/baseline_family_rescore.json")
