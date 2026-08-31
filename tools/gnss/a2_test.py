#!/usr/bin/env python3
"""The EphemErr A2 test, governed by frozen preregistration 0005.

Question: does a learned model beat the dumbest available rule at predicting when a GPS broadcast
ephemeris will be badly wrong?

Receiver emulation. At epoch t the record used is the most recent one whose TRANSMISSION TIME
precedes t - what a receiver actually holds. Pipeline validation used closest-toe selection, which
pinned age-of-data near zero and made its effect unobservable; that reading was recorded as COULD
NOT VERIFY and this fixes it.

Everything the student sees comes from the broadcast record. The label comes from precise products
reconstructed days later from a ~500-station network the receiver has no access to.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ephem import C, parse_clk, parse_nav, parse_sp3, propagate, rac_error  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FEATS = ["ura", "e", "sqrt_a", "delta_n", "idot", "omega_dot", "i0",
         "cuc", "cus", "crc", "crs", "cic", "cis",
         "af0", "af1", "af2", "tgd", "iode", "fit",
         "age_s", "abs_af1", "abs_af2", "prn"]


def day_rows(doy: str, data_dir: str):
    b = os.path.join(data_dir, f"brdc_{doy}.rnx.gz")
    s = os.path.join(data_dir, f"sp3_{doy}.SP3.gz")
    c = os.path.join(data_dir, f"clk_{doy}.CLK.gz")
    if not all(os.path.exists(p) and os.path.getsize(p) > 1000 for p in (b, s, c)):
        return []
    try:
        nav, sp3, clk = parse_nav(b), parse_sp3(s), parse_clk(c)
    except Exception:  # noqa: BLE001
        return []
    byprn = defaultdict(list)
    for r in nav:
        byprn[r["prn"]].append(r)
    for k in byprn:
        byprn[k].sort(key=lambda r: r["ttm"])
    out = []
    for (prn, sow), (px, py, pz, _) in sp3.items():
        if (prn, sow) not in clk:
            continue
        # RECEIVER EMULATION: the most recent record TRANSMITTED BEFORE this epoch.
        avail = [r for r in byprn.get(prn, []) if r["ttm"] <= sow and (sow - r["ttm"]) <= 4 * 3600]
        if not avail:
            continue
        r = avail[-1]
        if r["health"] != 0:
            continue
        p0 = propagate(r, sow)
        p1 = propagate(r, sow + 1.0)
        if p0 is None or p1 is None:
            continue
        bx, by, bz, dtsv = p0
        rac = rac_error(bx, by, bz, px, py, pz, (p1[0] - bx, p1[1] - by, p1[2] - bz))
        if rac is None:
            continue
        f = {k: float(r.get(k, 0.0)) for k in FEATS if k in r}
        f.update({"age_s": float(sow - r["ttm"]), "abs_af1": abs(r["af1"]),
                  "abs_af2": abs(r["af2"]), "prn": float(prn)})
        out.append((int(doy), prn, sow, rac[0], rac[1], rac[2],
                    (dtsv - clk[(prn, sow)]) * C, [f.get(k, 0.0) for k in FEATS]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(REPO, "data", "gnss"))
    ap.add_argument("--train-frac-days", type=float, default=0.7)
    ap.add_argument("--quantile", type=float, default=0.90)
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "ephemerr", "a2_result.json"))
    args = ap.parse_args()

    t0 = time.perf_counter()
    days = sorted({os.path.basename(p)[5:8] for p in glob.glob(os.path.join(args.data, "brdc_*.rnx.gz"))})
    rows = []
    for d in days:
        r = day_rows(d, args.data)
        rows += r
        print(f"  day {d}: {len(r)} epochs", flush=True)
    if not rows:
        print("no data", file=sys.stderr)
        return 2

    doy = np.array([r[0] for r in rows])
    prn = np.array([r[1] for r in rows])
    rac = np.array([[r[3], r[4], r[5]] for r in rows])
    clk = np.array([r[6] for r in rows])
    X = np.array([r[7] for r in rows], dtype=np.float64)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    udays = sorted(set(doy.tolist()))
    ntr = max(1, int(round(len(udays) * args.train_frac_days)))
    train_days, test_days = set(udays[:ntr]), set(udays[ntr:])
    istr = np.isin(doy, list(train_days))
    iste = np.isin(doy, list(test_days))
    print(f"\ntemporal split: train days {sorted(train_days)} ({istr.sum()} epochs), "
          f"test days {sorted(test_days)} ({iste.sum()} epochs)", flush=True)

    # per-satellite clock bias is unobservable to a receiver; estimate it on TRAIN DAYS ONLY
    cc = clk.copy()
    for p in np.unique(prn):
        m = prn == p
        b = np.median(cc[m & istr]) if (m & istr).any() else np.median(cc[m])
        cc[m] -= b
    sis = np.sqrt((0.98 * rac[:, 0] - cc) ** 2 + (rac[:, 1] ** 2 + rac[:, 2] ** 2) / 49.0)

    thr = float(np.quantile(sis[istr], args.quantile))          # threshold from TRAIN only
    ylab = (sis > thr).astype(int)
    print(f"threshold = {args.quantile:.2f} quantile of train SISRE = {thr:.3f} m   "
          f"positive rate: train {ylab[istr].mean():.4f}  test {ylab[iste].mean():.4f}", flush=True)

    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    yte = ylab[iste]

    # ---- FROZEN baseline set (preregistration 0005) -----------------------------------------
    base = {}
    base["global_mean"] = np.full(iste.sum(), 0.5)
    persat = {}
    for p in np.unique(prn):
        m = (prn == p) & istr
        persat[p] = float(np.mean(sis[m])) if m.any() else float(np.mean(sis[istr]))
    base["per_satellite_mean"] = np.array([persat[p] for p in prn[iste]])
    iu = FEATS.index("ura")
    base["ura_index_alone"] = X[iste, iu]
    age = X[:, FEATS.index("age_s")]
    amax = max(age[istr].max(), 1.0)
    base["per_satellite_mean_plus_age"] = base["per_satellite_mean"] * (1.0 + age[iste] / amax)

    print("\nFROZEN baselines (AUC on the temporal test split):", flush=True)
    baucs = {}
    for k, v in base.items():
        try:
            baucs[k] = round(float(roc_auc_score(yte, v)), 4)
        except ValueError:
            baucs[k] = 0.5
        print(f"  {k:<32} {baucs[k]:.4f}", flush=True)
    best_name = max(baucs, key=baucs.get)
    best_auc = baucs[best_name]

    # ---- learned -----------------------------------------------------------------------------
    t = time.perf_counter()
    clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, max_leaf_nodes=31,
                                         early_stopping=True, n_iter_no_change=15,
                                         random_state=args.seed).fit(X[istr], ylab[istr])
    learned = round(float(roc_auc_score(yte, clf.predict_proba(X[iste])[:, 1])), 4)
    tsec = round(time.perf_counter() - t, 1)
    print(f"\nlearned (HGB on broadcast fields only)   {learned:.4f}   ({tsec}s)", flush=True)

    rng = np.random.default_rng(args.seed)
    ysh = ylab[istr].copy()
    rng.shuffle(ysh)
    clf0 = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, max_leaf_nodes=31,
                                          early_stopping=True, n_iter_no_change=15,
                                          random_state=args.seed).fit(X[istr], ysh)
    null = round(float(roc_auc_score(yte, clf0.predict_proba(X[iste])[:, 1])), 4)
    print(f"null control (labels shuffled)           {null:.4f}", flush=True)

    res = {
        "schema": "raise-v1/ephemerr_a2_result/1",
        "preregistration": "0005-ephemerr-a2",
        "task": "predict whether a GPS broadcast ephemeris record's SISRE will exceed the "
                f"{args.quantile:.2f} quantile at a future epoch, from the broadcast record alone",
        "receiver_emulation": "the record used at epoch t is the most recent one TRANSMITTED before "
                              "t, within a 4-hour cutoff",
        "days": sorted(udays), "train_days": sorted(train_days), "test_days": sorted(test_days),
        "split_is_temporal": True,
        "n_epochs_total": int(len(sis)), "n_train_epochs": int(istr.sum()),
        "n_test_epochs": int(iste.sum()), "n_satellites": int(len(np.unique(prn))),
        "threshold_metres": round(thr, 4), "quantile": args.quantile,
        "positive_rate": round(float(yte.mean()), 4),
        "features": FEATS, "seed": args.seed,
        "baseline_aucs": baucs, "best_baseline_name": best_name, "best_baseline_auc": best_auc,
        "learned_auc": learned, "shuffled_label_auc": null,
        "margin_over_best_baseline": round(learned - best_auc, 4),
        "sisre_summary": {"train_median": round(float(np.median(sis[istr])), 4),
                          "test_median": round(float(np.median(sis[iste])), 4),
                          "train_rms": round(float(np.sqrt((sis[istr] ** 2).mean())), 4)},
        "cost": {"total_seconds": round(time.perf_counter() - t0, 1),
                 "learned_fit_seconds": tsec, "cpu_cores": 4, "gpu": "none"},
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"\nbest frozen baseline: {best_name} {best_auc:.4f}")
    print(f"margin: {learned:.4f} - {best_auc:.4f} = {learned-best_auc:+.4f}  (prereg needs >= 0.05)")
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
