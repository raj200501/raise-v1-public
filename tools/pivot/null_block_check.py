#!/usr/bin/env python3
"""Recompute a preregistration's null-control row block from the cache's y and g arrays alone, with the runner's own
split, and compare it with the sealed literal and (when given) the banked artifact. Added 2026-09-10 after 0018's frozen
reader voided an honest run on a null-block hash restated from 0017: the pre-freeze check had compared the reader's
copy of the literal to the preregistration's copy, and two copies of the same wrong literal agree with each other
(docs/OPERATING_RULES.md, section 4; CORRECTIONS.md 2026-09-10).

Usage: null_block_check.py --cache data/pivot/full_c4096.npz --sealed <sha256> [--artifact artifacts/pivot/X.json]
       [--seed 20260825] [--eval-frac 0.2] [--cap 800000] [--rows 20000] [--block pool|fold0]
Prints both blocks (the first `rows` pool rows, and the first `rows` training rows of the first leave-one-family-out
fold, gutenberg withheld) and exits 0 only if the sealed literal equals the named block and, when an artifact is given,
its partition.null_sorted_sha256 and fits.null.fit_rows_sorted_sha256 equal it too. Reads only y and g; never X."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import zipfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
from run_carve import grouped_split  # noqa: E402

FAMILIES = ["gutenberg", "base64", "binary", "code", "csv", "json", "log", "mixed"]


def sha(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True); ap.add_argument("--sealed", required=True); ap.add_argument("--artifact")
    ap.add_argument("--seed", type=int, default=20260825); ap.add_argument("--eval-frac", type=float, default=0.2)
    ap.add_argument("--cap", type=int, default=800000); ap.add_argument("--rows", type=int, default=20000)
    ap.add_argument("--block", choices=["pool", "fold0"], default="pool")
    a = ap.parse_args()
    zf = zipfile.ZipFile(a.cache)
    y = np.load(io.BytesIO(zf.read("y.npy"))); g = np.load(io.BytesIO(zf.read("g.npy")))
    ev, tr, _ = grouped_split(y, g, a.seed, a.eval_frac, a.cap)
    fam = np.asarray(FAMILIES)[g % 8]
    blocks = {"pool": sha(np.sort(tr[: a.rows]).astype(np.int64)),
              "fold0": sha(np.sort(tr[fam[tr] != FAMILIES[0]][: a.rows]).astype(np.int64))}
    print(f"pool_idx_sha256                 {sha(tr)}")
    print(f"eval_idx_sha256                 {sha(ev)}")
    print(f"first {a.rows} pool rows (sorted)     {blocks['pool']}")
    print(f"first fold's first {a.rows} rows     {blocks['fold0']}   (fold 0 = {FAMILIES[0]} withheld)")
    print(f"sealed literal                  {a.sealed}   named block: {a.block}")
    ok = blocks[a.block] == a.sealed
    if a.artifact:
        d = json.load(open(a.artifact, encoding="utf-8"))
        part = (d.get("partition") or {}).get("null_sorted_sha256")
        fit = ((d.get("fits") or {}).get("null") or d.get("null_control") or {}).get("fit_rows_sorted_sha256")
        print(f"artifact partition.null         {part}\nartifact null fit rows          {fit}")
        ok = ok and part == a.sealed and fit == a.sealed
    print("NULL BLOCK CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
