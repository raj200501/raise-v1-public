#!/usr/bin/env python3
"""Real-content FIT corpus: the chunks of preregistration 0018's pinned real files that its sealed
evaluation corpus does not use (preregistration 0020).

0018/0019 read `OOB_TRANSFER_FAILS`: 0014's searched model, fitted on the corpus builder's eight
generated families, identifies the encoder on five pinned real-file families at 0.0637 against a
0.088462 bar. That says nothing about whether real content carries the encoder signal at all - the
model had never seen a real file. This corpus is the training half that answers it: the SAME five
pinned files, cut into the SAME consecutive non-overlapping 32768-byte chunks, with the chunks the
sealed corpus uses removed. Sealed evaluation chunks and fit chunks therefore share no byte.

    sealed (0018):  a seeded sample of 300 chunk indices per real family   -> data/pivot/ext_c4096.npz
    fit    (0020):  every remaining chunk index, in blob order             -> data/pivot/realfit_c4096.npz

The label factory is imported from tools/pivot/corpus_ext.py, which imports it from tools/pivot/corpus.py:
the same 26 (implementation, level) configurations, the same mid-stream 4096-byte carve, the same 1108
features. Nothing here is generated and nothing here is synthetic; the three synthetic families of 0018
are not built, because the question is about real content.

Chunk ids live in their own space (20000000 + family stride + k), disjoint from the builder's (0..49999)
and from the sealed extension corpus's (10000000+), so a shared id is impossible rather than unlikely.

    python3 tools/pivot/corpus_realfit.py --build     # data/pivot/realfit_c4096.npz + artifacts/pivot/realfit_corpus_manifest.json
    python3 tools/pivot/corpus_realfit.py --check     # array hashes of the npz against the banked manifest
    python3 tools/pivot/corpus_realfit.py --disjoint  # prove fit and sealed chunks share no blob chunk and no id
    python3 tools/pivot/corpus_realfit.py --probe     # determinism: a small slice built twice, in two task orders
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corpus_ext as ce  # noqa: E402  (the label factory, the pinned blobs and the sealed selection)
from corpus import CONFIG_NAMES, N_CONFIGS  # noqa: E402
from features import N_FEATURES, features_many  # noqa: E402

REPO = ce.REPO
NPZ_PATH = os.path.join(REPO, "data", "pivot", "realfit_c4096.npz")
MANIFEST_PATH = os.path.join(REPO, "artifacts", "pivot", "realfit_corpus_manifest.json")
FAMILIES = ce.REAL_FAMILIES                      # ["c_src", "pe_bin", "py_src", "rfc_txt", "rst_doc"], 0018's order
CHUNK_ID_BASE = 20_000_000
FAMILY_STRIDE = ce.FAMILY_STRIDE
SEALED = {"n_per_family": 300, "seed": 20260909}  # what 0018 sealed; read back from its manifest by --build


def chunk_id(fam_index: int, k: int) -> int:
    return CHUNK_ID_BASE + fam_index * FAMILY_STRIDE + k


def sealed_selection(blobs, chunk_size):
    """0018's selection, recomputed from its own code and its sealed parameters."""
    return ce.real_selection(blobs, SEALED["n_per_family"], chunk_size, SEALED["seed"])


def _chunk_sha(blob, i, chunk_size):
    return hashlib.sha256(blob[i * chunk_size:(i + 1) * chunk_size]).hexdigest()


def fit_selection(blobs, chunk_size):
    """Every whole chunk of each pinned real blob that 0018's selection does not use, in blob order, MINUS any chunk
    whose bytes are not unique to it.

    Disjoint indices are not enough. A blob can hold the same 32768 bytes at two offsets - a run of zero padding in
    the PE family, a repeated licence header - so a fit chunk can be byte-identical to a sealed evaluation chunk
    even though their indices differ, and fitting on it would be fitting on evaluation rows. Every candidate chunk
    is hashed: one that matches ANY sealed chunk of ANY family is dropped, and a duplicate inside the fit selection
    itself keeps only its first occurrence. The dropped indices are banked in the manifest.
    """
    sealed = sealed_selection(blobs, chunk_size)
    sealed_hashes = {_chunk_sha(blobs[f], i, chunk_size) for f in FAMILIES for i in sealed[f]}
    sel, dropped = {}, {}
    seen = set()
    for f in FAMILIES:
        n_avail = len(blobs[f]) // chunk_size
        used = set(sealed[f])
        keep, drop_sealed, drop_dup = [], [], []
        for i in range(n_avail):
            if i in used:
                continue
            h = _chunk_sha(blobs[f], i, chunk_size)
            if h in sealed_hashes:
                drop_sealed.append(i)
            elif h in seen:
                drop_dup.append(i)
            else:
                seen.add(h); keep.append(i)
        sel[f] = keep
        dropped[f] = {"byte_identical_to_a_sealed_chunk": drop_sealed, "duplicate_within_the_fit_selection": drop_dup}
        assert not (set(keep) & used), f"{f}: fit and sealed selections overlap"
    return sel, sealed, dropped


_BLOBS = None
_SEL = None


def _init(src_dir, chunk_size):
    global _BLOBS, _SEL
    _BLOBS = ce.load_real_blobs(src_dir)
    _SEL, _, _ = fit_selection(_BLOBS, chunk_size)


def _one(args):
    family, k, chunk_size, carve_len = args
    frags, labels, n_streams, n_carved, src_sha = ce.chunk_rows(family, k, chunk_size, carve_len, _BLOBS, _SEL)
    fi = FAMILIES.index(family)
    meta = (chunk_id(fi, k), fi, k, _SEL[family][k], n_streams, n_carved, src_sha)
    if not frags:
        return np.empty((0, N_FEATURES), np.float32), np.empty(0, np.int16), meta
    return features_many(frags), np.asarray(labels, np.int16), meta


def build(chunk_size, carve_len, procs, src_dir=ce.SRC_DIR, order_seed=None, cap_per_family=None):
    blobs = ce.load_real_blobs(src_dir)
    sel, sealed, dropped = fit_selection(blobs, chunk_size)
    counts = {f: (len(sel[f]) if cap_per_family is None else min(cap_per_family, len(sel[f]))) for f in FAMILIES}
    tasks = [(f, k, chunk_size, carve_len) for f in FAMILIES for k in range(counts[f])]
    if order_seed is not None:   # the probe shuffles the task order: the corpus must not depend on it
        random.Random(order_seed).shuffle(tasks)
    cap = len(tasks) * N_CONFIGS
    X = np.empty((cap, N_FEATURES), np.float32); Y = np.empty(cap, np.int16)
    G = np.empty(cap, np.int32); F = np.empty(cap, np.int8)
    metas = []; n = 0; t0 = time.perf_counter()
    with Pool(procs, initializer=_init, initargs=(src_dir, chunk_size)) as pool:
        for j, (x, y, meta) in enumerate(pool.imap_unordered(_one, tasks, chunksize=4), 1):
            m = len(y)
            if m:
                X[n:n + m] = x; Y[n:n + m] = y; G[n:n + m] = meta[0]; F[n:n + m] = meta[1]; n += m
            metas.append(meta)
            if j % 200 == 0:
                print(f"    {j}/{len(tasks)} chunks, {n} rows, {time.perf_counter() - t0:.0f}s", flush=True)
    order = np.lexsort((Y[:n], G[:n]))      # canonical row order: chunk id then label
    X, Y, G, F = X[:n][order], Y[:n][order], G[:n][order], F[:n][order]
    metas.sort()
    meta_arr = {"chunk_ids": np.array([m[0] for m in metas], np.int32),
                "chunk_fam": np.array([m[1] for m in metas], np.int8),
                "chunk_k": np.array([m[2] for m in metas], np.int32),
                "blob_chunk_index": np.array([m[3] for m in metas], np.int32),
                "distinct_streams": np.array([m[4] for m in metas], np.int8),
                "distinct_fragments": np.array([m[5] for m in metas], np.int8),
                "src_sha256": np.array([m[6] for m in metas])}
    return X, Y, G, F, meta_arr, sel, sealed, dropped, counts, round(time.perf_counter() - t0, 1)


def manifest_of(X, Y, G, F, meta, sel, sealed, dropped, counts, chunk_size, carve_len, build_s, pins, blobs):
    ids_with_rows, first_pos, rows_per_chunk = np.unique(G, return_index=True, return_counts=True)
    order = np.argsort(first_pos); ids_with_rows = ids_with_rows[order]; rows_per_chunk = rows_per_chunk[order]
    without = sorted(set(int(c) for c in meta["chunk_ids"]) - set(int(c) for c in ids_with_rows))
    per_family = {}
    for fi, f in enumerate(FAMILIES):
        m = F == fi; cm = meta["chunk_fam"] == fi
        per_family[f] = {"n_rows": int(m.sum()), "n_chunks": int(cm.sum()),
                         "n_chunks_with_rows": int(np.unique(G[m]).size),
                         "n_chunks_sealed_for_evaluation": len(sealed[f]),
                         # The blob's whole-chunk count, measured from the blob. It is NOT fit+sealed: the two
                         # byte-identity drops sit in neither set, which made pe_bin read 507 against 509 whole
                         # chunks under the previous derivation (0020 pre-freeze review, corpus lens, finding 4).
                         "n_chunks_in_blob": len(blobs[f]) // chunk_size,
                         "n_chunks_fit_plus_sealed": len(sel[f]) + len(sealed[f]),
                         "share_of_fit_rows": round(float(m.sum() / max(len(Y), 1)), 4),
                         "rows_per_chunk_mean": round(float(m.sum() / max(cm.sum(), 1)), 4),
                         "ceiling_distinct_streams": round(float(meta["distinct_streams"][cm].mean() / N_CONFIGS), 4),
                         "ceiling_distinct_fragments": round(float(meta["distinct_fragments"][cm].mean() / N_CONFIGS), 4),
                         "fit_blob_chunk_index_sha256": hashlib.sha256(json.dumps(sel[f][:counts[f]]).encode()).hexdigest(),
                         "sealed_blob_chunk_index_sha256": hashlib.sha256(json.dumps(sealed[f]).encode()).hexdigest()}
    return {"schema": "raise-v1/realfit_corpus_manifest/1",
            "why": "content hashes of the real-content FIT corpus (preregistration 0020) and what it is disjoint from; a "
                   "rebuild is proven identical by `python3 tools/pivot/corpus_realfit.py --check` and the disjointness "
                   "from 0018's sealed evaluation corpus by `--disjoint`",
            "npz": os.path.relpath(NPZ_PATH, REPO), "families": FAMILIES, "kind": "real content only, no generated families",
            "selection_rule": "every whole 32768-byte chunk of each pinned blob that 0018's sealed selection "
                              f"(n_per_family {SEALED['n_per_family']}, seed {SEALED['seed']}, recomputed here from "
                              "tools/pivot/corpus_ext.py) does not use, in blob order, minus every chunk whose bytes "
                              "hash to a sealed chunk's or to an earlier fit chunk's; no seed of its own",
            "chunks_dropped_for_byte_identity": {f: dropped[f] for f in FAMILIES},
            "n_chunks_dropped": {f: len(dropped[f]["byte_identical_to_a_sealed_chunk"]) +
                                 len(dropped[f]["duplicate_within_the_fit_selection"]) for f in FAMILIES},
            "chunk_size": chunk_size, "carve": carve_len, "chunk_id_base": CHUNK_ID_BASE, "family_stride": FAMILY_STRIDE,
            "n_rows": int(len(Y)), "n_chunks": int(len(meta["chunk_ids"])), "n_chunks_with_rows": int(len(ids_with_rows)),
            "chunks_without_rows": without, "n_chunks_per_family": {f: counts[f] for f in FAMILIES},
            "chunk_ids_with_rows": [int(c) for c in ids_with_rows], "rows_per_chunk": [int(c) for c in rows_per_chunk],
            "chunk_order_note": "chunk_ids_with_rows and rows_per_chunk are in row order: g equals their expansion, fam is family-major",
            "label_histogram": np.bincount(np.asarray(Y), minlength=N_CONFIGS).tolist(),
            "majority_class_rate": round(float(np.bincount(np.asarray(Y)).max() / max(len(Y), 1)), 6),
            "library_versions": ce._library_versions(),
            "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
            "arrays": {"X": {"sha256": ce._sha(X), "shape": list(X.shape), "dtype": str(X.dtype)},
                       "y": {"sha256": ce._sha(Y), "shape": list(Y.shape), "dtype": str(Y.dtype)},
                       "g": {"sha256": ce._sha(G), "shape": list(G.shape), "dtype": str(G.dtype)},
                       "fam": {"sha256": ce._sha(F), "shape": list(F.shape), "dtype": str(F.dtype)}},
            "chunk_meta_sha256": {k: ce._sha(v) if v.dtype.kind != "U" else hashlib.sha256("\n".join(v).encode()).hexdigest()
                                  for k, v in meta.items()},
            "per_family": per_family, "source_pins": pins["files"], "build_seconds": build_s,
            "rows_dropped_short_stream": int(len(meta["chunk_ids"]) * N_CONFIGS - len(Y)),
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def save_npz(path, X, Y, G, F, meta, chunk_size, carve_len):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez(path, X=X, y=Y, g=G, fam=F, carve=np.int64(carve_len), chunk_size=np.int64(chunk_size),
             chunk_id_base=np.int64(CHUNK_ID_BASE), families=np.array(FAMILIES),
             **{f"meta_{k}": v for k, v in meta.items()})


def check(npz_path=NPZ_PATH, manifest_path=MANIFEST_PATH):
    from npzmap import npz_memmap
    man = json.load(open(manifest_path, encoding="utf-8"))
    ok = True
    for name, rec in man["arrays"].items():
        arr = npz_memmap(npz_path, name)
        h = hashlib.sha256()
        for i in range(0, len(arr), 20000):
            h.update(np.ascontiguousarray(arr[i:i + 20000]).tobytes())
        same = h.hexdigest() == rec["sha256"] and list(arr.shape) == rec["shape"] and str(arr.dtype) == rec["dtype"]
        print(f"  {'ok  ' if same else 'FAIL'} {name} {list(arr.shape)} {arr.dtype} {h.hexdigest()[:16]}")
        ok &= same
    print("REALFIT CORPUS: " + ("IDENTICAL to the banked manifest" if ok else "DIFFERS from the banked manifest"))
    return ok


def disjoint(chunk_size=32768):
    """Fit and sealed corpora share no blob chunk, no chunk id and no source-chunk hash."""
    from npzmap import npz_memmap
    blobs = ce.load_real_blobs()
    sel, sealed, dropped = fit_selection(blobs, chunk_size)
    ok = True
    n_drop = sum(len(v["byte_identical_to_a_sealed_chunk"]) + len(v["duplicate_within_the_fit_selection"]) for v in dropped.values())
    print(f"  ..   {n_drop} candidate chunks dropped for byte identity: "
          + ", ".join(f"{f} {len(dropped[f]['byte_identical_to_a_sealed_chunk'])}+{len(dropped[f]['duplicate_within_the_fit_selection'])}" for f in FAMILIES))
    for f in FAMILIES:
        share = set(sel[f]) & set(sealed[f])
        n_avail = len(blobs[f]) // chunk_size
        covered = len(set(sel[f]) | set(sealed[f]))
        print(f"  {'ok  ' if not share else 'FAIL'} {f:8} fit {len(sel[f]):4d} + sealed {len(sealed[f]):4d} = {covered:5d} "
              f"of {n_avail:5d} whole chunks; shared blob chunks {len(share)}")
        ok &= not share
    for path, name in ((NPZ_PATH, "fit"), (ce.NPZ_PATH, "sealed")):
        if not os.path.exists(path):
            print(f"  ..   {name} corpus not built yet: {os.path.relpath(path, REPO)}")
    if os.path.exists(NPZ_PATH) and os.path.exists(ce.NPZ_PATH):
        gf = set(int(v) for v in np.unique(npz_memmap(NPZ_PATH, "g")))
        gs = set(int(v) for v in np.unique(npz_memmap(ce.NPZ_PATH, "g")))
        print(f"  {'ok  ' if not (gf & gs) else 'FAIL'} chunk ids: {len(gf)} fit, {len(gs)} sealed, shared {len(gf & gs)}")
        ok &= not (gf & gs)
        sf = set(str(v) for v in npz_memmap(NPZ_PATH, "meta_src_sha256"))
        ss = set(str(v) for v in npz_memmap(ce.NPZ_PATH, "meta_src_sha256"))
        print(f"  {'ok  ' if not (sf & ss) else 'FAIL'} source-chunk sha256: {len(sf)} fit, {len(ss)} sealed, shared {len(sf & ss)}")
        ok &= not (sf & ss)
    print("DISJOINT: " + ("fit and sealed share nothing" if ok else "OVERLAP FOUND"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--disjoint", action="store_true"); ap.add_argument("--probe", action="store_true")
    ap.add_argument("--chunk-size", type=int, default=ce.DEFAULTS["chunk_size"])
    ap.add_argument("--carve", type=int, default=ce.DEFAULTS["carve"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--src", default=ce.SRC_DIR)
    ap.add_argument("--out", default=NPZ_PATH); ap.add_argument("--manifest", default=MANIFEST_PATH)
    ap.add_argument("--cap-per-family", type=int, default=None, help="probe/smoke only: at most this many chunks per family")
    a = ap.parse_args()
    if a.check:
        return 0 if check(a.out, a.manifest) else 1
    if a.disjoint:
        return 0 if disjoint(a.chunk_size) else 1
    if a.probe:
        r1 = build(a.chunk_size, a.carve, a.procs, a.src, cap_per_family=a.cap_per_family or 3)
        r2 = build(a.chunk_size, a.carve, a.procs, a.src, order_seed=7, cap_per_family=a.cap_per_family or 3)
        same = all(ce._sha(x) == ce._sha(y) for x, y in zip(r1[:4], r2[:4]))
        print(f"PROBE: {len(r1[1])} rows; two task orders give {'IDENTICAL' if same else 'DIFFERENT'} arrays")
        return 0 if same else 1
    if a.build:
        pins = ce.load_pins()
        ok, problems = ce.verify_pins(a.src, pins)
        if not ok:
            print("REFUSING: pinned sources differ: " + "; ".join(problems[:5]), file=sys.stderr); return 2
        X, Y, G, F, meta, sel, sealed, dropped, counts, secs = build(a.chunk_size, a.carve, a.procs, a.src,
                                                                     cap_per_family=a.cap_per_family)
        man = manifest_of(X, Y, G, F, meta, sel, sealed, dropped, counts, a.chunk_size, a.carve, secs, pins,
                          ce.load_real_blobs(a.src))
        save_npz(a.out, X, Y, G, F, meta, a.chunk_size, a.carve)
        os.makedirs(os.path.dirname(a.manifest), exist_ok=True)
        with open(a.manifest, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=2, sort_keys=True); fh.write("\n")
        print(f"built {man['n_rows']} rows from {man['n_chunks']} chunks over {len(FAMILIES)} real families in {secs}s")
        print(f"  {os.path.relpath(a.out, REPO)}  X {man['arrays']['X']['sha256'][:16]}  y {man['arrays']['y']['sha256'][:16]}")
        for f in FAMILIES:
            p = man["per_family"][f]
            print(f"    {f:8} {p['n_rows']:6d} rows  {p['n_chunks']:4d} chunks ({p['share_of_fit_rows']:.4f} of the fit rows), "
                  f"ceiling {p['ceiling_distinct_fragments']}")
        return 0
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
