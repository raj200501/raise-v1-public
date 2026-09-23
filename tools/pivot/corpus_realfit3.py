#!/usr/bin/env python3
"""Build the fourth-doubling real-content FIT corpus for preregistration 0025, nested on 0024's pool.

Per family the blob is 0024's blob byte for byte (corpus_realfit2.load_blobs over 0024's pins, which verifies them) followed
by the new pinned archives' matching members (tools/pivot/ext_source_pins3.json; vendored directories excluded by the member
rule) and the new rfc3 files. The candidate rule is 0024's over that longer blob, so 0024's candidates recur unchanged and
first; a NEW candidate is additionally dropped if it shares a run of 1024 bytes with 0024's blob of the same family at any
offset (the 0018 run-overlap rule, re-applied to the previous fit corpus, so that "other files" is proven). The pool is
0024's pool in 0024's order (recovered from the realfit2 npz metas and checked against 0024's manifest), then a seeded
permutation of the remaining candidates. Only the new pool positions are featurised; their chunk ids continue 0024's; the
npz holds the NEW rows only, and the runner concatenates [0021 fit corpus | realfit2 | realfit3].

  python3 tools/pivot/corpus_realfit3.py --verify-pins
  python3 tools/pivot/corpus_realfit3.py --build          # writes data/pivot/realfit3_c4096.npz + artifacts/pivot/realfit3_corpus_manifest.json
  python3 tools/pivot/corpus_realfit3.py --check          # the built arrays hash to the manifest
  python3 tools/pivot/corpus_realfit3.py --disjoint       # nothing shared with 0018's evaluation corpus, 0021's fit block or 0024's corpus
"""
import argparse, hashlib, json, os, re, sys, time
from multiprocessing import Pool
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corpus_realfit2 as c2                 # noqa: E402
import corpus_ext as ce                      # noqa: E402
from corpus_ext import N_FEATURES, N_CONFIGS, CONFIG_NAMES   # noqa: E402
REPO = c2.REPO
PINS_PATH = os.path.join(HERE, "ext_source_pins3.json")
SRC_DIR = os.path.join(REPO, "data", "pivot", "ext_src3")
NPZ_PATH = os.path.join(REPO, "data", "pivot", "realfit3_c4096.npz")
MANIFEST_PATH = os.path.join(REPO, "artifacts", "pivot", "realfit3_corpus_manifest.json")
FAMILIES = c2.FAMILIES; CHUNK_ID_BASE = c2.CHUNK_ID_BASE; FAMILY_STRIDE = c2.FAMILY_STRIDE; DEFAULTS = dict(c2.DEFAULTS)
OVERLAP = c2.OVERLAP


def load_pins(path=PINS_PATH):
    return json.load(open(path, encoding="utf-8"))


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def load_new_blobs(src_dir=SRC_DIR, pins=None):
    """The NEW part of each family's blob from 0025's pins: archives in sorted name order, matching members in sorted
    member-name order (the member rule excludes vendored directories); rfc_txt from the rfc3 files in sorted name order.
    Families with no new archive get b''. Refuses on any pin problem."""
    pins = pins or load_pins()
    ok, problems = c2.verify_pins(src_dir, pins)
    if not ok:
        raise RuntimeError("0025 sources do not match tools/pivot/ext_source_pins3.json: " + "; ".join(problems[:5]))
    rules = pins["family_rules"]; cache = {}; blobs, comp = {}, {}
    for f in FAMILIES:
        rule = rules[f]
        if "dir" in rule:
            rels = sorted(r for r in pins["files"] if r.startswith(rule["dir"] + "/"))
            blobs[f] = b"".join(open(os.path.join(src_dir, r), "rb").read() for r in rels)
            comp[f] = {"n_files": len(rels), "bytes": len(blobs[f]), "rule": dict(rule)}
            continue
        flags = re.I if rule.get("ignore_case") else 0
        rx = re.compile(rule["member_regex"], flags); parts = []; per = {}
        for a in sorted(rule.get("archives", [])):
            if a not in cache:
                cache[a] = c2._members(os.path.join(src_dir, a))
            names = sorted(n for n in cache[a] if rx.search(n))
            b = b"".join(cache[a][n] for n in names); per[a] = {"n_files": len(names), "bytes": len(b)}; parts.append(b)
        blobs[f] = b"".join(parts)
        comp[f] = {"n_files": sum(v["n_files"] for v in per.values()), "bytes": len(blobs[f]), "rule": dict(rule), "per_archive": per}
    return blobs, comp


def load_blobs(src_dir=SRC_DIR, pins=None, src_dir_0024=c2.SRC_DIR, pins_0024=None):
    """(blob3, composition, blob2_meta): blob3[f] = 0024's blob + the new part; blob2_meta banks 0024's blob length and sha256."""
    pins = pins or load_pins(); pins2 = pins_0024 or c2.load_pins()
    b2, comp2 = c2.load_blobs(src_dir_0024, pins2)
    bn, compn = load_new_blobs(src_dir, pins)
    blobs = {f: b2[f] + bn[f] for f in FAMILIES}
    meta2 = {f: {"bytes": len(b2[f]), "sha256": _sha_bytes(b2[f]), "n_whole_chunks": None} for f in FAMILIES}
    comp = {f: {"0024_part": comp2[f], "new_part": compn[f], "bytes": len(blobs[f])} for f in FAMILIES}
    return blobs, comp, meta2, b2


def pool2_from_npz(npz_path, manifest_path):
    """0024's selection per family, in pool order, recovered from the realfit2 npz metas and checked against 0024's manifest."""
    from npzmap import npz_memmap
    man = json.load(open(manifest_path, encoding="utf-8"))
    fam = np.asarray(npz_memmap(npz_path, "meta_chunk_fam")); k = np.asarray(npz_memmap(npz_path, "meta_chunk_k"))
    bidx = np.asarray(npz_memmap(npz_path, "meta_blob_chunk_index")); ids = np.asarray(npz_memmap(npz_path, "meta_chunk_ids"))
    sel2 = {}
    for fi, f in enumerate(FAMILIES):
        m = fam == fi; order = np.argsort(k[m]); kk = k[m][order]
        if not np.array_equal(kk, np.arange(len(kk))):
            raise RuntimeError(f"{f}: 0024's pool positions are not 0..n-1")
        sel2[f] = [int(x) for x in bidx[m][order]]
        if hashlib.sha256(json.dumps(sel2[f]).encode()).hexdigest() != man["per_family"][f]["pool_blob_chunk_index_sha256"]:
            raise RuntimeError(f"{f}: the realfit2 npz metas do not reproduce 0024's manifest pool_blob_chunk_index_sha256")
        if int(ids[m].max()) != c2.chunk_id(fi, len(sel2[f]) - 1):
            raise RuntimeError(f"{f}: 0024's chunk ids are not contiguous from the base")
    return sel2, man


def candidates3(blobs, blobs2, excluded, chunk_size, pinned_windows, man2):
    """Two passes with one shared 'seen' set: first 0024's candidate rule over every family's 0024 part (which reproduces 0024's
    candidates and dropped lists exactly, or the build refuses), then the same rule over every family's NEW part, so that a
    byte-identical collision between a new chunk and a 0024 chunk is always charged to the new chunk; then the extra rule for NEW
    candidates: no run of OVERLAP run_windows x window bytes shared with 0024's blob of the same family at any offset.
    Returns (cands, dropped, n_old_chunks)."""
    n_old = {f: len(blobs2[f]) // chunk_size for f in FAMILIES}
    cands, dropped = c2.candidates(blobs2, excluded, chunk_size, pinned_windows)          # pass 1: 0024's part, 0024's rule
    for f in FAMILIES:
        d2 = man2["chunks_dropped"][f]; d3 = dropped[f]
        same = (len(cands[f]) == man2["per_family"][f]["n_candidate_chunks"]
                and d3["byte_identical_to_a_0018_pinned_chunk"] == d2["byte_identical_to_a_0018_pinned_chunk"]
                and d3["shares_a_run_with_a_0018_pinned_blob"] == d2["shares_a_run_with_a_0018_pinned_blob"]
                and d3["duplicate_of_an_earlier_candidate"] == d2["duplicate_of_an_earlier_candidate"])
        if not same:
            raise RuntimeError(f"{f}: the 0024 part of the blob does not reproduce 0024's candidates (count {len(cands[f])} vs "
                               f"{man2['per_family'][f]['n_candidate_chunks']})")
    seen = set()                                                                            # 0024's seen state, rebuilt in 0024's order
    for f in FAMILIES:
        for i in cands[f]:
            seen.add(hashlib.sha256(blobs2[f][i * chunk_size:(i + 1) * chunk_size]).hexdigest())
    for f in FAMILIES:                                                                      # pass 2: the new parts, the same rule and set
        new_part = blobs[f][n_old[f] * chunk_size:]
        n_new = len(new_part) // chunk_size
        d_ex, d_run, d_dup, d_dup24, keep = [], [], [], [], []
        if n_new:
            runs18 = c2.shared_run_windows(new_part, chunk_size, pinned_windows)
            w2 = c2.window_hashes_all_offsets(blobs2[f]); runs24 = c2.shared_run_windows(new_part, chunk_size, w2); del w2
            hashes24 = {hashlib.sha256(blobs2[f][i * chunk_size:(i + 1) * chunk_size]).hexdigest() for i in range(n_old[f])}
            d_run24 = []
            for j in range(n_new):
                i = n_old[f] + j
                h = hashlib.sha256(new_part[j * chunk_size:(j + 1) * chunk_size]).hexdigest()
                if h in excluded:
                    d_ex.append(i)
                elif runs18[j] >= OVERLAP["run_windows"]:
                    d_run.append(i)
                elif h in seen or h in hashes24:
                    (d_dup24 if h in hashes24 else d_dup).append(i)
                elif runs24[j] >= OVERLAP["run_windows"]:
                    d_run24.append(i)
                else:
                    seen.add(h); keep.append(i)
            dropped[f]["longest_shared_run_windows_max"] = max(int(dropped[f]["longest_shared_run_windows_max"]), int(runs18.max()))
            dropped[f]["longest_shared_run_windows_with_0024_max"] = int(runs24.max())
        else:
            d_run24 = []
            dropped[f]["longest_shared_run_windows_with_0024_max"] = 0
        dropped[f]["byte_identical_to_a_0018_pinned_chunk"] = dropped[f]["byte_identical_to_a_0018_pinned_chunk"] + d_ex
        dropped[f]["shares_a_run_with_a_0018_pinned_blob"] = dropped[f]["shares_a_run_with_a_0018_pinned_blob"] + d_run
        dropped[f]["duplicate_of_an_earlier_candidate"] = dropped[f]["duplicate_of_an_earlier_candidate"] + d_dup
        dropped[f]["new_chunk_duplicate_of_a_0024_chunk"] = d_dup24
        dropped[f]["shares_a_run_with_0024s_blob_of_the_same_family"] = d_run24
        dropped[f]["n_new_whole_chunks"] = n_new
        cands[f] = cands[f] + keep
    return cands, dropped, n_old


def selection3(cands, sel2, sizes, seed):
    """Per family: 0024's pool first, in its order; then default_rng([seed, family_index + 1])'s permutation of the remaining
    candidates (blob order), taken to the pool size. Refuses if short."""
    sel = {}
    for i, f in enumerate(FAMILIES):
        have = set(sel2[f]); rest = [c for c in cands[f] if c not in have]
        need = sizes[f] - len(sel2[f])
        if need < 0:
            raise RuntimeError(f"{f}: pool size {sizes[f]} below 0024's pool {len(sel2[f])}")
        if len(rest) < need:
            raise RuntimeError(f"{f}: {len(rest)} remaining candidate chunks, {need} needed")
        perm = np.random.default_rng([int(seed), i + 1]).permutation(len(rest))
        sel[f] = list(sel2[f]) + [int(rest[j]) for j in perm[:need]]
    return sel


def plan(pins, chunk_size, src_dir=SRC_DIR, base=None, cap_per_family=None, realfit2_npz=c2.NPZ_PATH, realfit2_manifest=c2.MANIFEST_PATH,
         src_dir_0024=c2.SRC_DIR, pins_0024=None):
    blobs, comp, meta2, blobs2 = load_blobs(src_dir, pins, src_dir_0024, pins_0024)
    sel2, man2 = pool2_from_npz(realfit2_npz, realfit2_manifest)
    excluded = c2.pinned_chunk_hashes(chunk_size)
    pinned_windows = c2.pinned_window_hashes()
    cands, dropped, n_old = candidates3(blobs, blobs2, excluded, chunk_size, pinned_windows, man2)
    for f in FAMILIES:
        meta2[f]["n_whole_chunks"] = n_old[f]
    if base is None:
        man = json.load(open(c2.REALFIT_MANIFEST, encoding="utf-8"))
        base = {f: int(man["per_family"][f]["n_chunks_with_rows"]) for f in FAMILIES}
    sizes = c2.pool_sizes(base, int(pins["doublings"]), float(pins["pool_margin"]), int(pins["pool_extra"]))
    if cap_per_family is not None:
        sizes = {f: min(len(sel2[f]) + int(cap_per_family), sizes[f]) for f in FAMILIES}
    sel = selection3(cands, sel2, sizes, int(pins["seed"]))
    return dict(blobs=blobs, comp=comp, meta2=meta2, sel2=sel2, man2=man2, excluded=excluded, cands=cands, dropped=dropped,
                n_old=n_old, base=base, sizes=sizes, sel=sel, n_windows=len(pinned_windows))


def build(chunk_size, carve_len, procs, src_dir=SRC_DIR, pins=None, order_seed=None, cap_per_family=None, base=None, **plan_kw):
    pins = pins or load_pins()
    P = plan(pins, chunk_size, src_dir, base, cap_per_family, **plan_kw)
    sel, sel2, sizes, blobs = P["sel"], P["sel2"], P["sizes"], P["blobs"]
    tasks = [(f, k, chunk_size, carve_len) for f in FAMILIES for k in range(len(sel2[f]), sizes[f])]
    if order_seed is not None:
        import random
        random.Random(order_seed).shuffle(tasks)
    cap = max(len(tasks), 1) * N_CONFIGS
    X = np.empty((cap, N_FEATURES), np.float32); Y = np.empty(cap, np.int16); G = np.empty(cap, np.int32); F = np.empty(cap, np.int8)
    metas = []; n = 0; t0 = time.perf_counter()
    with Pool(procs, initializer=c2._init, initargs=(blobs, sel)) as pool:
        for j, (x, y, meta) in enumerate(pool.imap_unordered(c2._one, tasks, chunksize=4), 1):
            m = len(y)
            if m:
                X[n:n + m] = x; Y[n:n + m] = y; G[n:n + m] = meta[0]; F[n:n + m] = meta[1]; n += m
            metas.append(meta)
            if j % 500 == 0:
                print(f"    {j}/{len(tasks)} chunks, {n} rows, {time.perf_counter() - t0:.0f}s", flush=True)
    order = np.lexsort((Y[:n], G[:n]))
    X, Y, G, F = X[:n][order], Y[:n][order], G[:n][order], F[:n][order]
    metas.sort()
    meta_arr = {"chunk_ids": np.array([m[0] for m in metas], np.int32), "chunk_fam": np.array([m[1] for m in metas], np.int8),
                "chunk_k": np.array([m[2] for m in metas], np.int32), "blob_chunk_index": np.array([m[3] for m in metas], np.int32),
                "distinct_streams": np.array([m[4] for m in metas], np.int8), "distinct_fragments": np.array([m[5] for m in metas], np.int8),
                "src_sha256": np.array([m[6] for m in metas])}
    n_whole_0018 = sum(len(b) // chunk_size for b in ce.load_real_blobs().values())
    info = {"composition": P["comp"], "n_excluded_hashes": len(P["excluded"]), "n_whole_chunks_of_0018_pinned_blobs": n_whole_0018,
            "n_pinned_windows": P["n_windows"], "excluded_hashes_sha256": hashlib.sha256("\n".join(sorted(P["excluded"])).encode()).hexdigest(),
            "candidates_per_family": {f: len(P["cands"][f]) for f in FAMILIES},
            "candidates_in_0024_frame_per_family": {f: sum(1 for i in P["cands"][f] if i < P["n_old"][f]) for f in FAMILIES},
            "whole_chunks_per_family": {f: len(blobs[f]) // chunk_size for f in FAMILIES},
            "dropped": P["dropped"], "base_chunks_with_rows_0021": P["base"], "pool_sizes": sizes,
            "pool_sizes_0024": {f: len(sel2[f]) for f in FAMILIES}, "cap_per_family": cap_per_family,
            "blob_0024": P["meta2"], "sel2_sha256": {f: hashlib.sha256(json.dumps(sel2[f]).encode()).hexdigest() for f in FAMILIES},
            "man2": P["man2"]}
    return X, Y, G, F, meta_arr, sel, info, round(time.perf_counter() - t0, 1)


def manifest_of(X, Y, G, F, meta, sel, info, chunk_size, carve_len, build_s, pins, realfit2_npz, realfit2_manifest):
    ids_with_rows, first_pos, rows_per_chunk = np.unique(G, return_index=True, return_counts=True)
    order = np.argsort(first_pos); ids_with_rows = ids_with_rows[order]; rows_per_chunk = rows_per_chunk[order]
    without = sorted(set(int(c) for c in meta["chunk_ids"]) - set(int(c) for c in ids_with_rows))
    man2 = info["man2"]; per_family = {}
    for fi, f in enumerate(FAMILIES):
        m = F == fi; cm = meta["chunk_fam"] == fi; n2 = info["pool_sizes_0024"][f]
        per_family[f] = {"n_new_rows": int(m.sum()), "n_new_chunks": int(cm.sum()), "n_new_chunks_with_rows": int(np.unique(G[m]).size),
                         "pool_size": info["pool_sizes"][f], "pool_size_0024": n2,
                         "n_chunks_with_rows_0024": man2["per_family"][f]["n_chunks_with_rows"],
                         "n_pool_chunks_with_rows_total": man2["per_family"][f]["n_chunks_with_rows"] + int(np.unique(G[m]).size),
                         "n_whole_chunks_in_blob": info["whole_chunks_per_family"][f], "n_whole_chunks_in_0024_blob": info["blob_0024"][f]["n_whole_chunks"],
                         "n_candidate_chunks": info["candidates_per_family"][f],
                         "n_candidate_chunks_in_0024_frame": info["candidates_in_0024_frame_per_family"][f],
                         "n_candidate_chunks_0024_banked": man2["per_family"][f]["n_candidate_chunks"],
                         "n_dropped_byte_identical_to_0018": len(info["dropped"][f]["byte_identical_to_a_0018_pinned_chunk"]),
                         "n_dropped_sharing_a_run_with_0018": len(info["dropped"][f]["shares_a_run_with_a_0018_pinned_blob"]),
                         "n_dropped_sharing_a_run_with_0024_same_family": len(info["dropped"][f]["shares_a_run_with_0024s_blob_of_the_same_family"]),
                         "n_new_dropped_duplicate_of_a_0024_chunk": len(info["dropped"][f]["new_chunk_duplicate_of_a_0024_chunk"]),
                         "n_new_whole_chunks": info["dropped"][f]["n_new_whole_chunks"],
                         "n_new_candidate_chunks": info["candidates_per_family"][f] - info["candidates_in_0024_frame_per_family"][f],
                         "n_dropped_duplicate": len(info["dropped"][f]["duplicate_of_an_earlier_candidate"]),
                         "longest_shared_run_windows_max_over_whole_chunks": info["dropped"][f]["longest_shared_run_windows_max"],
                         "longest_shared_run_windows_with_0024_max_over_new_chunks": info["dropped"][f]["longest_shared_run_windows_with_0024_max"],
                         "base_chunks_with_rows_0021": info["base_chunks_with_rows_0021"][f],
                         "new_chunk_id_range": [c2.chunk_id(fi, n2), c2.chunk_id(fi, info["pool_sizes"][f] - 1)],
                         "share_of_new_rows": round(float(m.sum() / max(len(Y), 1)), 4),
                         "rows_per_chunk_mean": round(float(m.sum() / max(cm.sum(), 1)), 4),
                         "ceiling_distinct_streams": round(float(meta["distinct_streams"][cm].mean() / N_CONFIGS), 4) if cm.any() else None,
                         "ceiling_distinct_fragments": round(float(meta["distinct_fragments"][cm].mean() / N_CONFIGS), 4) if cm.any() else None,
                         "pool_blob_chunk_index_sha256": hashlib.sha256(json.dumps(sel[f]).encode()).hexdigest(),
                         "pool_prefix_is_0024s_pool": hashlib.sha256(json.dumps(sel[f][:n2]).encode()).hexdigest() == man2["per_family"][f]["pool_blob_chunk_index_sha256"],
                         "blob_0024_sha256": info["blob_0024"][f]["sha256"], "blob_0024_bytes": info["blob_0024"][f]["bytes"],
                         "composition": info["composition"][f]}
    return {"schema": "raise-v1/realfit3_corpus_manifest/1",
            "why": "content hashes of the fourth-doubling real-content FIT corpus (preregistration 0025): the NEW pool positions "
                   "nested on 0024's pool, and what they are disjoint from; a rebuild is proven identical by "
                   "`python3 tools/pivot/corpus_realfit3.py --check` and the disjointness from everything sealed or fitted before "
                   "(0018's evaluation corpus, 0021's fit block, 0024's corpus) by `--disjoint`",
            "npz": os.path.relpath(NPZ_PATH, REPO), "families": FAMILIES, "kind": "real content only; new pool positions nested on 0024's pool",
            "smoke": info["cap_per_family"] is not None,
            "nested_on": {"npz": os.path.relpath(realfit2_npz, REPO), "manifest": os.path.relpath(realfit2_manifest, REPO),
                          "realfit2_arrays": man2["arrays"], "pool_sizes_0024": info["pool_sizes_0024"], "sel2_sha256": info["sel2_sha256"],
                          "rule": pins["nested_on"]["rule"]},
            "selection_rule": pins["pool_rule"],
            "candidate_rule": "two passes with one shared seen-set: 0024's candidate rule over every family's 0024 part first (every whole chunk "
                              "whose bytes hash to no whole chunk of any 0018 pinned blob, share no run of 1024 bytes with any 0018 pinned blob "
                              "at any offset, and hash to no earlier candidate of any family, in blob order; reproduced and checked against "
                              "0024's manifest, refusing otherwise), then the same rule over every family's new part, so a collision with a "
                              "0024 chunk is charged to the new chunk; and for NEW candidates additionally: no run of 1024 bytes shared with "
                              "0024's blob of the same family at any offset",
            "seed": int(pins["seed"]), "doublings": int(pins["doublings"]), "pool_margin": float(pins["pool_margin"]),
            "pool_extra": int(pins["pool_extra"]), "pool_sizes": info["pool_sizes"], "cap_per_family": info["cap_per_family"],
            "base_chunks_with_rows_0021": info["base_chunks_with_rows_0021"],
            "exclusion": {"n_distinct_chunk_hashes_of_0018_pinned_blobs": info["n_excluded_hashes"],
                          "n_whole_chunks_of_0018_pinned_blobs": info["n_whole_chunks_of_0018_pinned_blobs"],
                          "hashes_sha256": info["excluded_hashes_sha256"],
                          "run_overlap": dict(OVERLAP, n_distinct_pinned_windows=info["n_pinned_windows"]),
                          "run_overlap_vs_0024": "every 64-byte window at every offset of 0024's blob of the same family; a new candidate "
                                                 "chunk is dropped if 16 consecutive aligned non-constant windows of it all occur there"},
            "chunks_dropped": {f: info["dropped"][f] for f in FAMILIES},
            "chunk_size": chunk_size, "carve": carve_len, "chunk_id_base": CHUNK_ID_BASE, "family_stride": FAMILY_STRIDE,
            "n_rows": int(len(Y)), "n_chunks": int(len(meta["chunk_ids"])), "n_chunks_with_rows": int(len(ids_with_rows)),
            "chunks_without_rows": without,
            "chunk_ids_with_rows": [int(c) for c in ids_with_rows], "rows_per_chunk": [int(c) for c in rows_per_chunk],
            "chunk_order_note": "the NEW rows only; chunk_ids_with_rows and rows_per_chunk are in row order: g equals their expansion; "
                                "fam is family-major and, within a family, pool order (chunk id ascending), continuing 0024's ids",
            "label_histogram": np.bincount(np.asarray(Y), minlength=N_CONFIGS).tolist(),
            "majority_class_rate": round(float(np.bincount(np.asarray(Y)).max() / max(len(Y), 1)), 6) if len(Y) else None,
            "library_versions": ce._library_versions(), "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
            "arrays": {"X": {"sha256": ce._sha(X), "shape": list(X.shape), "dtype": str(X.dtype)},
                       "y": {"sha256": ce._sha(Y), "shape": list(Y.shape), "dtype": str(Y.dtype)},
                       "g": {"sha256": ce._sha(G), "shape": list(G.shape), "dtype": str(G.dtype)},
                       "fam": {"sha256": ce._sha(F), "shape": list(F.shape), "dtype": str(F.dtype)}},
            "chunk_meta_sha256": {k: ce._sha(v) if v.dtype.kind != "U" else hashlib.sha256("\n".join(v).encode()).hexdigest() for k, v in meta.items()},
            "per_family": per_family, "source_pins": pins["files"], "family_rules": pins["family_rules"],
            "build_seconds": build_s, "rows_dropped_short_stream": int(len(meta["chunk_ids"]) * N_CONFIGS - len(Y)),
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def check(npz_path=NPZ_PATH, manifest_path=MANIFEST_PATH):
    from npzmap import npz_memmap
    man = json.load(open(manifest_path, encoding="utf-8")); ok = True
    for name, rec in man["arrays"].items():
        arr = npz_memmap(npz_path, name); h = hashlib.sha256()
        for i in range(0, len(arr), 20000):
            h.update(np.ascontiguousarray(arr[i:i + 20000]).tobytes())
        same = h.hexdigest() == rec["sha256"] and list(arr.shape) == rec["shape"] and str(arr.dtype) == rec["dtype"]
        print(f"  {'ok  ' if same else 'FAIL'} {name} {list(arr.shape)} {arr.dtype} {h.hexdigest()[:16]}"); ok &= same
    # the corpus it nests on is the one whose arrays 0024 banked
    n2 = man["nested_on"]; p2 = os.path.join(REPO, n2["npz"])
    if os.path.exists(p2):
        for name, rec in n2["realfit2_arrays"].items():
            arr = npz_memmap(p2, name); h = hashlib.sha256()
            for i in range(0, len(arr), 20000):
                h.update(np.ascontiguousarray(arr[i:i + 20000]).tobytes())
            same = h.hexdigest() == rec["sha256"]; print(f"  {'ok  ' if same else 'FAIL'} nested on realfit2.{name} {h.hexdigest()[:16]}"); ok &= same
    else:
        print(f"  FAIL the corpus this one nests on is absent: {n2['npz']}"); ok = False
    print("REALFIT3 CORPUS: " + ("IDENTICAL to the banked manifest" if ok else "DIFFERS from the banked manifest"))
    return ok


def disjoint(chunk_size=DEFAULTS["chunk_size"], npz_path=NPZ_PATH, src_dir=SRC_DIR, realfit2_npz=c2.NPZ_PATH, realfit2_manifest=c2.MANIFEST_PATH,
             src_dir_0024=c2.SRC_DIR):
    """Shares no chunk bytes, chunk id or source-chunk hash with 0018's sealed evaluation corpus, 0021's fit corpus or 0024's
    corpus; the exclusion set covers the first two; chunk ids continue 0024's; the run-overlap rules re-proved on the built chunks."""
    from npzmap import npz_memmap
    ok = True
    excluded = c2.pinned_chunk_hashes(chunk_size)
    if not os.path.exists(npz_path):
        print(f"  ..   this corpus not built yet: {os.path.relpath(npz_path, REPO)}"); return False
    s3 = set(str(v) for v in npz_memmap(npz_path, "meta_src_sha256")); g3 = set(int(v) for v in np.unique(npz_memmap(npz_path, "g")))
    shared_ex = s3 & excluded
    print(f"  {'ok  ' if not shared_ex else 'FAIL'} source-chunk sha256: {len(s3)} here, {len(excluded)} excluded, shared {len(shared_ex)}"); ok &= not shared_ex
    for path, label in ((ce.NPZ_PATH, "0018 sealed evaluation"), (os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"), "0021 fit"), (realfit2_npz, "0024 fit")):
        if not os.path.exists(path):
            print(f"  FAIL {label} corpus not present: {os.path.relpath(path, REPO)}"); ok = False; continue
        gs = set(int(v) for v in np.unique(npz_memmap(path, "g"))); ss = set(str(v) for v in npz_memmap(path, "meta_src_sha256"))
        good = not (g3 & gs) and not (s3 & ss)
        print(f"  {'ok  ' if good else 'FAIL'} vs {label}: shared chunk ids {len(g3 & gs)}, shared source hashes {len(s3 & ss)}"); ok &= good
    ids = np.asarray(npz_memmap(npz_path, "meta_chunk_ids")); fam_i = np.asarray(npz_memmap(npz_path, "meta_chunk_fam"))
    man2 = json.load(open(realfit2_manifest, encoding="utf-8"))
    ids2 = np.asarray(npz_memmap(realfit2_npz, "meta_chunk_ids")); fam2 = np.asarray(npz_memmap(realfit2_npz, "meta_chunk_fam"))
    cont = all((ids[fam_i == fi].min() == ids2[fam2 == fi].max() + 1) if (fam_i == fi).any() else True for fi in range(len(FAMILIES)))
    print(f"  {'ok  ' if cont else 'FAIL'} chunk ids continue 0024's per family (base {CHUNK_ID_BASE})"); ok &= cont
    # the run-overlap rules, re-proved on the built chunks' bytes: vs the 0018 blobs (every built chunk) and, for the chunks cut
    # from the NEW files, vs 0024's same-family blob at every offset (the build's rule for new candidates). A built chunk cut from
    # 0024's frame (a candidate 0024 did not use) IS a region of 0024's blob, so that rule cannot apply to it; for those the proof
    # is that no such chunk is one of 0024's pool positions (its bytes were never fitted).
    pins = load_pins(); blobs, _, _, blobs2 = load_blobs(src_dir, pins, src_dir_0024); pw = c2.pinned_window_hashes()
    bidx = np.asarray(npz_memmap(npz_path, "meta_blob_chunk_index"))
    sel2, _ = pool2_from_npz(realfit2_npz, realfit2_manifest)
    worst18 = worst24 = 0; bad18 = bad24 = 0; n_frame = n_newf = 0; reused = 0
    for fi, f in enumerate(FAMILIES):
        n_old = len(blobs2[f]) // chunk_size
        idx = [int(i) for i in bidx[fam_i == fi]]; old_idx = [i for i in idx if i < n_old]; new_idx = [i for i in idx if i >= n_old]
        n_frame += len(old_idx); n_newf += len(new_idx); reused += len(set(old_idx) & set(sel2[f]))
        sel_b = b"".join(blobs[f][i * chunk_size:(i + 1) * chunk_size] for i in idx)
        if sel_b:
            r18 = c2.shared_run_windows(sel_b, chunk_size, pw); worst18 = max(worst18, int(r18.max())); bad18 += int((r18 >= OVERLAP["run_windows"]).sum())
        new_b = b"".join(blobs[f][i * chunk_size:(i + 1) * chunk_size] for i in new_idx)
        if new_b:
            w2 = c2.window_hashes_all_offsets(blobs2[f]); r24 = c2.shared_run_windows(new_b, chunk_size, w2); del w2
            worst24 = max(worst24, int(r24.max())); bad24 += int((r24 >= OVERLAP["run_windows"]).sum())
    print(f"  {'ok  ' if bad18 == 0 else 'FAIL'} run overlap vs the 0018 files: {bad18} of {n_frame + n_newf} built chunks share a {OVERLAP['run_windows']} x {OVERLAP['window']}-byte run (longest {worst18} windows)")
    print(f"  {'ok  ' if bad24 == 0 else 'FAIL'} run overlap vs 0024's same-family blob: {bad24} of the {n_newf} built chunks cut from the new files share such a run (longest {worst24} windows)")
    print(f"  {'ok  ' if reused == 0 else 'FAIL'} the {n_frame} built chunks cut from 0024's frame: {reused} are 0024 pool positions (must be 0: candidates 0024 did not use)")
    ok &= bad18 == 0 and bad24 == 0 and reused == 0
    print("DISJOINT: " + ("this corpus shares nothing with anything scored or fitted before" if ok else "OVERLAP FOUND"))
    return ok


def save_npz(path, X, Y, G, F, meta, chunk_size, carve_len):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez(path, X=X, y=Y, g=G, fam=F, carve=np.int64(carve_len), chunk_size=np.int64(chunk_size),
             chunk_id_base=np.int64(CHUNK_ID_BASE), families=np.array(FAMILIES), **{f"meta_{k}": v for k, v in meta.items()})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true"); ap.add_argument("--check", action="store_true")
    ap.add_argument("--disjoint", action="store_true"); ap.add_argument("--probe", action="store_true")
    ap.add_argument("--verify-pins", action="store_true")
    ap.add_argument("--chunk-size", type=int, default=DEFAULTS["chunk_size"]); ap.add_argument("--carve", type=int, default=DEFAULTS["carve"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--src", default=SRC_DIR); ap.add_argument("--pins", default=PINS_PATH)
    ap.add_argument("--src-0024", default=c2.SRC_DIR, help="0024's pinned sources (verified against ext_source_pins2.json)")
    ap.add_argument("--realfit2", default=c2.NPZ_PATH); ap.add_argument("--realfit2-manifest", default=c2.MANIFEST_PATH)
    ap.add_argument("--out", default=NPZ_PATH); ap.add_argument("--manifest", default=MANIFEST_PATH)
    ap.add_argument("--cap-per-family", type=int, default=None, help="probe/smoke only: at most this many NEW pool chunks per family")
    ap.add_argument("--base-per-family", type=int, default=None, help="smoke only: the per-family base count the doublings start from")
    a = ap.parse_args()
    pins = load_pins(a.pins)
    base = None if a.base_per_family is None else {f: int(a.base_per_family) for f in FAMILIES}
    kw = dict(realfit2_npz=a.realfit2, realfit2_manifest=a.realfit2_manifest, src_dir_0024=a.src_0024)
    if a.verify_pins:
        ok, problems = c2.verify_pins(a.src, pins); ok2, problems2 = c2.verify_pins(a.src_0024, c2.load_pins())
        print("PINS: " + ("every 0025 and 0024 pinned file present and byte-identical" if ok and ok2 else "PROBLEMS: " + "; ".join((problems + problems2)[:10])))
        return 0 if ok and ok2 else 1
    if a.check:
        return 0 if check(a.out, a.manifest) else 1
    if a.disjoint:
        return 0 if disjoint(a.chunk_size, a.out, a.src, a.realfit2, a.realfit2_manifest, a.src_0024) else 1
    if a.probe:
        cap = a.cap_per_family or 3
        r1 = build(a.chunk_size, a.carve, a.procs, a.src, pins, cap_per_family=cap, base=base, **kw)
        r2 = build(a.chunk_size, a.carve, a.procs, a.src, pins, order_seed=7, cap_per_family=cap, base=base, **kw)
        same = all(ce._sha(x) == ce._sha(y) for x, y in zip(r1[:4], r2[:4]))
        print(f"PROBE: {len(r1[1])} rows; two task orders give {'IDENTICAL' if same else 'DIFFERENT'} arrays")
        return 0 if same else 1
    if a.build:
        if (a.cap_per_family is not None or base is not None) and os.path.abspath(a.out) == os.path.abspath(NPZ_PATH):
            print("REFUSING: a capped or rebased build is a smoke; it never writes the sealed corpus path", file=sys.stderr); return 2
        X, Y, G, F, meta, sel, info, secs = build(a.chunk_size, a.carve, a.procs, a.src, pins, cap_per_family=a.cap_per_family, base=base, **kw)
        man = manifest_of(X, Y, G, F, meta, sel, info, a.chunk_size, a.carve, secs, pins, a.realfit2, a.realfit2_manifest)
        save_npz(a.out, X, Y, G, F, meta, a.chunk_size, a.carve)
        os.makedirs(os.path.dirname(a.manifest), exist_ok=True)
        with open(a.manifest, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=2, sort_keys=True); fh.write("\n")
        print(f"built {man['n_rows']} NEW rows from {man['n_chunks']} new chunks over {len(FAMILIES)} real families in {secs}s, nested on 0024's pool")
        print(f"  {os.path.relpath(a.out, REPO)}  X {man['arrays']['X']['sha256'][:16]}  y {man['arrays']['y']['sha256'][:16]}")
        for f in FAMILIES:
            p = man["per_family"][f]
            print(f"    {f:8} +{p['n_new_rows']:6d} rows  +{p['n_new_chunks']:4d} chunks (with rows {p['n_new_chunks_with_rows']}; pool {p['pool_size_0024']} -> "
                  f"{p['pool_size']}, candidates {p['n_candidate_chunks']}, of which in 0024's frame {p['n_candidate_chunks_in_0024_frame']}; "
                  f"dropped for a run shared with 0024 {p['n_dropped_sharing_a_run_with_0024_same_family']}), prefix is 0024's pool: {p['pool_prefix_is_0024s_pool']}")
        return 0
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
