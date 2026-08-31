#!/usr/bin/env python3
"""Reproduction: the ACS PUMS allocation-flag leak.

Round 2 of domain selection nominated "recover the census imputation mask from released microdata"
as its strongest candidate, on the claim that the manufacturer's information — which questionnaire
boxes the respondent left blank — is destroyed by federal law and never released. An adversarial
review then killed it by showing that claim is false for ten of the input columns.

This re-derives the decisive part from the public corpus, from scratch:
  1. ACS never imputes ancestry, so FANCP fires on zero records;
  2. therefore ANC=4 ".Not reported" is published verbatim inside the student's own input;
  3. and because item nonresponse clusters within a respondent, that single published code predicts
     the allocation of OTHER items with a ONE-LINE rule and zero training records.

Downloads ~70 MB. Run:  python3 tools/repro/census_leak_check.py
Writes artifacts/phase0/reproduction_alloctrace.json (the `reproduced` block).
"""
from __future__ import annotations

import argparse
import csv
import collections
import io
import json
import os
import sys
import urllib.request
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL = "https://www2.census.gov/programs-surveys/acs/data/pums/2023/1-Year/csv_pca.zip"
MEMBER = "psam_p06.csv"
TARGETS = ["FPINCP", "FWAGP", "FHICOVP", "FSCHLP", "FESRP", "FMARP"]
NOT_FLAGS = {"FER", "FOD1P", "FOD2P"}   # F-prefixed columns that are data, not allocation flags


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", default=os.path.join(REPO, "data", "work", "csv_pca.zip"))
    ap.add_argument("--keep", action="store_true", help="keep the 70 MB download")
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "phase0", "repro_census_leak.json"))
    args = ap.parse_args()

    if not os.path.exists(args.zip):
        os.makedirs(os.path.dirname(args.zip), exist_ok=True)
        print(f"downloading {URL} ...")
        req = urllib.request.Request(URL, headers={"User-Agent": "raise-v1-repro/1.0"})
        with urllib.request.urlopen(req, timeout=900) as r, open(args.zip, "wb") as fh:
            fh.write(r.read())
    size = os.path.getsize(args.zip)
    print(f"archive bytes: {size}")

    z = zipfile.ZipFile(args.zip)
    rd = csv.reader(io.TextIOWrapper(z.open(MEMBER), encoding="utf-8"))
    hdr = next(rd)
    idx = {c: i for i, c in enumerate(hdr)}
    fcols = [c for c in hdr if c.startswith("F")]
    flags = [c for c in fcols if c not in NOT_FLAGS]

    n = 0
    anc = collections.Counter()
    fancp = collections.Counter()
    joint = {t: collections.Counter() for t in TARGETS}
    for row in rd:
        n += 1
        a = row[idx["ANC"]].strip()
        anc[a] += 1
        fancp[row[idx["FANCP"]].strip()] += 1
        fires = 1 if a == "4" else 0
        for t in TARGETS:
            joint[t][(fires, row[idx[t]].strip())] += 1

    per_flag = {}
    for t in TARGETS:
        c = joint[t]
        tp, fp, fn, tn = c[(1, "1")], c[(1, "0")], c[(0, "1")], c[(0, "0")]
        tpr = tp / (tp + fn) if (tp + fn) else float("nan")
        fpr = fp / (fp + tn) if (fp + tn) else float("nan")
        per_flag[t] = {"auc_binary_rule": round(0.5 * (1 + tpr - fpr), 4),
                       "p_rule_given_allocated": round(tpr, 4),
                       "p_rule_given_not_allocated": round(fpr, 4),
                       "base_rate_allocated": round((tp + fn) / n, 4)}
    mean_auc = round(sum(v["auc_binary_rule"] for v in per_flag.values()) / len(per_flag), 4)

    res = {
        "schema": "raise-v1/repro_census_leak/1",
        "corpus": {"url": URL, "member": MEMBER, "archive_bytes": size,
                   "licence": "US Census Bureau public-use microdata; US federal government work"},
        "n_records": n, "n_columns": len(hdr),
        "columns_starting_with_F": len(fcols),
        "allocation_flag_columns": len(flags),
        "allocation_flag_derivation": f"{len(fcols)} F-prefixed columns minus "
                                      f"{sorted(NOT_FLAGS)}, which are data variables, = {len(flags)}",
        "anc_distribution": dict(anc), "fancp_distribution": dict(fancp),
        "fancp_ever_fires": any(k != "0" and v for k, v in fancp.items()),
        "one_line_rule": "ANC == 4  (.Not reported)",
        "training_rows_required": 0,
        "per_flag": per_flag, "mean_auc_six_flags": mean_auc,
        "reading": "FANCP never fires, so ACS publishes the respondent's ancestry nonresponse "
                   "verbatim. A single equality test on that published code, with no training at "
                   "all, predicts the allocation of unrelated items at the AUCs above.",
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
        fh.write("\n")
    for t, v in per_flag.items():
        print(f"  {t:<9} AUC={v['auc_binary_rule']:.4f}  base_rate={v['base_rate_allocated']:.4f}")
    print(f"\nrecords={n}  columns={len(hdr)}  allocation flags={len(flags)}")
    print(f"FANCP distribution: {dict(fancp)}")
    print(f"mean AUC over {len(TARGETS)} flags, zero training rows: {mean_auc}")
    print(f"wrote {os.path.relpath(args.out, REPO)}")
    if not args.keep and os.path.exists(args.zip):
        os.remove(args.zip)
        print("removed the download (pass --keep to retain it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
