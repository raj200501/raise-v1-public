#!/usr/bin/env python3
"""Second-decade real-content FIT corpus (preregistration 0024): chunks of NEW pinned real files, disjoint by
byte from every chunk of 0018's pinned blobs.

0023 read REAL_CURVE_RISES over one decade of real plaintexts (130 -> 1029): the boosted model rose 0.007344 per
doubling and the standardised logistic 0.009551, the lead shrinking from 0.0063 to 0.0014 at the top. The top rung
was the WHOLE of 0021's fit block - every chunk of the five pinned files that 0018's sealed evaluation set does not
use - so the record held no more real plaintexts of those families. This corpus is the next decade: new upstream
files of the SAME five families (other Python projects' .py and .rst, other C projects' .c/.h, other Windows
programs' .exe/.dll, other RFCs), pinned by sha256 in tools/pivot/ext_source_pins2.json, cut into the same
consecutive non-overlapping 32768-byte chunks, compressed under the same 26 configurations, carved and featurised
by the same code (tools/pivot/corpus_ext.py imports it, this module imports corpus_ext).

    sealed (0018):  300 chunks per family of the 0018 pinned blobs    -> data/pivot/ext_c4096.npz   (scored, never fitted)
    fit    (0020):  every remaining chunk of those blobs               -> data/pivot/realfit_c4096.npz (0021's fit block)
    fit 2  (0024):  a seeded pool of chunks of NEW pinned blobs        -> data/pivot/realfit2_c4096.npz (this corpus)

Disjointness is by BYTES, not by file name, and at EVERY offset, not only at chunk boundaries: a candidate chunk is
dropped if it equals ANY whole chunk of ANY 0018 pinned blob (the sealed evaluation chunks and 0021's fit chunks are
both subsets of those, and --disjoint proves the two npz metas are covered), if it shares a RUN of at least 1024 bytes
with any 0018 pinned blob at any alignment (sixteen consecutive 64-byte windows of the candidate, aligned to its own
64-byte grid and none of them a constant window, each found somewhere in the 0018 blobs by a 64-bit polynomial rolling
hash - the 0024 pre-freeze review found node.exe carrying the same OpenSSL build as 0018's libcrypto DLL, so identical
code sat in both at shifted offsets, invisible to whole-chunk hashing), or if it duplicates an earlier candidate of any
family. What remains per family is permuted
by np.random.default_rng([seed, family_index + 1]) and the first pool_size chunks are built, where pool_size is
the count a lockstep doubling of 0021's block needs (per family, 0021's chunks-with-rows x (2^doublings - 1)) plus
a margin for chunks that yield no row. The preregistration seals the rungs from this pool; the pool order is the
nesting order. Chunk ids live in their own space (30000000 + family stride + k), disjoint from the builder's
(0..49999), the sealed extension corpus's (10000000+) and 0021's fit block's (20000000+).

    python3 tools/pivot/corpus_realfit2.py --verify-pins     # every pinned file present and byte-identical
    python3 tools/pivot/corpus_realfit2.py --build           # data/pivot/realfit2_c4096.npz + artifacts/pivot/realfit2_corpus_manifest.json
    python3 tools/pivot/corpus_realfit2.py --check           # array hashes of the npz against the banked manifest
    python3 tools/pivot/corpus_realfit2.py --disjoint        # nothing here shares a byte, a chunk id or a source hash with anything sealed or fitted before
    python3 tools/pivot/corpus_realfit2.py --probe           # determinism: a small slice built twice, in two task orders
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tarfile
import time
import zipfile
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corpus_ext as ce  # noqa: E402  (the label factory, the 0018 pinned blobs)
from corpus import CONFIG_NAMES, N_CONFIGS  # noqa: E402
from features import N_FEATURES, features_many  # noqa: E402

REPO = ce.REPO
PINS_PATH = os.path.join(HERE, "ext_source_pins2.json")
SRC_DIR = os.path.join(REPO, "data", "pivot", "ext_src2")
NPZ_PATH = os.path.join(REPO, "data", "pivot", "realfit2_c4096.npz")
MANIFEST_PATH = os.path.join(REPO, "artifacts", "pivot", "realfit2_corpus_manifest.json")
REALFIT_MANIFEST = os.path.join(REPO, "artifacts", "pivot", "realfit_corpus_manifest.json")
FAMILIES = ce.REAL_FAMILIES                      # ["c_src", "pe_bin", "py_src", "rfc_txt", "rst_doc"], 0018's order
CHUNK_ID_BASE = 30_000_000
FAMILY_STRIDE = ce.FAMILY_STRIDE
DEFAULTS = {"chunk_size": 32768, "carve": 4096}
OVERLAP = {"window": 64, "run_windows": 16, "hash": "polynomial mod 2^64, base 0x9E3779B97F4A7C15|1, H(i) = sum_k b[i+k] * base^k",
           "rule": "a candidate chunk is dropped if run_windows consecutive window-byte windows aligned to its own grid, none constant "
                   "(all bytes equal), each occur at ANY offset of ANY 0018 pinned blob; run_windows x window = 1024 shared bytes"}
_P = np.uint64(0x9E3779B97F4A7C15 | 1)
_PINV = np.uint64(pow(int(_P), -1, 1 << 64))
_SLICE = 1 << 22


def _powers(n, base):
    out = np.empty(n, np.uint64); out[0] = 1
    if n > 1:
        with np.errstate(over="ignore"):
            np.cumprod(np.full(n - 1, base, np.uint64), out=out[1:])
    return out


def window_hashes_all_offsets(b: bytes, window=OVERLAP["window"]):
    """The rolling hash of every window-byte window of b at every offset, as a sorted unique uint64 array; computed slice
    by slice (window - 1 bytes of overlap) so the transient stays small: H(i) = sum_k b[i+k] * base^k mod 2^64, obtained
    from prefix sums of b[j] * base^j and multiplied back by base^-i (base is odd, so invertible mod 2^64)."""
    n = len(b); outs = []
    pj = _powers(_SLICE + window, _P); qj = _powers(_SLICE + window, _PINV)
    for s0 in range(0, n - window + 1, _SLICE):
        seg = np.frombuffer(b[s0:min(n, s0 + _SLICE + window - 1)], np.uint8).astype(np.uint64); m = len(seg)
        with np.errstate(over="ignore"):
            C = np.empty(m + 1, np.uint64); C[0] = 0; np.cumsum(seg * pj[:m], out=C[1:])
            H = (C[window:] - C[:-window]) * qj[:m - window + 1]
        outs.append(np.unique(H))
    return np.unique(np.concatenate(outs)) if outs else np.empty(0, np.uint64)


def aligned_window_hashes(b: bytes, window=OVERLAP["window"]):
    """The same hash for the windows of b aligned to its own window-byte grid, and whether each window is constant."""
    n = (len(b) // window) * window; x = np.frombuffer(b[:n], np.uint8).astype(np.uint64).reshape(-1, window)
    with np.errstate(over="ignore"):
        H = (x * _powers(window, _P)).sum(axis=1, dtype=np.uint64)
    return H, (x == x[:, :1]).all(axis=1)


def pinned_window_hashes(src_dir_0018=ce.SRC_DIR, window=OVERLAP["window"]):
    """Every window-byte window at every offset of every 0018 pinned blob, hashed: the run-overlap exclusion set."""
    blobs = ce.load_real_blobs(src_dir_0018)
    return np.unique(np.concatenate([window_hashes_all_offsets(blobs[f], window) for f in FAMILIES]))


def shared_run_windows(blob: bytes, chunk_size, pinned_windows, window=OVERLAP["window"]):
    """Per whole chunk of blob: the longest run of consecutive aligned, non-constant windows found in pinned_windows."""
    n = len(blob) // chunk_size
    H, const = aligned_window_hashes(blob[:n * chunk_size], window)
    pos = np.searchsorted(pinned_windows, H); pos[pos >= len(pinned_windows)] = 0
    m = ((pinned_windows[pos] == H) & ~const).reshape(n, chunk_size // window)
    runs = np.zeros(n, np.int64); cur = np.zeros(n, np.int64)
    for j in range(m.shape[1]):
        cur = np.where(m[:, j], cur + 1, 0); runs = np.maximum(runs, cur)
    return runs


def chunk_id(fam_index: int, k: int) -> int:
    return CHUNK_ID_BASE + fam_index * FAMILY_STRIDE + k


def load_pins(path=PINS_PATH):
    return json.load(open(path, encoding="utf-8"))


def verify_pins(src_dir=SRC_DIR, pins=None):
    pins = pins or load_pins()
    problems = []
    for rel, rec in sorted(pins["files"].items()):
        p = os.path.join(src_dir, rel)
        if not os.path.exists(p):
            problems.append(f"missing {rel}"); continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != rec["sha256"]:
            problems.append(f"{rel}: sha256 {h[:12]}... != pinned {rec['sha256'][:12]}...")
    return (not problems), problems


def _members(path):
    """{member name: bytes} for every regular file of a .tar.gz or .zip archive."""
    out = {}
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            for i in z.infolist():
                if not i.is_dir():
                    out[i.filename] = z.read(i.filename)
    else:
        with tarfile.open(path) as t:
            for m in t.getmembers():
                if m.isfile():
                    out[m.name] = t.extractfile(m).read()
    return out


def load_blobs(src_dir=SRC_DIR, pins=None):
    """One blob per family: the pinned archives named by the family's rule, in sorted archive-name order, each
    contributing its matching members in sorted member-name order; rfc_txt is the pinned rfc2/ files in sorted name
    order. Refuses on any pin problem. Returns (blobs, composition) where composition banks files and bytes per archive."""
    pins = pins or load_pins()
    ok, problems = verify_pins(src_dir, pins)
    if not ok:
        raise RuntimeError("second-decade sources do not match tools/pivot/ext_source_pins2.json: " + "; ".join(problems[:5]))
    rules = pins["family_rules"]
    cache = {}
    blobs, comp = {}, {}
    for f in FAMILIES:
        rule = rules[f]
        if "dir" in rule:
            rels = sorted(r for r in pins["files"] if r.startswith(rule["dir"] + "/"))
            parts = [open(os.path.join(src_dir, r), "rb").read() for r in rels]
            blobs[f] = b"".join(parts)
            comp[f] = {"n_files": len(rels), "bytes": len(blobs[f]), "rule": dict(rule)}
            continue
        flags = re.I if rule.get("ignore_case") else 0
        rx = re.compile(rule["member_regex"], flags)
        parts = []; per = {}
        for a in sorted(rule["archives"]):
            if a not in cache:
                cache[a] = _members(os.path.join(src_dir, a))
            names = sorted(n for n in cache[a] if rx.search(n))
            b = b"".join(cache[a][n] for n in names)
            per[a] = {"n_files": len(names), "bytes": len(b)}
            parts.append(b)
        blobs[f] = b"".join(parts)
        comp[f] = {"n_files": sum(v["n_files"] for v in per.values()), "bytes": len(blobs[f]), "rule": dict(rule), "per_archive": per}
    return blobs, comp


def pinned_chunk_hashes(chunk_size, src_dir_0018=ce.SRC_DIR):
    """sha256 of EVERY whole chunk of every 0018 pinned blob: the exclusion set. The sealed evaluation chunks and
    0021's fit chunks are subsets of it (proved by --disjoint against the two npz metas)."""
    blobs = ce.load_real_blobs(src_dir_0018)
    hs = set()
    for f in FAMILIES:
        b = blobs[f]
        for i in range(len(b) // chunk_size):
            hs.add(hashlib.sha256(b[i * chunk_size:(i + 1) * chunk_size]).hexdigest())
    return hs


def candidates(blobs, excluded, chunk_size, pinned_windows=None):
    """Per family, in blob order: every whole chunk whose bytes hash to nothing excluded, share no run of OVERLAP
    run_windows x window bytes with any 0018 pinned blob at any offset (when pinned_windows is given), and hash to no
    earlier candidate of any family (families in FAMILIES order). Returns (cands, dropped)."""
    seen = set(); cands, dropped = {}, {}
    for f in FAMILIES:
        b = blobs[f]; keep, d_ex, d_run, d_dup = [], [], [], []
        runs = (shared_run_windows(b, chunk_size, pinned_windows) if pinned_windows is not None
                else np.zeros(len(b) // chunk_size, np.int64))
        for i in range(len(b) // chunk_size):
            h = hashlib.sha256(b[i * chunk_size:(i + 1) * chunk_size]).hexdigest()
            if h in excluded:
                d_ex.append(i)
            elif runs[i] >= OVERLAP["run_windows"]:
                d_run.append(i)
            elif h in seen:
                d_dup.append(i)
            else:
                seen.add(h); keep.append(i)
        cands[f] = keep
        dropped[f] = {"byte_identical_to_a_0018_pinned_chunk": d_ex, "shares_a_run_with_a_0018_pinned_blob": d_run,
                      "duplicate_of_an_earlier_candidate": d_dup,
                      "longest_shared_run_windows_max": int(runs.max()) if len(runs) else 0}
    return cands, dropped


def pool_sizes(base, doublings, margin, extra):
    """Chunks to build per family: base_f x (2^doublings - 1) new plaintexts, plus margin for chunks without rows."""
    return {f: int(np.ceil(base[f] * (2 ** doublings - 1) * (1.0 + margin))) + int(extra) for f in FAMILIES}


def selection(cands, sizes, seed):
    """Per family, np.random.default_rng([seed, family_index + 1]) permutes the candidates; the first sizes[f] are the
    pool, IN THAT ORDER (the nesting order the preregistration's rungs use). Refuses if a family is short."""
    sel = {}
    for i, f in enumerate(FAMILIES):
        n = len(cands[f])
        if n < sizes[f]:
            raise RuntimeError(f"{f}: {n} candidate chunks, {sizes[f]} needed")
        perm = np.random.default_rng([int(seed), i + 1]).permutation(n)
        sel[f] = [int(cands[f][j]) for j in perm[:sizes[f]]]
    return sel


_BLOBS = None
_SEL = None


def _init(blobs, sel):
    global _BLOBS, _SEL
    _BLOBS, _SEL = blobs, sel


def _one(args):
    family, k, chunk_size, carve_len = args
    frags, labels, n_streams, n_carved, src_sha = ce.chunk_rows(family, k, chunk_size, carve_len, _BLOBS, _SEL)
    fi = FAMILIES.index(family)
    meta = (chunk_id(fi, k), fi, k, _SEL[family][k], n_streams, n_carved, src_sha)
    if not frags:
        return np.empty((0, N_FEATURES), np.float32), np.empty(0, np.int16), meta
    return features_many(frags), np.asarray(labels, np.int16), meta


def plan(pins, chunk_size, src_dir=SRC_DIR, base=None, cap_per_family=None):
    """Everything before featurisation: blobs, exclusion set, candidates, pool sizes, selection."""
    blobs, comp = load_blobs(src_dir, pins)
    excluded = pinned_chunk_hashes(chunk_size)
    pinned_windows = pinned_window_hashes()
    cands, dropped = candidates(blobs, excluded, chunk_size, pinned_windows)
    if base is None:
        man = json.load(open(REALFIT_MANIFEST, encoding="utf-8"))
        base = {f: int(man["per_family"][f]["n_chunks_with_rows"]) for f in FAMILIES}
    sizes = pool_sizes(base, int(pins["doublings"]), float(pins["pool_margin"]), int(pins["pool_extra"]))
    if cap_per_family is not None:
        sizes = {f: min(int(cap_per_family), sizes[f]) for f in FAMILIES}
    sel = selection(cands, sizes, int(pins["seed"]))
    return blobs, comp, excluded, cands, dropped, base, sizes, sel, len(pinned_windows)


def build(chunk_size, carve_len, procs, src_dir=SRC_DIR, pins=None, order_seed=None, cap_per_family=None, base=None):
    pins = pins or load_pins()
    blobs, comp, excluded, cands, dropped, base, sizes, sel, n_windows = plan(pins, chunk_size, src_dir, base, cap_per_family)
    tasks = [(f, k, chunk_size, carve_len) for f in FAMILIES for k in range(sizes[f])]
    if order_seed is not None:   # the probe shuffles the task order: the corpus must not depend on it
        import random
        random.Random(order_seed).shuffle(tasks)
    cap = len(tasks) * N_CONFIGS
    X = np.empty((cap, N_FEATURES), np.float32); Y = np.empty(cap, np.int16)
    G = np.empty(cap, np.int32); F = np.empty(cap, np.int8)
    metas = []; n = 0; t0 = time.perf_counter()
    with Pool(procs, initializer=_init, initargs=(blobs, sel)) as pool:
        for j, (x, y, meta) in enumerate(pool.imap_unordered(_one, tasks, chunksize=4), 1):
            m = len(y)
            if m:
                X[n:n + m] = x; Y[n:n + m] = y; G[n:n + m] = meta[0]; F[n:n + m] = meta[1]; n += m
            metas.append(meta)
            if j % 500 == 0:
                print(f"    {j}/{len(tasks)} chunks, {n} rows, {time.perf_counter() - t0:.0f}s", flush=True)
    order = np.lexsort((Y[:n], G[:n]))      # canonical row order: chunk id then label -> family-major, pool order within
    X, Y, G, F = X[:n][order], Y[:n][order], G[:n][order], F[:n][order]
    metas.sort()
    meta_arr = {"chunk_ids": np.array([m[0] for m in metas], np.int32),
                "chunk_fam": np.array([m[1] for m in metas], np.int8),
                "chunk_k": np.array([m[2] for m in metas], np.int32),
                "blob_chunk_index": np.array([m[3] for m in metas], np.int32),
                "distinct_streams": np.array([m[4] for m in metas], np.int8),
                "distinct_fragments": np.array([m[5] for m in metas], np.int8),
                "src_sha256": np.array([m[6] for m in metas])}
    n_whole_0018 = sum(len(b) // chunk_size for b in ce.load_real_blobs().values())
    info = {"composition": comp, "n_excluded_hashes": len(excluded), "n_whole_chunks_of_0018_pinned_blobs": n_whole_0018,
            "n_pinned_windows": n_windows,
            "excluded_hashes_sha256": hashlib.sha256("\n".join(sorted(excluded)).encode()).hexdigest(),
            "candidates_per_family": {f: len(cands[f]) for f in FAMILIES},
            "whole_chunks_per_family": {f: len(blobs[f]) // chunk_size for f in FAMILIES},
            "dropped": dropped, "base_chunks_with_rows_0021": base, "pool_sizes": sizes,
            "cap_per_family": cap_per_family}
    return X, Y, G, F, meta_arr, sel, info, round(time.perf_counter() - t0, 1)


def manifest_of(X, Y, G, F, meta, sel, info, chunk_size, carve_len, build_s, pins):
    ids_with_rows, first_pos, rows_per_chunk = np.unique(G, return_index=True, return_counts=True)
    order = np.argsort(first_pos); ids_with_rows = ids_with_rows[order]; rows_per_chunk = rows_per_chunk[order]
    without = sorted(set(int(c) for c in meta["chunk_ids"]) - set(int(c) for c in ids_with_rows))
    per_family = {}
    for fi, f in enumerate(FAMILIES):
        m = F == fi; cm = meta["chunk_fam"] == fi
        per_family[f] = {"n_rows": int(m.sum()), "n_chunks": int(cm.sum()),
                         "n_chunks_with_rows": int(np.unique(G[m]).size),
                         "n_whole_chunks_in_blob": info["whole_chunks_per_family"][f],
                         "n_candidate_chunks": info["candidates_per_family"][f],
                         "n_dropped_byte_identical_to_0018": len(info["dropped"][f]["byte_identical_to_a_0018_pinned_chunk"]),
                         "n_dropped_sharing_a_run_with_0018": len(info["dropped"][f]["shares_a_run_with_a_0018_pinned_blob"]),
                         "n_dropped_duplicate": len(info["dropped"][f]["duplicate_of_an_earlier_candidate"]),
                         "longest_shared_run_windows_max_over_whole_chunks": info["dropped"][f]["longest_shared_run_windows_max"],
                         "pool_size": info["pool_sizes"][f], "base_chunks_with_rows_0021": info["base_chunks_with_rows_0021"][f],
                         "share_of_rows": round(float(m.sum() / max(len(Y), 1)), 4),
                         "rows_per_chunk_mean": round(float(m.sum() / max(cm.sum(), 1)), 4),
                         "ceiling_distinct_streams": round(float(meta["distinct_streams"][cm].mean() / N_CONFIGS), 4),
                         "ceiling_distinct_fragments": round(float(meta["distinct_fragments"][cm].mean() / N_CONFIGS), 4),
                         "pool_blob_chunk_index_sha256": hashlib.sha256(json.dumps(sel[f]).encode()).hexdigest(),
                         "composition": info["composition"][f]}
    return {"schema": "raise-v1/realfit2_corpus_manifest/1",
            "why": "content hashes of the second-decade real-content FIT corpus (preregistration 0024) and what it is disjoint "
                   "from; a rebuild is proven identical by `python3 tools/pivot/corpus_realfit2.py --check` and the "
                   "disjointness from everything sealed or fitted before by `--disjoint`",
            "npz": os.path.relpath(NPZ_PATH, REPO), "families": FAMILIES, "kind": "real content only, new pinned files",
            "smoke": info["cap_per_family"] is not None,
            "selection_rule": "per family: every whole chunk of the family blob (pinned archives in sorted name order, matching "
                              "members in sorted name order) whose bytes hash to no whole chunk of any 0018 pinned blob, share no run "
                              "of 1024 bytes with any 0018 pinned blob at any offset (exclusion.run_overlap), and hash to no earlier "
                              "candidate of any family, in blob order; np.random.default_rng([seed, family_index + 1]) permutes those "
                              "candidates and the first pool_size are built, in that order",
            "seed": int(pins["seed"]), "doublings": int(pins["doublings"]), "pool_margin": float(pins["pool_margin"]),
            "pool_extra": int(pins["pool_extra"]), "pool_sizes": info["pool_sizes"], "cap_per_family": info["cap_per_family"],
            "base_chunks_with_rows_0021": info["base_chunks_with_rows_0021"],
            "exclusion": {"n_distinct_chunk_hashes_of_0018_pinned_blobs": info["n_excluded_hashes"],
                          "n_whole_chunks_of_0018_pinned_blobs": info["n_whole_chunks_of_0018_pinned_blobs"],
                          "hashes_sha256": info["excluded_hashes_sha256"],
                          "run_overlap": dict(OVERLAP, n_distinct_pinned_windows=info["n_pinned_windows"])},
            "chunks_dropped": {f: info["dropped"][f] for f in FAMILIES},
            "chunk_size": chunk_size, "carve": carve_len, "chunk_id_base": CHUNK_ID_BASE, "family_stride": FAMILY_STRIDE,
            "n_rows": int(len(Y)), "n_chunks": int(len(meta["chunk_ids"])), "n_chunks_with_rows": int(len(ids_with_rows)),
            "chunks_without_rows": without,
            "chunk_ids_with_rows": [int(c) for c in ids_with_rows], "rows_per_chunk": [int(c) for c in rows_per_chunk],
            "chunk_order_note": "chunk_ids_with_rows and rows_per_chunk are in row order: g equals their expansion; fam is "
                                "family-major and, within a family, pool order (chunk id ascending)",
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
            "per_family": per_family, "source_pins": pins["files"], "family_rules": pins["family_rules"],
            "build_seconds": build_s,
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
    print("REALFIT2 CORPUS: " + ("IDENTICAL to the banked manifest" if ok else "DIFFERS from the banked manifest"))
    return ok


def disjoint(chunk_size=DEFAULTS["chunk_size"], npz_path=NPZ_PATH, src_dir=SRC_DIR):
    """This corpus shares no chunk bytes, no chunk id and no source-chunk hash with 0018's sealed evaluation corpus or
    0021's fit corpus; and the exclusion set covers both of those corpora's source hashes."""
    from npzmap import npz_memmap
    ok = True
    excluded = pinned_chunk_hashes(chunk_size)
    for path, label in ((ce.NPZ_PATH, "0018 sealed evaluation"), (os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"), "0021 fit")):
        if not os.path.exists(path):
            print(f"  ..   {label} corpus not present: {os.path.relpath(path, REPO)}"); ok = False; continue
        ss = set(str(v) for v in npz_memmap(path, "meta_src_sha256"))
        real = ss  # the 0018 corpus meta also holds the synthetic families' hashes; only the real ones can be covered
        if label.startswith("0018"):
            fam = np.asarray(npz_memmap(path, "meta_chunk_fam")); names = [str(x) for x in npz_memmap(path, "families")]
            real = set(str(v) for v, fi in zip(npz_memmap(path, "meta_src_sha256"), fam) if names[fi] in FAMILIES)
        cov = real <= excluded
        print(f"  {'ok  ' if cov else 'FAIL'} exclusion set covers every real source hash of the {label} corpus ({len(real)} hashes)")
        ok &= cov
    if not os.path.exists(npz_path):
        print(f"  ..   this corpus not built yet: {os.path.relpath(npz_path, REPO)}")
        print("DISJOINT: " + ("exclusion set covers the sealed and fitted corpora" if ok else "PROBLEM"))
        return ok
    s2 = set(str(v) for v in npz_memmap(npz_path, "meta_src_sha256")); g2 = set(int(v) for v in np.unique(npz_memmap(npz_path, "g")))
    shared_ex = s2 & excluded
    print(f"  {'ok  ' if not shared_ex else 'FAIL'} source-chunk sha256: {len(s2)} here, {len(excluded)} excluded, shared {len(shared_ex)}")
    ok &= not shared_ex
    for path, label in ((ce.NPZ_PATH, "0018 sealed evaluation"), (os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"), "0021 fit")):
        if not os.path.exists(path):
            continue
        gs = set(int(v) for v in np.unique(npz_memmap(path, "g"))); ss = set(str(v) for v in npz_memmap(path, "meta_src_sha256"))
        print(f"  {'ok  ' if not (g2 & gs) and not (s2 & ss) else 'FAIL'} vs {label}: shared chunk ids {len(g2 & gs)}, shared source hashes {len(s2 & ss)}")
        ok &= not (g2 & gs) and not (s2 & ss)
    ids = np.asarray(npz_memmap(npz_path, "meta_chunk_ids"))
    print(f"  {'ok  ' if ids.min() >= CHUNK_ID_BASE else 'FAIL'} chunk ids start at {int(ids.min())} (base {CHUNK_ID_BASE})")
    ok &= bool(ids.min() >= CHUNK_ID_BASE)
    # the run-overlap rule, re-proved on the built pool: rebuild each built chunk's bytes from the pinned blobs and scan them
    man_path = os.path.join(os.path.dirname(npz_path), "..", "..", "artifacts", "pivot", "realfit2_corpus_manifest.json")
    pins = load_pins(); blobs, _ = load_blobs(src_dir, pins); pw = pinned_window_hashes()
    fam_i = np.asarray(npz_memmap(npz_path, "meta_chunk_fam")); bidx = np.asarray(npz_memmap(npz_path, "meta_blob_chunk_index"))
    worst = 0; n_bad = 0
    for fi, f in enumerate(FAMILIES):
        sel_b = b"".join(blobs[f][int(i) * chunk_size:(int(i) + 1) * chunk_size] for i in bidx[fam_i == fi])
        runs = shared_run_windows(sel_b, chunk_size, pw)
        worst = max(worst, int(runs.max()) if len(runs) else 0); n_bad += int((runs >= OVERLAP["run_windows"]).sum())
    print(f"  {'ok  ' if n_bad == 0 else 'FAIL'} run overlap: {n_bad} built chunks share a {OVERLAP['run_windows']} x {OVERLAP['window']}-byte run "
          f"with a 0018 pinned blob at any offset (longest shared run {worst} windows, {len(pw)} distinct pinned windows)")
    ok &= n_bad == 0
    print("DISJOINT: " + ("this corpus shares nothing with anything scored or fitted before" if ok else "OVERLAP FOUND"))
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--disjoint", action="store_true"); ap.add_argument("--probe", action="store_true")
    ap.add_argument("--verify-pins", action="store_true")
    ap.add_argument("--chunk-size", type=int, default=DEFAULTS["chunk_size"])
    ap.add_argument("--carve", type=int, default=DEFAULTS["carve"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--src", default=SRC_DIR); ap.add_argument("--pins", default=PINS_PATH)
    ap.add_argument("--out", default=NPZ_PATH); ap.add_argument("--manifest", default=MANIFEST_PATH)
    ap.add_argument("--cap-per-family", type=int, default=None, help="probe/smoke only: at most this many pool chunks per family")
    ap.add_argument("--base-per-family", type=int, default=None,
                    help="smoke only: the per-family base count the lockstep doubling starts from (the real build reads 0021's manifest)")
    a = ap.parse_args()
    pins = load_pins(a.pins)
    base = None if a.base_per_family is None else {f: int(a.base_per_family) for f in FAMILIES}
    if a.verify_pins:
        ok, problems = verify_pins(a.src, pins)
        print("PINS: " + ("every pinned file present and byte-identical" if ok else "PROBLEMS: " + "; ".join(problems[:10])))
        return 0 if ok else 1
    if a.check:
        return 0 if check(a.out, a.manifest) else 1
    if a.disjoint:
        return 0 if disjoint(a.chunk_size, a.out, a.src) else 1
    if a.probe:
        cap = a.cap_per_family or 3
        r1 = build(a.chunk_size, a.carve, a.procs, a.src, pins, cap_per_family=cap, base=base)
        r2 = build(a.chunk_size, a.carve, a.procs, a.src, pins, order_seed=7, cap_per_family=cap, base=base)
        same = all(ce._sha(x) == ce._sha(y) for x, y in zip(r1[:4], r2[:4]))
        print(f"PROBE: {len(r1[1])} rows; two task orders give {'IDENTICAL' if same else 'DIFFERENT'} arrays")
        return 0 if same else 1
    if a.build:
        if (a.cap_per_family is not None or base is not None) and os.path.abspath(a.out) == os.path.abspath(NPZ_PATH):
            print("REFUSING: a capped or rebased build is a smoke; it never writes the sealed corpus path", file=sys.stderr); return 2
        ok, problems = verify_pins(a.src, pins)
        if not ok:
            print("REFUSING: pinned sources differ: " + "; ".join(problems[:5]), file=sys.stderr); return 2
        X, Y, G, F, meta, sel, info, secs = build(a.chunk_size, a.carve, a.procs, a.src, pins, cap_per_family=a.cap_per_family, base=base)
        man = manifest_of(X, Y, G, F, meta, sel, info, a.chunk_size, a.carve, secs, pins)
        save_npz(a.out, X, Y, G, F, meta, a.chunk_size, a.carve)
        os.makedirs(os.path.dirname(a.manifest), exist_ok=True)
        with open(a.manifest, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=2, sort_keys=True); fh.write("\n")
        print(f"built {man['n_rows']} rows from {man['n_chunks']} chunks over {len(FAMILIES)} real families in {secs}s")
        print(f"  {os.path.relpath(a.out, REPO)}  X {man['arrays']['X']['sha256'][:16]}  y {man['arrays']['y']['sha256'][:16]}")
        for f in FAMILIES:
            p = man["per_family"][f]
            print(f"    {f:8} {p['n_rows']:6d} rows  {p['n_chunks']:4d} chunks (with rows {p['n_chunks_with_rows']}; pool {p['pool_size']}, "
                  f"candidates {p['n_candidate_chunks']}), ceiling {p['ceiling_distinct_fragments']}")
        return 0
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
