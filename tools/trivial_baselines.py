#!/usr/bin/env python3
"""The A2 gate: measure the dumbest thing that could work, before believing anything.

Round 1 of domain selection killed a candidate because a reviewer wrote fifty lines of
non-learned rules and reached F1 0.768 on a task whose entire thesis was that it needed a
learned model. Twenty thousand training records bought 1.4 more points. That failure mode is
cheap to test for and expensive to miss, so it is mechanised here rather than left to memory.

Given features and labels, this runs a battery of baselines that contain no learning worth the
name, and reports the best of them as the floor any real result must clear:

  majority          always predict the most frequent class
  stratified        sample from the label prior, ignoring the input entirely
  uniform           uniform random over observed classes
  best_single_feat  the single most informative feature, thresholded by a depth-1 tree
  depth3_tree       a decision tree of depth 3 (a rule a person could write out by hand)
  nearest_neighbour 1-NN on standardised features
  linear            logistic regression on standardised features

`--floor-from` reads a preregistered margin and exits non-zero when a claimed model score does
not clear best-baseline + margin. That makes "we beat the trivial baseline" a gate that can
fail rather than a sentence in a paragraph.

Exit codes: 0 pass; 1 the claimed score does not clear the floor; 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainlib import REPO_ROOT, sha256_file  # noqa: E402


def _load(path: str):
    """Accepts .npz with X,y or JSON with {'X': [[...]], 'y': [...]}"""
    if path.endswith(".npz"):
        d = np.load(path, allow_pickle=False)
        return np.asarray(d["X"], dtype=float), np.asarray(d["y"])
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return np.asarray(d["X"], dtype=float), np.asarray(d["y"])


def _metrics(y_true, y_pred, labels):
    from sklearn.metrics import accuracy_score, f1_score
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", labels=labels, zero_division=0)),
    }


def run(Xtr, ytr, Xte, yte, seed: int = 0) -> dict:
    from sklearn.dummy import DummyClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier

    labels = sorted(set(ytr.tolist()) | set(yte.tolist()))
    scaler = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = scaler.transform(Xtr), scaler.transform(Xte)

    models = {
        "majority": (DummyClassifier(strategy="most_frequent"), False),
        "stratified": (DummyClassifier(strategy="stratified", random_state=seed), False),
        "uniform": (DummyClassifier(strategy="uniform", random_state=seed), False),
        "best_single_feat": (DecisionTreeClassifier(max_depth=1, random_state=seed), False),
        "depth3_tree": (DecisionTreeClassifier(max_depth=3, random_state=seed), False),
        "nearest_neighbour": (KNeighborsClassifier(n_neighbors=1), True),
        "linear": (LogisticRegression(max_iter=2000, random_state=seed), True),
    }

    out = {}
    for name, (clf, scaled) in models.items():
        t0 = time.perf_counter()
        a, b = (Xtr_s, Xte_s) if scaled else (Xtr, Xte)
        try:
            clf.fit(a, ytr)
            pred = clf.predict(b)
            m = _metrics(yte, pred, labels)
            m["fit_seconds"] = round(time.perf_counter() - t0, 4)
        except Exception as e:  # noqa: BLE001
            m = {"COULD_NOT_RUN": f"{type(e).__name__}: {e}"[:200]}
        out[name] = m

    chance = 1.0 / max(len(labels), 1)
    scored = {k: v for k, v in out.items() if "accuracy" in v}
    best_acc = max(scored, key=lambda k: scored[k]["accuracy"]) if scored else None
    best_f1 = max(scored, key=lambda k: scored[k]["macro_f1"]) if scored else None

    return {
        "schema": "raise-v1/trivial_baselines/1",
        "n_train": int(len(ytr)), "n_test": int(len(yte)),
        "n_classes": len(labels), "chance_accuracy": round(chance, 6),
        "seed": seed,
        "baselines": out,
        "best_baseline_accuracy": {"name": best_acc, "value": scored[best_acc]["accuracy"]} if best_acc else None,
        "best_baseline_macro_f1": {"name": best_f1, "value": scored[best_f1]["macro_f1"]} if best_f1 else None,
        "reading": "Any learned result must be compared against best_baseline_*, not against chance. "
                   "A learned model that does not clear the best trivial baseline by a preregistered "
                   "margin has not demonstrated that the manufactured labels carry learnable signal.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("train", help=".npz (X,y) or .json {X,y}")
    ap.add_argument("test", help=".npz (X,y) or .json {X,y}")
    ap.add_argument("--out")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--claimed-score", type=float,
                    help="a learned model's score, to be gated against the baseline floor")
    ap.add_argument("--metric", default="accuracy", choices=["accuracy", "macro_f1"])
    ap.add_argument("--margin", type=float, default=None,
                    help="preregistered margin the claimed score must clear above the best baseline")
    args = ap.parse_args()

    Xtr, ytr = _load(args.train)
    Xte, yte = _load(args.test)
    res = run(Xtr, ytr, Xte, yte, seed=args.seed)
    res["train_artifact"] = os.path.relpath(os.path.abspath(args.train), REPO_ROOT)
    res["test_artifact"] = os.path.relpath(os.path.abspath(args.test), REPO_ROOT)
    res["train_sha256"] = sha256_file(args.train)
    res["test_sha256"] = sha256_file(args.test)

    key = "best_baseline_accuracy" if args.metric == "accuracy" else "best_baseline_macro_f1"
    best = res[key]
    print(f"chance {args.metric}: {res['chance_accuracy']:.4f}" if args.metric == "accuracy" else "")
    for name, m in res["baselines"].items():
        if "accuracy" in m:
            print(f"  {name:<18} accuracy={m['accuracy']:.4f}  macro_f1={m['macro_f1']:.4f}  "
                  f"({m['fit_seconds']}s)")
        else:
            print(f"  {name:<18} {m['COULD_NOT_RUN']}")
    if best:
        print(f"\nbest trivial baseline ({args.metric}): {best['name']} = {best['value']:.4f}")

    rc = 0
    if args.claimed_score is not None:
        if args.margin is None:
            print("--claimed-score requires --margin (the preregistered margin)", file=sys.stderr)
            return 2
        floor = best["value"] + args.margin
        res["gate"] = {"metric": args.metric, "claimed_score": args.claimed_score,
                       "best_baseline": best["value"], "margin": args.margin,
                       "floor": floor, "clears_floor": bool(args.claimed_score >= floor)}
        print(f"\nfloor = best baseline {best['value']:.4f} + preregistered margin {args.margin:.4f} "
              f"= {floor:.4f}")
        if args.claimed_score >= floor:
            print(f"A2 GATE: PASS - claimed {args.claimed_score:.4f} clears the floor")
        else:
            print(f"A2 GATE: FAIL - claimed {args.claimed_score:.4f} does NOT clear the floor "
                  f"{floor:.4f}. The manufactured labels have not been shown to carry learnable "
                  f"signal beyond a rule anyone could write by hand.")
            rc = 1

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"wrote {args.out}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
