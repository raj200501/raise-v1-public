#!/usr/bin/env python3
"""A scaling curve on REAL plaintexts at 4096 (preregistration 0023).

Question. 0021 read REAL_FIT_FAILS: fitted on 26346 rows from 1029 plaintexts of real content, 0014's searched
model reads 0.1193 on the 38452 sealed real-family rows, a depth-3 tree 0.0929 and the standardised logistic
0.1179. 0022 read REAL_RECIPE_FAILS: searching the recipe on that content moved nothing (model -0.0004,
logistic +0.0003). Both left one excuse open, named in 0022's what_this_does_not_cover: the BUDGET. Does the
signal on real content rise with the volume of real plaintexts at all - and does the boosted model rise faster
than the linear rule? This is the FDM-1 question (quality against manufactured-label volume) asked of real
content, with the only real content the record has: 0021's fit block, cut into nested rungs.

Design. One fit corpus (0021's, sealed by array hash), one seed, 0021's three FIXED recipes (M4, L3, D1: 0022
showed the search is immaterial), four nested rungs of PLAINTEXTS: per family, a seeded permutation of the fit
block's chunk ids with rows; rung d takes the first ceil(n_f / d) of them for d in the sealed denominators
(8, 4, 2, 1), so every rung has the fit block's family mix and rung d's chunks are a subset of rung d/2's; a
rung's rows are those chunks' rows in 0021's fit-block order, so the top rung IS 0021's fit block row for row
and the recipes' last-10% validation split is what 0021 fitted. Every fit is scored once on 0018's and 0021's
scoring set (the sealed 260000-row evaluation set plus the whole 61409-row extension corpus); the curve is each
role's top-1 on the 38452 real-family rows against log2(plaintexts), an ordinary-least-squares slope in accuracy
per doubling of plaintexts, with a cluster bootstrap over scored chunks (the same resamples for every rung and
every role, so role differences are paired).

Order, sealed: the null control first (the model recipe on the top rung with 0021's permuted labels, hash for
hash, first so the generator state is 0021's), then the TOP rung's three roles (the reproduction of 0021's
three banked readings, within tolerance, before a new number exists), then the lower rungs ascending, the
model last within each rung, and last an informational REPLICATE of the smallest rung under a second seeded
nesting (the same rule, a different permutation of each family's chunks), so that the fit-side variance the
scored-chunk bootstrap cannot see is read directly where it is largest. The artifact is re-assembled after
every role, so an abandoned run reads VOID.

Everything the script does is read from prereg["scope"]["curve"] (sealed by the chain). It banks what it
actually did - rung row and chunk counts, index hashes, nesting checks, per-role records, the ledger, the
environment - and the frozen reader compares those against the constants sealed in it and recounts every
reading, the slope and the bootstrap from the banked per-example vectors.

Reuses tools/pivot/run_recipe_search.py's machinery (blocks, fits, checkpoints, heartbeat, memory accounting,
launch rules), tools/pivot/run_realfit.py's corpora and row-identity scan and tools/pivot/run_realsearch.py's
per-family scorer. Digest convention as in those: sha256 of np.ascontiguousarray(a).tobytes(); index arrays are
int64 in their order; y int16, g int32; sorted sets np.sort(...).astype(np.int64).
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
import run_recipe_search as _rrs  # noqa: E402
from run_recipe_search import (  # noqa: E402
    REPO, _sha, sha_obj, _utc, fingerprint, environment, npz_memmap, fill_f32, Block, run_fit, Store, NotRun,
    cluster_ci, _rss_gb, _rss_total_gb, grouped_split, FAMILIES, N_CONFIGS, CONFIG_NAMES)
from run_realfit import corpus_block, _array_sha, STRUCTURED_TEXT, HIGH_ENTROPY  # noqa: E402
from run_realsearch import score_by_family  # noqa: E402  (installs itself as run_recipe_search.score)
from corpus_ext import EXT_FAMILIES, REAL_FAMILIES, SYNTH_FAMILIES  # noqa: E402
from corpus_realfit import FAMILIES as FIT_FAMILIES  # noqa: E402

_rrs.score = score_by_family   # per_family over the families PRESENT in the scoring set (0022's convention)

ROLES = ["depth3_tree", "logistic", "model"]     # per rung, in this order: the model last


REPLICATE = "rep1"      # the smallest rung cut again under a second seeded nesting; informational, fitted last


def sealed_order(n_rungs):
    """null, the top rung's three roles (the reproduction of 0021), the lower rungs ascending, then the replicate."""
    return (["null"] + [f"r{n_rungs}_{r}" for r in ROLES] + [f"r{k}_{r}" for k in range(1, n_rungs) for r in ROLES]
            + [f"{REPLICATE}_{r}" for r in ROLES])


def parse_name(name, n_rungs):
    """'null' -> (n_rungs, 'null'); 'r2_model' -> (2, 'model'); 'rep1_model' -> ('rep1', 'model')."""
    if name == "null":
        return n_rungs, "null"
    rung, role = name.split("_", 1)
    return (REPLICATE if rung == REPLICATE else int(rung[1:])), role


def ols_slope(xs, ys):
    x = np.asarray(xs, np.float64); y = np.asarray(ys, np.float64); xm = x - x.mean()
    return float((xm * (y - y.mean())).sum() / (xm * xm).sum())


def slope_bootstrap(correct_by_role, log2x, chunk_ids, n_boot, seed):
    """Cluster bootstrap over scored chunks of each role's OLS slope against log2(plaintexts). One resample of chunks
    serves every rung and every role, so the per-resample slopes are paired across roles. Rung accuracies inside a
    resample are rounded to 4 decimals, as the banked readings are. Returns {role: slopes[n_boot]}."""
    _, inv = np.unique(chunk_ids, return_inverse=True); counts = np.bincount(inv).astype(np.float64)
    sums = {r: [np.bincount(inv, weights=np.asarray(c, np.float64), minlength=len(counts)) for c in vecs]
            for r, vecs in correct_by_role.items()}
    rng = np.random.default_rng(seed); n = len(counts)
    x = np.asarray(log2x, np.float64); xm = x - x.mean(); den = float((xm * xm).sum())
    out = {r: np.empty(n_boot) for r in correct_by_role}
    for b in range(n_boot):
        idx = rng.integers(0, n, n); tot = counts[idx].sum()
        for r, s in sums.items():
            accs = np.array([round(float(v[idx].sum() / tot), 4) for v in s])
            out[r][b] = float((xm * (accs - accs.mean())).sum() / den)
    return out


def rung_partition(yr, gr, fam_r, fit_names, seed, denominators):
    """0021's fit block and the nested rungs cut from it, with every hash and count the runner banks. Module-level so the
    preregistration generator and the pre-freeze check CALL it rather than retype it (docs/OPERATING_RULES.md section 4).

    Returns (fit_order, rung_rows, replicate_rows, keys). fit_order is 0021's fit block row for row (the seeded permutation
    of the corpus's rows). Per family, np.random.default_rng([seed, family_index + 1]) permutes that family's chunk ids WITH
    ROWS; rung d takes the first ceil(n_f / d) of them; a rung's rows are the fit-block rows of its chunks, in fit-block
    order. The replicate cuts the smallest rung again under np.random.default_rng([seed, family_index + 1, 1])."""
    fit_order = np.random.default_rng(seed).permutation(len(yr))
    gr = np.asarray(gr); fam = np.asarray(fam_r); g_o = gr[fit_order]; fam_o = fam[fit_order]
    perm = {}; perm_rep = {}
    for i, f in enumerate(fit_names):
        chunks = np.sort(np.unique(gr[fam == f])).astype(np.int64)
        # entropy words [seed, family_index + 1]: a second word of 0 would give the fit-block permutation's own stream
        # (SeedSequence pads short entropy with zeros; 0023 pre-freeze review, runner lens, finding 1)
        perm[f] = chunks[np.random.default_rng([int(seed), i + 1]).permutation(len(chunks))]
        perm_rep[f] = chunks[np.random.default_rng([int(seed), i + 1, 1]).permutation(len(chunks))]
    rungs = []; rows_by_rung = []; prev = None; nested = True; increasing = True
    for k, d in enumerate(denominators, start=1):
        take = {f: int(np.ceil(len(perm[f]) / int(d))) for f in fit_names}
        chosen = np.sort(np.concatenate([perm[f][:take[f]] for f in fit_names])).astype(np.int64)
        in_rung = np.isin(g_o, chosen); rows = fit_order[in_rung]
        if prev is not None:
            nested = nested and bool(np.isin(prev, chosen).all()); increasing = increasing and chosen.size > prev.size
        rungs.append({"rung": k, "denominator": int(d), "n_chunks": int(chosen.size), "n_rows": int(len(rows)),
                      "chunks_per_family": take, "rows_per_family": {f: int((fam_o[in_rung] == f).sum()) for f in fit_names},
                      "log2_chunks": round(float(np.log2(chosen.size)), 6),
                      "idx_sha256": _sha(rows), "sorted_sha256": _sha(np.sort(rows).astype(np.int64)),
                      "chunks_sha256": _sha(chosen)})
        rows_by_rung.append(rows); prev = chosen
    # the replicate of the smallest rung: the same rule and denominator, the second nesting
    d0 = int(denominators[0]); take0 = {f: int(np.ceil(len(perm_rep[f]) / d0)) for f in fit_names}
    chosen_rep = np.sort(np.concatenate([perm_rep[f][:take0[f]] for f in fit_names])).astype(np.int64)
    in_rep = np.isin(g_o, chosen_rep); rep_rows = fit_order[in_rep]
    first = np.sort(np.concatenate([perm[f][:take0[f]] for f in fit_names])).astype(np.int64)
    replicate = {"rung": REPLICATE, "replicates_rung": 1, "denominator": d0, "n_chunks": int(chosen_rep.size), "n_rows": int(len(rep_rows)),
                 "chunks_per_family": take0, "rows_per_family": {f: int((fam_o[in_rep] == f).sum()) for f in fit_names},
                 "log2_chunks": round(float(np.log2(chosen_rep.size)), 6),
                 "idx_sha256": _sha(rep_rows), "sorted_sha256": _sha(np.sort(rep_rows).astype(np.int64)),
                 "chunks_sha256": _sha(chosen_rep), "chunks_shared_with_rung_1": int(np.isin(chosen_rep, first).sum()),
                 "rule": "the smallest rung's rule and denominator under np.random.default_rng([seed, family_index + 1, 1]); "
                         "informational: a direct reading of how much the smallest rung moves under a second draw of plaintexts"}
    keys = {"fit_rows": int(len(fit_order)), "fit_idx_sha256": _sha(fit_order),
            "fit_sorted_sha256": _sha(np.sort(fit_order).astype(np.int64)),
            "fit_order_rule": f"np.random.default_rng({seed}).permutation of the fit corpus's rows, so the recipes' "
                              "last-10% validation split is a random tenth rather than one family (0021's fit block)",
            "fit_block_chunks": int(np.unique(gr).size),
            "fit_chunks_per_family": {f: int(len(perm[f])) for f in fit_names},
            "rung_rule": "stratified_nested_by_family_chunk: per family, np.random.default_rng([seed, family_index + 1]) permutes "
                         "its chunk ids with rows; rung d takes the first ceil(n_f / d); rows are the fit block's rows of those "
                         "chunks in fit-block order",
            "denominators": [int(d) for d in denominators], "n_rungs": len(rungs), "rungs": rungs, "replicate_rung_1": replicate,
            "rungs_nested": bool(nested), "rung_chunks_strictly_increasing": bool(increasing),
            "top_rung_is_fit_block": rungs[-1]["idx_sha256"] == _sha(fit_order),
            "doublings_spanned": round(rungs[-1]["log2_chunks"] - rungs[0]["log2_chunks"], 6)}
    return fit_order, rows_by_rung, rep_rows, keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["run"], default="run")
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0023-realcurve-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--ext", default=os.path.join(REPO, "data", "pivot", "ext_c4096.npz"))
    ap.add_argument("--realfit", default=os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "realcurve_4096_ckpt"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "realcurve_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "realcurve_4096_scores.json"))
    ap.add_argument("--smoke", action="store_true",
                    help="override the corpora with the prereg file's 'smoke' block; every output is stamped "
                         "smoke=true, written only to the scratchpad, and the reader VOIDs it")
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
    curve = prereg["scope"]["curve"]
    P = dict(curve["protocol"]); recipes = curve["recipes"]
    if args.smoke:
        P.update(prereg.get("smoke", {}))
    stamp = f"{prereg['id']}-{prereg['slug']}"
    seed = int(P["seed"]); eval_frac = float(P["eval_frac"]); top_rung = int(P["top_rung"]); caps = P["caps"]
    denominators = [int(d) for d in P["denominators"]]; n_rungs = len(denominators)
    if list(P["families"]) != FAMILIES or list(P["ext_families"]) != EXT_FAMILIES or list(P["fit_families"]) != FIT_FAMILIES:
        print("REFUSING: a sealed family order is not the corpus module's order", file=sys.stderr)
        return 3
    if set(recipes) != set(ROLES) or set(P["recipe_ids"]) != set(ROLES) or any(recipes[r]["id"] != P["recipe_ids"][r] for r in ROLES):
        print(f"REFUSING: the sealed recipes must be the roles {ROLES} carrying the sealed recipe_ids", file=sys.stderr)
        return 3
    if n_rungs < 2 or any(denominators[i] <= denominators[i + 1] for i in range(n_rungs - 1)) or denominators[-1] != 1:
        print("REFUSING: denominators must be strictly decreasing and end at 1 (the top rung is the whole fit block)", file=sys.stderr)
        return 3
    if list(P["order"]) != sealed_order(n_rungs):
        print(f"REFUSING: the sealed order must be {sealed_order(n_rungs)}", file=sys.stderr)
        return 3
    if set(P["reference_top1"]) != set(ROLES):
        print("REFUSING: reference_top1 must name 0021's reading for each of the three roles", file=sys.stderr)
        return 3
    if list(P.get("roles", [])) != ROLES or P.get("null_rows") != "all":
        print(f"REFUSING: the sealed roles must be {ROLES} and null_rows 'all'", file=sys.stderr)
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
    launch_env["loadavg_waited_seconds"] = 0
    if not args.smoke and load1 > max_load:
        for _ in range(20):          # wait for the box to settle rather than refuse on the first sample (0022's rule)
            time.sleep(15); launch_env["loadavg_waited_seconds"] += 15
            load1, load5, load15 = os.getloadavg()
            if load1 <= max_load:
                break
        launch_env["loadavg_1_5_15"] = [round(load1, 2), round(load5, 2), round(load15, 2)]
        if load1 > max_load:
            launch_env["problems"].append(f"1-minute load {load1:.2f} > {max_load} after waiting {launch_env['loadavg_waited_seconds']} s: "
                                          f"the machine is not idle")
    launch_env["ok"] = not launch_env["problems"]
    if launch_env["problems"]:
        print("REFUSING TO LAUNCH: " + "; ".join(launch_env["problems"]), file=sys.stderr)
        return 3
    if os.path.exists(not_run_path) and not args.smoke:
        print(f"REFUSING: {os.path.relpath(not_run_path, REPO)} exists; this run was filed NOT RUN", file=sys.stderr)
        return 3
    if not args.smoke and os.path.exists(args.out):
        try:
            _prev = json.load(open(args.out, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            _prev = {}
        if _prev.get("complete") is True:
            print(f"REFUSING: {os.path.relpath(args.out, REPO)} is a complete artifact; one run per preregistration", file=sys.stderr)
            return 3

    # [1] corpus A (the builder's): y and g are read without touching X, which is memmapped; X is hashed whole
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
    cache_x_sha = None
    if (P.get("cache_identity") or {}).get("X_sha256"):
        cache_x_sha, x_shape, x_dtype = _array_sha(args.cache, "X")
        if cache_x_sha != P["cache_identity"]["X_sha256"]:
            print(f"REFUSING: the builder cache's X hashes to {cache_x_sha[:12]}..., not the sealed "
                  f"{P['cache_identity']['X_sha256'][:12]}...", file=sys.stderr)
            return 3
        if list(x_shape) != list(P["cache_identity"].get("X_shape", x_shape)) or x_dtype != P["cache_identity"].get("X_dtype", x_dtype):
            print(f"REFUSING: the builder cache's X is {x_shape} {x_dtype}, not the sealed shape or dtype", file=sys.stderr)
            return 3
    corpus = {"carve_bytes": cache_carve, "carve_bytes_source": carve_source, "chunk_size": cache_cs, "chunk_offset": cache_off,
              "chunk_id_min": int(g.min()), "chunk_id_max": int(g.max()), "n_source_chunks": int(np.unique(g).size),
              "cache_y_sha256": cache_y_sha, "cache_g_sha256": cache_g_sha, "n_rows": int(len(y)), "n_features": int(ncols)}
    if cache_x_sha:
        corpus["cache_X_sha256"] = cache_x_sha
    print(f"[1] corpus A: {corpus}", flush=True)

    # [1b] the sealed extension corpus (0018's): scored, never fitted
    ext_sealed = dict(P["ext_corpus"]); ext_hashes = {}
    for name in ("X", "y", "g", "fam"):
        h, shape, dtype = _array_sha(args.ext, name)
        ext_hashes[name] = {"sha256": h, "shape": shape, "dtype": dtype}
    mism = [n for n in ext_hashes if ext_hashes[n]["sha256"] != (ext_sealed.get("arrays") or {}).get(n, {}).get("sha256")]
    if mism:
        print(f"REFUSING: extension corpus arrays {mism} do not hash to the {'smoke' if args.smoke else 'sealed'} ext_corpus.arrays",
              file=sys.stderr)
        return 3
    # [1c] the real-content FIT corpus (0021's): fitted, never scored
    fit_sealed = dict(P["fit_corpus"]); fit_hashes = {}
    for name in ("X", "y", "g", "fam"):
        h, shape, dtype = _array_sha(args.realfit, name)
        fit_hashes[name] = {"sha256": h, "shape": shape, "dtype": dtype}
    mism = [n for n in fit_hashes if fit_hashes[n]["sha256"] != (fit_sealed.get("arrays") or {}).get(n, {}).get("sha256")]
    if mism:
        print(f"REFUSING: fit corpus arrays {mism} do not hash to the {'smoke' if args.smoke else 'sealed'} fit_corpus.arrays",
              file=sys.stderr)
        return 3
    if args.smoke:
        sealed_fit_x = (((curve["protocol"].get("fit_corpus") or {}).get("arrays") or {}).get("X") or {}).get("sha256")
        sealed_ext_x = (((curve["protocol"].get("ext_corpus") or {}).get("arrays") or {}).get("X") or {}).get("sha256")
        if ext_hashes["X"]["sha256"] == sealed_ext_x or fit_hashes["X"]["sha256"] == sealed_fit_x:
            print("REFUSING: a smoke must never touch the sealed corpora", file=sys.stderr)
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

    # [2] the sealed split (0003's by construction) gives the scored evaluation set; the fit block and its rungs are cut here
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e = fam_all[ev]
    ev_chunks = np.unique(g[ev])
    fit_order, rung_rows, rep_rows, rung_part = rung_partition(yr, gr, fam_r, fit_names, seed, denominators)
    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam_e != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev), "eval_g_sha256": _sha(np.asarray(g[ev])),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64)),
                 "families": list(FAMILIES), **rung_part,
                 "pool_chunks_shared_with_ext": int(np.intersect1d(np.unique(g[tr]), np.unique(gx)).size),
                 "eval_chunks_shared_with_ext": int(np.intersect1d(ev_chunks, np.unique(gx)).size),
                 "fit_chunks_shared_with_ext": int(np.intersect1d(np.unique(gr), np.unique(gx)).size),
                 "fit_chunks_shared_with_builder": int(np.intersect1d(np.unique(gr), np.unique(g)).size),
                 "fit_source_chunks_shared_with_ext": int(len(fit_src & ext_src)),
                 "n_fit_source_chunks": int(len(fit_src)), "n_ext_source_chunks": int(len(ext_src))}
    t_id = time.perf_counter()
    scored_digests = {hashlib.blake2b(np.ascontiguousarray(Xx[i], dtype=np.float32).tobytes(), digest_size=16).digest()
                      for i in range(len(Xx))}
    for i in range(0, len(ev), 20000):
        blk = np.ascontiguousarray(X[np.sort(ev)[i:i + 20000], :ncols], dtype=np.float32)
        for j in range(len(blk)):
            scored_digests.add(hashlib.blake2b(blk[j].tobytes(), digest_size=16).digest())
    n_same = 0
    for i in range(len(Xr)):
        if hashlib.blake2b(np.ascontiguousarray(Xr[i], dtype=np.float32).tobytes(), digest_size=16).digest() in scored_digests:
            n_same += 1
    partition["fit_rows_identical_to_a_scored_row"] = int(n_same)
    partition["row_identity_digest"] = "blake2b-128 of the contiguous float32 feature row, over every scored row"
    del scored_digests
    print(f"[2] row identity scan: {n_same} fit rows are byte-identical to a scored row ({time.perf_counter() - t_id:.0f}s)", flush=True)
    if not args.smoke:
        if partition["pool_idx_sha256"] != P["pool_idx_sha256"]:
            print(f"REFUSING: the pool hashes to {partition['pool_idx_sha256'][:12]}..., not the sealed {P['pool_idx_sha256'][:12]}...",
                  file=sys.stderr)
            return 3
        if (partition["fit_source_chunks_shared_with_ext"] or partition["fit_chunks_shared_with_ext"]
                or partition["fit_chunks_shared_with_builder"]):
            print("REFUSING: the fit corpus shares a chunk id or a source chunk with a scored corpus", file=sys.stderr)
            return 3
        bad = [k for k, v in (P.get("fit_block_hashes") or {}).items() if partition.get(k) != v]
        if bad:
            print(f"REFUSING: the fit block {bad} does not hash to the sealed fit_block_hashes", file=sys.stderr)
            return 3
        sealed_rungs = P.get("rung_hashes") or []
        for k, sr in enumerate(sealed_rungs):
            got = partition["rungs"][k] if k < len(partition["rungs"]) else {}
            badk = [kk for kk, v in sr.items() if got.get(kk) != v]
            if badk:
                print(f"REFUSING: rung {k + 1} {badk} does not match the sealed rung_hashes", file=sys.stderr)
                return 3
        badr = [kk for kk, v in (P.get("replicate_rung_1_hashes") or {}).items() if partition["replicate_rung_1"].get(kk) != v]
        if badr:
            print(f"REFUSING: the replicate rung {badr} does not match the sealed replicate_rung_1_hashes", file=sys.stderr)
            return 3
        if partition["fit_rows_identical_to_a_scored_row"] != 0:
            print(f"REFUSING: {partition['fit_rows_identical_to_a_scored_row']} fit rows are byte-identical to a scored row; "
                  f"the clause's own corpus must share nothing with anything scored", file=sys.stderr)
            return 3
        if not (partition["rungs_nested"] and partition["rung_chunks_strictly_increasing"] and partition["top_rung_is_fit_block"]):
            print("REFUSING: the rungs are not nested, strictly increasing in plaintexts and topped by the whole fit block", file=sys.stderr)
            return 3
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, fit block {partition['fit_rows']}"
          f"/{partition['fit_block_chunks']} chunks; rungs "
          + ", ".join(f"r{r['rung']} 1/{r['denominator']}: {r['n_rows']} rows/{r['n_chunks']} chunks" for r in partition["rungs"]),
          flush=True)

    store = Store(args.workdir)
    curve_sha = sha_obj(curve)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "curve_sha256": curve_sha, "curve_spec": curve, "corpus": corpus, "ext_corpus": ext, "fit_corpus": fit,
              "partition": partition, "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
              "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    yr_np = np.asarray(yr); gr_np = np.asarray(gr)

    started = None
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev]); n_eval = int(len(ev)); n_ext = int(len(yx))
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}
    r4 = lambda v: round(float(v), 4)  # noqa: E731
    order = list(P["order"])
    real_mask = np.isin(fam_x, REAL_FAMILIES); n_real = int(real_mask.sum())
    log2x = [r["log2_chunks"] for r in partition["rungs"]]

    def readings(name):
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
                "ext_real_top1": r4(ex[real_mask].mean()), "ext_real_correct": int(ex[real_mask].sum()),
                "n_ext_real_rows": n_real,
                "ext_synthetic_correct": int(ex[np.isin(fam_x, SYNTH_FAMILIES)].sum()),
                "ext_synthetic_top1": r4(ex[np.isin(fam_x, SYNTH_FAMILIES)].mean()),
                "builder_eval_per_family": {f: r4(rep[fam_e == f].mean()) for f in FAMILIES}}

    def role_curve(role, reads):
        pts = []
        for r in partition["rungs"]:
            rd = reads.get(f"r{r['rung']}_{role}")
            pts.append(None if rd is None else {"rung": r["rung"], "denominator": r["denominator"], "n_chunks": r["n_chunks"],
                                                "n_rows": r["n_rows"], "log2_chunks": r["log2_chunks"],
                                                "ext_real_top1": rd["ext_real_top1"], "ext_real_correct": rd["ext_real_correct"],
                                                "builder_eval_top1": rd["builder_eval_top1"],
                                                "ext_per_family": {f: rd["ext_per_family"][f] for f in REAL_FAMILIES}})
        c = {"rungs": pts, "complete": all(p is not None for p in pts)}
        if c["complete"]:
            ys = [p["ext_real_top1"] for p in pts]
            c["slope_per_doubling"] = round(ols_slope(log2x, ys), 6)
            c["end_to_end_gain"] = round(ys[-1] - ys[0], 4)
            c["rung_to_rung_gains"] = [round(ys[i + 1] - ys[i], 4) for i in range(len(ys) - 1)]
            c["slope_with_top_rung_at_reference"] = round(ols_slope(log2x, ys[:-1] + [float(P["reference_top1"][role])]), 6)
            c["per_family_slope_per_doubling"] = {f: round(ols_slope(log2x, [p["ext_per_family"][f] for p in pts]), 6)
                                                  for f in REAL_FAMILIES}
            c["builder_eval_slope_per_doubling"] = round(ols_slope(log2x, [p["builder_eval_top1"] for p in pts]), 6)
        return c

    def assemble(complete, launch_no, ci=None, boot=None):
        reads = {n: readings(n) for n in order if per_ex.get(n) is not None}
        curves = {role: role_curve(role, reads) for role in ROLES}
        ms = curves["model"].get("slope_per_doubling"); ls = curves["logistic"].get("slope_per_doubling")
        ts = curves["depth3_tree"].get("slope_per_doubling")
        top = f"r{n_rungs}_"
        repro_top1 = {role: (reads.get(top + role) or {}).get("ext_real_top1") for role in ROLES}
        rep_block = {"rung": partition["replicate_rung_1"], "readings": {}, "difference_from_rung_1": {}, "slope_with_replicate_at_rung_1": {},
                     "note": "informational: the smallest rung cut again under a second seeded nesting of each family's chunks and "
                             "fitted with the same three recipes; the difference from rung 1 is a direct reading of the fit-side "
                             "variance the scored-chunk bootstrap does not resample; never a verdict"}
        for role in ROLES:
            rr_ = reads.get(f"{REPLICATE}_{role}"); r1 = reads.get(f"r1_{role}")
            if rr_ is None:
                continue
            rep_block["readings"][role] = {"ext_real_top1": rr_["ext_real_top1"], "ext_real_correct": rr_["ext_real_correct"],
                                           "builder_eval_top1": rr_["builder_eval_top1"],
                                           "ext_per_family": {f: rr_["ext_per_family"][f] for f in REAL_FAMILIES}}
            if r1 is not None:
                rep_block["difference_from_rung_1"][role] = round(rr_["ext_real_top1"] - r1["ext_real_top1"], 4)
            if curves[role].get("complete"):
                ys = [p["ext_real_top1"] for p in curves[role]["rungs"]]
                rep_block["slope_with_replicate_at_rung_1"][role] = round(ols_slope(log2x, [rr_["ext_real_top1"]] + ys[1:]), 6)
        doc = dict(common, stage="run", environment=environment(), launch_environment=launch_env, launch_number=launch_no,
                   complete=bool(complete), missing_roles=[n for n in order if n not in records],
                   fits=records, readings=reads,
                   ext_real_top1={n: (reads[n] or {}).get("ext_real_top1") for n in reads},
                   ext_real_correct={n: (reads[n] or {}).get("ext_real_correct") for n in reads},
                   ext_top1={n: (reads[n] or {}).get("ext_top1") for n in reads},
                   builder_eval_top1={n: (reads[n] or {}).get("builder_eval_top1") for n in reads},
                   ext_per_family={n: (reads[n] or {}).get("ext_per_family") for n in reads},
                   curves=curves, roles=list(ROLES), n_rungs=n_rungs, denominators=denominators, log2_chunks=log2x,
                   model_slope_per_doubling=ms, logistic_slope_per_doubling=ls, depth3_tree_slope_per_doubling=ts,
                   slope_model_minus_logistic=(None if ms is None or ls is None else round(ms - ls, 6)),
                   slope_model_minus_depth3_tree=(None if ms is None or ts is None else round(ms - ts, 6)),
                   bar={"slope_per_doubling": float(P["bar"]["slope_per_doubling"]),
                        "bootstrap_lower_bound_gt": float(P["bar"]["bootstrap_lower_bound_gt"]),
                        "n_boot": int(P["bootstrap"]["n_boot"]), "bootstrap_seed": int(P["bootstrap"]["seed"])},
                   slope_bootstrap=boot or {}, replicate_rung_1=rep_block,
                   n_ext_real_rows=n_real, n_ext_rows=n_ext, n_eval_rows=n_eval,
                   ext_real_families=list(REAL_FAMILIES), ext_synthetic_families=list(SYNTH_FAMILIES),
                   fit_families=list(fit_names), fit_rows_per_family=fit["rows_per_family"],
                   reference_top1=dict(P["reference_top1"]), reproduction_top1=repro_top1,
                   reproduction_drift={role: (None if repro_top1[role] is None
                                              else round(repro_top1[role] - float(P["reference_top1"][role]), 6)) for role in ROLES},
                   shuffled_label_accuracy_ext=(reads.get("null") or {}).get("ext_top1"),
                   shuffled_label_accuracy_eval=(reads.get("null") or {}).get("builder_eval_top1"),
                   shuffled_label_accuracy_real=(reads.get("null") or {}).get("ext_real_top1"),
                   null_control=records.get("null"), null_rows=int(len(fit_order)),
                   fit_info_by_name={n: (records.get(n) or {}).get("fit_info") for n in order},
                   ledger=store.ledger(),
                   fit_record_top1_is="each record's top1 and top1_non_gutenberg are over the concatenated "
                                      f"{n_eval} + {n_ext} scoring set; per_family is over every family present in it - "
                                      "the builder's eight on the evaluation rows and the eight 'ext:'-prefixed extension families",
                   cluster_ci95_informational=ci or {},
                   cluster_ci95_note="95% cluster-bootstrap intervals over source chunks (2000 resamples), informational",
                   cost={"wall_seconds_this_invocation": round(time.perf_counter() - t_all, 1),
                         "seconds_by_name": {k: v.get("seconds") for k, v in records.items()},
                         "interruptions_by_name": {k: v.get("interruptions_before_this_fit") for k, v in records.items()},
                         "banked_fit_seconds_total": round(store.banked_seconds("run"), 1),
                         "checkpoints": os.path.relpath(args.workdir, REPO)},
                   run_started_utc=started, first_launch_utc=first_launch,
                   run_finished_utc=_utc() if complete else None)
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
        any_run = any(f.startswith("run_") and f.endswith(".json") for f in os.listdir(args.workdir)) if os.path.isdir(args.workdir) else False
        launch_no = store.launches("run", any_run)
        with open(os.path.join(args.workdir, "launches.jsonl")) as fh:
            _launches = [json.loads(l) for l in fh if l.strip()]
        first_launch = next(e["utc"] for e in _launches if e.get("stage") == "run")
        started = first_launch
        Xs = np.empty((n_eval + n_ext, ncols), np.float32)
        fill_f32(Xs[:n_eval], X, ev, ncols); Xs[n_eval:] = Xx
        del Xx
        ys = np.concatenate([ye, np.asarray(yx)]); fam_s = np.concatenate([fam_e, np.array(["ext:" + f for f in fam_x])])
        partition["eval_y_sha256"] = _sha(ye)
        print(f"[run] scoring set {n_eval} + {n_ext} rows materialised, anonymous RSS {_rss_gb():.2f} GB "
              f"(total {_rss_total_gb():.2f} GB)", flush=True)
        chance = 1.0 / N_CONFIGS
        blocks: dict = {}

        def rows_of(k):
            return rep_rows if k == REPLICATE else rung_rows[k - 1]

        def rk_of(k):
            return partition["replicate_rung_1"] if k == REPLICATE else partition["rungs"][k - 1]

        def block_of(k):
            if k not in blocks:
                blocks[k] = Block(Xr, rows_of(k), ncols, f"r{k}")
            return blocks[k]

        def fit_role(name, role, cand, y_all, stage, k):
            rk = rk_of(k)
            fp = fingerprint(prereg=stamp, seed=seed, head=role, cand=cand, stage=stage, rung=k, rows=rk["sorted_sha256"],
                             eval=partition["eval_idx_sha256"], ext=ext_hashes["X"]["sha256"], fit=fit_hashes["X"]["sha256"])
            store.log(f"run_{name}", fp, "rung_bound", rung=k, rung_sorted_sha256=rk["sorted_sha256"])
            r, pe = run_fit(store, f"run_{name}", fp, role, cand, seed, block_of(k), y_all, gr_np, Xs, ys, fam_s, stage, caps,
                            keep_per_example=True, confirmatory=True)
            records[name] = dict(r, fingerprint=fp, rung=k, role=role, n_rung_rows=rk["n_rows"], n_rung_chunks=rk["n_chunks"],
                                 per_example_sha256=(hashlib.sha256(np.asarray(pe, np.int8).tobytes()).hexdigest()
                                                     if pe is not None else None))
            if pe is not None:
                per_ex[name] = pe
            rd = readings(name)
            if rd:
                print(f"      {name:<18} BUILDER EVAL {rd['builder_eval_top1']} | EXTENSION {rd['ext_top1']} | REAL "
                      f"{rd['ext_real_correct']}/{rd['n_ext_real_rows']} = {rd['ext_real_top1']} "
                      f"{ {f: rd['ext_per_family'][f] for f in REAL_FAMILIES} }", flush=True)
            assemble(False, launch_no)
            if rd is None:
                raise NotRun(f"{name}: no per-example vector was banked (status {records[name].get('status')!r}); one scoring per role")
            return rd

        for step in order:
            if step == "null":
                y_sh = yr_np.copy(); rng.shuffle(y_sh)
                partition["null_y_shuffled_sha256"] = _sha(y_sh)
                partition["null_labels_permuted"] = bool(not np.array_equal(y_sh, yr_np))
                partition["null_labels_same_multiset"] = bool(np.array_equal(np.sort(y_sh), np.sort(yr_np)))
                if not args.smoke and not (partition["null_labels_permuted"] and partition["null_labels_same_multiset"]):
                    raise NotRun("the null control's labels are not a permutation of the fit corpus's own labels")
                want_null = P.get("null_y_shuffled_sha256_expected")
                if not args.smoke and want_null and partition["null_y_shuffled_sha256"] != want_null:
                    raise NotRun(f"the null control's permuted labels hash to {partition['null_y_shuffled_sha256'][:12]}..., not 0021's "
                                 f"sealed {want_null[:12]}...: the generator state or the label array is not 0021's")
                rd = fit_role("null", "null", recipes["model"], y_sh, "null", n_rungs)
                if rd and not args.smoke:
                    tol = float(P["null_tolerance"])
                    if rd["ext_top1"] > chance + tol or rd["builder_eval_top1"] > chance + tol:
                        raise NotRun(f"null control read {rd['ext_top1']} on the extension rows and {rd['builder_eval_top1']} on "
                                     f"the sealed evaluation rows against chance {chance:.6f} + {tol}: the scoring path leaks")
            else:
                k, role = parse_name(step, n_rungs)
                if role not in ROLES or (k != REPLICATE and not (1 <= k <= n_rungs)):
                    raise NotRun(f"unknown order step {step!r}")
                rd = fit_role(step, role, recipes[role], yr_np, ("replicate" if k == REPLICATE else "curve"), k)
                if rd and not args.smoke and k == n_rungs:
                    drift = round(abs(rd["ext_real_top1"] - float(P["reference_top1"][role])), 6)
                    if drift > float(P["reproduction_tolerance"]):
                        raise NotRun(f"{step} read {rd['ext_real_top1']} on the real-family rows against 0021's banked "
                                     f"{P['reference_top1'][role]} (drift {drift} > {P['reproduction_tolerance']}): the fit block, "
                                     f"the scoring set or the machinery is not 0021's")
                if step.endswith("_model") and k in blocks:
                    del blocks[k]                    # the rung's last role is fitted; free its block (the top block too)
        ci = {}
        for n in order:
            v = per_ex.get(n)
            if v is None:
                continue
            ex = v[n_eval:]
            ci[f"{n}_ext"] = cluster_ci(ex, gx, seed=seed)
            ci[f"{n}_ext_real"] = cluster_ci(ex[real_mask], gx[real_mask], seed=seed)
            for f in ext_names:
                m = fam_x == f
                ci[f"{n}_ext_{f}"] = cluster_ci(ex[m], gx[m], seed=seed)
            ci[f"{n}_builder_eval"] = cluster_ci(v[:n_eval], ge, seed=seed)
        # the verdict's bootstrap: every role's rung vectors on the real rows, one resample per draw for all of them
        by_role = {role: [per_ex[f"r{k}_{role}"][n_eval:][real_mask] for k in range(1, n_rungs + 1)] for role in ROLES}
        sl = slope_bootstrap(by_role, log2x, gx[real_mask], int(P["bootstrap"]["n_boot"]), int(P["bootstrap"]["seed"]))
        boot = {role: {"ci95": [round(float(np.percentile(sl[role], 2.5)), 6), round(float(np.percentile(sl[role], 97.5)), 6)],
                       "n_boot": int(P["bootstrap"]["n_boot"]), "seed": int(P["bootstrap"]["seed"]),
                       "mean": round(float(sl[role].mean()), 6)} for role in ROLES}
        for a, b_ in (("model", "logistic"), ("model", "depth3_tree")):
            d = sl[a] - sl[b_]
            boot[f"{a}_minus_{b_}"] = {"ci95": [round(float(np.percentile(d, 2.5)), 6), round(float(np.percentile(d, 97.5)), 6)],
                                       "paired": True, "share_of_resamples_with_model_ahead": round(float((d > 0).mean()), 4)}
        boot["unit"] = "accuracy on the real-family rows per doubling of plaintexts; cluster bootstrap over the scored real chunks"
        out = assemble(True, launch_no, ci=ci, boot=boot)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "run", "reason": str(e),
                       "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])}, fh, indent=2)
        return 4
    print(f"[run] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; model slope "
          f"{out['model_slope_per_doubling']} per doubling (bootstrap {out['slope_bootstrap'].get('model', {}).get('ci95')}), "
          f"logistic {out['logistic_slope_per_doubling']}, depth-3 tree {out['depth3_tree_slope_per_doubling']}; rung readings "
          f"{[p['ext_real_top1'] for p in out['curves']['model']['rungs']]}; null {out['shuffled_label_accuracy_real']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
