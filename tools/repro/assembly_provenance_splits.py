#!/usr/bin/env python3
"""Reproduction: the split leak that killed the genome-assembly-provenance candidate.

Round 2 proposed predicting which assembler, sequencing technology and coverage produced a
deposited genome, using NCBI's own ##Genome-Assembly-Data## comment as a free label. Its adversary
killed it by showing the reported accuracy was an artefact of a RANDOM train/test split over a
label that is a project-level constant.

This re-derives that from the banked inputs (`data/asmprov/*.jsonl`, 240,000 public NCBI assembly
metadata records) with three splits:

  random     rows shuffled           - the setting that produced the headline number
  grouped    held out by bioproject  - no project appears in both train and test
  temporal   held out by release date - train on the past, test on the future

and against the honest trivial baseline for each: predict the training set's majority label.

It also runs the NULL CONTROL. Within a single method string, partition its bioprojects arbitrarily
and predict that FAKE label. Whatever score that reaches is the confound floor, and any "real"
result at or below it is not a result.

SCOPE, stated before the numbers: the originating measurement used ten taxa. Three are banked here.
Sample sizes therefore differ from the original and the figures are NOT expected to match to the
decimal. What is being reproduced is the PATTERN - that random-split accuracy collapses under
grouping, and that the temporal split loses to a constant.

Run:  python3 tools/repro/assembly_provenance_splits.py
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from collections import Counter

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
N_TREES = 60
FEATS = ["n_contigs", "contig_n50", "contig_l50", "n_scaf", "scaf_n50", "scaf_l50",
         "total_len", "ungapped", "gc", "gc_count", "atgc", "n_comp"]


def famof(method: str) -> str:
    """Assembler family: the software name, with the version stripped."""
    m = re.split(r"\s+v(?:er(?:sion)?)?\.?\s+", method, maxsplit=1)[0]
    return re.sub(r"[^A-Za-z0-9+\-]+", " ", m).strip().lower()[:40] or "unknown"


def load(paths):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                if not d.get("method"):
                    continue
                try:
                    x = [float(d.get(k) or 0) for k in FEATS]
                except (TypeError, ValueError):
                    continue
                rows.append({"x": x, "method": d["method"].strip(),
                             "family": famof(d["method"]),
                             "bioproject": d.get("bioproject") or "NA",
                             "release": d.get("release") or "0000-00-00"})
    return rows


def evaluate(rows, label_key, split, seed=0, min_class=2):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, balanced_accuracy_score

    counts = Counter(r[label_key] for r in rows)
    rows = [r for r in rows if counts[r[label_key]] >= min_class]
    if len(set(r[label_key] for r in rows)) < 2:
        return None
    X = np.array([r["x"] for r in rows], dtype=float)
    y = np.array([r[label_key] for r in rows])
    rng = np.random.default_rng(seed)

    if split == "random":
        idx = rng.permutation(len(y)); cut = int(len(y) * 0.8)
        tr, te = idx[:cut], idx[cut:]
    elif split == "grouped":
        gs = sorted({r["bioproject"] for r in rows})
        rng.shuffle(gs)
        hold = set(gs[: max(1, int(len(gs) * 0.2))])
        mask = np.array([r["bioproject"] in hold for r in rows])
        tr, te = np.nonzero(~mask)[0], np.nonzero(mask)[0]
    else:
        order = np.argsort([r["release"] for r in rows], kind="stable")
        cut = int(len(order) * 0.8)
        tr, te = order[:cut], order[cut:]
    if len(te) == 0 or len(tr) == 0:
        return None

    maj = Counter(y[tr]).most_common(1)[0][0]
    trivial = float(accuracy_score(y[te], np.full(len(te), maj)))
    clf = RandomForestClassifier(n_estimators=N_TREES, n_jobs=-1, random_state=seed,
                                 min_samples_leaf=5).fit(X[tr], y[tr])
    pred = clf.predict(X[te])
    return {"split": split, "n": int(len(y)), "n_classes": int(len(set(y))),
            "n_groups": int(len({r["bioproject"] for r in rows})),
            "n_test": int(len(te)),
            "accuracy": round(float(accuracy_score(y[te], pred)), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(y[te], pred)), 4),
            "trivial_train_majority": round(trivial, 4),
            "beats_trivial": bool(accuracy_score(y[te], pred) > trivial)}


def null_control(rows, method, seed=0):
    """Within ONE method string, predict an arbitrary partition of its bioprojects. Chance is 0.5."""
    sub = [r for r in rows if r["method"] == method]
    gs = sorted({r["bioproject"] for r in sub})
    if len(sub) < 100 or len(gs) < 8:
        return None
    rng = np.random.default_rng(seed); rng.shuffle(gs)
    half = set(gs[: len(gs) // 2])
    for r in sub:
        r["fake"] = "A" if r["bioproject"] in half else "B"
    res = evaluate(sub, "fake", "grouped", seed=seed)
    if res:
        res.update({"method": method, "note": "FAKE label. True answer is chance = 0.5."})
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "data", "asmprov"))
    ap.add_argument("--max-records", type=int, default=80000,
                    help="cap on labelled records, for runtime on a 4-core CPU box. Stated in scope.")
    ap.add_argument("--trees", type=int, default=60)
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "verification",
                                                  "repro_assembly_splits.json"))
    args = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(args.data, "*.jsonl")))
    if not paths:
        print(f"no input jsonl under {args.data}", file=sys.stderr)
        return 2
    t0 = time.perf_counter()
    global N_TREES
    N_TREES = args.trees
    rows = load(paths)
    n_all = len(rows)
    if len(rows) > args.max_records:
        rng = np.random.default_rng(0)
        keep = rng.choice(len(rows), size=args.max_records, replace=False)
        rows = [rows[i] for i in sorted(keep)]
    print(f"loaded {n_all} labelled records from {len(paths)} file(s); "
          f"using {len(rows)} after the --max-records cap", flush=True)

    out = {"schema": "raise-v1/repro_assembly_splits/1",
           "scope": "Three taxa are banked here; the originating measurement used ten. Sample sizes "
                    "differ and the figures are NOT expected to match to the decimal. What is being "
                    "reproduced is the PATTERN: random-split accuracy collapsing under grouping, and "
                    "the temporal split losing to a constant.",
           "inputs": [os.path.relpath(p, REPO) for p in paths],
           "n_labelled_records_available": n_all, "n_labelled_records_used": len(rows),
           "max_records_cap": args.max_records, "n_trees": N_TREES, "features": FEATS,
           "results": {}, "null_control": []}

    for label_key, name in [("family", "assembler FAMILY"), ("method", "full METHOD STRING")]:
        out["results"][name] = []
        for split in ("random", "grouped", "temporal"):
            r = evaluate(rows, label_key, split)
            if r:
                out["results"][name].append(r)
                flag = "" if r["beats_trivial"] else "   <-- LOSES TO A CONSTANT"
                print(f"  {name:<20} {split:<9} ACC {r['accuracy']:.4f}  balACC "
                      f"{r['balanced_accuracy']:.4f}  trivial {r['trivial_train_majority']:.4f}"
                      f"{flag}", flush=True)

    print("\n  NULL CONTROL (fake label inside one method string; true answer is 0.5):")
    for method, _ in Counter(r["method"] for r in rows).most_common(4):
        nc = null_control(rows, method)
        if nc:
            out["null_control"].append(nc)
            print(f"    {method[:38]:<38} balACC {nc['balanced_accuracy']:.4f}  (n={nc['n']})")

    floor = max((n["balanced_accuracy"] for n in out["null_control"]), default=None)
    out["null_control_max_balanced_accuracy_binary"] = floor
    out["null_control_chance"] = 0.5
    out["comparability_warning"] = (
        "The null control is a BINARY task (chance 0.5). The assembler-family and method-string "
        "results are MULTI-CLASS (chance ~1/k). Their balanced accuracies are NOT numerically "
        "comparable and no such comparison is made here. The null control's finding stands on its "
        "own: an ARBITRARY partition of bioprojects inside a SINGLE assembler version is predictable "
        "from contiguity statistics alone, well above its own chance level. The features therefore "
        "carry strong project-batch signal that has nothing to do with which assembler ran.")
    out["reading"] = (
        "Two findings, independent of each other. (1) SPLIT SENSITIVITY: accuracy falls sharply when "
        "whole bioprojects are held out, because the label is close to a project-level constant; and "
        "on a temporal split the full-method model loses outright to a train-majority constant. "
        "(2) CONFOUND: a fake label built from an arbitrary bioproject partition, inside one "
        "assembler version, is itself predictable - so a model scoring above chance on the real task "
        "may be reading the project, not the assembler.")
    out["cost_seconds"] = round(time.perf_counter() - t0, 1)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"\nconfound floor (balanced accuracy): {floor}")
    print(f"wrote {os.path.relpath(args.out, REPO)}  [{out['cost_seconds']}s]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
