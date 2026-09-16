#!/usr/bin/env python3
"""Real-content fit at 4096 (preregistration 0020).

Question. 0018/0019 read OOB_TRANSFER_FAILS: 0014's searched HGB M4, fitted on the corpus builder's
eight generated families, identifies the encoder on five pinned real-file families at 0.0637 against a
0.088462 bar. The model had never seen a real file, so that reading cannot tell a training-distribution
failure from real content carrying little encoder signal. This run separates them: the same recipes are
fitted on REAL content - the chunks of the same pinned files 0018's sealed evaluation corpus does not
use (tools/pivot/corpus_realfit.py; disjoint by index, by chunk id and by source-chunk hash) - and
scored once on the same sealed rows 0018 scored.

Arms, in the sealed order:
  repro            0003's incumbent M1 on the pool's first 100000 rows; must reproduce 0003's banked
                   0.1965 on the sealed evaluation set (0016 reproduced the same rung in this environment)
  null             M4 on the fit corpus with its labels permuted; must sit at chance on both row sets
  real_model       M4 on the whole fit corpus                      <- THE CLAUSE, on the real-family rows
  real_incumbent   0003's M1 on the same rows                      (flag)
  real_logistic    0014's standardised L3 on the same rows         (flag)
  builder_matched  M4 on the pool's first N rows, N = the fit corpus's row count (flag: content, not volume)

Every fit is scored exactly once, on the concatenation of the sealed 260000-row evaluation set and the
whole 61409-row extension corpus - 0018's scoring set, row for row - so every reading here is directly
comparable to 0018's banked ones. The clause is M4's count of correct rows over the five real-file
families against chance + 0.05; the builder-matched arm, the two other recipes, the synthetic families,
the reverse reading on the builder's evaluation set and the per-family readings are flags.

Reuses tools/pivot/run_recipe_search.py's machinery (blocks, fits, checkpoints, heartbeat, memory
accounting, launch rules) unchanged, and tools/pivot/run_oob.py's shape. Nothing here searches or selects
a recipe. No scored row is ever in a fit block, and that is measured, not assumed.

Stages: one invocation (--stage run). Checkpoints resume; a container restart is recovered by relaunching
the identical command.
"""
from __future__ import annotations

import argparse
import hashlib
import io as _io
import json
import os
import sys
import time
import zipfile as _zf

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_recipe_search import (  # noqa: E402
    REPO, _sha, sha_obj, _utc, fingerprint, environment, npz_memmap, fill_f32, Block, run_fit, Store,
    NotRun, cluster_ci, _rss_gb, _rss_total_gb, grouped_split, FAMILIES, N_CONFIGS, CONFIG_NAMES)
from corpus_ext import EXT_FAMILIES, REAL_FAMILIES, SYNTH_FAMILIES  # noqa: E402
from corpus_realfit import FAMILIES as FIT_FAMILIES  # noqa: E402

STRUCTURED_TEXT = ["c_src", "py_src", "rfc_txt", "rst_doc", "sql", "xml"]
HIGH_ENTROPY = ["hexdump", "pe_bin"]
# The four trivial-baseline arms are OPERATING_RULES §4a: a learned score is compared against the floor the dumbest
# thing that could work reaches on the same rows, plus a preregistered margin, never against chance. They are fitted
# on the same sealed fit block as real_model and scored on the same scoring set, so the floor is measured on this
# content at this budget rather than inherited from 0003's builder-content battery.
FLOOR_ROLES = ["floor_majority", "floor_stratified", "floor_feat1", "floor_tree3"]
ROLES = ["real_model", "real_incumbent", "real_logistic"] + FLOOR_ROLES + ["builder_matched", "builder_chunk_matched"]
RECIPE_OF = {"real_model": "model", "real_incumbent": "incumbent", "real_logistic": "logistic_l3",
             "builder_matched": "model", "builder_chunk_matched": "model", "repro": "incumbent", "null": "model",
             "floor_majority": "floor_majority", "floor_stratified": "floor_stratified",
             "floor_feat1": "floor_feat1", "floor_tree3": "floor_tree3"}


def corpus_block(npz_rel, arr_hashes, y, g, fam, names, labels):
    """The corpus description the runner banks and the frozen reader compares against, key for key.

    It lives here rather than inline in main() so that the preregistration generator, the pre-freeze check and the
    mutation gate's control can all produce it by CALLING the runner instead of retyping its keys. 0020's pre-freeze
    review found four values sealed from the corpus manifest's BUILT counts (chunks selected) where the runner
    measures the counts of chunks that actually carry rows - 1035 against 1029 - each of which would have voided an
    honest run. Two copies of one wrong literal agree with each other; one copy cannot.
    """
    block = {"npz": npz_rel, "arrays": arr_hashes, "n_rows": int(len(y)),
             "n_chunks": int(np.unique(g).size), "families": list(names),
             "rows_per_family": {f: int((fam == f).sum()) for f in names},
             "chunks_per_family": {f: int(np.unique(g[fam == f]).size) for f in names},
             "chunk_id_min": int(g.min()), "chunk_id_max": int(g.max())}
    if labels:
        block["label_histogram"] = np.bincount(np.asarray(y), minlength=N_CONFIGS).tolist()
        block["majority_class_rate"] = round(float(np.bincount(np.asarray(y)).max() / max(len(y), 1)), 6)
    return block


def _array_sha(path, name):
    arr = npz_memmap(path, name)
    h = hashlib.sha256()
    for i in range(0, len(arr), 20000):
        h.update(np.ascontiguousarray(arr[i:i + 20000]).tobytes())
    return h.hexdigest(), list(arr.shape), str(arr.dtype)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["run"], default="run")
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0020-realfit-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--ext", default=os.path.join(REPO, "data", "pivot", "ext_c4096.npz"))
    ap.add_argument("--realfit", default=os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "realfit_4096_ckpt"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "realfit_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "realfit_4096_scores.json"))
    ap.add_argument("--smoke", action="store_true", help="tiny rows, scratchpad outputs only; the reader voids it")
    args = ap.parse_args()
    out_stem = os.path.splitext(os.path.basename(args.out))[0]
    art = os.path.join(REPO, "artifacts") + os.sep
    outputs = {"--workdir": args.workdir, "--out": args.out, "--scores-out": args.scores_out}
    under = {k: os.path.abspath(v).startswith(art) for k, v in outputs.items()}
    if args.smoke and any(under.values()):
        print(f"REFUSING: --smoke with an output path under artifacts/: {[k for k, v in under.items() if v]}", file=sys.stderr)
        return 3
    if not args.smoke and not all(under.values()):
        print(f"REFUSING: a real run must write every output under artifacts/: {[k for k, v in under.items() if not v]}",
              file=sys.stderr)
        return 3
    t_all = time.perf_counter()
    not_run_path = args.out[:-5] + "_not_run.json"

    prereg = json.load(open(args.prereg_file, encoding="utf-8"))
    if not args.smoke and prereg.get("frozen") is not True:
        print("REFUSING: a real run needs a frozen preregistration (the reader's literals are generated from it)", file=sys.stderr)
        return 3
    if not args.smoke:
        others = []
        for pid in os.listdir("/proc"):
            if not pid.isdigit() or int(pid) == os.getpid():
                continue
            try:
                parts = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
            except OSError:
                continue
            argv = [x.decode("utf-8", "replace") for x in parts if x]
            if argv and os.path.basename(argv[0]).startswith("python") and any("tools/pivot/run_" in a for a in argv[1:]):
                others.append(f"{pid}: {' '.join(argv)[:120]}")
        if others:
            print("REFUSING: another tools/pivot runner is alive: " + "; ".join(others), file=sys.stderr)
            return 3
    P = dict(prereg["scope"]["protocol"]); recipes = prereg["scope"]["recipes"]
    if args.smoke:
        P.update(prereg.get("smoke", {}))
    stamp = f"{prereg['id']}-{prereg['slug']}"
    seed = int(P["seed"]); eval_frac = float(P["eval_frac"]); top_rung = int(P["top_rung"]); caps = P["caps"]
    families = list(P["families"])
    if families != FAMILIES:
        print("REFUSING: the sealed builder family order is not the corpus family order", file=sys.stderr)
        return 3
    if list(P["ext_families"]) != EXT_FAMILIES or list(P["fit_families"]) != FIT_FAMILIES:
        print("REFUSING: a sealed family order is not the corpus module's order", file=sys.stderr)
        return 3
    if list(P["order"]) != ["repro", "null"] + ROLES or set(recipes) != {"incumbent", "logistic_l3", "model"} | set(FLOOR_ROLES):
        print(f"REFUSING: the sealed order must be {['repro', 'null'] + ROLES} with 0018's three recipes and the "
              f"four trivial-baseline recipes", file=sys.stderr)
        return 3
    env = environment()
    load1, load5, load15 = os.getloadavg()
    launch_env = {"env": env, "loadavg_1_5_15": [round(load1, 2), round(load5, 2), round(load15, 2)], "problems": []}
    if env["threads"] != P["threads"]:
        launch_env["problems"].append(f"threads {env['threads']} != preregistered {P['threads']}")
    if env["nice"] != P["nice"]:
        launch_env["problems"].append(f"nice {env['nice']} != preregistered {P['nice']}")
    for k, v in (P.get("environment") or {}).items():
        if env.get(k) != v:
            launch_env["problems"].append(f"{k} {env.get(k)!r} != preregistered {v!r}")
    if (env["disk_free_gb"] or 0) < P["launch"]["min_disk_free_gb"]:
        launch_env["problems"].append(f"disk free {env['disk_free_gb']} GB < {P['launch']['min_disk_free_gb']}")
    if (env["mem_available_gb"] or 0) < P["launch"]["min_mem_available_gb"]:
        launch_env["problems"].append(f"MemAvailable {env['mem_available_gb']} GB < {P['launch']['min_mem_available_gb']}")
    max_load = float(P["launch"].get("max_load1", 2.0))
    if not args.smoke and load1 > max_load:
        launch_env["problems"].append(f"1-minute load {load1:.2f} > {max_load}: the machine is not idle")
    launch_env["ok"] = not launch_env["problems"]
    if launch_env["problems"]:
        print("REFUSING TO LAUNCH: " + "; ".join(launch_env["problems"]), file=sys.stderr)
        return 3
    if os.path.exists(not_run_path) and not args.smoke:
        print(f"REFUSING: {os.path.relpath(not_run_path, REPO)} exists; this run was filed NOT RUN", file=sys.stderr)
        return 3

    # [1] corpus A (the builder's): y and g are read without touching X, which is memmapped
    with _zf.ZipFile(args.cache) as zf:
        names = zf.namelist()
        y = np.load(_io.BytesIO(zf.read("y.npy"))); g = np.load(_io.BytesIO(zf.read("g.npy")))
        has_meta = "carve.npy" in names
        if has_meta:
            cache_carve = int(np.load(_io.BytesIO(zf.read("carve.npy"))))
            cache_off = int(np.load(_io.BytesIO(zf.read("chunk_offset.npy"))))
            cache_cs = int(np.load(_io.BytesIO(zf.read("chunk_size.npy"))))
    cache_y_sha, cache_g_sha = _sha(y), _sha(g)
    if has_meta:
        if (cache_carve, cache_off, cache_cs) != (P["carve"], P["chunk_offset"], P["chunk_size"]):
            print(f"REFUSING: cache built at carve {cache_carve}, offset {cache_off}, chunk size {cache_cs}", file=sys.stderr)
            return 3
        carve_source = "cache metadata written at build time"
    else:
        ident = P.get("cache_identity") or {}
        if ident.get("y_sha256") != cache_y_sha or ident.get("g_sha256") != cache_g_sha:
            print("REFUSING: cache carries no build metadata and its y/g hashes are not the sealed cache_identity", file=sys.stderr)
            return 3
        cache_carve, cache_off, cache_cs = int(P["carve"]), int(P["chunk_offset"]), int(P["chunk_size"])
        carve_source = "sealed cache identity (sha256 of y and g); the cache carries no build metadata"
    X = npz_memmap(args.cache, "X"); ncols = X.shape[1]
    corpus = {"carve_bytes": cache_carve, "carve_bytes_source": carve_source, "chunk_size": cache_cs, "chunk_offset": cache_off,
              "chunk_id_min": int(g.min()), "chunk_id_max": int(g.max()), "n_source_chunks": int(np.unique(g).size),
              "cache_y_sha256": cache_y_sha, "cache_g_sha256": cache_g_sha, "n_rows": int(len(y)), "n_features": int(ncols)}
    print(f"[1] corpus A: {corpus}", flush=True)

    # [1b] the sealed extension corpus (0018's): scored, never fitted
    ext_sealed = dict(P["ext_corpus"]); ext_hashes = {}
    for name in ("X", "y", "g", "fam"):
        h, shape, dtype = _array_sha(args.ext, name)
        ext_hashes[name] = {"sha256": h, "shape": shape, "dtype": dtype}
    if args.smoke:
        ext_sealed = dict((prereg.get("smoke") or {}).get("ext_corpus") or {})
    mism = [n for n in ext_hashes if ext_hashes[n]["sha256"] != (ext_sealed.get("arrays") or {}).get(n, {}).get("sha256")]
    if mism:
        print(f"REFUSING: extension corpus arrays {mism} do not hash to the "
              f"{'smoke' if args.smoke else 'sealed'} ext_corpus.arrays", file=sys.stderr)
        return 3
    # [1c] the real-content FIT corpus (0020's): fitted, never scored
    fit_sealed = dict(P["fit_corpus"]); fit_hashes = {}
    for name in ("X", "y", "g", "fam"):
        h, shape, dtype = _array_sha(args.realfit, name)
        fit_hashes[name] = {"sha256": h, "shape": shape, "dtype": dtype}
    if args.smoke:
        fit_sealed = dict((prereg.get("smoke") or {}).get("fit_corpus") or {})
    mism = [n for n in fit_hashes if fit_hashes[n]["sha256"] != (fit_sealed.get("arrays") or {}).get(n, {}).get("sha256")]
    if mism:
        print(f"REFUSING: fit corpus arrays {mism} do not hash to the "
              f"{'smoke' if args.smoke else 'sealed'} fit_corpus.arrays", file=sys.stderr)
        return 3
    if args.smoke:
        sealed_fit_x = (((prereg["scope"]["protocol"].get("fit_corpus") or {}).get("arrays") or {}).get("X") or {}).get("sha256")
        sealed_ext_x = (((prereg["scope"]["protocol"].get("ext_corpus") or {}).get("arrays") or {}).get("X") or {}).get("sha256")
        if ext_hashes["X"]["sha256"] == sealed_ext_x or fit_hashes["X"]["sha256"] == sealed_fit_x:
            print("REFUSING: a smoke must never touch the sealed corpora", file=sys.stderr)
            return 3
        if int(P["repro_rows"]) > 20000 or int(P["matched_rows"]) > 20000:
            print("REFUSING: a smoke fits at most 20000 rows per arm", file=sys.stderr)
            return 3

    Xx = np.load(_io.BytesIO(_zf.ZipFile(args.ext).read("X.npy"))).astype(np.float32, copy=False)
    with _zf.ZipFile(args.ext) as zf:
        yx = np.load(_io.BytesIO(zf.read("y.npy"))); gx = np.load(_io.BytesIO(zf.read("g.npy")))
        famx = np.load(_io.BytesIO(zf.read("fam.npy")))
        ext_names = [str(s) for s in np.load(_io.BytesIO(zf.read("families.npy")))]
        ext_src = set(str(v) for v in np.load(_io.BytesIO(zf.read("meta_src_sha256.npy")), allow_pickle=False))
    Xr = np.load(_io.BytesIO(_zf.ZipFile(args.realfit).read("X.npy"))).astype(np.float32, copy=False)
    with _zf.ZipFile(args.realfit) as zf:
        yr = np.load(_io.BytesIO(zf.read("y.npy"))); gr = np.load(_io.BytesIO(zf.read("g.npy")))
        famr = np.load(_io.BytesIO(zf.read("fam.npy")))
        fit_names = [str(s) for s in np.load(_io.BytesIO(zf.read("families.npy")))]
        fit_src = set(str(v) for v in np.load(_io.BytesIO(zf.read("meta_src_sha256.npy")), allow_pickle=False))
    if ext_names != list(P["ext_families"]) or fit_names != list(P["fit_families"]):
        print("REFUSING: a corpus family order differs from the sealed one", file=sys.stderr)
        return 3
    if Xx.shape[1] != ncols or Xr.shape[1] != ncols:
        print("REFUSING: a corpus feature width differs from the builder's", file=sys.stderr)
        return 3
    fam_x = np.array(ext_names)[famx]; fam_r = np.array(fit_names)[famr]
    ext = corpus_block(os.path.relpath(args.ext, REPO), ext_hashes, yx, gx, fam_x, ext_names, labels=False)
    fit = corpus_block(os.path.relpath(args.realfit, REPO), fit_hashes, yr, gr, fam_r, fit_names, labels=True)
    print(f"[1b] sealed evaluation corpus: {ext['n_rows']} rows, {ext['n_chunks']} chunks", flush=True)
    print(f"[1c] real-content fit corpus: {fit['n_rows']} rows, {fit['n_chunks']} chunks, {fit['rows_per_family']}", flush=True)

    # [2] the sealed split (0003's by construction): the evaluation set and the pool the two builder arms draw from
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e = fam_all[ev]
    ev_chunks = np.unique(g[ev])
    repro_rows = tr[:int(P["repro_rows"])]
    matched_rows = tr[:int(P["matched_rows"])]
    # The plaintext-matched builder block: every pool row of the first N pool chunks in pool order, where N is the
    # number of source chunks the fit corpus actually contributes rows from. builder_matched matches the fit
    # corpus's ROW budget (26346 rows over 19413 builder plaintexts); this arm matches its PLAINTEXT budget. The
    # two together bracket the rival explanation "the fit corpus is too small to learn anything", which neither
    # closes alone, because 0003's curve moves on plaintexts and not on rows.
    _seen, _order = set(), []
    for _v in g[tr]:
        _v = int(_v)
        if _v not in _seen:
            _seen.add(_v); _order.append(_v)
            if len(_order) >= int(P["chunk_matched_chunks"]):
                break
    _first_chunks = set(_order)
    chunk_matched_rows = tr[np.fromiter((int(v) in _first_chunks for v in g[tr]), bool, len(tr))]
    fit_order = np.random.default_rng(seed).permutation(len(yr))   # the recipe's last-10% validation split is then a random 10%
    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam_e != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev), "eval_y_sha256": _sha(np.asarray(y[ev])),
                 "eval_g_sha256": _sha(np.asarray(g[ev])),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64)),
                 "families": families,
                 "repro_rows": int(len(repro_rows)), "repro_idx_sha256": _sha(repro_rows),
                 "repro_sorted_sha256": _sha(np.sort(repro_rows).astype(np.int64)),
                 "matched_rows": int(len(matched_rows)), "matched_idx_sha256": _sha(matched_rows),
                 "matched_sorted_sha256": _sha(np.sort(matched_rows).astype(np.int64)),
                 "fit_rows": int(len(fit_order)), "fit_idx_sha256": _sha(fit_order),
                 "fit_sorted_sha256": _sha(np.sort(fit_order).astype(np.int64)),
                 "fit_order_rule": f"np.random.default_rng({seed}).permutation of the fit corpus's rows, so the recipes' "
                                   "last-10% validation split is a random tenth rather than one family",
                 "pool_chunks_shared_with_ext": int(np.intersect1d(np.unique(g[tr]), np.unique(gx)).size),
                 "eval_chunks_shared_with_ext": int(np.intersect1d(ev_chunks, np.unique(gx)).size),
                 "fit_chunks_shared_with_ext": int(np.intersect1d(np.unique(gr), np.unique(gx)).size),
                 "fit_chunks_shared_with_builder": int(np.intersect1d(np.unique(gr), np.unique(g)).size),
                 "fit_source_chunks_shared_with_ext": int(len(fit_src & ext_src)),
                 "n_fit_source_chunks": int(len(fit_src)), "n_ext_source_chunks": int(len(ext_src)),
                 # Distinct source chunks (plaintexts) behind each fit block. The row budget and the plaintext
                 # budget are different axes and 0003's curve moves on the second one, so both are banked and the
                 # reader states them beside every reading (0020 pre-freeze review, three lenses).
                 "repro_block_chunks": int(np.unique(g[repro_rows]).size),
                 "matched_block_chunks": int(np.unique(g[matched_rows]).size),
                 "chunk_matched_block_chunks": int(np.unique(g[chunk_matched_rows]).size),
                 "chunk_matched_rows": int(len(chunk_matched_rows)),
                 "chunk_matched_idx_sha256": _sha(chunk_matched_rows),
                 "chunk_matched_sorted_sha256": _sha(np.sort(chunk_matched_rows).astype(np.int64)),
                 "fit_block_chunks": int(np.unique(gr).size)}
    # Row identity, measured rather than assumed (0018's review): no scored row may sit in a fit block. Every scored
    # row is digested once; the fit corpus and the two builder fit blocks are then checked against those digests.
    t_id = time.perf_counter()
    scored_digests = {hashlib.blake2b(np.ascontiguousarray(Xx[i], dtype=np.float32).tobytes(), digest_size=16).digest()
                      for i in range(len(Xx))}
    for i in range(0, len(ev), 20000):
        blk = np.ascontiguousarray(X[np.sort(ev)[i:i + 20000], :ncols], dtype=np.float32)
        for j in range(len(blk)):
            scored_digests.add(hashlib.blake2b(blk[j].tobytes(), digest_size=16).digest())

    def _identical_rows_of(arr, rows=None):
        n_same = 0
        if rows is None:
            for i in range(len(arr)):
                if hashlib.blake2b(np.ascontiguousarray(arr[i], dtype=np.float32).tobytes(), digest_size=16).digest() in scored_digests:
                    n_same += 1
            return int(n_same)
        order = np.sort(np.asarray(rows))
        for i in range(0, len(order), 20000):
            blk = np.ascontiguousarray(arr[order[i:i + 20000], :ncols], dtype=np.float32)
            for j in range(len(blk)):
                if hashlib.blake2b(blk[j].tobytes(), digest_size=16).digest() in scored_digests:
                    n_same += 1
        return int(n_same)
    partition["fit_rows_identical_to_a_scored_row"] = _identical_rows_of(Xr)
    partition["repro_rows_identical_to_a_scored_row"] = _identical_rows_of(X, repro_rows)
    partition["matched_rows_identical_to_a_scored_row"] = _identical_rows_of(X, matched_rows)
    partition["row_identity_digest"] = "blake2b-128 of the contiguous float32 feature row, over every scored row"
    print(f"[2] row identity scan: fit {partition['fit_rows_identical_to_a_scored_row']}, repro "
          f"{partition['repro_rows_identical_to_a_scored_row']}, matched {partition['matched_rows_identical_to_a_scored_row']} "
          f"rows are byte-identical to a scored row ({time.perf_counter() - t_id:.0f}s)", flush=True)
    if not args.smoke and partition["pool_idx_sha256"] != P["pool_idx_sha256"]:
        print(f"REFUSING: the pool hashes to {partition['pool_idx_sha256'][:12]}..., not the sealed "
              f"{P['pool_idx_sha256'][:12]}...", file=sys.stderr)
        return 3
    if not args.smoke and (partition["fit_source_chunks_shared_with_ext"] or partition["fit_chunks_shared_with_ext"]
                           or partition["fit_chunks_shared_with_builder"]):
        print("REFUSING: the fit corpus shares a chunk id or a source chunk with a scored corpus", file=sys.stderr)
        return 3
    # The preregistration says the runner REQUIRES these counts to be zero, not merely that it measures them
    # (0020 pre-freeze review, runner lens, finding 4). A leak found here costs ten seconds; found by the reader
    # it costs the whole run.
    if not args.smoke and (partition["fit_rows_identical_to_a_scored_row"]
                           or partition["repro_rows_identical_to_a_scored_row"]
                           or partition["matched_rows_identical_to_a_scored_row"]):
        print("REFUSING: a fit, repro or matched row is byte-identical to a scored row", file=sys.stderr)
        return 3
    # The four sealed block hashes: the runner must notice a divergent permutation now, not the reader an hour later
    # (same review, finding 5).
    if not args.smoke:
        bad = [k for k, v in (P.get("fit_block_hashes") or {}).items() if partition.get(k) != v]
        if bad:
            print(f"REFUSING: the fit blocks {bad} do not hash to the sealed fit_block_hashes", file=sys.stderr)
            return 3
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, pool "
          f"{partition['n_pool_rows']}, repro {partition['repro_rows']}, matched {partition['matched_rows']}, fit "
          f"{partition['fit_rows']}", flush=True)

    store = Store(args.workdir)
    proto_sha = sha_obj(prereg["scope"]["protocol"]); recipes_sha = sha_obj(recipes)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "stage": "run", "protocol": prereg["scope"]["protocol"], "protocol_sha256": proto_sha,
              "recipes": recipes, "recipes_sha256": recipes_sha, "corpus": corpus, "ext_corpus": ext, "fit_corpus": fit,
              "partition": partition, "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
              "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    names_expected = ["repro", "null"] + ROLES

    started = _utc()
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev]); n_eval = int(len(ev)); n_ext = int(len(yx))
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}
    r4 = lambda v: round(float(v), 4)  # noqa: E731

    def readings(name):
        """Split one per-example vector into the builder-evaluation reading and the extension readings."""
        v = per_ex.get(name)
        if v is None or len(v) != n_eval + n_ext:
            return None
        rep, ex = v[:n_eval], v[n_eval:]
        return {"builder_eval_top1": r4(rep.mean()), "builder_eval_correct": int(rep.sum()),
                "ext_top1": r4(ex.mean()), "ext_correct": int(ex.sum()), "n_ext_rows": n_ext,
                "ext_per_family": {f: r4(ex[fam_x == f].mean()) for f in ext_names},
                "ext_per_family_correct": {f: int(ex[fam_x == f].sum()) for f in ext_names},
                "ext_structured_text_top1": r4(ex[np.isin(fam_x, STRUCTURED_TEXT)].mean()),
                "ext_high_entropy_top1": r4(ex[np.isin(fam_x, HIGH_ENTROPY)].mean()),
                "ext_real_top1": r4(ex[np.isin(fam_x, REAL_FAMILIES)].mean()),
                "ext_real_correct": int(ex[np.isin(fam_x, REAL_FAMILIES)].sum()),
                "n_ext_real_rows": int(np.isin(fam_x, REAL_FAMILIES).sum()),
                "ext_synthetic_correct": int(ex[np.isin(fam_x, SYNTH_FAMILIES)].sum()),
                "ext_synthetic_top1": r4(ex[np.isin(fam_x, SYNTH_FAMILIES)].mean()),
                "builder_eval_per_family": {f: r4(rep[fam_e == f].mean()) for f in families}}

    def assemble(complete, launch_no, ci=None):
        reads = {n: readings(n) for n in names_expected if per_ex.get(n) is not None}
        rm = reads.get("real_model") or {}
        doc = dict(common, complete=bool(complete),
                   missing_roles=[n for n in names_expected if n not in records],
                   environment=environment(), launch_environment=launch_env, launch_number=launch_no,
                   fits=records, readings=reads,
                   ext_real_top1={n: (reads[n] or {}).get("ext_real_top1") for n in reads},
                   ext_real_correct={n: (reads[n] or {}).get("ext_real_correct") for n in reads},
                   ext_top1={n: (reads[n] or {}).get("ext_top1") for n in reads},
                   ext_correct={n: (reads[n] or {}).get("ext_correct") for n in reads},
                   builder_eval_top1={n: (reads[n] or {}).get("builder_eval_top1") for n in reads},
                   ext_per_family={n: (reads[n] or {}).get("ext_per_family") for n in reads},
                   ext_real_top1_model=rm.get("ext_real_top1"), ext_real_correct_model=rm.get("ext_real_correct"),
                   ext_top1_model=rm.get("ext_top1"), ext_correct_model=rm.get("ext_correct"),
                   n_ext_real_rows=rm.get("n_ext_real_rows"), n_ext_rows=n_ext, n_eval_rows=n_eval,
                   ext_real_families=list(REAL_FAMILIES), ext_synthetic_families=list(SYNTH_FAMILIES),
                   fit_families=list(fit_names), fit_rows_per_family=fit["rows_per_family"],
                   reproduction_top1=(reads.get("repro") or {}).get("builder_eval_top1"),
                   reference_top1=dict(P["reference_top1"]),
                   shuffled_label_accuracy_ext=(reads.get("null") or {}).get("ext_top1"),
                   shuffled_label_accuracy_eval=(reads.get("null") or {}).get("builder_eval_top1"),
                   null_control=records.get("null"),
                   fit_info_by_name={n: (records.get(n) or {}).get("fit_info") for n in names_expected},
                   ledger=store.ledger(),
                   fit_record_top1_is="each fit record's top1 and top1_non_gutenberg are over the concatenated "
                                      f"{n_eval} + {n_ext} scoring set; per_family is over the sealed evaluation "
                                      "rows only, because extension rows carry an 'ext:' family prefix",
                   cluster_ci95_informational=ci or {},
                   cluster_ci95_note="95% cluster-bootstrap intervals over source chunks (2000 resamples), informational",
                   cost={"wall_seconds_this_invocation": round(time.perf_counter() - t_all, 1),
                         "seconds_by_name": {k: v.get("seconds") for k, v in records.items()},
                         "interruptions_by_name": {k: v.get("interruptions_before_this_fit") for k, v in records.items()},
                         "banked_fit_seconds_total": round(sum((v.get("seconds") or 0) for v in records.values()), 1),
                         "checkpoints": os.path.relpath(args.workdir, REPO)},
                   run_started_utc=started, first_launch_utc=first_launch, run_finished_utc=_utc() if complete else None)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, sort_keys=True); fh.write("\n")
        os.replace(args.out + ".tmp", args.out)
        with open(args.scores_out + ".tmp", "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_scores/1", "preregistration": stamp, "smoke": bool(args.smoke),
                       "n_eval_rows": n_eval, "n_ext_rows": n_ext, "eval_idx_sha256": partition["eval_idx_sha256"],
                       "eval_chunk_ids": ge.tolist(), "ext_chunk_ids": gx.tolist(), "ext_fam": famx.tolist(),
                       "ext_families": ext_names, "ext_arrays_sha256": {k: v["sha256"] for k, v in ext_hashes.items()},
                       "fit_arrays_sha256": {k: v["sha256"] for k, v in fit_hashes.items()},
                       "layout": "each per_example vector is [sealed evaluation rows (n_eval_rows)] + [extension rows (n_ext_rows)]",
                       "per_example": {k: v.tolist() for k, v in per_ex.items()}}, fh)
        os.replace(args.scores_out + ".tmp", args.scores_out)
        return doc

    try:
        any_ckpt = any(f.endswith(".json") for f in os.listdir(args.workdir))
        launch_no = store.launches("run", any_ckpt)
        with open(os.path.join(args.workdir, "launches.jsonl")) as fh:
            first_launch = json.loads(fh.readline())["utc"]
        Xs = np.empty((n_eval + n_ext, ncols), np.float32)
        fill_f32(Xs[:n_eval], X, ev, ncols); Xs[n_eval:] = Xx
        del Xx
        ys = np.concatenate([ye, np.asarray(yx)]); fam_s = np.concatenate([fam_e, np.array(["ext:" + f for f in fam_x])])
        print(f"[run] scoring set {n_eval} + {n_ext} rows materialised, anonymous RSS {_rss_gb():.2f} GB "
              f"(total {_rss_total_gb():.2f} GB)", flush=True)

        def fit_arm(name, rows_arr, rows, y_all, g_all, stage, rows_sha):
            cand = recipes[RECIPE_OF[name]]
            fp = fingerprint(prereg=stamp, seed=seed, role=name, cand=cand, stage=stage, rows=rows_sha,
                             eval=partition["eval_idx_sha256"], ext=ext_hashes["X"]["sha256"],
                             fit=fit_hashes["X"]["sha256"])
            block = None if store.load(name, fp) is not None else Block(rows_arr, rows, ncols, name)
            r, pe = run_fit(store, name, fp, name, cand, seed, block, y_all, g_all, Xs, ys, fam_s, stage, caps,
                            keep_per_example=True, confirmatory=True)
            del block
            records[name] = dict(r, fingerprint=fp,
                                 per_example_sha256=(hashlib.sha256(np.asarray(pe, np.int8).tobytes()).hexdigest()
                                                     if pe is not None else None))
            if pe is not None:
                per_ex[name] = pe
            rd = readings(name)
            if rd:
                print(f"      {name:<16} BUILDER EVAL {rd['builder_eval_top1']} | EXTENSION {rd['ext_top1']} "
                      f"({rd['ext_correct']}/{n_ext}; real families {rd['ext_real_correct']}/{rd['n_ext_real_rows']}) "
                      f"{rd['ext_per_family']}", flush=True)
            assemble(False, launch_no)
            if rd and not args.smoke:
                chance = 1.0 / N_CONFIGS
                if name == "null":
                    tol = float(P["null_tolerance"])
                    if rd["ext_top1"] > chance + tol or rd["builder_eval_top1"] > chance + tol:
                        raise NotRun(f"null control read {rd['ext_top1']} on the extension rows and {rd['builder_eval_top1']} "
                                     f"on the sealed evaluation rows against chance {chance:.6f} + {tol}: the scoring path leaks")
                if name == "repro":
                    drift = round(abs(rd["builder_eval_top1"] - float(P["reference_top1"]["repro"])), 6)
                    if drift > float(P["reproduction_tolerance"]):
                        raise NotRun(f"the reproduction rung read {rd['builder_eval_top1']} against the banked "
                                     f"{P['reference_top1']['repro']} (drift {drift} > {P['reproduction_tolerance']}): the pool, "
                                     f"the evaluation set or the machinery is not 0003's")
            return r

        for step in P["order"]:
            if step == "repro":
                fit_arm("repro", X, repro_rows, y, g, "pool_rung", partition["repro_sorted_sha256"])
            elif step == "null":
                y_sh = np.asarray(yr).copy(); rng.shuffle(y_sh)
                partition["null_y_shuffled_sha256"] = _sha(y_sh)
                partition["null_labels_permuted"] = bool(not np.array_equal(y_sh, np.asarray(yr)))
                partition["null_labels_same_multiset"] = bool(np.array_equal(np.sort(y_sh), np.sort(np.asarray(yr))))
                if not args.smoke and not (partition["null_labels_permuted"] and partition["null_labels_same_multiset"]):
                    raise NotRun("the null control's labels are not a permutation of the fit corpus's own labels")
                fit_arm("null", Xr, fit_order, y_sh, gr, "fit_null", partition["fit_sorted_sha256"])
            elif step in ("real_model", "real_incumbent", "real_logistic"):
                fit_arm(step, Xr, fit_order, yr, gr, "realfit", partition["fit_sorted_sha256"])
            elif step in FLOOR_ROLES:
                fit_arm(step, Xr, fit_order, yr, gr, "realfit_floor", partition["fit_sorted_sha256"])
            elif step == "builder_matched":
                fit_arm(step, X, matched_rows, y, g, "pool_matched", partition["matched_sorted_sha256"])
            elif step == "builder_chunk_matched":
                fit_arm(step, X, chunk_matched_rows, y, g, "pool_chunk_matched",
                        partition["chunk_matched_sorted_sha256"])
            else:
                raise NotRun(f"unknown order step {step!r}")
        ci = {}
        for n in names_expected:
            v = per_ex.get(n)
            if v is None:
                continue
            ex = v[n_eval:]
            ci[f"{n}_ext"] = cluster_ci(ex, gx, seed=seed)
            ci[f"{n}_ext_real"] = cluster_ci(ex[np.isin(fam_x, REAL_FAMILIES)], gx[np.isin(fam_x, REAL_FAMILIES)], seed=seed)
            for f in ext_names:
                m = fam_x == f
                ci[f"{n}_ext_{f}"] = cluster_ci(ex[m], gx[m], seed=seed)
            ci[f"{n}_builder_eval"] = cluster_ci(v[:n_eval], ge, seed=seed)
        out = assemble(True, launch_no, ci=ci)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "run", "reason": str(e),
                       "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])}, fh, indent=2)
        return 4
    print(f"[run] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; real_model on the "
          f"real families {out['ext_real_correct_model']}/{out['n_ext_real_rows']} ({out['ext_real_top1_model']}), "
          f"reproduction {out['reproduction_top1']}, null on extension {out['shuffled_label_accuracy_ext']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
