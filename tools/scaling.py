#!/usr/bin/env python3
"""Fit the scaling curve and put an honest interval around its slope.

The headline claim of this repository is a SLOPE: how much quality is bought per 10x of
manufactured data. A slope without an interval is a decoration, and with only four rungs the
interval cannot come from the four points alone. So:

  - every rung is evaluated on the SAME held-out evaluation set, example by example;
  - the interval comes from bootstrapping the EVALUATION EXAMPLES (paired across rungs, so
    the resampling respects that all rungs saw the same items), refitting the slope on each
    resample;

DEFECT, found by adversarial audit (2026-08-31) and filed in CORRECTIONS.md: resampling
EXAMPLES treats them as independent, but this repository's corpora carve 26 fragments from
each source chunk - fragments that share a plaintext and whose correctness indicators are
correlated (measured within-chunk correlation 0.140 at the top rung, vs 0.016 across chunk
boundaries). The grouped split itself declares the chunk to be the dependence unit, and this
fitter ignored that very unit, understating the headline 0003 interval by roughly half again
(the 0006 and 0007 intervals by less; every pair is banked side by side in
artifacts/pivot/audit_rederivations.json). Since 2026-09-02 this file performs the CLUSTER
bootstrap itself when a caller passes group labels (fit(groups=...)); a caller that has them
and does not pass them gets the fragment-level interval, which is ANTI-CONSERVATIVE whenever
the per-example data is clustered, which here is always, and must label it as such.
  - a separate exact permutation test over rung orderings gives a p-value whose granularity
    is stated rather than hidden (with R rungs there are R! orderings, so the smallest
    attainable p-value is 1/R!; with four rungs that is 1/24).

WHAT THE INTERVAL DOES NOT COVER, stated because the intervals come out tight enough to be
over-read. Bootstrapping the evaluation examples measures ONE source of uncertainty: how much the
slope would move if a different sample of evaluation items had been drawn from the same
distribution. It does NOT cover

  - seed variance          one seed is trained per rung; a re-run with another seed is not sampled
  - manufacture variance   one corpus is built; a differently drawn corpus is not sampled
  - model-class choice     one class is held fixed across rungs, by design, and not varied

So an interval like [0.0485, 0.0497] means "given this corpus, this seed and this model class, the
slope is pinned to about a thousandth by the evaluation set". It does not mean the slope of the
underlying phenomenon is known to a thousandth. A reader wanting that needs repeated seeds and
repeated corpora, neither of which this instrument has been run with.

Two fits are reported, and the preregistration names which one is primary:
  points_per_decade : mean score      regressed on log10(n_units)
  error_exponent    : log10(1 - score) regressed on log10(n_units)   [power law on error]

Refuses to report a curve that does not meet the study's own scope conditions: at least
four rungs spanning at least two orders of magnitude. Those refusals are exit code 3.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chainlib import REPO_ROOT, sha256_file  # noqa: E402

MIN_RUNGS = 4
MIN_DECADES = 2.0


def _ols(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Slope, intercept, r2 for a simple least-squares line."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    xm, ym = x.mean(), y.mean()
    sxx = float(((x - xm) ** 2).sum())
    if sxx == 0.0:
        return float("nan"), float("nan"), float("nan")
    slope = float(((x - xm) * (y - ym)).sum() / sxx)
    intercept = float(ym - slope * xm)
    resid = y - (slope * x + intercept)
    sst = float(((y - ym) ** 2).sum())
    r2 = float("nan") if sst == 0.0 else float(1.0 - (resid ** 2).sum() / sst)
    return slope, intercept, r2


def _error_transform(means: np.ndarray) -> np.ndarray:
    """log10(1 - score), with scores clipped away from 1 so the transform stays finite."""
    return np.log10(np.clip(1.0 - means, 1e-6, None))


SCOPE_REFUSAL = 3


def _refuse(msg: str):
    """Scope conditions are refusals, not warnings. Distinct exit code so CI can tell them apart."""
    print(f"scaling: REFUSED - {msg}", file=sys.stderr)
    raise SystemExit(SCOPE_REFUSAL)


def fit(rungs: list[dict], n_boot: int = 2000, seed: int = 0, groups=None) -> dict:
    """Slope of mean score on log10(n_units), with a paired bootstrap interval.

    groups: optional array of length eval_set_size giving each evaluation example's cluster id
    (here: its source chunk). When given, the bootstrap resamples CLUSTERS with replacement - the
    dependence unit the grouped split declares - and the interval is the cluster-level one the
    2026-08-31 audit called for. When omitted, the bootstrap resamples examples and the interval
    is fragment-level and ANTI-CONSERVATIVE under clustering (see the DEFECT note above); callers
    that bank a fragment-level interval must label it as such.
    """
    ns = np.array([r["n_units"] for r in rungs], dtype=float)
    order = np.argsort(ns)
    ns = ns[order]
    scores = [np.asarray(rungs[i]["per_example"], dtype=float) for i in order]
    names = [rungs[i].get("name", f"rung{int(ns[k])}") for k, i in enumerate(order)]

    n_eval = {len(s) for s in scores}
    if len(n_eval) != 1:
        _refuse(f"rungs were evaluated on different numbers of examples ({sorted(n_eval)}); "
                f"the paired bootstrap requires one shared evaluation set")
    m = n_eval.pop()
    if len(ns) < MIN_RUNGS:
        _refuse(f"{len(ns)} rung(s); the preregistered scope requires >= {MIN_RUNGS}")
    decades = float(math.log10(ns.max() / ns.min()))
    if decades < MIN_DECADES - 1e-9:
        _refuse(f"rungs span {decades:.3f} orders of magnitude; the preregistered scope "
                f"requires >= {MIN_DECADES}")

    logn = np.log10(ns)
    S = np.vstack(scores)                       # rungs x examples, paired
    means = S.mean(axis=1)

    ppd, ppd_b, ppd_r2 = _ols(logn, means)
    ee, ee_b, ee_r2 = _ols(logn, _error_transform(means))

    rng = np.random.default_rng(seed)
    boot_ppd = np.empty(n_boot)
    boot_ee = np.empty(n_boot)
    if groups is not None:
        g = np.asarray(groups)
        if len(g) != m:
            _refuse(f"groups has {len(g)} entries but the evaluation set has {m}")
        _, gi = np.unique(g, return_inverse=True)
        n_groups = int(gi.max()) + 1
        counts = np.bincount(gi, minlength=n_groups).astype(float)
        sums = np.vstack([np.bincount(gi, weights=S[r], minlength=n_groups)
                          for r in range(S.shape[0])])          # rungs x clusters
        for b in range(n_boot):
            idx = rng.integers(0, n_groups, size=n_groups)     # paired resample of CLUSTERS
            bm = sums[:, idx].sum(axis=1) / counts[idx].sum()
            boot_ppd[b] = _ols(logn, bm)[0]
            boot_ee[b] = _ols(logn, _error_transform(bm))[0]
        covers = (f"cluster bootstrap: {n_groups} evaluation clusters (source chunks) resampled "
                  f"with replacement, paired across rungs - the dependence unit the grouped split "
                  f"declares, per the 2026-08-31 correction")
    else:
        n_groups = None
        for b in range(n_boot):
            idx = rng.integers(0, m, size=m)         # paired resample: same items for every rung
            bm = S[:, idx].mean(axis=1)
            boot_ppd[b] = _ols(logn, bm)[0]
            boot_ee[b] = _ols(logn, _error_transform(bm))[0]
        covers = ("evaluation-example sampling only, treating examples as independent "
                  "- ANTI-CONSERVATIVE under the clustered eval sets this repository "
                  "uses; see the DEFECT note in this module and CORRECTIONS.md")

    def ci(a):
        return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))]

    ppd_ci, ee_ci = ci(boot_ppd), ci(boot_ee)

    perms = list(itertools.permutations(range(len(ns))))
    observed = ppd
    at_least = sum(1 for p in perms if _ols(logn, means[list(p)])[0] >= observed - 1e-12)
    p_perm = at_least / len(perms)

    return {
        "schema": "raise-v1/scaling_fit/1",
        "n_rungs": int(len(ns)),
        "orders_of_magnitude_spanned": round(decades, 4),
        "eval_set_size": int(m),
        "bootstrap_resamples": int(n_boot),
        "bootstrap_seed": int(seed),
        "bootstrap_unit": "cluster" if groups is not None else "example",
        "n_clusters": n_groups,
        "interval_covers": covers,
        "interval_does_not_cover": ("seed variance (one seed per rung), corpus-manufacture variance "
                                    "(one corpus), and model-class choice (one class held fixed by "
                                    "design). A tight interval here pins the slope GIVEN this "
                                    "corpus, seed and model class; it does not pin the slope of the "
                                    "underlying phenomenon."),
        "rungs": [{"name": names[i], "n_units": int(ns[i]), "mean_score": float(means[i])}
                  for i in range(len(ns))],
        "primary_fit": {
            "name": "points_per_decade",
            "definition": "mean score regressed on log10(n_units); units = score points per 10x data",
            "slope": float(ppd), "intercept": float(ppd_b), "r2": float(ppd_r2),
            "slope_ci95": ppd_ci,
            "slope_ci95_excludes_zero": bool(ppd_ci[0] > 0.0 or ppd_ci[1] < 0.0),
            "positive_slope_survives": bool(ppd_ci[0] > 0.0),
        },
        "secondary_fit": {
            "name": "error_exponent",
            "definition": "log10(1 - mean score) regressed on log10(n_units); more negative = faster error decay",
            "slope": float(ee), "intercept": float(ee_b), "r2": float(ee_r2),
            "slope_ci95": ee_ci,
            "negative_slope_survives": bool(ee_ci[1] < 0.0),
        },
        "permutation_test": {
            "definition": "exact test over all orderings of the rung means against log10(n_units)",
            "n_permutations": len(perms),
            "p_value": float(p_perm),
            "smallest_attainable_p": float(1.0 / len(perms)),
            "note": "with this many rungs the p-value is coarse; the bootstrap interval is the "
                    "primary evidence and the permutation test is a sanity check",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scores", help="JSON with {'rungs': [{'n_units': int, 'per_example': [...]}, ...]}")
    ap.add_argument("--out", help="write the fit artifact here")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    with open(args.scores, encoding="utf-8") as fh:
        payload = json.load(fh)
    # Score files written since the 2026-08-31 audit carry the evaluation rows' source-chunk ids;
    # when they are present the CLI fits the cluster interval, never the fragment-level one.
    groups = payload.get("eval_chunk_ids")
    result = fit(payload["rungs"], n_boot=args.boot, seed=args.seed, groups=groups)
    result["source_artifact"] = os.path.relpath(os.path.abspath(args.scores), REPO_ROOT)
    result["source_artifact_sha256"] = sha256_file(args.scores)
    for k in ("cost", "arms", "metric", "provenance"):
        if k in payload:
            result[k] = payload[k]

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {args.out}")
    p = result["primary_fit"]
    print(f"points_per_decade slope = {p['slope']:+.4f}  ci95 = [{p['slope_ci95'][0]:+.4f}, "
          f"{p['slope_ci95'][1]:+.4f}]  r2 = {p['r2']:.4f}")
    print(f"positive slope survives the interval: {p['positive_slope_survives']}")
    print(f"permutation p = {result['permutation_test']['p_value']:.4f} "
          f"(floor {result['permutation_test']['smallest_attainable_p']:.4f})")
    if not args.out:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
