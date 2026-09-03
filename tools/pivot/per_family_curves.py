#!/usr/bin/env python3
"""Per-family decomposition of a carve study from its banked per-example scores. Arithmetic only.

For each content family: accuracy at every rung, the slope with a CLUSTER bootstrap over that
family's held-out source chunks (tools/scaling.py fit(groups=...)), and - where the study banked
per-family baselines - the family's margin over its own best baseline, on both the frozen set and
the expanded set. No model is re-run and no new measurement is made; every number follows from
artifacts/pivot/carve_rung_scores_<size>.json and artifacts/pivot/carve_generalisation<_size>.json.

Why it exists: the headline of every carve study is a mixture over eight families, and the 2048
result misses its bar by 0.0025 on the frozen set. Whether that near-miss is spread evenly or is
a pass on structured content masked by incompressible content is a question the banked scores
already answer. It is a decomposition, not a preregistered clause: nothing here changes a verdict.

The family of an evaluation row is FAMILIES[chunk_id % len(FAMILIES)], exactly as the corpus
builder assigns it (tools/pivot/run_study.py build()).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
from corpus import FAMILIES  # noqa: E402
from scaling import fit  # noqa: E402

FROZEN_SET = ["majority", "stratified", "depth3_tree", "logistic"]
BAR = 0.05


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True, help="e.g. '2048-byte carve, preregistration 0011'")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260825)
    args = ap.parse_args()

    sc = json.load(open(args.scores, encoding="utf-8"))
    art = json.load(open(args.artifact, encoding="utf-8"))
    g = np.asarray(sc["eval_chunk_ids"])
    fam = np.array([FAMILIES[int(v) % len(FAMILIES)] for v in g])
    rungs = sorted(sc["rungs"], key=lambda r: r["n_units"])
    top = rungs[-1]["n_units"]
    S = {r["n_units"]: np.asarray(r["per_example"], dtype=float) for r in rungs}
    banked_top = art.get("within_per_family_top_rung") or {}
    banked_base = art.get("within_per_family_baselines") or {}

    out = {"schema": "raise-v1/per_family_curves/1", "study": args.label,
           "source_scores": os.path.relpath(args.scores, REPO),
           "source_artifact": os.path.relpath(args.artifact, REPO),
           "derivation": ("per-family accuracy per rung and per-family slope with a cluster bootstrap "
                          f"over that family's held-out source chunks ({args.boot} resamples, seed "
                          f"{args.seed}), all from the banked per-example scores; per-family margins "
                          "are the family's top-rung accuracy minus that family's best baseline as "
                          "banked by the measurement script. No model re-run. Cluster unit = source "
                          "chunk, per the 2026-08-31 correction."),
           "bar": BAR, "families": {}}
    mism = []
    for f in FAMILIES:
        m = fam == f
        acc = {str(n): round(float(S[n][m].mean()), 4) for n in S}
        r = fit([{"n_units": n, "per_example": S[n][m].tolist()} for n in S],
                n_boot=args.boot, seed=args.seed, groups=g[m])
        rec = {"n_eval": int(m.sum()), "n_chunks": int(np.unique(g[m]).size),
               "rung_accuracies": acc,
               "slope": round(r["primary_fit"]["slope"], 6),
               "slope_ci95": [round(x, 6) for x in r["primary_fit"]["slope_ci95"]],
               "ci_excludes_zero": bool(r["primary_fit"]["slope_ci95"][0] > 0)}
        if f in banked_top and abs(banked_top[f] - acc[str(top)]) > 1e-4:
            mism.append((f, banked_top[f], acc[str(top)]))
        if banked_base:
            per_b = {b: banked_base[b][f] for b in banked_base}
            frozen = {b: v for b, v in per_b.items() if b in FROZEN_SET}
            bf = max(frozen, key=frozen.get); be = max(per_b, key=per_b.get)
            rec["baselines"] = per_b
            rec["margin_frozen"] = {"value": round(acc[str(top)] - frozen[bf], 4), "baseline": bf,
                                    "baseline_accuracy": frozen[bf],
                                    "clears_bar": bool(round(acc[str(top)] - frozen[bf], 6) >= BAR - 1e-9)}
            rec["margin_expanded"] = {"value": round(acc[str(top)] - per_b[be], 4), "baseline": be,
                                      "baseline_accuracy": per_b[be],
                                      "clears_bar": bool(round(acc[str(top)] - per_b[be], 6) >= BAR - 1e-9)}
        out["families"][f] = rec
    if mism:
        print("MISMATCH against the artifact's banked per-family top-rung accuracies:", mism,
              file=sys.stderr)
        return 1
    # Subset mixtures: the question "is the miss carried by the incompressible families?" has a
    # banked answer only if the mixture EXCLUDING them is computed, weighted by evaluation rows,
    # with every baseline re-weighted the same way. Both readings, both subsets.
    if banked_base:
        subsets = {"without_base64_binary_mixed": [f for f in FAMILIES if f not in ("base64", "binary", "mixed")],
                   "structured_only_csv_log_json_code": ["code", "csv", "json", "log"]}
        out["subsets"] = {}
        for name, fams in subsets.items():
            m = np.isin(fam, fams)
            acc = round(float(S[top][m].mean()), 4)
            base_acc = {b: round(sum(banked_base[b][f] * int((fam == f).sum()) for f in fams)
                                 / int(m.sum()), 4) for b in banked_base}
            frozen = {b: v for b, v in base_acc.items() if b in FROZEN_SET}
            bf = max(frozen, key=frozen.get); be = max(base_acc, key=base_acc.get)
            out["subsets"][name] = {
                "families": fams, "n_eval": int(m.sum()), "top_rung_accuracy": acc,
                "baselines": base_acc,
                "margin_frozen": {"value": round(acc - frozen[bf], 4), "baseline": bf,
                                  "clears_bar": bool(round(acc - frozen[bf], 6) >= BAR - 1e-9)},
                "margin_expanded": {"value": round(acc - base_acc[be], 4), "baseline": be,
                                    "clears_bar": bool(round(acc - base_acc[be], 6) >= BAR - 1e-9)}}
            print(f"  subset {name:<36} top {acc:.4f}  frozen {out['subsets'][name]['margin_frozen']['value']:+.4f} "
                  f"({bf})  expanded {out['subsets'][name]['margin_expanded']['value']:+.4f} ({be})")
    out["consistency"] = ("per-family top-rung accuracies re-derived here equal the measurement "
                          "script's banked within_per_family_top_rung to 4 decimals")
    if banked_base:
        out["families_clearing_bar_frozen"] = [f for f in FAMILIES if out["families"][f]["margin_frozen"]["clears_bar"]]
        out["families_clearing_bar_expanded"] = [f for f in FAMILIES if out["families"][f]["margin_expanded"]["clears_bar"]]
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
    for f in sorted(FAMILIES, key=lambda x: -out["families"][x]["slope"]):
        rec = out["families"][f]
        line = (f"  {f:<10} top {rec['rung_accuracies'][str(top)]:.4f}  slope {rec['slope']:+.4f} "
                f"[{rec['slope_ci95'][0]:+.4f}, {rec['slope_ci95'][1]:+.4f}]")
        if "margin_frozen" in rec:
            line += (f"  margin frozen {rec['margin_frozen']['value']:+.4f} ({rec['margin_frozen']['baseline']})"
                     f"  expanded {rec['margin_expanded']['value']:+.4f} ({rec['margin_expanded']['baseline']})")
        print(line)
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
