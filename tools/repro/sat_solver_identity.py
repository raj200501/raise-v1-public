#!/usr/bin/env python3
"""Reproduction: can a learned model beat re-running the solvers?

This is the load-bearing measurement behind law L3(i) in docs/DOMAIN_SELECTION.md — that when a
MACHINE does the labelling, the machine is re-runnable, and "re-run everything and compare" is a
zero-training decoder that a learned model cannot approach.

The setup is the archetype of "a search whose result is kept but whose trajectory is discarded":
six CDCL SAT solvers each return a satisfying assignment for the same random 3-SAT instance. The
trajectory is gone; only the model survives. Which solver produced it?

  free decoder : re-run all six solvers on the instance and see whose model matches. No training.
  learned      : gradient boosting on joint (formula, assignment) features, grouped by instance so
                 no instance appears in both train and test.

Run:  python3 tools/repro/sat_solver_identity.py --instances 2500
Writes artifacts/verification/repro_sat_solver_identity.json
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

import numpy as np
from pysat.formula import CNF
from pysat.solvers import Solver

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOLVERS = ["Cadical153", "Glucose42", "Lingeling", "Minisat22", "MapleChrono", "Mergesat3"]
NVARS, NCLAUSES = 120, 492          # ratio 4.1, near the satisfiability phase transition


def random_3sat(rng: random.Random, n: int, m: int) -> list[list[int]]:
    clauses = []
    for _ in range(m):
        vs = rng.sample(range(1, n + 1), 3)
        clauses.append([v if rng.random() < 0.5 else -v for v in vs])
    return clauses


def solve_with(name: str, clauses) -> list[int] | None:
    with Solver(name=name, bootstrap_with=clauses) as s:
        return s.get_model() if s.solve() else None


def sign_vec(model, n: int) -> np.ndarray:
    v = np.zeros(n, dtype=np.int8)
    for lit in model[:n]:
        idx = abs(lit) - 1
        if idx < n:
            v[idx] = 1 if lit > 0 else -1
    return v


def features(clauses, assign: np.ndarray, n: int) -> list[float]:
    """Joint formula x assignment features. Nothing here identifies a solver by name."""
    a = assign.astype(np.int8)
    pos = int((a > 0).sum())
    occ_p = np.zeros(n); occ_n = np.zeros(n)
    per_clause_true = np.zeros(len(clauses), dtype=np.int8)
    for ci, cl in enumerate(clauses):
        t = 0
        for lit in cl:
            i = abs(lit) - 1
            if lit > 0:
                occ_p[i] += 1
                if a[i] > 0:
                    t += 1
            else:
                occ_n[i] += 1
                if a[i] < 0:
                    t += 1
        per_clause_true[ci] = t
    deg = occ_p + occ_n
    bias = occ_p - occ_n
    hist = [float((per_clause_true == k).sum()) / len(clauses) for k in range(4)]
    agree = float(np.mean(np.sign(bias) == a))                      # follows majority polarity?
    top = np.argsort(-deg)[: max(1, n // 10)]
    bot = np.argsort(deg)[: max(1, n // 10)]
    crit = per_clause_true == 1
    critvars = np.zeros(n)
    for ci in np.nonzero(crit)[0]:
        for lit in clauses[ci]:
            critvars[abs(lit) - 1] += 1
    return [
        pos / n, float(a.mean()), float(a.std()),
        *hist,
        float(per_clause_true.mean()), float(per_clause_true.std()),
        float(per_clause_true.min()), float(per_clause_true.max()),
        agree,
        float(np.mean(np.sign(bias[top]) == a[top])),
        float(np.mean(np.sign(bias[bot]) == a[bot])),
        float(np.corrcoef(deg, a)[0, 1]) if deg.std() > 0 else 0.0,
        float(np.corrcoef(bias, a)[0, 1]) if bias.std() > 0 else 0.0,
        float(critvars.sum()) / n, float(critvars.max()),
        float(np.mean(a[critvars > 0])) if (critvars > 0).any() else 0.0,
        float(np.mean(deg[a > 0])), float(np.mean(deg[a < 0])) if (a < 0).any() else 0.0,
        float(np.mean(bias[a > 0])), float(np.mean(bias[a < 0])) if (a < 0).any() else 0.0,
        float((deg == 0).sum()) / n,
        float(np.percentile(deg, 90)), float(np.percentile(deg, 10)),
        float(np.sum(a > 0) - np.sum(a < 0)) / n,
        float(np.mean(np.abs(bias))),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instances", type=int, default=2500)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--determinism-checks", type=int, default=200)
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "verification",
                                                  "repro_sat_solver_identity.json"))
    args = ap.parse_args()

    rng = random.Random(args.seed)
    t0 = time.perf_counter()

    X, y, groups = [], [], []
    models_by_inst = []
    n_sat = n_gen = 0
    while n_sat < args.instances:
        n_gen += 1
        clauses = random_3sat(rng, NVARS, NCLAUSES)
        ms = {}
        for name in SOLVERS:
            m = solve_with(name, clauses)
            if m is None:
                break
            ms[name] = sign_vec(m, NVARS)
        if len(ms) != len(SOLVERS):
            continue
        models_by_inst.append((clauses, ms))
        for si, name in enumerate(SOLVERS):
            X.append(features(clauses, ms[name], NVARS)); y.append(si); groups.append(n_sat)
        n_sat += 1
    gen_seconds = time.perf_counter() - t0

    # (1) determinism: re-run each solver on the same instance and compare models
    det_same = det_total = 0
    for clauses, ms in models_by_inst[: args.determinism_checks]:
        for name in SOLVERS:
            again = sign_vec(solve_with(name, clauses), NVARS)
            det_total += 1
            det_same += int(np.array_equal(again, ms[name]))

    # (2) divergence: do the six ever agree?
    all_agree = 0
    pair_same = {f"{a}|{b}": 0 for i, a in enumerate(SOLVERS) for b in SOLVERS[i + 1:]}
    for _, ms in models_by_inst:
        vecs = [ms[s] for s in SOLVERS]
        all_agree += int(all(np.array_equal(vecs[0], v) for v in vecs[1:]))
        for i, a in enumerate(SOLVERS):
            for b in SOLVERS[i + 1:]:
                pair_same[f"{a}|{b}"] += int(np.array_equal(ms[a], ms[b]))

    # (3) the free decoder: re-run all six, take the match. Ties broken by first index.
    t1 = time.perf_counter()
    dec_correct = dec_total = dec_ties = 0
    for clauses, ms in models_by_inst:
        rerun = {name: sign_vec(solve_with(name, clauses), NVARS) for name in SOLVERS}
        for si, name in enumerate(SOLVERS):
            target = ms[name]
            matches = [j for j, o in enumerate(SOLVERS) if np.array_equal(rerun[o], target)]
            dec_total += 1
            if len(matches) > 1:
                dec_ties += 1
            if matches and matches[0] == si:
                dec_correct += 1
            elif matches and si in matches:
                pass  # tie resolved to another solver: counted as wrong, the strict reading
    decoder_seconds = time.perf_counter() - t1

    # (4) the learned model, grouped by instance
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import accuracy_score
    X = np.asarray(X, dtype=float); y = np.asarray(y); groups = np.asarray(groups)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    uniq = np.unique(groups); rs = np.random.default_rng(args.seed); rs.shuffle(uniq)
    n_test_g = max(1, len(uniq) // 5)
    test_g, train_g = set(uniq[:n_test_g].tolist()), uniq[n_test_g:]
    te = np.array([g in test_g for g in groups])
    Xte, yte = X[te], y[te]

    curve = []
    for rung in [r for r in (300, 900, 3000, 13500) if r <= (len(train_g) * len(SOLVERS))]:
        keep = set(train_g[: max(1, rung // len(SOLVERS))].tolist())
        m = np.array([g in keep for g in groups])
        t2 = time.perf_counter()
        clf = HistGradientBoostingClassifier(max_iter=200, random_state=0).fit(X[m], y[m])
        acc = float(accuracy_score(yte, clf.predict(Xte)))
        curve.append({"n_rows": int(m.sum()), "accuracy": round(acc, 4),
                      "fit_seconds": round(time.perf_counter() - t2, 2)})

    res = {
        "schema": "raise-v1/repro_sat_solver_identity/1",
        "what": "Load-bearing reproduction for law L3(i): when a machine does the labelling, "
                "re-run-and-compare is a zero-training decoder that a learned model cannot approach.",
        "setup": {"solvers": SOLVERS, "n_vars": NVARS, "n_clauses": NCLAUSES,
                  "clause_ratio": round(NCLAUSES / NVARS, 3), "seed": args.seed,
                  "instances_satisfiable": n_sat, "instances_generated": n_gen,
                  "rows": int(len(y)), "n_classes": len(SOLVERS),
                  "chance_accuracy": round(1.0 / len(SOLVERS), 4)},
        "determinism": {"checks": det_total, "identical": det_same,
                        "rate": round(det_same / det_total, 6) if det_total else None},
        "divergence": {"instances": n_sat, "all_six_agree": all_agree,
                       "pairwise_identical": pair_same},
        "free_decoder_rerun_and_compare": {
            "items": dec_total, "correct": dec_correct,
            "accuracy": round(dec_correct / dec_total, 4) if dec_total else None,
            "tie_rate": round(dec_ties / dec_total, 4) if dec_total else None,
            "seconds": round(decoder_seconds, 1),
            "training_rows_required": 0},
        "learned_model_curve": curve,
        "cost": {"data_generation_seconds": round(gen_seconds, 1),
                 "total_seconds": round(time.perf_counter() - t0, 1),
                 "cpu_cores": os.cpu_count()},
    }
    if len(curve) >= 2:
        d = np.log10(curve[-1]["n_rows"] / curve[0]["n_rows"])
        res["learned_points_per_decade"] = round((curve[-1]["accuracy"] - curve[0]["accuracy"]) / d, 4)
        gap = res["free_decoder_rerun_and_compare"]["accuracy"] - curve[-1]["accuracy"]
        res["gap_to_free_decoder"] = round(gap, 4)
        if res["learned_points_per_decade"] > 0:
            res["decades_to_close_gap_at_observed_slope"] = round(gap / res["learned_points_per_decade"], 1)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps({k: res[k] for k in
                      ("determinism", "free_decoder_rerun_and_compare", "learned_model_curve",
                       "learned_points_per_decade", "gap_to_free_decoder",
                       "decades_to_close_gap_at_observed_slope") if k in res}, indent=2))
    print(f"all six agree on {all_agree} of {n_sat} instances")
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
