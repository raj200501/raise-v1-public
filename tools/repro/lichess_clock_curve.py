#!/usr/bin/env python3
"""Round-4 PIPELINE VALIDATION - a real scaling curve on a candidate already known to be dead.

READ THIS FIRST. This is NOT a candidate selection and cannot become one. The domain it uses
(predicting a chess player's rating band from clock-time behaviour) FAILS gate G4: the task is
already occupied, including by work that uses clock times explicitly. Preregistration 0002
requires `g4_verdict == "PASS"`, so no number produced here can qualify a domain.

Why run it at all. Until now every part of the Phase 2 apparatus - the paired bootstrap, the
permutation test, the scope refusals in `tools/scaling.py` - had only ever been exercised on
SYNTHETIC data. An instrument that has only ever measured its own test fixtures has not been
shown to work. This runs the whole chain end to end on a real public corpus, and deliberately
does so on a domain where there is no incentive to flatter the result, because the result
cannot be used for anything.

Corpus: Lichess standard rated games, CC0 (https://database.lichess.org/). A prefix of one
monthly dump is streamed rather than downloaded whole.

Unit: one player-side of one game that carries clock annotations.
Label: rating band (Elo bucketed).
Features: derived from the CLOCK TRACE ONLY - never the moves, never either player's Elo.

Scope, stated before the numbers: games are taken from the START of one month's file, so they
are not a random sample of the month. One corpus, one month, one seed.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import sys
from collections import Counter

import numpy as np
import zstandard as zstd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLK = re.compile(r"\[%clk (\d+):(\d+):(\d+(?:\.\d+)?)\]")
TC = re.compile(r"^(\d+)\+(\d+)$")
BANDS = [(0, 1200), (1200, 1500), (1500, 1800), (1800, 2100), (2100, 9999)]


def band(elo: int) -> int:
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= elo < hi:
            return i
    return len(BANDS) - 1


def feats(secs, base: int, inc: int):
    """Everything here comes from the clock trace and the advertised time control. No moves."""
    if len(secs) < 8:
        return None
    s = np.asarray(secs, dtype=float)
    used = np.maximum(0.0, (s[:-1] + inc) - s[1:])
    if len(used) < 6:
        return None
    u = np.clip(used, 0, base + inc * len(used))
    n = len(u)
    third = max(1, n // 3)
    lo, hi = u[:third], u[-third:]
    with np.errstate(all="ignore"):
        trend = float(np.polyfit(np.arange(n), u, 1)[0]) if n > 2 and u.std() > 0 else 0.0
        ac1 = float(np.corrcoef(u[:-1], u[1:])[0, 1]) if n > 3 and u.std() > 0 else 0.0
    return [
        float(base), float(inc), float(n),
        float(u.mean()), float(u.std()), float(np.median(u)),
        float(np.percentile(u, 10)), float(np.percentile(u, 25)),
        float(np.percentile(u, 75)), float(np.percentile(u, 90)), float(u.max()),
        float(u[0]), float(u[1]) if n > 1 else 0.0, float(u[2]) if n > 2 else 0.0,
        float((u < 1.0).mean()), float((u < 0.5).mean()), float((u > 10.0).mean()),
        float(lo.mean()), float(hi.mean()), float(hi.mean() - lo.mean()),
        trend, ac1,
        float(u.sum()), float(u.sum() / max(base, 1)),
        float(s[-1]), float(s[-1] / max(base, 1)),
        float(np.mean(np.abs(np.diff(u)))) if n > 1 else 0.0,
        float(u.std() / (u.mean() + 1e-9)),
    ]


def extract(path: str, max_units: int):
    dctx = zstd.ZstdDecompressor()
    X, y = [], []
    hdr = {}
    truncated = False
    with open(path, "rb") as fh:
        try:
            with dctx.stream_reader(fh) as reader:
                text = io.TextIOWrapper(reader, encoding="utf-8", errors="ignore")
                for line in text:
                    if line.startswith("["):
                        sp = line.find(" ")
                        if sp > 0:
                            hdr[line[1:sp]] = line[line.find('"') + 1: line.rfind('"')]
                    elif line.startswith("1."):
                        clocks = [int(h) * 3600 + int(m) * 60 + float(sec)
                                  for h, m, sec in CLK.findall(line)]
                        tcm = TC.match(hdr.get("TimeControl", ""))
                        if clocks and tcm and len(clocks) >= 16:
                            base, inc = int(tcm.group(1)), int(tcm.group(2))
                            for side, key in ((0, "WhiteElo"), (1, "BlackElo")):
                                try:
                                    elo = int(hdr.get(key, ""))
                                except ValueError:
                                    continue
                                f = feats(clocks[side::2], base, inc)
                                if f is not None:
                                    X.append(f); y.append(band(elo))
                        hdr = {}
                        if len(y) >= max_units:
                            return X, y, truncated
        except Exception:  # noqa: BLE001 - the input is a deliberately truncated stream
            truncated = True
    return X, y, truncated


def entropy_bits(labels) -> float:
    c = Counter(labels); n = sum(c.values())
    return -sum((v / n) * math.log2(v / n) for v in c.values() if v)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chunk", default=os.path.join(REPO, "data", "work", "lichess_chunk.zst"))
    ap.add_argument("--max-units", type=int, default=400000)
    ap.add_argument("--rungs", type=int, nargs="*", default=[1000, 10000, 100000])
    ap.add_argument("--eval-size", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "phase0",
                                                  "round4_lichess_pipeline_validation.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "phase0",
                                                         "round4_lichess_rung_scores.json"))
    args = ap.parse_args()

    if not os.path.exists(args.chunk):
        print(f"missing input chunk: {args.chunk}\n  fix: stream one with\n"
              f"    curl -sS 'https://database.lichess.org/standard/"
              f"lichess_db_standard_rated_2017-04.pgn.zst' | head -c 700000000 > {args.chunk}",
              file=sys.stderr)
        return 2

    X, y, truncated = extract(args.chunk, args.max_units)
    print(f"extracted {len(y)} player-side units (input truncated: {truncated})", flush=True)
    X = np.nan_to_num(np.asarray(X, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    y = np.asarray(y)
    if len(y) < 5000:
        print("too few units extracted to proceed", file=sys.stderr)
        return 2

    rng = np.random.default_rng(args.seed)
    idx = rng.permutation(len(y))
    ev_n = min(args.eval_size, len(y) // 3)
    ev, tr_pool = idx[:ev_n], idx[ev_n:]
    Xe, ye = X[ev], y[ev]
    ent = entropy_bits(y.tolist())
    print(f"label entropy: {ent:.4f} bits over {len(set(y.tolist()))} bands", flush=True)

    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier

    base_tr = tr_pool[: min(len(tr_pool), 50000)]
    sc = StandardScaler().fit(X[base_tr])
    baselines = {}
    for nm, clf, scaled in [
        ("majority", DummyClassifier(strategy="most_frequent"), False),
        ("stratified", DummyClassifier(strategy="stratified", random_state=0), False),
        ("best_single_feat", DecisionTreeClassifier(max_depth=1, random_state=0), False),
        ("depth3_tree", DecisionTreeClassifier(max_depth=3, random_state=0), False),
        ("linear", LogisticRegression(max_iter=1500), True),
    ]:
        a, b = (sc.transform(X[base_tr]), sc.transform(Xe)) if scaled else (X[base_tr], Xe)
        clf.fit(a, y[base_tr])
        baselines[nm] = round(float(accuracy_score(ye, clf.predict(b))), 4)
        print(f"  baseline {nm:<18} {baselines[nm]:.4f}", flush=True)
    best_name = max(baselines, key=baselines.get)
    best_val = baselines[best_name]

    rungs, per_ex, skipped = [], [], []
    for r in args.rungs:
        if r > len(tr_pool):
            skipped.append(r)
            print(f"  rung {r}: SKIPPED, only {len(tr_pool)} training units available", flush=True)
            continue
        clf = HistGradientBoostingClassifier(max_iter=200, random_state=0).fit(
            X[tr_pool[:r]], y[tr_pool[:r]])
        correct = (clf.predict(Xe) == ye).astype(int)
        rungs.append({"n_units": int(r), "accuracy": round(float(correct.mean()), 4)})
        per_ex.append({"n_units": int(r), "per_example": correct.tolist()})
        print(f"  rung {r:>7}: accuracy {correct.mean():.4f}", flush=True)

    json.dump({"schema": "raise-v1/rung_scores/1",
               "metric": "accuracy on a shared held-out evaluation set",
               "rungs": per_ex}, open(args.scores_out, "w"))

    out = {
        "schema": "raise-v1/round4_pipeline_validation/1",
        "STATUS": "PIPELINE VALIDATION, NOT A CANDIDATE SELECTION",
        "why_this_cannot_select": (
            "The domain fails G4 - rating estimation from chess moves and clock times is already "
            "published, including a CNN-LSTM that uses clock times explicitly. Preregistration 0002 "
            "requires g4_verdict == PASS, so nothing here can qualify a domain."),
        "why_it_was_run": (
            "Every part of the Phase 2 apparatus had until now only ever been exercised on synthetic "
            "data. This runs the chain end to end on a real public corpus, on a domain where there is "
            "no incentive to flatter the result because the result cannot be used."),
        "corpus": {"source": "https://database.lichess.org/", "licence": "CC0",
                   "file": "lichess_db_standard_rated_2017-04.pgn.zst (streamed prefix)",
                   "input_truncated": truncated},
        "scope": "Games taken from the START of one month's file, so not a random sample of the "
                 "month. One corpus, one month, one seed.",
        "unit": "one player-side of one game carrying clock annotations",
        "label": f"rating band, {len(BANDS)} buckets: {BANDS}",
        "features": "clock trace only - never the moves, never either player's Elo",
        "n_units_extracted": int(len(y)), "eval_set_size": int(len(ye)),
        "rungs_skipped_for_lack_of_units": skipped,
        "a1_label_entropy_bits": round(ent, 4),
        "trivial_baselines": baselines,
        "best_baseline": {"name": best_name, "accuracy": best_val},
        "rungs": rungs,
    }
    if rungs:
        out["a2_margin_over_best_baseline"] = round(rungs[-1]["accuracy"] - best_val, 4)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"\nlabel entropy {ent:.4f} bits | best baseline {best_name} {best_val:.4f}")
    if rungs:
        print(f"top rung {rungs[-1]['accuracy']:.4f} | margin {out['a2_margin_over_best_baseline']:+.4f}")
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
