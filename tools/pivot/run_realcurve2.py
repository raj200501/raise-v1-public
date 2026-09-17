#!/usr/bin/env python3
"""Runner for preregistration 0024: the SECOND decade of real plaintexts at 4096.

0023 read REAL_CURVE_RISES over one decade (130 -> 1029 real plaintexts, all of them chunks of 0018's five pinned
files): the boosted model rose 0.007344 per doubling, the standardised logistic 0.009551, and the model's lead
shrank from 0.0063 to 0.0014 at the top rung, which was 0021's whole fit block. The record held no more real
plaintexts. This run adds three more doublings from NEW pinned files of the same five families (0024's corpus,
tools/pivot/corpus_realfit2.py), nested on 0021's block: rung 4 + d holds 0021's block plus, per family, the first
n_f x (2^d - 1) new plaintexts of the seeded pool, so every rung has exactly 2^d times rung 4's plaintexts of every
family. The three fixed recipes (M4, L3, D1) are fitted on every rung, scored once each on 0018's scoring set, and
read against log2(plaintexts): the slope of the SECOND decade (rungs 4..7) is the clause, the lead of the model
over the logistic at the top rung is the sealed reading rule, and rungs 1..4 are 0023's rungs row for row, so their
readings reproduce 0023's.

Everything scored is 0018's sealed corpus and 0003's sealed evaluation set; nothing fitted is ever scored, and
the runner measures that (chunk ids, source-chunk hashes, byte-identical rows) rather than assuming it.

    python3 tools/pivot/run_realcurve2.py --stage run            # the one run; resumable from its checkpoints
    python3 tools/pivot/run_realcurve2.py --stage run --smoke    # scratchpad-only rehearsal on the smoke corpora
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
from run_recipe_search import (REPO, _sha, sha_obj, _utc, fingerprint, environment, npz_memmap, fill_f32, Block,  # noqa: E402
                               run_fit, Store, NotRun, cluster_ci, _rss_gb, _rss_total_gb, grouped_split, FAMILIES,
                               N_CONFIGS, CONFIG_NAMES)
from run_realfit import corpus_block, _array_sha, STRUCTURED_TEXT, HIGH_ENTROPY  # noqa: E402
from run_realsearch import score_by_family  # noqa: E402  (installs itself as run_recipe_search.score)
from run_realcurve import ROLES, ols_slope, slope_bootstrap, rung_partition  # noqa: E402
from corpus_ext import EXT_FAMILIES, REAL_FAMILIES, SYNTH_FAMILIES  # noqa: E402
from corpus_realfit import FAMILIES as FIT_FAMILIES  # noqa: E402

_rrs.score = score_by_family   # per_family over the families PRESENT in the scoring set (0022's convention)

N_FIRST = 4                    # 0023's rungs: 1..4, the fourth being 0021's whole fit block
RUNG_STREAM_OFFSET = 100       # np.random.default_rng([seed2, 100 + k]) permutes rung k's rows (k > N_FIRST)
NULL_STREAM_WORD = 200         # np.random.default_rng([seed2, 200]) permutes the top rung's labels for the null control
SHIFT = "s4"                   # the shift arm: rung 5's NEW plaintexts alone (rung 4's size, other files only); informational, fitted last
SHIFT_STREAM_WORD = 150        # np.random.default_rng([seed2, 150]) permutes the shift arm's rows


def sealed_order(n_rungs, n_first=N_FIRST):
    """null on the top rung; rung 4 (the reproduction of 0021 and of 0023's top rung); 0023's lower rungs (the reproduction of
    its curve) - every reproduction before any new plaintext is fitted; the new rungs ascending; then the shift arm."""
    return (["null"] + [f"r{n_first}_{r}" for r in ROLES]
            + [f"r{k}_{r}" for k in range(1, n_first) for r in ROLES]
            + [f"r{k}_{r}" for k in range(n_first + 1, n_rungs + 1) for r in ROLES]
            + [f"{SHIFT}_{r}" for r in ROLES])


def parse_name(name, n_rungs):
    """'null' -> (n_rungs, 'null'); 'r2_model' -> (2, 'model'); 's4_model' -> ('s4', 'model')."""
    if name == "null":
        return n_rungs, "null"
    rung, role = name.split("_", 1)
    return (SHIFT if rung == SHIFT else int(rung[1:])), role


def paired_lead_bootstrap(vec_a, vec_b, chunk_ids, n_boot, seed):
    """Cluster bootstrap over scored chunks of accuracy(a) - accuracy(b), the same resample serving both vectors, with
    the same generator construction and draw order as slope_bootstrap (so the resamples are the slope bootstrap's).
    Accuracies inside a resample are rounded to 4 decimals, as the banked readings are. Returns diffs[n_boot]."""
    _, inv = np.unique(chunk_ids, return_inverse=True); counts = np.bincount(inv).astype(np.float64)
    sa = np.bincount(inv, weights=np.asarray(vec_a, np.float64), minlength=len(counts))
    sb = np.bincount(inv, weights=np.asarray(vec_b, np.float64), minlength=len(counts))
    rng = np.random.default_rng(seed); n = len(counts); out = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n); tot = counts[idx].sum()
        out[b] = round(float(sa[idx].sum() / tot), 4) - round(float(sb[idx].sum() / tot), 4)
    return out


def rung_partition2(yr, gr, fam_r, fit_names, seed, denominators, y2, g2, fam_2, seed2, doublings):
    """0023's four rungs (by calling run_realcurve.rung_partition) and the second decade's rungs nested on them. Module-
    level so the preregistration generator and the pre-freeze check CALL it rather than retype it (OPERATING_RULES 4).

    Rows live in the concatenated index space [0021's fit corpus rows] + [0024's corpus rows offset by n_r]. Per family
    f with n_f chunks with rows in 0021's block, rung 4 + d takes 0021's whole block plus the first n_f x (2^d - 1)
    chunks with rows of f in 0024's pool order (chunk id ascending); its rows are that set's rows permuted by
    np.random.default_rng([seed2, 100 + (4 + d)]) so the recipes' last-10% validation split is a random tenth.
    Returns (fit_order, rows_by_rung [all rungs, in the concatenated space], keys)."""
    fit_order, rung_rows, _rep_rows, k1 = rung_partition(yr, gr, fam_r, fit_names, seed, denominators)
    n_r = int(len(yr)); g2 = np.asarray(g2); fam_2 = np.asarray(fam_2); gr = np.asarray(gr); fam_r = np.asarray(fam_r)
    base = dict(k1["fit_chunks_per_family"])            # chunks WITH ROWS per family in 0021's block
    pool = {f: np.sort(np.unique(g2[fam_2 == f])).astype(np.int64) for f in fit_names}
    rungs = [dict(r, decade=1, new_chunks_per_family={f: 0 for f in fit_names}, n_new_chunks=0, n_new_rows=0) for r in k1["rungs"]]
    rows_all = [np.asarray(r, np.int64) for r in rung_rows]
    prev_new = np.empty(0, np.int64); nested = bool(k1["rungs_nested"]); increasing = bool(k1["rung_chunks_strictly_increasing"])
    exact = True; short = {}
    for d in range(1, int(doublings) + 1):
        k = N_FIRST + d
        take = {f: int(base[f] * (2 ** d - 1)) for f in fit_names}
        for f in fit_names:
            if len(pool[f]) < take[f]:
                short[f] = {"needed": take[f], "in_pool": int(len(pool[f]))}
        chosen_new = np.sort(np.concatenate([pool[f][:min(take[f], len(pool[f]))] for f in fit_names])).astype(np.int64)
        in_new = np.isin(g2, chosen_new); rows2 = np.nonzero(in_new)[0].astype(np.int64)
        combined = np.concatenate([np.asarray(fit_order, np.int64), n_r + rows2])
        perm = np.random.default_rng([int(seed2), RUNG_STREAM_OFFSET + k]).permutation(len(combined))
        rows = combined[perm]
        chosen_all = np.sort(np.concatenate([np.unique(gr), chosen_new])).astype(np.int64)
        cpf = {f: int(base[f] + int(np.isin(chosen_new, pool[f]).sum())) for f in fit_names}
        exact = exact and all(cpf[f] == base[f] * (2 ** d) for f in fit_names)
        nested = nested and bool(np.isin(prev_new, chosen_new).all()); increasing = increasing and chosen_all.size > rungs[-1]["n_chunks"]
        fam_rows2 = fam_2[rows2]
        rungs.append({"rung": k, "decade": 2, "doubling": d, "denominator": None, "n_chunks": int(chosen_all.size), "n_rows": int(len(rows)),
                      "chunks_per_family": cpf, "new_chunks_per_family": {f: int(np.isin(chosen_new, pool[f]).sum()) for f in fit_names},
                      "n_new_chunks": int(chosen_new.size), "n_new_rows": int(len(rows2)),
                      "rows_per_family": {f: int((fam_r == f).sum() + (fam_rows2 == f).sum()) for f in fit_names},
                      "log2_chunks": round(float(np.log2(chosen_all.size)), 6),
                      "idx_sha256": _sha(rows), "sorted_sha256": _sha(np.sort(rows).astype(np.int64)),
                      "chunks_sha256": _sha(chosen_all), "new_chunks_sha256": _sha(chosen_new),
                      "row_order_rule": f"np.random.default_rng([{int(seed2)}, {RUNG_STREAM_OFFSET + k}]).permutation over "
                                        f"[0021's fit block in its order] + [{n_r} + 0024 rows of the rung's chunks in npz order]"})
        rows_all.append(rows); prev_new = chosen_new
    # the shift arm: rung 5's new plaintexts alone (per family the first n_f chunks with rows of the pool), rows permuted
    first_new = np.sort(np.concatenate([pool[f][:min(base[f], len(pool[f]))] for f in fit_names])).astype(np.int64)
    in_s = np.isin(g2, first_new); rows_s2 = np.nonzero(in_s)[0].astype(np.int64)
    perm_s = np.random.default_rng([int(seed2), SHIFT_STREAM_WORD]).permutation(len(rows_s2))
    shift_rows = (n_r + rows_s2)[perm_s]; fam_s2 = fam_2[rows_s2]
    shift = {"rung": SHIFT, "decade": 2, "n_chunks": int(first_new.size), "n_rows": int(len(shift_rows)),
             "chunks_per_family": {f: int(np.isin(first_new, pool[f]).sum()) for f in fit_names},
             "rows_per_family": {f: int((fam_s2 == f).sum()) for f in fit_names},
             "log2_chunks": round(float(np.log2(first_new.size)), 6),
             "idx_sha256": _sha(shift_rows), "sorted_sha256": _sha(np.sort(shift_rows).astype(np.int64)), "chunks_sha256": _sha(first_new),
             "same_chunks_as_rung_5s_new_chunks": bool(len(rungs) > N_FIRST and _sha(first_new) == rungs[N_FIRST]["new_chunks_sha256"]),
             "same_plaintext_count_as_rung_4": bool(first_new.size == rungs[N_FIRST - 1]["n_chunks"]),
             "rule": f"rung 5's new plaintexts alone - per family the first n_f chunks with rows of 0024's pool, none of 0021's block - "
                     f"with rows permuted by np.random.default_rng([{int(seed2)}, {SHIFT_STREAM_WORD}]); informational: read beside rung 4 "
                     "(the same plaintext count, the scored files' own chunks) as a direct reading of what other files of the same "
                     "families buy for the original files"}
    keys = {"fit_rows": k1["fit_rows"], "fit_idx_sha256": k1["fit_idx_sha256"], "fit_sorted_sha256": k1["fit_sorted_sha256"],
            "fit_order_rule": k1["fit_order_rule"], "fit_block_chunks": k1["fit_block_chunks"], "fit_chunks_per_family": base,
            "rung_rule": k1["rung_rule"],
            "second_decade_rule": "lockstep_nested_on_0021_block: rung 4 + d is 0021's whole fit block plus, per family, the first "
                                  "n_f x (2^d - 1) chunks with rows of 0024's pool in pool order (chunk id ascending), n_f being the "
                                  "family's chunks with rows in 0021's block; every rung therefore holds exactly 2^d x n_f plaintexts "
                                  "of every family; rows are permuted by np.random.default_rng([seed2, 100 + rung])",
            "denominators": [int(d) for d in denominators], "doublings": int(doublings), "seed2": int(seed2),
            "n_first_decade_rungs": N_FIRST, "n_rungs": len(rungs), "rungs": rungs,
            "pool_chunks_with_rows_per_family": {f: int(len(pool[f])) for f in fit_names},
            "shift_arm": shift,
            "pool_short": short, "rungs_nested": bool(nested), "rung_chunks_strictly_increasing": bool(increasing),
            "rung4_is_fit_block": bool(rungs[N_FIRST - 1]["idx_sha256"] == _sha(np.asarray(fit_order, np.int64))),
            "second_decade_exact_doublings": bool(exact),
            "doublings_spanned": round(rungs[-1]["log2_chunks"] - rungs[0]["log2_chunks"], 6),
            "doublings_spanned_second_decade": round(rungs[-1]["log2_chunks"] - rungs[N_FIRST - 1]["log2_chunks"], 6),
            "n_fit_rows_total": int(n_r + len(y2))}
    return fit_order, rows_all + [shift_rows], keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["run"], default="run")
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0024-realcurve2-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--ext", default=os.path.join(REPO, "data", "pivot", "ext_c4096.npz"))
    ap.add_argument("--realfit", default=os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"))
    ap.add_argument("--realfit2", default=os.path.join(REPO, "data", "pivot", "realfit2_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "realcurve2_4096_ckpt"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "realcurve2_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "realcurve2_4096_scores.json"))
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
    seed = int(P["seed"]); seed2 = int(P["seed2"]); eval_frac = float(P["eval_frac"]); top_rung = int(P["top_rung"]); caps = P["caps"]
    denominators = [int(d) for d in P["denominators"]]; doublings = int(P["doublings"]); n_rungs = len(denominators) + doublings
    if list(P["families"]) != FAMILIES or list(P["ext_families"]) != EXT_FAMILIES or list(P["fit_families"]) != FIT_FAMILIES:
        print("REFUSING: a sealed family order is not the corpus module's order", file=sys.stderr)
        return 3
    if set(recipes) != set(ROLES) or set(P["recipe_ids"]) != set(ROLES) or any(recipes[r]["id"] != P["recipe_ids"][r] for r in ROLES):
        print(f"REFUSING: the sealed recipes must be the roles {ROLES} carrying the sealed recipe_ids", file=sys.stderr)
        return 3
    if len(denominators) != N_FIRST or any(denominators[i] <= denominators[i + 1] for i in range(N_FIRST - 1)) or denominators[-1] != 1:
        print(f"REFUSING: denominators must be 0023's {N_FIRST}, strictly decreasing and ending at 1", file=sys.stderr)
        return 3
    if doublings < 1 or list(P["order"]) != sealed_order(n_rungs):
        print(f"REFUSING: doublings must be >= 1 and the sealed order must be {sealed_order(n_rungs)}", file=sys.stderr)
        return 3
    if set(P["reference_top1"]) != set(ROLES) or set(P["reference_first_decade"]) != set(ROLES) \
            or any(len(P["reference_first_decade"][r]) != N_FIRST for r in ROLES):
        print("REFUSING: reference_top1 must name 0021's reading per role and reference_first_decade 0023's four readings per role",
              file=sys.stderr)
        return 3
    if list(P.get("roles", [])) != ROLES or P.get("null_rows") != "top_rung":
        print(f"REFUSING: the sealed roles must be {ROLES} and null_rows 'top_rung'", file=sys.stderr)
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

    # [1b..1d] the sealed evaluation corpus (scored, never fitted), 0021's fit corpus and 0024's fit corpus (fitted, never scored)
    def _hashes(path, key, label):
        sealed = dict(P[key]); hs = {}
        for name in ("X", "y", "g", "fam"):
            h, shape, dtype = _array_sha(path, name)
            hs[name] = {"sha256": h, "shape": shape, "dtype": dtype}
        mism = [n for n in hs if hs[n]["sha256"] != (sealed.get("arrays") or {}).get(n, {}).get("sha256")]
        if mism:
            raise SystemExit(f"REFUSING: {label} arrays {mism} do not hash to the {'smoke' if args.smoke else 'sealed'} {key}.arrays")
        return hs
    try:
        ext_hashes = _hashes(args.ext, "ext_corpus", "extension corpus")
        fit_hashes = _hashes(args.realfit, "fit_corpus", "0021 fit corpus")
        fit2_hashes = _hashes(args.realfit2, "fit2_corpus", "0024 fit corpus")
    except SystemExit as e:
        print(str(e), file=sys.stderr); return 3
    if args.smoke:
        sealed_x = {k: (((curve["protocol"].get(k) or {}).get("arrays") or {}).get("X") or {}).get("sha256")
                    for k in ("ext_corpus", "fit_corpus", "fit2_corpus")}
        if ext_hashes["X"]["sha256"] == sealed_x["ext_corpus"] or fit_hashes["X"]["sha256"] == sealed_x["fit_corpus"] \
                or fit2_hashes["X"]["sha256"] == sealed_x["fit2_corpus"]:
            print("REFUSING: a smoke must never touch the sealed corpora", file=sys.stderr)
            return 3

    def _load(path):
        Xa = np.load(_io.BytesIO(_zf.ZipFile(path).read("X.npy"))).astype(np.float32, copy=False)
        with _zf.ZipFile(path) as zf:
            ya = np.load(_io.BytesIO(zf.read("y.npy"))); ga = np.load(_io.BytesIO(zf.read("g.npy")))
            fa = np.load(_io.BytesIO(zf.read("fam.npy")))
            names_ = [str(s) for s in np.load(_io.BytesIO(zf.read("families.npy")))]
            src_ = set(str(v) for v in np.load(_io.BytesIO(zf.read("meta_src_sha256.npy")), allow_pickle=False))
        return Xa, ya, ga, fa, names_, src_
    Xx, yx, gx, famx, ext_names, ext_src = _load(args.ext)
    Xr, yr, gr, famr, fit_names, fit_src = _load(args.realfit)
    X2, y2, g2, fam2, fit2_names, fit2_src = _load(args.realfit2)
    if ext_names != list(P["ext_families"]) or fit_names != list(P["fit_families"]) or fit2_names != list(P["fit_families"]):
        print("REFUSING: a corpus family order differs from the sealed one", file=sys.stderr)
        return 3
    if Xx.shape[1] != ncols or Xr.shape[1] != ncols or X2.shape[1] != ncols:
        print("REFUSING: a corpus feature width differs from the builder's", file=sys.stderr)
        return 3
    fam_x = np.array(ext_names)[famx]; fam_r = np.array(fit_names)[famr]; fam_2 = np.array(fit2_names)[fam2]
    ext = corpus_block(os.path.relpath(args.ext, REPO), ext_hashes, yx, gx, fam_x, ext_names, labels=False)
    fit = corpus_block(os.path.relpath(args.realfit, REPO), fit_hashes, yr, gr, fam_r, fit_names, labels=True)
    fit2 = corpus_block(os.path.relpath(args.realfit2, REPO), fit2_hashes, y2, g2, fam_2, fit2_names, labels=True)
    print(f"[1b] sealed evaluation corpus: {ext['n_rows']} rows, {ext['n_chunks']} chunks", flush=True)
    print(f"[1c] 0021 fit corpus: {fit['n_rows']} rows, {fit['n_chunks']} chunks, {fit['rows_per_family']}", flush=True)
    print(f"[1d] 0024 fit corpus: {fit2['n_rows']} rows, {fit2['n_chunks']} chunks, {fit2['rows_per_family']}", flush=True)

    # [2] the sealed split gives the scored evaluation set; the rungs of both decades are cut here
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e = fam_all[ev]
    ev_chunks = np.unique(g[ev])
    fit_order, rows_all, rung_part = rung_partition2(yr, gr, fam_r, fit_names, seed, denominators, y2, g2, fam_2, seed2, doublings)
    n_r = int(len(yr))
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
                 "fit2_chunks_shared_with_ext": int(np.intersect1d(np.unique(g2), np.unique(gx)).size),
                 "fit2_chunks_shared_with_builder": int(np.intersect1d(np.unique(g2), np.unique(g)).size),
                 "fit2_chunks_shared_with_fit": int(np.intersect1d(np.unique(g2), np.unique(gr)).size),
                 "fit2_source_chunks_shared_with_ext": int(len(fit2_src & ext_src)),
                 "fit2_source_chunks_shared_with_fit": int(len(fit2_src & fit_src)),
                 "n_fit_source_chunks": int(len(fit_src)), "n_ext_source_chunks": int(len(ext_src)),
                 "n_fit2_source_chunks": int(len(fit2_src))}
    t_id = time.perf_counter()
    scored_digests = {hashlib.blake2b(np.ascontiguousarray(Xx[i], dtype=np.float32).tobytes(), digest_size=16).digest()
                      for i in range(len(Xx))}
    for i in range(0, len(ev), 20000):
        blk = np.ascontiguousarray(X[np.sort(ev)[i:i + 20000], :ncols], dtype=np.float32)
        for j in range(len(blk)):
            scored_digests.add(hashlib.blake2b(blk[j].tobytes(), digest_size=16).digest())
    n_same = sum(1 for i in range(len(Xr))
                 if hashlib.blake2b(np.ascontiguousarray(Xr[i], dtype=np.float32).tobytes(), digest_size=16).digest() in scored_digests)
    n_same2 = sum(1 for i in range(len(X2))
                  if hashlib.blake2b(np.ascontiguousarray(X2[i], dtype=np.float32).tobytes(), digest_size=16).digest() in scored_digests)
    partition["fit_rows_identical_to_a_scored_row"] = int(n_same)
    partition["fit2_rows_identical_to_a_scored_row"] = int(n_same2)
    partition["row_identity_digest"] = "blake2b-128 of the contiguous float32 feature row, over every scored row"
    del scored_digests
    print(f"[2] row identity scan: {n_same} 0021 fit rows and {n_same2} 0024 fit rows are byte-identical to a scored row "
          f"({time.perf_counter() - t_id:.0f}s)", flush=True)
    if not args.smoke:
        if partition["pool_idx_sha256"] != P["pool_idx_sha256"]:
            print(f"REFUSING: the pool hashes to {partition['pool_idx_sha256'][:12]}..., not the sealed {P['pool_idx_sha256'][:12]}...",
                  file=sys.stderr)
            return 3
        leak = [k for k in ("fit_source_chunks_shared_with_ext", "fit_chunks_shared_with_ext", "fit_chunks_shared_with_builder",
                            "fit2_chunks_shared_with_ext", "fit2_chunks_shared_with_builder", "fit2_chunks_shared_with_fit",
                            "fit2_source_chunks_shared_with_ext", "fit2_source_chunks_shared_with_fit",
                            "fit_rows_identical_to_a_scored_row", "fit2_rows_identical_to_a_scored_row") if partition[k]]
        if leak:
            print(f"REFUSING: a fit corpus shares something with a scored corpus or with the other fit corpus: {leak}", file=sys.stderr)
            return 3
        bad = [k for k, v in (P.get("fit_block_hashes") or {}).items() if partition.get(k) != v]
        if bad:
            print(f"REFUSING: the fit block {bad} does not hash to the sealed fit_block_hashes", file=sys.stderr)
            return 3
        sealed_rungs = P.get("rung_hashes") or []
        if len(sealed_rungs) != n_rungs:
            print(f"REFUSING: {len(sealed_rungs)} sealed rung_hashes for {n_rungs} rungs", file=sys.stderr)
            return 3
        for k, sr in enumerate(sealed_rungs):
            got = partition["rungs"][k]
            badk = [kk for kk, v in sr.items() if got.get(kk) != v]
            if badk:
                print(f"REFUSING: rung {k + 1} {badk} does not match the sealed rung_hashes", file=sys.stderr)
                return 3
        if partition["pool_short"]:
            print(f"REFUSING: 0024's pool is short of the lockstep doubling: {partition['pool_short']}", file=sys.stderr)
            return 3
        if not (partition["rungs_nested"] and partition["rung_chunks_strictly_increasing"] and partition["rung4_is_fit_block"]
                and partition["second_decade_exact_doublings"]):
            print("REFUSING: the rungs are not nested, strictly increasing, exact doublings on 0021's block at rung 4", file=sys.stderr)
            return 3
        if partition["pool_chunks_with_rows_per_family"] != P["pool_chunks_with_rows_per_family"]:
            print("REFUSING: 0024's pool chunks with rows per family are not the sealed ones", file=sys.stderr)
            return 3
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, fit block {partition['fit_rows']}"
          f"/{partition['fit_block_chunks']} chunks; rungs "
          + ", ".join(f"r{r['rung']}: {r['n_rows']} rows/{r['n_chunks']} chunks" for r in partition["rungs"]), flush=True)

    store = Store(args.workdir)
    curve_sha = sha_obj(curve)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "curve_sha256": curve_sha, "curve_spec": curve, "corpus": corpus, "ext_corpus": ext, "fit_corpus": fit,
              "fit2_corpus": fit2, "partition": partition, "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
              "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    y_all = np.concatenate([np.asarray(yr), np.asarray(y2)]); g_all = np.concatenate([np.asarray(gr), np.asarray(g2)])
    X_all = np.concatenate([Xr, X2]); del Xr, X2

    started = None
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev]); n_eval = int(len(ev)); n_ext = int(len(yx))
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}
    r4 = lambda v: round(float(v), 4)  # noqa: E731
    order = list(P["order"])
    real_mask = np.isin(fam_x, REAL_FAMILIES); n_real = int(real_mask.sum())
    log2x = [r["log2_chunks"] for r in partition["rungs"]]
    log2x_second = log2x[N_FIRST - 1:]; log2x_first = log2x[:N_FIRST]
    n_boot = int(P["bootstrap"]["n_boot"]); boot_seed = int(P["bootstrap"]["seed"])

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
            pts.append(None if rd is None else {"rung": r["rung"], "decade": r["decade"], "n_chunks": r["n_chunks"], "n_rows": r["n_rows"],
                                                "log2_chunks": r["log2_chunks"],
                                                "ext_real_top1": rd["ext_real_top1"], "ext_real_correct": rd["ext_real_correct"],
                                                "builder_eval_top1": rd["builder_eval_top1"],
                                                "ext_per_family": {f: rd["ext_per_family"][f] for f in REAL_FAMILIES}})
        c = {"rungs": pts, "complete": all(p is not None for p in pts)}
        if c["complete"]:
            ys = [p["ext_real_top1"] for p in pts]; ys2 = ys[N_FIRST - 1:]; ys1 = ys[:N_FIRST]
            c["slope_per_doubling_second_decade"] = round(ols_slope(log2x_second, ys2), 6)
            c["slope_per_doubling_first_decade"] = round(ols_slope(log2x_first, ys1), 6)
            c["slope_per_doubling_both_decades"] = round(ols_slope(log2x, ys), 6)
            c["end_to_end_gain_second_decade"] = round(ys[-1] - ys[N_FIRST - 1], 4)
            c["end_to_end_gain_both_decades"] = round(ys[-1] - ys[0], 4)
            c["rung_to_rung_gains"] = [round(ys[i + 1] - ys[i], 4) for i in range(len(ys) - 1)]
            c["slope_second_decade_with_rung4_at_reference"] = round(ols_slope(log2x_second, [float(P["reference_top1"][role])] + ys2[1:]), 6)
            c["per_family_slope_per_doubling_second_decade"] = {
                f: round(ols_slope(log2x_second, [p["ext_per_family"][f] for p in pts[N_FIRST - 1:]]), 6) for f in REAL_FAMILIES}
            c["builder_eval_slope_per_doubling_second_decade"] = round(ols_slope(log2x_second, [p["builder_eval_top1"] for p in pts[N_FIRST - 1:]]), 6)
        return c

    def assemble(complete, launch_no, ci=None, boot=None, lead=None):
        reads = {n: readings(n) for n in order if per_ex.get(n) is not None}
        curves = {role: role_curve(role, reads) for role in ROLES}
        ms = curves["model"].get("slope_per_doubling_second_decade"); ls = curves["logistic"].get("slope_per_doubling_second_decade")
        ts = curves["depth3_tree"].get("slope_per_doubling_second_decade")
        top = f"r{n_rungs}_"; r4_ = f"r{N_FIRST}_"
        repro_top1 = {role: (reads.get(r4_ + role) or {}).get("ext_real_top1") for role in ROLES}
        repro_first = {role: [(reads.get(f"r{k}_{role}") or {}).get("ext_real_top1") for k in range(1, N_FIRST + 1)] for role in ROLES}
        top_top1 = {role: (reads.get(top + role) or {}).get("ext_real_top1") for role in ROLES}
        shift_block = {"arm": partition["shift_arm"], "readings": {}, "difference_from_rung_4": {}, "difference_from_rung_5": {},
                       "note": "informational: rung 5's new plaintexts alone (rung 4's plaintext count, other files only), fitted with the "
                               "same three recipes and scored on the same rows; its difference from rung 4 reads what other files of the "
                               "same families buy for the original files at the same plaintext count, and its difference from rung 5 what "
                               "the original files' own chunks add on top of it; never a verdict"}
        for role in ROLES:
            rs_ = reads.get(f"{SHIFT}_{role}")
            if rs_ is None:
                continue
            shift_block["readings"][role] = {"ext_real_top1": rs_["ext_real_top1"], "ext_real_correct": rs_["ext_real_correct"],
                                             "builder_eval_top1": rs_["builder_eval_top1"],
                                             "ext_per_family": {f: rs_["ext_per_family"][f] for f in REAL_FAMILIES}}
            for kk, key in ((N_FIRST, "difference_from_rung_4"), (N_FIRST + 1, "difference_from_rung_5")):
                rk_ = reads.get(f"r{kk}_{role}")
                if rk_ is not None:
                    shift_block[key][role] = round(rs_["ext_real_top1"] - rk_["ext_real_top1"], 4)
        doc = dict(common, stage="run", environment=environment(), launch_environment=launch_env, launch_number=launch_no,
                   complete=bool(complete), missing_roles=[n for n in order if n not in records],
                   fits=records, readings=reads,
                   ext_real_top1={n: (reads[n] or {}).get("ext_real_top1") for n in reads},
                   ext_real_correct={n: (reads[n] or {}).get("ext_real_correct") for n in reads},
                   ext_top1={n: (reads[n] or {}).get("ext_top1") for n in reads},
                   builder_eval_top1={n: (reads[n] or {}).get("builder_eval_top1") for n in reads},
                   ext_per_family={n: (reads[n] or {}).get("ext_per_family") for n in reads},
                   curves=curves, roles=list(ROLES), n_rungs=n_rungs, n_first_decade_rungs=N_FIRST, denominators=denominators,
                   doublings=doublings, log2_chunks=log2x, log2_chunks_second_decade=log2x_second,
                   model_slope_per_doubling=ms, logistic_slope_per_doubling=ls, depth3_tree_slope_per_doubling=ts,
                   slope_model_minus_logistic=(None if ms is None or ls is None else round(ms - ls, 6)),
                   slope_model_minus_depth3_tree=(None if ms is None or ts is None else round(ms - ts, 6)),
                   top_rung_top1=top_top1,
                   top_rung_model_minus_logistic=(None if top_top1["model"] is None or top_top1["logistic"] is None
                                                  else round(top_top1["model"] - top_top1["logistic"], 4)),
                   top_rung_model_minus_depth3_tree=(None if top_top1["model"] is None or top_top1["depth3_tree"] is None
                                                     else round(top_top1["model"] - top_top1["depth3_tree"], 4)),
                   bar={"slope_per_doubling": float(P["bar"]["slope_per_doubling"]),
                        "bootstrap_lower_bound_gt": float(P["bar"]["bootstrap_lower_bound_gt"]),
                        "n_boot": n_boot, "bootstrap_seed": boot_seed, "lead_rule": str(P["bar"]["lead_rule"])},
                   slope_bootstrap=boot or {}, lead_at_top=lead or {}, shift_arm=shift_block,
                   n_ext_real_rows=n_real, n_ext_rows=n_ext, n_eval_rows=n_eval,
                   ext_real_families=list(REAL_FAMILIES), ext_synthetic_families=list(SYNTH_FAMILIES),
                   fit_families=list(fit_names), fit_rows_per_family=fit["rows_per_family"], fit2_rows_per_family=fit2["rows_per_family"],
                   reference_top1=dict(P["reference_top1"]), reproduction_top1=repro_top1,
                   reproduction_drift={role: (None if repro_top1[role] is None
                                              else round(repro_top1[role] - float(P["reference_top1"][role]), 6)) for role in ROLES},
                   reference_first_decade={r: list(P["reference_first_decade"][r]) for r in ROLES},
                   reproduction_first_decade=repro_first,
                   reproduction_first_decade_drift={r: [None if a is None else round(a - float(b), 6)
                                                        for a, b in zip(repro_first[r], P["reference_first_decade"][r])] for r in ROLES},
                   shuffled_label_accuracy_ext=(reads.get("null") or {}).get("ext_top1"),
                   shuffled_label_accuracy_eval=(reads.get("null") or {}).get("builder_eval_top1"),
                   shuffled_label_accuracy_real=(reads.get("null") or {}).get("ext_real_top1"),
                   null_control=records.get("null"), null_rows=int(partition["rungs"][-1]["n_rows"]),
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
                       "fit2_arrays_sha256": {k: v["sha256"] for k, v in fit2_hashes.items()},
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

        def rk_of(k):
            return partition["shift_arm"] if k == SHIFT else partition["rungs"][k - 1]

        def rows_of(k):
            return rows_all[n_rungs] if k == SHIFT else rows_all[k - 1]

        def block_of(k):
            if k not in blocks:
                blocks[k] = Block(X_all, rows_of(k), ncols, f"{k if k == SHIFT else 'r' + str(k)}")
            return blocks[k]

        def fit_role(name, role, cand, y_fit, stage, k):
            rk = rk_of(k)
            fp = fingerprint(prereg=stamp, seed=seed, seed2=seed2, head=role, cand=cand, stage=stage, rung=k, rows=rk["sorted_sha256"],
                             eval=partition["eval_idx_sha256"], ext=ext_hashes["X"]["sha256"], fit=fit_hashes["X"]["sha256"],
                             fit2=fit2_hashes["X"]["sha256"])
            store.log(f"run_{name}", fp, "rung_bound", rung=k, rung_sorted_sha256=rk["sorted_sha256"])
            blk = None if store.load(f"run_{name}", fp) is not None else block_of(k)   # a banked checkpoint needs no block
            r, pe = run_fit(store, f"run_{name}", fp, role, cand, seed, blk, y_fit, g_all, Xs, ys, fam_s, stage, caps,
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
                top_rows = rows_all[n_rungs - 1]
                y_sh = y_all.copy()
                sub = y_all[top_rows].copy()
                np.random.default_rng([seed2, NULL_STREAM_WORD]).shuffle(sub)
                y_sh[top_rows] = sub
                partition["null_y_shuffled_sha256"] = _sha(sub)
                partition["null_labels_permuted"] = bool(not np.array_equal(sub, y_all[top_rows]))
                partition["null_labels_same_multiset"] = bool(np.array_equal(np.sort(sub), np.sort(y_all[top_rows])))
                partition["null_rule"] = (f"the top rung's labels, in rung order, permuted by np.random.default_rng([{seed2}, "
                                          f"{NULL_STREAM_WORD}]).shuffle; hashed in rung order")
                if not args.smoke and not (partition["null_labels_permuted"] and partition["null_labels_same_multiset"]):
                    raise NotRun("the null control's labels are not a permutation of the top rung's own labels")
                want_null = P.get("null_y_shuffled_sha256_expected")
                if not args.smoke and want_null and partition["null_y_shuffled_sha256"] != want_null:
                    raise NotRun(f"the null control's permuted labels hash to {partition['null_y_shuffled_sha256'][:12]}..., not the "
                                 f"sealed {want_null[:12]}...: the generator state or the label arrays are not the sealed ones")
                rd = fit_role("null", "null", recipes["model"], y_sh, "null", n_rungs)
                del y_sh, sub
                if rd and not args.smoke:
                    tol = float(P["null_tolerance"])
                    if rd["ext_top1"] > chance + tol or rd["builder_eval_top1"] > chance + tol:
                        raise NotRun(f"null control read {rd['ext_top1']} on the extension rows and {rd['builder_eval_top1']} on "
                                     f"the sealed evaluation rows against chance {chance:.6f} + {tol}: the scoring path leaks")
            else:
                k, role = parse_name(step, n_rungs)
                if role not in ROLES or (k != SHIFT and not (1 <= k <= n_rungs)):
                    raise NotRun(f"unknown order step {step!r}")
                rd = fit_role(step, role, recipes[role], y_all, ("shift" if k == SHIFT else "curve" if k > N_FIRST else "reproduction"), k)
                if rd and not args.smoke and k != SHIFT and k <= N_FIRST:
                    ref = float(P["reference_first_decade"][role][k - 1])
                    if k == N_FIRST and ref != float(P["reference_top1"][role]):
                        raise NotRun(f"{step}: the sealed reference_first_decade[{role}][{k - 1}] {ref} is not reference_top1 "
                                     f"{P['reference_top1'][role]}: the sealed references disagree")
                    drift = round(abs(rd["ext_real_top1"] - ref), 6)
                    if drift > float(P["reproduction_tolerance"]):
                        raise NotRun(f"{step} read {rd['ext_real_top1']} on the real-family rows against 0023's banked {ref} "
                                     f"(drift {drift} > {P['reproduction_tolerance']}): the rung, the scoring set or the machinery is "
                                     f"not 0023's")
                if step.endswith("_model") and k in blocks:
                    del blocks[k]                    # the rung's last role is fitted; free its block (the top block too)
            if step == "null" and n_rungs in blocks and order[order.index(step) + 1].split("_")[0] != f"r{n_rungs}":
                del blocks[n_rungs]                  # the null used the top block; the next step is not the top rung - free it
            if step == f"{SHIFT}_model" and SHIFT in blocks:
                del blocks[SHIFT]
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
        # the verdict's bootstrap: every role's SECOND-decade rung vectors on the real rows, one resample per draw for all of them
        by_role = {role: [per_ex[f"r{k}_{role}"][n_eval:][real_mask] for k in range(N_FIRST, n_rungs + 1)] for role in ROLES}
        sl = slope_bootstrap(by_role, log2x_second, gx[real_mask], n_boot, boot_seed)
        boot = {role: {"ci95": [round(float(np.percentile(sl[role], 2.5)), 6), round(float(np.percentile(sl[role], 97.5)), 6)],
                       "n_boot": n_boot, "seed": boot_seed, "mean": round(float(sl[role].mean()), 6)} for role in ROLES}
        for a, b_ in (("model", "logistic"), ("model", "depth3_tree")):
            d = sl[a] - sl[b_]
            boot[f"{a}_minus_{b_}"] = {"ci95": [round(float(np.percentile(d, 2.5)), 6), round(float(np.percentile(d, 97.5)), 6)],
                                       "paired": True, "share_of_resamples_with_model_ahead": round(float((d > 0).mean()), 4)}
        boot["unit"] = ("accuracy on the real-family rows per doubling of plaintexts over the second decade (rungs "
                        f"{N_FIRST}..{n_rungs}); cluster bootstrap over the scored real chunks")
        # the lead at the top rung (and, informationally, at rung 4): paired cluster bootstrap of the accuracy difference
        lead = {}
        for k in (n_rungs, N_FIRST):
            for a, b_ in (("model", "logistic"), ("model", "depth3_tree")):
                dv = paired_lead_bootstrap(per_ex[f"r{k}_{a}"][n_eval:][real_mask], per_ex[f"r{k}_{b_}"][n_eval:][real_mask],
                                           gx[real_mask], n_boot, boot_seed)
                lo, hi = round(float(np.percentile(dv, 2.5)), 6), round(float(np.percentile(dv, 97.5)), 6)
                rd_a = readings(f"r{k}_{a}"); rd_b = readings(f"r{k}_{b_}")
                lead[f"r{k}_{a}_minus_{b_}"] = {
                    "point": round(rd_a["ext_real_top1"] - rd_b["ext_real_top1"], 4), "ci95": [lo, hi], "n_boot": n_boot, "seed": boot_seed,
                    "share_of_resamples_with_model_ahead": round(float((dv > 0).mean()), 4),
                    "reading": ("MODEL_LEADS" if lo > 0 else "LINEAR_LEADS" if hi < 0 else "NO_SEPARATION") if b_ == "logistic"
                               else ("MODEL_LEADS" if lo > 0 else "TREE_LEADS" if hi < 0 else "NO_SEPARATION")}
        lead["unit"] = "accuracy on the real-family rows; paired cluster bootstrap over the scored real chunks, the slope bootstrap's resamples"
        lead["verdict_pair"] = f"r{n_rungs}_model_minus_logistic"
        out = assemble(True, launch_no, ci=ci, boot=boot, lead=lead)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "run", "reason": str(e),
                       "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])}, fh, indent=2)
        return 4
    print(f"[run] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; second-decade model "
          f"slope {out['model_slope_per_doubling']} per doubling (bootstrap {out['slope_bootstrap'].get('model', {}).get('ci95')}), "
          f"logistic {out['logistic_slope_per_doubling']}, depth-3 tree {out['depth3_tree_slope_per_doubling']}; model rungs "
          f"{[p['ext_real_top1'] for p in out['curves']['model']['rungs']]}; lead at top "
          f"{out['lead_at_top'].get(out['lead_at_top'].get('verdict_pair'), {}).get('reading')}; null {out['shuffled_label_accuracy_real']}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
