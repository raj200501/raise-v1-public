#!/usr/bin/env python3
"""A budgeted, SYMMETRIC recipe search on REAL content at 4096 (preregistration 0022).

Question. 0021 read REAL_FIT_FAILS: 0014's searched model M4, fitted on 26346 rows of real content (the
chunks of 0018's five pinned real files that its sealed evaluation corpus does not use), identifies the
encoder on the 38452 sealed real-family rows at 0.1193 - and a depth-3 tree fitted on the same rows reads
0.0929, 0014's standardised logistic 0.1179, so the margin over the best trivial baseline was 0.0264 of
the 0.05 the record demands. 0021's own scope deferred one question: "what a recipe searched on real
content would do (the search is a different preregistration)". This is that preregistration. Every HEAD
with a hyperparameter - the model, the logistic, the depth-3 tree, the deep tree - gets 0014's roster
VERBATIM (eight enumerated recipes, 0003's recipe first in every list), selected by 0014's rule in one stage on a chunk-rule
holdout cut INSIDE the real fit block, and each head's winner is fitted once on the whole fit block and
scored once on 0018's scoring set, row for row. The bar is OPERATING_RULES 4a's: the best searched
baseline on the real-family rows, each floored at what 0021 measured for it, plus 0.05.

Two invocations, so that selection can be shown never to have held a scored row:

  --stage select   gathers the holdout and the stage block from the FIT corpus only, runs every roster
                   through the stage, and writes the --selection-out file.
  --stage confirm  refuses without that file; materialises the scoring set (the sealed 260000-row
                   evaluation set plus the whole 61409-row extension corpus - 0018's and 0021's scoring
                   set) and the fit block once; fits the roles in the PREREGISTERED ORDER - the four
                   reproduction arms tied to 0021's banked readings, the null control, the knob-free
                   heads, the searched baseline heads, and the model's selected recipe LAST - and
                   re-assembles the artifact after every role, so an abandoned stage reads VOID rather
                   than vanishing.

Everything the script does is read from prereg["scope"]["roster"] (sealed by the chain): the heads and
their rosters, the holdout rule, the stage, the caps, the fit order, the floors. It banks what it actually
did - row counts, index hashes, measured overlaps, per-candidate records with status, the append-only
attempt ledger, the environment - and the frozen reader compares those against the constants sealed in it.

Partition (the builder cache's y and g give the sealed evaluation set; the fit corpus gives the rest):
  eval        grouped_split(seed, eval_frac, cap) held-out chunks - 0003's sealed evaluation set, scored
  ext         the whole extension corpus, scored; the clause is over its five real-file families
  fit block   every row of the real-content fit corpus, in the seeded permutation 0021 fitted it in, so
              the recipes' last-10% validation split is a random tenth and 0021's fits reproduce exactly
  holdout     fit-block rows whose chunk id satisfies the preregistered rule (a rule, not a draw)
  fit pool    the other fit-block rows, in fit-block order; the single stage fits on all of them

Selection per head: every candidate is fitted on the fit pool and scored on the holdout; the top `keep`
(1) is the head's recipe; ties at 4 decimals go to the LOWER roster index, so a tie can only favour the
recipe listed first, and every roster lists the record's recipe first. Knob-free heads skip selection.

Reuses tools/pivot/run_recipe_search.py's machinery (blocks, fits, checkpoints, heartbeat, memory
accounting, launch rules, the selection rule) and tools/pivot/run_realfit.py's corpora, split and
row-identity scan. One thing is replaced: run_recipe_search.score() names per-family accuracies over the
BUILDER's eight families, which the holdout does not contain; here every record's per_family is over the
families actually present in its scoring set (the five real families on the holdout; the builder's eight
plus the eight 'ext:'-prefixed extension families on the confirmatory set).

Digest convention, for every hash banked here: sha256 of np.ascontiguousarray(a).tobytes(); index arrays
are int64 arrays in their order; y is the stored int16, g the stored int32; sorted sets are
np.sort(...).astype(np.int64).
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
    cluster_ci, _rss_gb, _rss_total_gb, grouped_split, ranked_ids, predict_chunked, FAMILIES, N_CONFIGS, CONFIG_NAMES)
from run_realfit import corpus_block, _array_sha, STRUCTURED_TEXT, HIGH_ENTROPY  # noqa: E402
from corpus_ext import EXT_FAMILIES, REAL_FAMILIES, SYNTH_FAMILIES  # noqa: E402
from corpus_realfit import FAMILIES as FIT_FAMILIES  # noqa: E402

FROZEN_HEADS = ["majority", "stratified", "depth3_tree", "logistic"]
EXPANDED_HEADS = FROZEN_HEADS + ["best_single_feat", "deep_tree"]
# The four reproduction arms: 0021's banked readings of these four recipes on this fit block and these rows
# (real_incumbent = M1, real_model = M4, real_logistic = L3, floor_tree3 = D1). Each is tied to (head, protocol key
# naming the roster id). When that head SELECTED the reference recipe, the head's own confirmatory record is the
# reproduction (0014's convention for the incumbent) and the arm is banked as aliased rather than fitted twice.
REPRO_ARMS = {"repro_m1": ("model", "incumbent_id"), "repro_m4": ("model", "model_reference_id"),
              "repro_l3": ("logistic", "logistic_reference_id"), "repro_d1": ("depth3_tree", "tree_reference_id")}


def score_by_family(est, Xs32, ys, fam_s):
    """run_recipe_search.score() with per_family over the families PRESENT in the scoring set."""
    correct = (predict_chunked(est, Xs32) == ys).astype(np.int8)
    fams = sorted(set(fam_s.tolist()))
    return {"top1": round(float(correct.mean()), 4),
            "top1_non_gutenberg": round(float(correct[fam_s != "gutenberg"].mean()), 4),
            "per_family": {f: round(float(correct[fam_s == f].mean()), 4) for f in fams}}, correct


_rrs.score = score_by_family   # run_fit looks the scorer up in its own module at call time


def fit_block_partition(yr, gr, fam_r, fit_names, seed, rule, stage):
    """The fit block, the holdout and the fit pool, cut from the fit corpus by the sealed rule, with every hash and count
    the runner banks for them. Module-level so the preregistration generator and the pre-freeze check CALL it rather
    than retype it (docs/OPERATING_RULES.md section 4; CORRECTIONS.md 2026-09-16 and 2026-09-17).

    Returns (fit_order, hold, fitpool, stage_rows, keys). fit_order is 0021's fit block row for row - the seeded
    permutation of the corpus's rows, so the recipes' last-10% validation split is a random tenth - and the holdout
    is the fit-block rows whose chunk id satisfies the rule, in fit-block order; the fit pool is the rest."""
    fit_order = np.random.default_rng(seed).permutation(len(yr))
    gr = np.asarray(gr); gr_o = gr[fit_order]; fam_o = np.asarray(fam_r)[fit_order]
    if rule["rule"] != "chunk_id_mod":
        raise ValueError(f"unknown holdout rule {rule['rule']!r}")
    in_hold = (gr_o % int(rule["modulus"])) == int(rule["residue"])
    hold = fit_order[in_hold]; fitpool = fit_order[~in_hold]
    stage_rows = fitpool if stage["rows"] == "all" else fitpool[:int(stage["rows"])]
    keys = {"fit_rows": int(len(fit_order)), "fit_idx_sha256": _sha(fit_order),
            "fit_sorted_sha256": _sha(np.sort(fit_order).astype(np.int64)),
            "fit_order_rule": f"np.random.default_rng({seed}).permutation of the fit corpus's rows, so the recipes' "
                              "last-10% validation split is a random tenth rather than one family (0021's fit block)",
            "fit_block_chunks": int(np.unique(gr).size),
            "holdout_rule": f"fit-block chunk_id % {rule['modulus']} == {rule['residue']}",
            "n_holdout_rows": int(len(hold)), "n_holdout_chunks": int(np.unique(gr_o[in_hold]).size),
            "holdout_idx_sha256": _sha(hold), "holdout_sorted_sha256": _sha(np.sort(hold).astype(np.int64)),
            "holdout_chunks_sha256": _sha(np.sort(np.unique(gr_o[in_hold])).astype(np.int64)),
            "holdout_rows_per_family": {f: int((fam_o[in_hold] == f).sum()) for f in fit_names},
            "holdout_chunks_per_family": {f: int(np.unique(gr_o[in_hold & (fam_o == f)]).size) for f in fit_names},
            "n_fitpool_rows": int(len(fitpool)), "n_fitpool_chunks": int(np.unique(gr_o[~in_hold]).size),
            "fitpool_idx_sha256": _sha(fitpool), "fitpool_sorted_sha256": _sha(np.sort(fitpool).astype(np.int64)),
            "fitpool_chunks_sha256": _sha(np.sort(np.unique(gr_o[~in_hold])).astype(np.int64)),
            "fitpool_rows_per_family": {f: int((fam_o[~in_hold] == f).sum()) for f in fit_names},
            "stage_rows": [int(len(stage_rows))], "stage_keep": [int(stage["keep"])],
            "stage_chunks": [int(np.unique(gr[stage_rows]).size)],
            "stage_idx_sha256": [_sha(stage_rows)], "stage_sorted_sha256": [_sha(np.sort(stage_rows).astype(np.int64))],
            "n_chunks_holdout_and_fitpool": int(np.intersect1d(np.unique(gr_o[in_hold]), np.unique(gr_o[~in_hold])).size),
            "n_holdout_rows_in_fitpool": int(np.intersect1d(hold, fitpool).size)}
    return fit_order, hold, fitpool, stage_rows, keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["select", "confirm"], required=True)
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0022-realsearch-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--ext", default=os.path.join(REPO, "data", "pivot", "ext_c4096.npz"))
    ap.add_argument("--realfit", default=os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "realsearch_4096_ckpt"))
    ap.add_argument("--selection-out", default=os.path.join(REPO, "artifacts", "pivot", "realsearch_4096_selection.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "realsearch_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "realsearch_4096_scores.json"))
    ap.add_argument("--smoke", action="store_true",
                    help="override the corpora with the prereg file's 'smoke' block; every output is stamped "
                         "smoke=true, written only to the scratchpad, and the reader VOIDs it")
    args = ap.parse_args()
    out_stem = os.path.splitext(os.path.basename(args.out))[0]
    art = os.path.join(REPO, "artifacts") + os.sep
    outputs = {"--workdir": args.workdir, "--selection-out": args.selection_out, "--out": args.out,
               "--scores-out": args.scores_out}
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
    roster = prereg["scope"]["roster"]
    P = dict(roster["protocol"]); heads = roster["heads"]
    if args.smoke:
        P.update(prereg.get("smoke", {}))
    stamp = f"{prereg['id']}-{prereg['slug']}"
    seed = int(P["seed"]); eval_frac = float(P["eval_frac"]); top_rung = int(P["top_rung"]); caps = P["caps"]
    if list(P["families"]) != FAMILIES or list(P["ext_families"]) != EXT_FAMILIES or list(P["fit_families"]) != FIT_FAMILIES:
        print("REFUSING: a sealed family order is not the corpus module's order", file=sys.stderr)
        return 3
    by_id = {c["id"]: c for h in heads for c in h["candidates"]}
    by_head = {h["id"]: h for h in heads}
    if len(by_id) != sum(len(h["candidates"]) for h in heads):
        print("REFUSING: candidate ids must be unique across the roster", file=sys.stderr)
        return 3
    model_head = next((h for h in heads if h["side"] == "model"), None)
    if model_head is None or model_head["candidates"][0]["id"] != P["incumbent_id"]:
        print("REFUSING: the incumbent must lead the model roster", file=sys.stderr)
        return 3
    if any(h not in by_head for h in EXPANDED_HEADS + [model_head["id"]]):
        print(f"REFUSING: the roster must carry the heads {EXPANDED_HEADS + [model_head['id']]}", file=sys.stderr)
        return 3
    for arm, (hid, key) in REPRO_ARMS.items():
        want = P[key]
        head_ids = [c["id"] for c in by_head[hid if hid != "model" else model_head["id"]]["candidates"]]
        if want not in head_ids:
            print(f"REFUSING: reproduction arm {arm} names {want!r}, which is not on head {hid}'s roster", file=sys.stderr)
            return 3
    if list(P["confirm_order"]) != list(REPRO_ARMS) + ["null"] + EXPANDED_HEADS + [model_head["id"]]:
        print(f"REFUSING: the sealed confirm_order must be {list(REPRO_ARMS) + ['null'] + EXPANDED_HEADS + [model_head['id']]}",
              file=sys.stderr)
        return 3
    if len(P["stages"]) != 1 or P["stages"][0]["rows"] != "all" or int(P["stages"][0]["keep"]) != 1:
        print("REFUSING: this design has exactly one selection stage on the whole fit pool, keeping one", file=sys.stderr)
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
        # The sealed threshold is unchanged; the runner waits for the box to settle rather than refusing on the first sample.
        # A confirm launched right after select sees the three fit threads' load decaying for about a minute (0022 pre-freeze
        # review, runner lens, finding 1), and a refusal there stops an unattended chain for nothing.
        for _ in range(20):
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
    # [1c] the real-content FIT corpus (0021's): searched and fitted, never scored
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
        sealed_fit_x = (((roster["protocol"].get("fit_corpus") or {}).get("arrays") or {}).get("X") or {}).get("sha256")
        sealed_ext_x = (((roster["protocol"].get("ext_corpus") or {}).get("arrays") or {}).get("X") or {}).get("sha256")
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

    # [2] the sealed split (0003's by construction) gives the scored evaluation set; the fit block is 0021's permutation
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e = fam_all[ev]
    ev_chunks = np.unique(g[ev])
    fit_order, hold, fitpool, stage_rows, fit_part = fit_block_partition(yr, gr, fam_r, fit_names, seed, P["holdout"], P["stages"][0])
    st = P["stages"][0]
    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam_e != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev), "eval_g_sha256": _sha(np.asarray(g[ev])),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64)),
                 "families": list(FAMILIES), **fit_part,
                 "pool_chunks_shared_with_ext": int(np.intersect1d(np.unique(g[tr]), np.unique(gx)).size),
                 "eval_chunks_shared_with_ext": int(np.intersect1d(ev_chunks, np.unique(gx)).size),
                 "fit_chunks_shared_with_ext": int(np.intersect1d(np.unique(gr), np.unique(gx)).size),
                 "fit_chunks_shared_with_builder": int(np.intersect1d(np.unique(gr), np.unique(g)).size),
                 "fit_source_chunks_shared_with_ext": int(len(fit_src & ext_src)),
                 "n_fit_source_chunks": int(len(fit_src)), "n_ext_source_chunks": int(len(ext_src))}
    # Row identity, measured rather than assumed: no scored row may sit in the fit block (which contains the holdout and
    # the fit pool). Every scored row is digested once; the fit corpus is checked against those digests.
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
            print(f"REFUSING: the fit blocks {bad} do not hash to the sealed fit_block_hashes", file=sys.stderr)
            return 3
        if partition["fit_rows_identical_to_a_scored_row"] != 0:
            print(f"REFUSING: {partition['fit_rows_identical_to_a_scored_row']} fit rows are byte-identical to a scored row; "
                  f"the clause's own corpus must share nothing with anything scored", file=sys.stderr)
            return 3
        if partition["n_chunks_holdout_and_fitpool"] or partition["n_holdout_rows_in_fitpool"]:
            print("REFUSING: the holdout and the fit pool share a chunk or a row", file=sys.stderr)
            return 3
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, fit block {partition['fit_rows']}"
          f"/{partition['fit_block_chunks']} chunks, holdout {partition['n_holdout_rows']}/{partition['n_holdout_chunks']} chunks "
          f"{partition['holdout_rows_per_family']}, fit pool {partition['n_fitpool_rows']}/{partition['n_fitpool_chunks']} chunks",
          flush=True)

    store = Store(args.workdir)
    roster_sha = sha_obj(roster)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "roster_sha256": roster_sha, "roster": roster, "corpus": corpus, "ext_corpus": ext, "fit_corpus": fit,
              "partition": partition, "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
              "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    yr_np = np.asarray(yr); gr_np = np.asarray(gr)

    # ================================================================================ stage select
    if args.stage == "select":
        if os.path.exists(args.selection_out) and not args.smoke:
            print(f"REFUSING: {os.path.relpath(args.selection_out, REPO)} exists; selection is done once", file=sys.stderr)
            return 3
        gathers = []

        def gather(name, rows):
            # every gather is from the FIT corpus; the count of scored rows in it is the row-identity scan's, banked
            gathers.append({"name": name, "source": "fit_corpus", "n_rows": int(len(rows)), "idx_sha256": _sha(rows),
                            "n_rows_identical_to_a_scored_row": 0 if partition["fit_rows_identical_to_a_scored_row"] == 0
                            else None})
            return rows

        started = _utc()
        try:
            launch_no = store.launches("select", False)
            hrows = gather("holdout", hold)
            Xh = np.ascontiguousarray(Xr[hrows], dtype=np.float32); yh = yr_np[hrows]; fam_h = fam_r[hrows]
            srows = gather("stage1", stage_rows)
            block = Block(Xr, srows, ncols, "stage1")
            rows_sha = partition["stage_idx_sha256"][0]
            selection = {h["id"]: {"side": h["side"], "stages": [], "selected_id": None} for h in heads}
            for h in heads:
                hid = h["id"]; entry = selection[hid]
                if len(h["candidates"]) == 1:
                    continue      # knob-free heads are fitted only at the confirmatory stage
                recs = []
                for c in h["candidates"]:
                    fp = fingerprint(prereg=stamp, seed=seed, head=hid, cand=c, stage=1, rows=rows_sha,
                                     holdout=partition["holdout_idx_sha256"], fit=fit_hashes["X"]["sha256"])
                    r, _ = run_fit(store, f"sel1_{hid}_{c['id']}", fp, hid, c, seed, block, yr_np, gr_np,
                                   Xh, yh, fam_h, "selection-1", caps)
                    recs.append(r)
                ranked = ranked_ids(recs)
                entry["stages"].append({"stage": 1, "n_fit_rows": int(len(srows)), "fit_rows_sha256": rows_sha,
                                        "records": recs, "eligible_ranked_ids": ranked, "advanced_ids": ranked[:int(st["keep"])]})
            del block
            for hid, entry in selection.items():
                if entry["stages"]:
                    last = entry["stages"][-1]
                    entry["selected_id"] = last["advanced_ids"][0] if last["advanced_ids"] else None
                else:
                    entry["selected_id"] = by_head[hid]["candidates"][0]["id"]
                print(f"      head {hid:<18} selected {entry['selected_id']}", flush=True)
            sel_secs = {hid: round(sum((r.get("seconds") or 0) for s in e["stages"] for r in s["records"]), 1)
                        for hid, e in selection.items()}
            out = dict(common, stage="select", gathers=gathers,
                       scored_rows_gathered_in_selection=int(partition["fit_rows_identical_to_a_scored_row"]),
                       environment=env, launch_environment=launch_env, launch_number=launch_no,
                       selection=selection, selected_ids={hid: e["selected_id"] for hid, e in selection.items()},
                       ledger=store.ledger(),
                       cost={"selection_seconds_by_head": sel_secs,
                             "selection_seconds_total": round(sum(sel_secs.values()), 1),
                             "wall_seconds_this_invocation": round(time.perf_counter() - t_all, 1),
                             "interruptions_by_head": {hid: sum((r.get("interruptions_before_this_fit") or 0)
                                                                for s in e["stages"] for r in s["records"])
                                                       for hid, e in selection.items()}},
                       selection_started_utc=started, selection_finished_utc=_utc())
        except NotRun as e:
            print(f"NOT RUN: {e}", file=sys.stderr)
            with open(not_run_path, "w") as fh:
                json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "select",
                           "reason": str(e), "utc": _utc(), "smoke": bool(args.smoke),
                           "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])}, fh, indent=2)
            return 4
        os.makedirs(os.path.dirname(args.selection_out), exist_ok=True)
        with open(args.selection_out + ".tmp", "w", encoding="utf-8") as fh:
            fh.write(_rrs.canon(out))
        os.replace(args.selection_out + ".tmp", args.selection_out)
        print(f"[select] wrote {os.path.relpath(args.selection_out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; "
              f"selected {out['selected_ids']}", flush=True)
        return 0

    # =============================================================================== stage confirm
    if not args.smoke and os.path.exists(args.out):
        try:
            _prev = json.load(open(args.out, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            _prev = {}
        if _prev.get("complete") is True:
            print(f"REFUSING: {os.path.relpath(args.out, REPO)} is a complete confirmatory artifact; one confirmation per run "
                  f"(a relaunch would rewrite launch_number, the timestamps and the ledger)", file=sys.stderr)
            return 3
    if not os.path.exists(args.selection_out):
        print(f"REFUSING: {os.path.relpath(args.selection_out, REPO)} absent; run --stage select first", file=sys.stderr)
        return 3
    sel_bytes = open(args.selection_out, "rb").read()
    selection_sha = hashlib.sha256(sel_bytes).hexdigest()
    sel_doc = json.loads(sel_bytes)
    if sel_doc.get("roster_sha256") != roster_sha or sel_doc.get("preregistration") != stamp \
            or bool(sel_doc.get("smoke")) != bool(args.smoke) or sel_doc.get("stage") != "select":
        print("REFUSING: the selection file was not produced under this preregistration's sealed roster", file=sys.stderr)
        return 3
    for e in store.ledger():
        if e.get("name", "").startswith("confirm_") and e.get("selection_sha256") not in (None, selection_sha):
            print("REFUSING: an earlier confirmatory ledger entry carries a different selection hash", file=sys.stderr)
            return 3
    selected = sel_doc["selected_ids"]
    for hid, entry in sel_doc["selection"].items():
        if entry["stages"]:
            last = entry["stages"][-1]
            if ranked_ids(last["records"])[:1] != ([entry["selected_id"]] if entry["selected_id"] else []):
                print(f"REFUSING: head {hid}'s selected id is not the rule's winner from its own records", file=sys.stderr)
                return 3
    mh = model_head["id"]
    if selected.get(mh) is None or any(selected.get(h) is None for h in EXPANDED_HEADS):
        print("REFUSING: a head has no selected recipe; a symmetric search with a missing head is not symmetric", file=sys.stderr)
        return 3
    aliased = {}
    for arm, (hid, key) in REPRO_ARMS.items():
        head_id = mh if hid == "model" else hid
        if selected.get(head_id) == P[key]:
            aliased[arm] = head_id
    print(f"[confirm] selected {selected}; reproduction arms aliased to a head's own fit: {aliased}", flush=True)

    started = None                                   # set to the confirm stage's first launch below
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev]); n_eval = int(len(ev)); n_ext = int(len(yx))
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}
    r4 = lambda v: round(float(v), 4)  # noqa: E731
    order = list(P["confirm_order"])
    names_expected = [n for n in order if n not in aliased]

    def readings(name):
        """Split one per-example vector into the builder-evaluation reading and the extension readings (0021's shape)."""
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
                "builder_eval_per_family": {f: r4(rep[fam_e == f].mean()) for f in FAMILIES}}

    def reading_of(name):
        """A role's readings, following an aliased reproduction arm to the head that carries it."""
        return readings(aliased.get(name, name))

    def assemble(complete, launch_no, ci=None):
        reads = {n: readings(n) for n in names_expected if per_ex.get(n) is not None}
        n_real = int(np.isin(fam_x, REAL_FAMILIES).sum())
        floors = P["floors"]
        per_head = {}; per_head_searched = {}
        for hid in EXPANDED_HEADS:
            rd = reads.get(hid)
            per_head_searched[hid] = None if rd is None else rd["ext_real_top1"]
            per_head[hid] = None if rd is None else max(rd["ext_real_top1"], float(floors.get(hid, 0.0)))

        def best(hs):
            vals = [(per_head[h], h) for h in hs if per_head[h] is not None]
            if len(vals) != len(hs):
                return None, None
            b = max(vals); return b[0], sorted(h for v, h in vals if v == b[0])[0]
        bf, bfh = best(FROZEN_HEADS); be, beh = best(EXPANDED_HEADS)
        margin = float(P["bar"]["margin"])
        need = lambda b: None if b is None else int(np.ceil(n_real * (b + margin) - 1e-9))  # noqa: E731
        rm = reads.get(mh) or {}
        repro_top1 = {arm: (reading_of(arm) or {}).get("ext_real_top1") for arm in REPRO_ARMS}
        doc = dict(common, stage="confirm", selection_sha256=selection_sha, selection=sel_doc, selected_ids=selected,
                   selected_model_id=selected.get(mh), aliased_reproductions=aliased,
                   environment=environment(), launch_environment=launch_env, launch_number=launch_no,
                   complete=bool(complete), missing_roles=[n for n in names_expected if n not in records],
                   fits=records, readings=reads,
                   ext_real_top1={n: (reads[n] or {}).get("ext_real_top1") for n in reads},
                   ext_real_correct={n: (reads[n] or {}).get("ext_real_correct") for n in reads},
                   ext_top1={n: (reads[n] or {}).get("ext_top1") for n in reads},
                   ext_correct={n: (reads[n] or {}).get("ext_correct") for n in reads},
                   builder_eval_top1={n: (reads[n] or {}).get("builder_eval_top1") for n in reads},
                   ext_per_family={n: (reads[n] or {}).get("ext_per_family") for n in reads},
                   bars={"per_head": per_head, "per_head_searched": per_head_searched, "floors": floors,
                         "frozen_heads": list(FROZEN_HEADS), "expanded_heads": list(EXPANDED_HEADS),
                         "best_frozen_for_bar": bf, "best_frozen_head": bfh,
                         "best_frozen_searched": None if bfh is None else per_head_searched[bfh],
                         "best_expanded_for_bar": be, "best_expanded_head": beh,
                         "best_expanded_searched": None if beh is None else per_head_searched[beh],
                         "margin": margin, "n_real_rows": n_real,
                         "min_correct_real_frozen": need(bf), "min_correct_real_expanded": need(be)},
                   model_real_top1=rm.get("ext_real_top1"), model_real_correct=rm.get("ext_real_correct"),
                   model_ext_top1=rm.get("ext_top1"), model_ext_correct=rm.get("ext_correct"),
                   n_ext_real_rows=n_real, n_ext_rows=n_ext, n_eval_rows=n_eval,
                   ext_real_families=list(REAL_FAMILIES), ext_synthetic_families=list(SYNTH_FAMILIES),
                   fit_families=list(fit_names), fit_rows_per_family=fit["rows_per_family"],
                   reference_top1=dict(P["reference_top1"]), reproduction_top1=repro_top1,
                   reproduction_drift={arm: (None if repro_top1[arm] is None
                                             else round(repro_top1[arm] - float(P["reference_top1"][arm]), 6))
                                       for arm in REPRO_ARMS},
                   shuffled_label_accuracy_ext=(reads.get("null") or {}).get("ext_top1"),
                   shuffled_label_accuracy_eval=(reads.get("null") or {}).get("builder_eval_top1"),
                   null_control=records.get("null"), null_rows=int(len(fit_order)),
                   fit_info_by_name={n: (records.get(n) or {}).get("fit_info") for n in names_expected},
                   ledger=store.ledger(),
                   fit_record_top1_is="each confirmatory record's top1 and top1_non_gutenberg are over the concatenated "
                                      f"{n_eval} + {n_ext} scoring set; per_family is over every family present in it - "
                                      "the builder's eight on the evaluation rows and the eight 'ext:'-prefixed extension "
                                      "families; selection records' per_family is over the holdout's five real families",
                   cluster_ci95_informational=ci or {},
                   cluster_ci95_note="95% cluster-bootstrap intervals over source chunks (2000 resamples), informational",
                   cost={"wall_seconds_this_invocation": round(time.perf_counter() - t_all, 1),
                         "selection_seconds_total": sel_doc["cost"]["selection_seconds_total"],
                         "seconds_by_name": {k: v.get("seconds") for k, v in records.items()},
                         "interruptions_by_name": {k: v.get("interruptions_before_this_fit") for k, v in records.items()},
                         "banked_fit_seconds_total": round(store.banked_seconds("sel") + store.banked_seconds("confirm"), 1),
                         "checkpoints": os.path.relpath(args.workdir, REPO)},
                   confirmatory_started_utc=started, first_launch_utc=first_launch,
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
        any_conf = any(f.startswith("confirm_") and f.endswith(".json") for f in os.listdir(args.workdir))
        launch_no = store.launches("confirm", any_conf)
        with open(os.path.join(args.workdir, "launches.jsonl")) as fh:
            _launches = [json.loads(l) for l in fh if l.strip()]
        first_launch = next(e["utc"] for e in _launches if e.get("stage") == "confirm")   # this stage's first launch, on every launch
        started = first_launch
        Xs = np.empty((n_eval + n_ext, ncols), np.float32)
        fill_f32(Xs[:n_eval], X, ev, ncols); Xs[n_eval:] = Xx
        del Xx
        ys = np.concatenate([ye, np.asarray(yx)]); fam_s = np.concatenate([fam_e, np.array(["ext:" + f for f in fam_x])])
        partition["eval_y_sha256"] = _sha(ye)
        fit_block = Block(Xr, fit_order, ncols, "fit")
        print(f"[confirm] scoring set {n_eval} + {n_ext} rows and fit block {len(fit_order)} rows materialised, anonymous RSS "
              f"{_rss_gb():.2f} GB (total {_rss_total_gb():.2f} GB)", flush=True)
        chance = 1.0 / N_CONFIGS

        def confirm(name, head, cand, y_all, stage):
            fp = fingerprint(prereg=stamp, seed=seed, head=head, cand=cand, stage=stage, rows=partition["fit_sorted_sha256"],
                             eval=partition["eval_idx_sha256"], ext=ext_hashes["X"]["sha256"], fit=fit_hashes["X"]["sha256"],
                             selection=selection_sha)
            store.log(f"confirm_{name}", fp, "selection_bound", selection_sha256=selection_sha)
            r, pe = run_fit(store, f"confirm_{name}", fp, head, cand, seed, fit_block, y_all, gr_np, Xs, ys, fam_s, stage, caps,
                            keep_per_example=True, confirmatory=True)
            records[name] = dict(r, fingerprint=fp,
                                 per_example_sha256=(hashlib.sha256(np.asarray(pe, np.int8).tobytes()).hexdigest()
                                                     if pe is not None else None))
            if pe is not None:
                per_ex[name] = pe
            rd = readings(name)
            if rd:
                print(f"      {name:<18} BUILDER EVAL {rd['builder_eval_top1']} | EXTENSION {rd['ext_top1']} | REAL "
                      f"{rd['ext_real_correct']}/{rd['n_ext_real_rows']} = {rd['ext_real_top1']} {rd['ext_per_family']}", flush=True)
            assemble(False, launch_no)
            return rd

        for step in order:
            if step in REPRO_ARMS:
                if step in aliased:
                    continue                        # the head's own confirmatory fit is the reproduction
                hid, key = REPRO_ARMS[step]
                rd = confirm(step, step, by_id[P[key]], yr_np, "reproduction")
                if rd and not args.smoke:
                    drift = round(abs(rd["ext_real_top1"] - float(P["reference_top1"][step])), 6)
                    if drift > float(P["reproduction_tolerance"]):
                        raise NotRun(f"{step} read {rd['ext_real_top1']} on the real-family rows against 0021's banked "
                                     f"{P['reference_top1'][step]} (drift {drift} > {P['reproduction_tolerance']}): the fit block, "
                                     f"the scoring set or the machinery is not 0021's")
            elif step == "null":
                y_sh = yr_np.copy(); rng.shuffle(y_sh)
                partition["null_y_shuffled_sha256"] = _sha(y_sh)
                partition["null_labels_permuted"] = bool(not np.array_equal(y_sh, yr_np))
                partition["null_labels_same_multiset"] = bool(np.array_equal(np.sort(y_sh), np.sort(yr_np)))
                if not args.smoke and not (partition["null_labels_permuted"] and partition["null_labels_same_multiset"]):
                    raise NotRun("the null control's labels are not a permutation of the fit corpus's own labels")
                # the permuted array must be 0021's, hash for hash: the runner notices a divergent permutation now, not the
                # reader after the model has been fitted and the sealed set scored again (0022 pre-freeze review, condition lens)
                want_null = P.get("null_y_shuffled_sha256_expected")
                if not args.smoke and want_null and partition["null_y_shuffled_sha256"] != want_null:
                    raise NotRun(f"the null control's permuted labels hash to {partition['null_y_shuffled_sha256'][:12]}..., not 0021's "
                                 f"sealed {want_null[:12]}...: the generator state or the label array is not 0021's")
                rd = confirm("null", "null", by_id[selected[mh]], y_sh, "null")
                if rd and not args.smoke:
                    tol = float(P["null_tolerance"])
                    if rd["ext_top1"] > chance + tol or rd["builder_eval_top1"] > chance + tol:
                        raise NotRun(f"null control read {rd['ext_top1']} on the extension rows and {rd['builder_eval_top1']} on "
                                     f"the sealed evaluation rows against chance {chance:.6f} + {tol}: the scoring path leaks")
            elif step == mh or step in EXPANDED_HEADS:
                rd = confirm(step, step, by_id[selected[step]], yr_np, "confirmatory")
                # an aliased reproduction arm is this head's own fit; on a baseline head the runner applies the same tolerance
                # it applies to a fitted arm, before the model is fitted; on the model head only the reader can (as VOID)
                if rd and not args.smoke and step != mh:
                    for arm, hid in aliased.items():
                        if hid == step:
                            drift = round(abs(rd["ext_real_top1"] - float(P["reference_top1"][arm])), 6)
                            if drift > float(P["reproduction_tolerance"]):
                                raise NotRun(f"{step} selected the reference recipe of {arm} and read {rd['ext_real_top1']} against "
                                             f"0021's banked {P['reference_top1'][arm]} (drift {drift} > {P['reproduction_tolerance']}): "
                                             f"the fit block, the scoring set or the machinery is not 0021's")
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
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "confirm", "reason": str(e),
                       "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])}, fh, indent=2)
        return 4
    b = out["bars"]
    print(f"[confirm] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; model "
          f"{out['selected_model_id']} {out['model_real_correct']}/{out['n_ext_real_rows']} = {out['model_real_top1']} on the real "
          f"families against frozen bar {b['best_frozen_for_bar']} ({b['best_frozen_head']}, need {b['min_correct_real_frozen']}) "
          f"/ expanded {b['best_expanded_for_bar']} ({b['best_expanded_head']}, need {b['min_correct_real_expanded']}); "
          f"null {out['shuffled_label_accuracy_ext']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
