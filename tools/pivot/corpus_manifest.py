#!/usr/bin/env python3
"""Bank content hashes of the manufactured corpora, so a stranger's rebuild can be PROVEN identical.

The corpora (5.4 GB and friends) are not committed; a cold clone re-manufactures them with the
shipped tools. Every "a stranger can re-derive it" claim therefore rests on the rebuild actually
matching ours - which until this manifest existed could not be checked, only assumed. Hashes cover
the ARRAY CONTENTS (X, y, g), not the .npz container, because the container embeds a build-time
field that legitimately differs between runs.

Re-verify after a rebuild:  python3 tools/pivot/corpus_manifest.py --check
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from npzmap import npz_memmap

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "artifacts", "pivot", "corpus_manifest.json")
CORPORA = ["data/pivot/full_c4096.npz", "data/pivot/carve_c1024.npz", "data/pivot/raw_c1024.npz"]

def digest(path):
    rec = {}
    for name in ("X", "y", "g"):
        try:
            arr = npz_memmap(path, name)
        except Exception:
            with np.load(path) as z:
                arr = np.asarray(z[name])
        h = hashlib.sha256()
        if arr.ndim == 1:
            h.update(np.ascontiguousarray(arr).tobytes())
        else:
            for i in range(0, len(arr), 20000):          # chunked so 5.7 GB never lands in RAM
                h.update(np.ascontiguousarray(arr[i:i+20000]).tobytes())
        rec[name] = {"sha256": h.hexdigest(), "shape": list(arr.shape), "dtype": str(arr.dtype)}
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        want = json.load(open(OUT, encoding="utf-8"))["corpora"]
        bad = 0
        for rel, rec in want.items():
            p = os.path.join(REPO, rel)
            if not os.path.exists(p):
                print(f"MISSING {rel} - rebuild it first"); bad += 1; continue
            got = digest(p)
            for name in rec:
                ok = got[name]["sha256"] == rec[name]["sha256"]
                print(f"{'ok  ' if ok else 'DIFF'} {rel}:{name}")
                bad += 0 if ok else 1
        print("MANIFEST CHECK:", "PASS - rebuild is byte-identical" if not bad else f"FAIL ({bad})")
        return 1 if bad else 0
    out = {"schema": "raise-v1/corpus_manifest/1",
           "why": __doc__.strip().split("\n\n")[1],
           "sources_sha256": {}, "corpora": {}}
    src = os.path.join(REPO, "data", "pivot", "src")
    for f in sorted(os.listdir(src)):
        out["sources_sha256"][f] = hashlib.sha256(open(os.path.join(src, f), "rb").read()).hexdigest()
    for rel in CORPORA:
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            print(f"skip {rel} (absent)"); continue
        out["corpora"][rel] = digest(p)
        print(f"hashed {rel}: X {out['corpora'][rel]['X']['sha256'][:16]}…")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
