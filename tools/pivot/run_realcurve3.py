#!/usr/bin/env python3
"""Runner for preregistration 0025: TWO decades of real plaintexts at 4096 - the fourth doubling of other files.

0024 read SECOND_DECADE_RISES_MODEL_LEADS over seven nested rungs (130 -> 8232 real plaintexts; rungs 5..7 other files of
the same five families, nested on 0021's block): the model's second-decade slope 0.00697 per doubling, the model 0.0039
ahead of the standardised logistic at the top rung with a paired interval [0.0001, 0.0077]. The span was 1.8016 decades,
short of 0003's two-decade scope rule. This run adds ONE more exact per-family doubling from 0025's corpus
(tools/pivot/corpus_realfit3.py: 0024's pool in 0024's order, then a seeded permutation of the remaining and new
candidates), so rung 8 holds 16 x rung 4's plaintexts of every family and the curve spans 2.1026 decades. 0024's seven
rungs and its shift arm are refitted row for row under 0024's own seeds and must reproduce 0024's readings (rung 7's
three roles within 0.0005, the rest within 0.005) and 0024's banked bootstrap intervals exactly (0024's bootstrap seed is
sealed for every verdict interval here). Three of 0021's four trivial-baseline floors are refitted on rungs 7 and 8; the
fourth, B-tree3, is D1 itself (a depth-3 tree, seed 0: fitted once per rung, it would bank the same vector twice). The reader's
verdict is read on the FOURTH DOUBLING: rung 8 minus rung 7 for the model, with a paired cluster-bootstrap interval over
the scored real chunks, into RISES / BELOW_RATE / NOT_RESOLVED / FALLS, suffixed by the lead of the model over the
logistic at rung 8 by 0024's sealed rule. A second shift arm - rung 8's plaintexts from the new files alone at rung 4's
count - is fitted last, informational, beside 0024's.

Everything scored is 0018's sealed corpus and 0003's sealed evaluation set; nothing fitted is ever scored, and the runner
measures that (chunk ids, source-chunk hashes, byte-identical rows) rather than assuming it.

    python3 tools/pivot/run_realcurve3.py --stage run            # the one run; resumable from its checkpoints
    python3 tools/pivot/run_realcurve3.py --stage run --smoke    # scratchpad-only rehearsal on the smoke corpora
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
from run_realfit import corpus_block, _array_sha, STRUCTURED_TEXT, HIGH_ENTROPY, FLOOR_ROLES as FLOOR_ROLES_0021  # noqa: E402
from run_realsearch import score_by_family  # noqa: E402  (installs itself as run_recipe_search.score)
from run_realcurve import ROLES, ols_slope, slope_bootstrap  # noqa: E402
from run_realcurve2 import rung_partition2, paired_lead_bootstrap, N_FIRST, RUNG_STREAM_OFFSET, NULL_STREAM_WORD, SHIFT as SHIFT4  # noqa: E402
from corpus_ext import EXT_FAMILIES, REAL_FAMILIES, SYNTH_FAMILIES  # noqa: E402
from corpus_realfit import FAMILIES as FIT_FAMILIES  # noqa: E402

_rrs.score = score_by_family   # per_family over the families PRESENT in the scoring set (0022's convention)

N_0024_RUNGS = 7               # 0024's rungs 1..7, reproduced row for row under 0024's seeds
SHIFT8 = "s8"                  # the new shift arm: rung 8's plaintexts from the NEW files alone, rung 4's count; informational, last
SHIFT8_STREAM_WORD = 150       # np.random.default_rng([seed3, 150]) permutes the new shift arm's rows (seed3 != seed2, so the stream is new)
STABILITY_SEEDS = 20           # the rung-8 gain and lead intervals are recomputed under this many other seeds (a flag)
# 0021's four floors are B-majority, B-stratified, B-feat1 and B-tree3; B-tree3 is D1 (DecisionTreeClassifier(max_depth=3,
# random_state=0), the curve's depth3_tree role), so on the same rung it would produce the identical per-example vector and the
# reader's pairwise-distinct clause would VOID the run. Three floors are refitted; the tree floor is the rung's depth3_tree reading.
FLOOR_ROLES = [r for r in FLOOR_ROLES_0021 if r != "floor_tree3"]
assert FLOOR_ROLES == ["floor_majority", "floor_stratified", "floor_feat1"]


def sealed_order(n_rungs, n_first=N_FIRST):
    """null on the top rung; rung 7 first (the anchor the fourth-doubling gain and the lead read against: three of 0021's floors refitted,
    then 0024's three roles, so a failed reproduction of the anchor is seen before anything else is spent); then rung 4 (0021's
    block), rungs 1..3 (0023's), rungs 5 and 6 (0024's); rung 8 (the floors first, then the three recipes, the model last); then
    0024's shift arm and the new one. The floors precede a rung's model so that the rung's block is freed after its last recipe."""
    o = (["null"] + [f"r{N_0024_RUNGS}_{r}" for r in FLOOR_ROLES] + [f"r{N_0024_RUNGS}_{r}" for r in ROLES]
         + [f"r{n_first}_{r}" for r in ROLES] + [f"r{k}_{r}" for k in range(1, n_first) for r in ROLES]
         + [f"r{k}_{r}" for k in range(n_first + 1, N_0024_RUNGS) for r in ROLES])
    for k in range(N_0024_RUNGS + 1, n_rungs + 1):
        o += [f"r{k}_{r}" for r in FLOOR_ROLES] + [f"r{k}_{r}" for r in ROLES]
    return o + [f"{SHIFT4}_{r}" for r in ROLES] + [f"{SHIFT8}_{r}" for r in ROLES]


def parse_name(name, n_rungs):
    """'null' -> (n_rungs, 'null'); 'r2_model' -> (2, 'model'); 's4_model' -> ('s4', 'model'); 'r8_floor_feat1' -> (8, 'floor_feat1')."""
    if name == "null":
        return n_rungs, "null"
    rung, role = name.split("_", 1)
    return (rung if rung in (SHIFT4, SHIFT8) else int(rung[1:])), role


def rung_partition3(yr, gr, fam_r, fit_names, seed, denominators, y23, g23, fam_23, seed2, doublings2, seed3, doublings3,
                    max_id_0024, blob_index_by_id, n_old_chunks):
    """0024's seven rungs and its shift arm by calling rung_partition2 on the concatenated [0024 | 0025] arrays under 0024's seed2
    (0025's chunk ids continue 0024's, so the pool prefix is 0024's pool and rungs 5..7 and s4 are 0024's chunk for chunk), then
    the fourth doubling: rung 8 = rung 7 plus, per family, the next n_f x 8 chunks with rows in pool order, rows permuted by
    np.random.default_rng([seed3, 100 + 8]); and the new shift arm: per family the first n_f chunks with rows of rung 8's new
    chunks whose id is above 0024's (0025's corpus), rows permuted by np.random.default_rng([seed3, 150]). Compositions per
    family are banked: chunks from 0024's pool, from 0024's archives' unused candidates (0025's corpus, blob index below 0024's
    blob length) and from the new files. Returns (fit_order, rows_all [rungs 1..8, s4, s8], keys)."""
    fit_order, rows_all2, k2 = rung_partition2(yr, gr, fam_r, fit_names, seed, denominators, y23, g23, fam_23, seed2, doublings2)
    n_r = int(len(yr)); g23 = np.asarray(g23); fam_23 = np.asarray(fam_23); gr = np.asarray(gr)
    base = dict(k2["fit_chunks_per_family"]); rungs = [dict(r) for r in k2["rungs"]]; rows_all = list(rows_all2[:-1]); s4_rows = rows_all2[-1]
    pool = {f: np.sort(np.unique(g23[fam_23 == f])).astype(np.int64) for f in fit_names}
    prev_new = np.sort(np.concatenate([pool[f][:base[f] * (2 ** doublings2 - 1)] for f in fit_names])).astype(np.int64)
    short = dict(k2["pool_short"]); exact = bool(k2["second_decade_exact_doublings"]); nested = bool(k2["rungs_nested"])

    def comp_of(chunks):
        out = {}
        for f in fit_names:
            c = chunks[np.isin(chunks, pool[f])]
            from_0024 = int((c <= max_id_0024[f]).sum())
            rest = c[c > max_id_0024[f]]
            bi = np.asarray([blob_index_by_id.get(int(x), -1) for x in rest], np.int64)
            out[f] = {"from_0024_pool": from_0024, "from_0024_archives_unused": int((bi < n_old_chunks[f]).sum()) if len(bi) else 0,
                      "from_new_files": int((bi >= n_old_chunks[f]).sum()) if len(bi) else 0, "n": int(c.size)}
        return out
    for d in range(doublings2 + 1, doublings2 + doublings3 + 1):
        k = N_FIRST + d
        take = {f: int(base[f] * (2 ** d - 1)) for f in fit_names}
        for f in fit_names:
            if len(pool[f]) < take[f]:
                short[f] = {"needed": take[f], "in_pool": int(len(pool[f]))}
        chosen_new = np.sort(np.concatenate([pool[f][:min(take[f], len(pool[f]))] for f in fit_names])).astype(np.int64)
        rows2 = np.nonzero(np.isin(g23, chosen_new))[0].astype(np.int64)
        combined = np.concatenate([np.asarray(fit_order, np.int64), n_r + rows2])
        rows = combined[np.random.default_rng([int(seed3), RUNG_STREAM_OFFSET + k]).permutation(len(combined))]
        chosen_all = np.sort(np.concatenate([np.unique(gr), chosen_new])).astype(np.int64)
        cpf = {f: int(base[f] + int(np.isin(chosen_new, pool[f]).sum())) for f in fit_names}
        exact = exact and all(cpf[f] == base[f] * (2 ** d) for f in fit_names)
        nested = nested and bool(np.isin(prev_new, chosen_new).all())
        added = chosen_new[~np.isin(chosen_new, prev_new)]
        fam_rows2 = fam_23[rows2]
        rungs.append({"rung": k, "decade": 2, "doubling": d, "denominator": None, "n_chunks": int(chosen_all.size), "n_rows": int(len(rows)),
                      "chunks_per_family": cpf, "new_chunks_per_family": {f: int(np.isin(chosen_new, pool[f]).sum()) for f in fit_names},
                      "n_new_chunks": int(chosen_new.size), "n_new_rows": int(len(rows2)),
                      "rows_per_family": {f: int((fam_r == f).sum() + (fam_rows2 == f).sum()) for f in fit_names},
                      "log2_chunks": round(float(np.log2(chosen_all.size)), 6),
                      "idx_sha256": _sha(rows), "sorted_sha256": _sha(np.sort(rows).astype(np.int64)),
                      "chunks_sha256": _sha(chosen_all), "new_chunks_sha256": _sha(chosen_new),
                      "added_above_previous_rung_sha256": _sha(added), "n_added_above_previous_rung": int(added.size),
                      "added_composition_per_family": comp_of(added),
                      "row_order_rule": f"np.random.default_rng([{int(seed3)}, {RUNG_STREAM_OFFSET + k}]).permutation over "
                                        f"[0021's fit block in its order] + [{n_r} + rows of the rung's 0024/0025 chunks in npz order]"})
        rows_all.append(rows); prev_new = chosen_new
    # the new shift arm: per family the first n_f chunks with rows among the top rung's new chunks that lie in 0025's corpus
    top_added = prev_new
    s8_chunks = np.sort(np.concatenate([top_added[np.isin(top_added, pool[f]) & (top_added > max_id_0024[f])][:base[f]] for f in fit_names])).astype(np.int64)
    rows_s8 = np.nonzero(np.isin(g23, s8_chunks))[0].astype(np.int64)
    s8_rows = (n_r + rows_s8)[np.random.default_rng([int(seed3), SHIFT8_STREAM_WORD]).permutation(len(rows_s8))]
    fam_s8 = fam_23[rows_s8]
    shift8 = {"rung": SHIFT8, "decade": 2, "n_chunks": int(s8_chunks.size), "n_rows": int(len(s8_rows)),
              "chunks_per_family": {f: int(np.isin(s8_chunks, pool[f]).sum()) for f in fit_names},
              "rows_per_family": {f: int((fam_s8 == f).sum()) for f in fit_names},
              "log2_chunks": round(float(np.log2(max(s8_chunks.size, 1))), 6),
              "idx_sha256": _sha(s8_rows), "sorted_sha256": _sha(np.sort(s8_rows).astype(np.int64)), "chunks_sha256": _sha(s8_chunks),
              "composition_per_family": comp_of(s8_chunks),
              "all_chunks_in_the_top_rung": bool(np.isin(s8_chunks, prev_new).all()),
              "all_chunks_above_0024s_ids": bool(all(bool((s8_chunks[np.isin(s8_chunks, pool[f])] > max_id_0024[f]).all()) for f in fit_names)),
              "same_plaintext_count_as_rung_4": bool(s8_chunks.size == rungs[N_FIRST - 1]["n_chunks"]),
              "rule": f"the top rung's new plaintexts from 0025's corpus alone - per family the first n_f chunks with rows of the top rung's "
                      f"added chunks whose id is above 0024's - with rows permuted by np.random.default_rng([{int(seed3)}, {SHIFT8_STREAM_WORD}]); "
                      "informational: read beside rung 4, rung 7, rung 8 and 0024's shift arm as a direct reading of what the fourth "
                      "doubling's files buy alone for the original files at 0021's plaintext count"}
    keys = dict(k2)
    keys.update({"rungs": rungs, "n_rungs": len(rungs), "doublings": int(doublings2 + doublings3), "doublings_0024": int(doublings2),
                 "doublings_0025": int(doublings3), "seed3": int(seed3), "pool_short": short,
                 "pool_chunks_with_rows_per_family": {f: int(len(pool[f])) for f in fit_names},
                 "pool_chunks_with_rows_per_family_0024": {f: int((pool[f] <= max_id_0024[f]).sum()) for f in fit_names},
                 "shift_arm": k2["shift_arm"], "shift_arm_0025": shift8,
                 "rungs_nested": bool(nested), "rung_chunks_strictly_increasing": bool(all(rungs[i + 1]["n_chunks"] > rungs[i]["n_chunks"] for i in range(len(rungs) - 1))),
                 "second_decade_exact_doublings": bool(exact),
                 "fourth_doubling_rule": "rung 8 is rung 7 plus, per family, the next n_f x 8 chunks with rows of the concatenated pool "
                                         "([0024's pool in 0024's order] + [0025's pool positions in order]); every rung therefore holds exactly "
                                         "2^d x n_f plaintexts of every family; rung 8's rows are permuted by np.random.default_rng([seed3, 108])",
                 "doublings_spanned": round(rungs[-1]["log2_chunks"] - rungs[0]["log2_chunks"], 6),
                 "doublings_spanned_second_decade": round(rungs[-1]["log2_chunks"] - rungs[N_FIRST - 1]["log2_chunks"], 6),
                 "doublings_spanned_0024": round(rungs[N_0024_RUNGS - 1]["log2_chunks"] - rungs[0]["log2_chunks"], 6),
                 "n_fit_rows_total": int(n_r + len(y23))})
    return fit_order, rows_all + [s4_rows, s8_rows], keys


def gain_reading(gain, lo, hi, bar):
    """The sealed four-way reading of a one-doubling gain with its paired interval (the reader carries the same function)."""
    if hi < 0:
        return "FOURTH_DOUBLING_FALLS"
    if gain >= bar - 1e-9 and lo > 0:
        return "FOURTH_DOUBLING_RISES"
    if lo > 0:
        return "FOURTH_DOUBLING_BELOW_RATE"
    return "FOURTH_DOUBLING_NOT_RESOLVED"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["run"], default="run")
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0025-realcurve3-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--ext", default=os.path.join(REPO, "data", "pivot", "ext_c4096.npz"))
    ap.add_argument("--realfit", default=os.path.join(REPO, "data", "pivot", "realfit_c4096.npz"))
    ap.add_argument("--realfit2", default=os.path.join(REPO, "data", "pivot", "realfit2_c4096.npz"))
    ap.add_argument("--realfit3", default=os.path.join(REPO, "data", "pivot", "realfit3_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096_ckpt"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "realcurve3_4096_scores.json"))
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
        print(f"REFUSING: a real run must write every output under artifacts/: {[k for k, v in under.items() if not v]}", file=sys.stderr)
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
            if argv and os.path.basename(argv[0]).startswith("python") and any(("tools/pivot/run_" in a or "tools/pivot/corpus_" in a or "tests/mutation_test.py" in a) for a in argv[1:]):
                others.append(f"{pid}: {' '.join(argv)[:120]}")
        if others:
            print("REFUSING: another tools/pivot runner is alive: " + "; ".join(others), file=sys.stderr)
            return 3
    curve = prereg["scope"]["curve"]
    P = dict(curve["protocol"]); recipes = curve["recipes"]
    if args.smoke:
        P.update(prereg.get("smoke", {}))
    stamp = f"{prereg['id']}-{prereg['slug']}"
    seed = int(P["seed"]); seed2 = int(P["seed2"]); seed3 = int(P["seed3"]); eval_frac = float(P["eval_frac"]); top_rung = int(P["top_rung"]); caps = P["caps"]
    denominators = [int(d) for d in P["denominators"]]; doublings2 = int(P["doublings_0024"]); doublings3 = int(P["doublings_0025"])
    n_rungs = len(denominators) + doublings2 + doublings3
    ALL_ROLES = list(ROLES) + list(FLOOR_ROLES)
    if list(P["families"]) != FAMILIES or list(P["ext_families"]) != EXT_FAMILIES or list(P["fit_families"]) != FIT_FAMILIES:
        print("REFUSING: a sealed family order is not the corpus module's order", file=sys.stderr)
        return 3
    if set(recipes) != set(ALL_ROLES) or set(P["recipe_ids"]) != set(ALL_ROLES) or any(recipes[r]["id"] != P["recipe_ids"][r] for r in ALL_ROLES):
        print(f"REFUSING: the sealed recipes must be the roles {ALL_ROLES} carrying the sealed recipe_ids", file=sys.stderr)
        return 3
    if len(denominators) != N_FIRST or any(denominators[i] <= denominators[i + 1] for i in range(N_FIRST - 1)) or denominators[-1] != 1:
        print(f"REFUSING: denominators must be 0023's {N_FIRST}, strictly decreasing and ending at 1", file=sys.stderr)
        return 3
    if doublings2 != N_0024_RUNGS - N_FIRST or doublings3 < 1 or list(P["order"]) != sealed_order(n_rungs):
        print(f"REFUSING: doublings_0024 must be {N_0024_RUNGS - N_FIRST}, doublings_0025 >= 1 and the sealed order {sealed_order(n_rungs)}", file=sys.stderr)
        return 3
    if set(P["reference_top1"]) != set(ROLES) or set(P["reference_first_decade"]) != set(ROLES) \
            or any(len(P["reference_first_decade"][r]) != N_FIRST for r in ROLES) \
            or set(P["reference_0024"]) != set(ROLES) or any(len(P["reference_0024"][r]) != N_0024_RUNGS for r in ROLES) \
            or set(P["reference_shift_arm_0024"]) != set(ROLES):
        print("REFUSING: reference_top1 (0021), reference_first_decade (0023), reference_0024 (seven per role) and reference_shift_arm_0024 "
              "must name every role", file=sys.stderr)
        return 3
    if list(P.get("roles", [])) != ROLES or list(P.get("floor_roles", [])) != FLOOR_ROLES or P.get("null_rows") != "top_rung":
        print(f"REFUSING: the sealed roles must be {ROLES}, the floor roles {FLOOR_ROLES}, and null_rows 'top_rung'", file=sys.stderr)
        return 3
    if int(P["bootstrap"]["seed"]) != seed2:
        print("REFUSING: the bootstrap seed must be 0024's seed2 so that 0024's intervals reproduce exactly", file=sys.stderr)
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
            print(f"REFUSING: the builder cache's X hashes to {cache_x_sha[:12]}..., not the sealed {P['cache_identity']['X_sha256'][:12]}...", file=sys.stderr)
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

    # [1b..1e] the sealed evaluation corpus (scored, never fitted); 0021's, 0024's and 0025's fit corpora (fitted, never scored)
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
        fit3_hashes = _hashes(args.realfit3, "fit3_corpus", "0025 fit corpus")
    except SystemExit as e:
        print(str(e), file=sys.stderr); return 3
    if args.smoke:
        sealed_x = {k: (((curve["protocol"].get(k) or {}).get("arrays") or {}).get("X") or {}).get("sha256")
                    for k in ("ext_corpus", "fit_corpus", "fit2_corpus", "fit3_corpus")}
        got_x = {"ext_corpus": ext_hashes, "fit_corpus": fit_hashes, "fit2_corpus": fit2_hashes, "fit3_corpus": fit3_hashes}
        if any(got_x[k]["X"]["sha256"] == sealed_x[k] for k in sealed_x):
            print("REFUSING: a smoke must never touch the sealed corpora", file=sys.stderr)
            return 3

    def _load(path, metas=False):
        Xa = np.load(_io.BytesIO(_zf.ZipFile(path).read("X.npy"))).astype(np.float32, copy=False)
        with _zf.ZipFile(path) as zf:
            ya = np.load(_io.BytesIO(zf.read("y.npy"))); ga = np.load(_io.BytesIO(zf.read("g.npy")))
            fa = np.load(_io.BytesIO(zf.read("fam.npy")))
            names_ = [str(s) for s in np.load(_io.BytesIO(zf.read("families.npy")))]
            src_ = set(str(v) for v in np.load(_io.BytesIO(zf.read("meta_src_sha256.npy")), allow_pickle=False))
            extra = None
            if metas:
                extra = {"ids": np.load(_io.BytesIO(zf.read("meta_chunk_ids.npy"))), "bidx": np.load(_io.BytesIO(zf.read("meta_blob_chunk_index.npy"))),
                         "fam": np.load(_io.BytesIO(zf.read("meta_chunk_fam.npy")))}
        return Xa, ya, ga, fa, names_, src_, extra
    Xx, yx, gx, famx, ext_names, ext_src, _ = _load(args.ext)
    Xr, yr, gr, famr, fit_names, fit_src, _ = _load(args.realfit)
    X2, y2, g2, fam2, fit2_names, fit2_src, m2 = _load(args.realfit2, metas=True)
    X3, y3, g3, fam3, fit3_names, fit3_src, m3 = _load(args.realfit3, metas=True)
    if ext_names != list(P["ext_families"]) or fit_names != list(P["fit_families"]) or fit2_names != list(P["fit_families"]) or fit3_names != list(P["fit_families"]):
        print("REFUSING: a corpus family order differs from the sealed one", file=sys.stderr)
        return 3
    if Xx.shape[1] != ncols or Xr.shape[1] != ncols or X2.shape[1] != ncols or X3.shape[1] != ncols:
        print("REFUSING: a corpus feature width differs from the builder's", file=sys.stderr)
        return 3
    fam_x = np.array(ext_names)[famx]; fam_r = np.array(fit_names)[famr]; fam_2 = np.array(fit2_names)[fam2]; fam_3 = np.array(fit3_names)[fam3]
    ext = corpus_block(os.path.relpath(args.ext, REPO), ext_hashes, yx, gx, fam_x, ext_names, labels=False)
    fit = corpus_block(os.path.relpath(args.realfit, REPO), fit_hashes, yr, gr, fam_r, fit_names, labels=True)
    fit2 = corpus_block(os.path.relpath(args.realfit2, REPO), fit2_hashes, y2, g2, fam_2, fit2_names, labels=True)
    fit3 = corpus_block(os.path.relpath(args.realfit3, REPO), fit3_hashes, y3, g3, fam_3, fit3_names, labels=True)
    print(f"[1b] sealed evaluation corpus: {ext['n_rows']} rows, {ext['n_chunks']} chunks", flush=True)
    print(f"[1c] 0021 fit corpus: {fit['n_rows']} rows, {fit['n_chunks']} chunks, {fit['rows_per_family']}", flush=True)
    print(f"[1d] 0024 fit corpus: {fit2['n_rows']} rows, {fit2['n_chunks']} chunks, {fit2['rows_per_family']}", flush=True)
    print(f"[1e] 0025 fit corpus: {fit3['n_rows']} rows, {fit3['n_chunks']} chunks, {fit3['rows_per_family']}", flush=True)
    # 0025's chunk ids continue 0024's per family; 0024's pool prefix is intact
    max_id_0024 = {f: int(m2["ids"][m2["fam"] == fi].max()) for fi, f in enumerate(fit2_names)}
    id_continuity = {f: (int(m3["ids"][m3["fam"] == fi].min()) == max_id_0024[f] + 1) if (m3["fam"] == fi).any() else True for fi, f in enumerate(fit3_names)}
    blob_index_by_id = {int(i): int(b) for i, b in zip(m3["ids"], m3["bidx"])}
    n_old_chunks = dict(P["n_whole_chunks_in_0024_blob_per_family"])

    # [2] the sealed split gives the scored evaluation set; the rungs of both decades and the two shift arms are cut here
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e = fam_all[ev]
    ev_chunks = np.unique(g[ev])
    y23 = np.concatenate([np.asarray(y2), np.asarray(y3)]); g23 = np.concatenate([np.asarray(g2), np.asarray(g3)]); fam_23 = np.concatenate([fam_2, fam_3])
    fit_order, rows_all, rung_part = rung_partition3(yr, gr, fam_r, fit_names, seed, denominators, y23, g23, fam_23, seed2, doublings2, seed3, doublings3,
                                                     max_id_0024, blob_index_by_id, n_old_chunks)
    n_r = int(len(yr))
    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam_e != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev), "eval_g_sha256": _sha(np.asarray(g[ev])),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64)),
                 "families": list(FAMILIES), **rung_part,
                 "chunk_ids_0025_continue_0024s_per_family": id_continuity, "max_chunk_id_0024_per_family": max_id_0024,
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
                 "fit3_chunks_shared_with_ext": int(np.intersect1d(np.unique(g3), np.unique(gx)).size),
                 "fit3_chunks_shared_with_builder": int(np.intersect1d(np.unique(g3), np.unique(g)).size),
                 "fit3_chunks_shared_with_fit": int(np.intersect1d(np.unique(g3), np.unique(gr)).size),
                 "fit3_chunks_shared_with_fit2": int(np.intersect1d(np.unique(g3), np.unique(g2)).size),
                 "fit3_source_chunks_shared_with_ext": int(len(fit3_src & ext_src)),
                 "fit3_source_chunks_shared_with_fit": int(len(fit3_src & fit_src)),
                 "fit3_source_chunks_shared_with_fit2": int(len(fit3_src & fit2_src)),
                 "n_fit_source_chunks": int(len(fit_src)), "n_ext_source_chunks": int(len(ext_src)),
                 "n_fit2_source_chunks": int(len(fit2_src)), "n_fit3_source_chunks": int(len(fit3_src))}
    t_id = time.perf_counter()
    scored_digests = {hashlib.blake2b(np.ascontiguousarray(Xx[i], dtype=np.float32).tobytes(), digest_size=16).digest() for i in range(len(Xx))}
    for i in range(0, len(ev), 20000):
        blk = np.ascontiguousarray(X[np.sort(ev)[i:i + 20000], :ncols], dtype=np.float32)
        for j in range(len(blk)):
            scored_digests.add(hashlib.blake2b(blk[j].tobytes(), digest_size=16).digest())
    def _n_same(Xa):
        return sum(1 for i in range(len(Xa)) if hashlib.blake2b(np.ascontiguousarray(Xa[i], dtype=np.float32).tobytes(), digest_size=16).digest() in scored_digests)
    partition["fit_rows_identical_to_a_scored_row"] = int(_n_same(Xr))
    partition["fit2_rows_identical_to_a_scored_row"] = int(_n_same(X2))
    partition["fit3_rows_identical_to_a_scored_row"] = int(_n_same(X3))
    partition["row_identity_digest"] = "blake2b-128 of the contiguous float32 feature row, over every scored row"
    del scored_digests
    print(f"[2] row identity scan: {partition['fit_rows_identical_to_a_scored_row']} 0021, {partition['fit2_rows_identical_to_a_scored_row']} 0024 and "
          f"{partition['fit3_rows_identical_to_a_scored_row']} 0025 fit rows are byte-identical to a scored row ({time.perf_counter() - t_id:.0f}s)", flush=True)
    if not args.smoke:
        if partition["pool_idx_sha256"] != P["pool_idx_sha256"]:
            print(f"REFUSING: the pool hashes to {partition['pool_idx_sha256'][:12]}..., not the sealed {P['pool_idx_sha256'][:12]}...", file=sys.stderr)
            return 3
        leak = [k for k in ("fit_source_chunks_shared_with_ext", "fit_chunks_shared_with_ext", "fit_chunks_shared_with_builder",
                            "fit2_chunks_shared_with_ext", "fit2_chunks_shared_with_builder", "fit2_chunks_shared_with_fit",
                            "fit2_source_chunks_shared_with_ext", "fit2_source_chunks_shared_with_fit",
                            "fit3_chunks_shared_with_ext", "fit3_chunks_shared_with_builder", "fit3_chunks_shared_with_fit", "fit3_chunks_shared_with_fit2",
                            "fit3_source_chunks_shared_with_ext", "fit3_source_chunks_shared_with_fit", "fit3_source_chunks_shared_with_fit2",
                            "fit_rows_identical_to_a_scored_row", "fit2_rows_identical_to_a_scored_row", "fit3_rows_identical_to_a_scored_row") if partition[k]]
        if leak:
            print(f"REFUSING: a fit corpus shares something with a scored corpus or with another fit corpus: {leak}", file=sys.stderr)
            return 3
        if not all(id_continuity.values()):
            print(f"REFUSING: 0025's chunk ids do not continue 0024's per family: {id_continuity}", file=sys.stderr)
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
        for key in ("shift_arm_hashes", "shift_arm_0025_hashes"):
            pk = "shift_arm" if key == "shift_arm_hashes" else "shift_arm_0025"
            badk = [kk for kk, v in (P.get(key) or {}).items() if partition[pk].get(kk) != v]
            if badk:
                print(f"REFUSING: {pk} {badk} does not match the sealed {key}", file=sys.stderr)
                return 3
        if partition["pool_short"]:
            print(f"REFUSING: the pool is short of the lockstep doubling: {partition['pool_short']}", file=sys.stderr)
            return 3
        if not (partition["rungs_nested"] and partition["rung_chunks_strictly_increasing"] and partition["rung4_is_fit_block"]
                and partition["second_decade_exact_doublings"] and partition["shift_arm_0025"]["all_chunks_in_the_top_rung"]
                and partition["shift_arm_0025"]["all_chunks_above_0024s_ids"] and partition["shift_arm_0025"]["same_plaintext_count_as_rung_4"]):
            print("REFUSING: the rungs are not nested, strictly increasing, exact doublings on 0021's block at rung 4, or the new shift arm is not "
                  "the top rung's new-file plaintexts at rung 4's count", file=sys.stderr)
            return 3
        if partition["pool_chunks_with_rows_per_family"] != P["pool_chunks_with_rows_per_family"] \
                or partition["pool_chunks_with_rows_per_family_0024"] != P["pool_chunks_with_rows_per_family_0024"]:
            print("REFUSING: the pool chunks with rows per family (0024's and in all) are not the sealed ones", file=sys.stderr)
            return 3
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, fit block {partition['fit_rows']}"
          f"/{partition['fit_block_chunks']} chunks; rungs "
          + ", ".join(f"r{r['rung']}: {r['n_rows']} rows/{r['n_chunks']} chunks" for r in partition["rungs"])
          + f"; s4 {partition['shift_arm']['n_rows']} rows, s8 {partition['shift_arm_0025']['n_rows']} rows", flush=True)

    store = Store(args.workdir)
    curve_sha = sha_obj(curve)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "curve_sha256": curve_sha, "curve_spec": curve, "corpus": corpus, "ext_corpus": ext, "fit_corpus": fit,
              "fit2_corpus": fit2, "fit3_corpus": fit3, "partition": partition, "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES,
              "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    y_all = np.concatenate([np.asarray(yr), y23]); g_all = np.concatenate([np.asarray(gr), g23])
    X_all = np.concatenate([Xr, X2, X3]); del Xr, X2, X3

    started = None
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev]); n_eval = int(len(ev)); n_ext = int(len(yx))
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}
    r4 = lambda v: round(float(v), 4)  # noqa: E731
    order = list(P["order"])
    real_mask = np.isin(fam_x, REAL_FAMILIES); n_real = int(real_mask.sum())
    log2x = [r["log2_chunks"] for r in partition["rungs"]]
    log2x_second = log2x[N_FIRST - 1:]; log2x_first = log2x[:N_FIRST]; log2x_0024 = log2x[:N_0024_RUNGS]; log2x_second_0024 = log2x[N_FIRST - 1:N_0024_RUNGS]
    n_boot = int(P["bootstrap"]["n_boot"]); boot_seed = int(P["bootstrap"]["seed"]); bar_gain = float(P["bar"]["gain_per_doubling"])
    TOPK = n_rungs; R7 = N_0024_RUNGS

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
            c["slope_per_doubling_second_decade_0024"] = round(ols_slope(log2x_second_0024, ys[N_FIRST - 1:N_0024_RUNGS]), 6)
            c["slope_per_doubling_both_decades_0024"] = round(ols_slope(log2x_0024, ys[:N_0024_RUNGS]), 6)
            c["fourth_doubling_gain"] = round(ys[TOPK - 1] - ys[R7 - 1], 4)
            c["fourth_doubling_gain_with_rung7_at_reference"] = round(ys[TOPK - 1] - float(P["reference_0024"][role][R7 - 1]), 4)
            c["end_to_end_gain_second_decade"] = round(ys[-1] - ys[N_FIRST - 1], 4)
            c["end_to_end_gain_both_decades"] = round(ys[-1] - ys[0], 4)
            c["rung_to_rung_gains"] = [round(ys[i + 1] - ys[i], 4) for i in range(len(ys) - 1)]
            c["per_family_fourth_doubling_gain"] = {f: round(pts[TOPK - 1]["ext_per_family"][f] - pts[R7 - 1]["ext_per_family"][f], 4) for f in REAL_FAMILIES}
            c["per_family_slope_per_doubling_second_decade"] = {
                f: round(ols_slope(log2x_second, [p["ext_per_family"][f] for p in pts[N_FIRST - 1:]]), 6) for f in REAL_FAMILIES}
            c["builder_eval_slope_per_doubling_second_decade"] = round(ols_slope(log2x_second, [p["builder_eval_top1"] for p in pts[N_FIRST - 1:]]), 6)
            c["builder_eval_fourth_doubling_gain"] = round(pts[TOPK - 1]["builder_eval_top1"] - pts[R7 - 1]["builder_eval_top1"], 4)
        return c

    def floors_block(reads):
        out = {}
        for k in (R7, TOPK):
            model = (reads.get(f"r{k}_model") or {}).get("ext_real_top1"); log = (reads.get(f"r{k}_logistic") or {}).get("ext_real_top1")
            tree = (reads.get(f"r{k}_depth3_tree") or {}).get("ext_real_top1")
            fl = {fr: (reads.get(f"r{k}_{fr}") or {}).get("ext_real_top1") for fr in FLOOR_ROLES}
            fl["floor_tree3"] = tree   # B-tree3 is D1: the rung's depth3_tree reading is the tree floor
            have = all(v is not None for v in fl.values()) and model is not None and log is not None and tree is not None
            best = max(fl.values()) if have else None
            out[f"r{k}"] = {"floors": fl, "best_floor": best, "best_floor_role": (max(fl, key=fl.get) if have else None),
                            "model": model, "logistic": log, "depth3_tree": tree,
                            "needed_0021_clause": (round(best + 0.05, 4) if have else None), "clears_0021_clause": (bool(model >= round(best + 0.05, 4)) if have else None),
                            "needed_with_logistic_as_floor": (round(max(best, log) + 0.05, 4) if have else None),
                            "clears_with_logistic_as_floor": (bool(model >= round(max(best, log) + 0.05, 4)) if have else None)}
        out["note"] = ("informational: 0021's clause (best of its four trivial baselines on the same rows plus 0.05, OPERATING_RULES 4a) "
                       "re-applied with the floors REFITTED on rung 7 and on rung 8 (B-majority, B-stratified and B-feat1 refitted; B-tree3 is D1, "
                       "the curve's depth-3 tree at the rung, fitted once), and the same with the standardised logistic "
                       "counted among the floors; a 'clears' reading is 0021's margin re-applied at eight or sixteen times 0021's plaintexts "
                       "and revises nothing of 0021's verdict; never a verdict here")
        return out

    def shift_blocks(reads):
        s4 = {"arm": partition["shift_arm"], "readings": {}, "difference_from_rung_4": {}, "difference_from_rung_5": {},
              "note": "0024's shift arm, reproduced: rung 5's new plaintexts alone (rung 4's plaintext count, other files only); informational"}
        s8 = {"arm": partition["shift_arm_0025"], "readings": {}, "difference_from_rung_4": {}, "difference_from_rung_7": {}, "difference_from_rung_8": {},
              "difference_from_shift_arm_0024": {},
              "note": "informational: rung 8's plaintexts from 0025's corpus alone at rung 4's count, fitted with the same three recipes and "
                      "scored on the same rows; its difference from rung 4 reads what the fourth doubling's files buy alone for the original "
                      "files at 0021's plaintext count, its difference from 0024's shift arm is the between-draw comparison of two draws of "
                      "other files at the same count, and its differences from rungs 7 and 8 what the rest of the corpus adds on top; never a verdict"}
        for role in ROLES:
            a4 = reads.get(f"{SHIFT4}_{role}"); a8 = reads.get(f"{SHIFT8}_{role}")
            if a4 is not None:
                s4["readings"][role] = {"ext_real_top1": a4["ext_real_top1"], "ext_real_correct": a4["ext_real_correct"], "builder_eval_top1": a4["builder_eval_top1"],
                                        "ext_per_family": {f: a4["ext_per_family"][f] for f in REAL_FAMILIES}}
                for kk, key in ((N_FIRST, "difference_from_rung_4"), (N_FIRST + 1, "difference_from_rung_5")):
                    rk_ = reads.get(f"r{kk}_{role}")
                    if rk_ is not None:
                        s4[key][role] = round(a4["ext_real_top1"] - rk_["ext_real_top1"], 4)
            if a8 is not None:
                s8["readings"][role] = {"ext_real_top1": a8["ext_real_top1"], "ext_real_correct": a8["ext_real_correct"], "builder_eval_top1": a8["builder_eval_top1"],
                                        "ext_per_family": {f: a8["ext_per_family"][f] for f in REAL_FAMILIES}}
                for kk, key in ((N_FIRST, "difference_from_rung_4"), (R7, "difference_from_rung_7"), (TOPK, "difference_from_rung_8")):
                    rk_ = reads.get(f"r{kk}_{role}")
                    if rk_ is not None:
                        s8[key][role] = round(a8["ext_real_top1"] - rk_["ext_real_top1"], 4)
                if a4 is not None:
                    s8["difference_from_shift_arm_0024"][role] = round(a8["ext_real_top1"] - a4["ext_real_top1"], 4)
        return s4, s8

    def assemble(complete, launch_no, ci=None, boot=None, lead=None, repro_boot=None, gain=None, stability=None):
        reads = {n: readings(n) for n in order if per_ex.get(n) is not None}
        curves = {role: role_curve(role, reads) for role in ROLES}
        gm = curves["model"].get("fourth_doubling_gain")
        s4b, s8b = shift_blocks(reads)
        top_top1 = {role: (reads.get(f"r{TOPK}_{role}") or {}).get("ext_real_top1") for role in ROLES}
        repro_top1 = {role: (reads.get(f"r{N_FIRST}_{role}") or {}).get("ext_real_top1") for role in ROLES}
        repro_first = {role: [(reads.get(f"r{k}_{role}") or {}).get("ext_real_top1") for k in range(1, N_FIRST + 1)] for role in ROLES}
        repro_0024 = {role: [(reads.get(f"r{k}_{role}") or {}).get("ext_real_top1") for k in range(1, N_0024_RUNGS + 1)] for role in ROLES}
        repro_s4 = {role: (reads.get(f"{SHIFT4}_{role}") or {}).get("ext_real_top1") for role in ROLES}
        doc = dict(common, stage="run", environment=environment(), launch_environment=launch_env, launch_number=launch_no,
                   complete=bool(complete), missing_roles=[n for n in order if n not in records],
                   fits=records, readings=reads,
                   ext_real_top1={n: (reads[n] or {}).get("ext_real_top1") for n in reads},
                   ext_real_correct={n: (reads[n] or {}).get("ext_real_correct") for n in reads},
                   ext_top1={n: (reads[n] or {}).get("ext_top1") for n in reads},
                   builder_eval_top1={n: (reads[n] or {}).get("builder_eval_top1") for n in reads},
                   ext_per_family={n: (reads[n] or {}).get("ext_per_family") for n in reads},
                   curves=curves, roles=list(ROLES), floor_roles=list(FLOOR_ROLES), n_rungs=n_rungs, n_first_decade_rungs=N_FIRST, n_0024_rungs=N_0024_RUNGS,
                   denominators=denominators, doublings_0024=doublings2, doublings_0025=doublings3, log2_chunks=log2x, log2_chunks_second_decade=log2x_second,
                   model_fourth_doubling_gain=gm,
                   logistic_fourth_doubling_gain=curves["logistic"].get("fourth_doubling_gain"),
                   depth3_tree_fourth_doubling_gain=curves["depth3_tree"].get("fourth_doubling_gain"),
                   model_slope_per_doubling=curves["model"].get("slope_per_doubling_second_decade"),
                   logistic_slope_per_doubling=curves["logistic"].get("slope_per_doubling_second_decade"),
                   depth3_tree_slope_per_doubling=curves["depth3_tree"].get("slope_per_doubling_second_decade"),
                   top_rung_top1=top_top1,
                   top_rung_model_minus_logistic=(None if top_top1["model"] is None or top_top1["logistic"] is None else round(top_top1["model"] - top_top1["logistic"], 4)),
                   top_rung_model_minus_depth3_tree=(None if top_top1["model"] is None or top_top1["depth3_tree"] is None else round(top_top1["model"] - top_top1["depth3_tree"], 4)),
                   bar={"gain_per_doubling": bar_gain, "gain_rule": str(P["bar"]["gain_rule"]), "lead_rule": str(P["bar"]["lead_rule"]),
                        "n_boot": n_boot, "bootstrap_seed": boot_seed},
                   fourth_doubling=gain or {}, slope_bootstrap=boot or {}, lead_at_top=lead or {}, reproduction_bootstrap_0024=repro_boot or {},
                   seed_stability=stability or {},
                   shift_arm=s4b, shift_arm_0025=s8b, floors=floors_block(reads),
                   n_ext_real_rows=n_real, n_ext_rows=n_ext, n_eval_rows=n_eval,
                   ext_real_families=list(REAL_FAMILIES), ext_synthetic_families=list(SYNTH_FAMILIES),
                   fit_families=list(fit_names), fit_rows_per_family=fit["rows_per_family"], fit2_rows_per_family=fit2["rows_per_family"],
                   fit3_rows_per_family=fit3["rows_per_family"],
                   reference_top1=dict(P["reference_top1"]), reproduction_top1=repro_top1,
                   reproduction_drift={role: (None if repro_top1[role] is None else round(repro_top1[role] - float(P["reference_top1"][role]), 6)) for role in ROLES},
                   reference_first_decade={r: list(P["reference_first_decade"][r]) for r in ROLES}, reproduction_first_decade=repro_first,
                   reproduction_first_decade_drift={r: [None if a is None else round(a - float(b), 6) for a, b in zip(repro_first[r], P["reference_first_decade"][r])] for r in ROLES},
                   reference_0024={r: list(P["reference_0024"][r]) for r in ROLES}, reproduction_0024=repro_0024,
                   reproduction_0024_drift={r: [None if a is None else round(a - float(b), 6) for a, b in zip(repro_0024[r], P["reference_0024"][r])] for r in ROLES},
                   reference_shift_arm_0024=dict(P["reference_shift_arm_0024"]), reproduction_shift_arm_0024=repro_s4,
                   reproduction_shift_arm_0024_drift={r: (None if repro_s4[r] is None else round(repro_s4[r] - float(P["reference_shift_arm_0024"][r]), 6)) for r in ROLES},
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
                       "fit3_arrays_sha256": {k: v["sha256"] for k, v in fit3_hashes.items()},
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
        print(f"[run] scoring set {n_eval} + {n_ext} rows materialised, anonymous RSS {_rss_gb():.2f} GB (total {_rss_total_gb():.2f} GB)", flush=True)
        chance = 1.0 / N_CONFIGS
        blocks: dict = {}

        def rk_of(k):
            return partition["shift_arm"] if k == SHIFT4 else partition["shift_arm_0025"] if k == SHIFT8 else partition["rungs"][k - 1]

        def rows_of(k):
            return rows_all[n_rungs] if k == SHIFT4 else rows_all[n_rungs + 1] if k == SHIFT8 else rows_all[k - 1]

        def block_of(k):
            if k not in blocks:
                blocks[k] = Block(X_all, rows_of(k), ncols, f"{k if k in (SHIFT4, SHIFT8) else 'r' + str(k)}")
            return blocks[k]

        def fit_role(name, role, cand, y_fit, stage, k):
            rk = rk_of(k)
            fp = fingerprint(prereg=stamp, seed=seed, seed2=seed2, seed3=seed3, head=role, cand=cand, stage=stage, rung=k, rows=rk["sorted_sha256"],
                             eval=partition["eval_idx_sha256"], ext=ext_hashes["X"]["sha256"], fit=fit_hashes["X"]["sha256"],
                             fit2=fit2_hashes["X"]["sha256"], fit3=fit3_hashes["X"]["sha256"])
            store.log(f"run_{name}", fp, "rung_bound", rung=k, rung_sorted_sha256=rk["sorted_sha256"])
            blk = None if store.load(f"run_{name}", fp) is not None else block_of(k)
            r, pe = run_fit(store, f"run_{name}", fp, role, cand, seed, blk, y_fit, g_all, Xs, ys, fam_s, stage, caps,
                            keep_per_example=True, confirmatory=True)
            records[name] = dict(r, fingerprint=fp, rung=k, role=role, n_rung_rows=rk["n_rows"], n_rung_chunks=rk["n_chunks"],
                                 per_example_sha256=(hashlib.sha256(np.asarray(pe, np.int8).tobytes()).hexdigest() if pe is not None else None))
            if pe is not None:
                per_ex[name] = pe
            rd = readings(name)
            if rd:
                print(f"      {name:<20} BUILDER EVAL {rd['builder_eval_top1']} | EXTENSION {rd['ext_top1']} | REAL "
                      f"{rd['ext_real_correct']}/{rd['n_ext_real_rows']} = {rd['ext_real_top1']} "
                      f"{ {f: rd['ext_per_family'][f] for f in REAL_FAMILIES} }", flush=True)
            assemble(False, launch_no)
            if rd is None:
                raise NotRun(f"{name}: no per-example vector was banked (status {records[name].get('status')!r}); one scoring per role")
            return rd

        def check_repro(step, k, role, rd):
            if args.smoke or role not in ROLES:
                return
            if k == SHIFT4:
                ref = float(P["reference_shift_arm_0024"][role]); tol = float(P["reproduction_tolerance"]); what = "0024's shift arm"
            elif k == SHIFT8 or k > N_0024_RUNGS:
                return
            elif k <= N_FIRST:
                ref = float(P["reference_first_decade"][role][k - 1]); tol = float(P["reproduction_tolerance"]); what = "0023's"
                if k == N_FIRST and ref != float(P["reference_top1"][role]):
                    raise NotRun(f"{step}: the sealed reference_first_decade[{role}][{k - 1}] {ref} is not reference_top1 {P['reference_top1'][role]}")
                if float(P["reference_0024"][role][k - 1]) != ref:
                    raise NotRun(f"{step}: the sealed reference_0024[{role}][{k - 1}] is not 0023's {ref}: the sealed references disagree")
            else:
                ref = float(P["reference_0024"][role][k - 1]); what = "0024's"
                tol = float(P["reproduction_tolerance_rung7"]) if k == N_0024_RUNGS else float(P["reproduction_tolerance"])
            drift = round(abs(rd["ext_real_top1"] - ref), 6)
            if drift > tol:
                raise NotRun(f"{step} read {rd['ext_real_top1']} on the real-family rows against {what} banked {ref} (drift {drift} > {tol}): "
                             f"the rung, the scoring set or the machinery is not the banked run's")

        def repro_intervals_0024():
            """0024's verdict intervals (its second-decade slope over rungs 4..7, its leads at rungs 7 and 4) recomputed from this run's
            vectors under 0024's bootstrap seed, and whether they equal 0024's banked values exactly. Called by the fit loop once all
            twenty-one reproduction fits are banked (NOT RUN before rung 8 if they do not reproduce) and by the post-run assembly."""
            vec = lambda n: per_ex[n][n_eval:][real_mask]  # noqa: E731
            cid = gx[real_mask]

            def pct(a):
                return [round(float(np.percentile(a, 2.5)), 6), round(float(np.percentile(a, 97.5)), 6)]
            by_role_0024 = {role: [vec(f"r{k}_{role}") for k in range(N_FIRST, N_0024_RUNGS + 1)] for role in ROLES}
            sl24 = slope_bootstrap(by_role_0024, log2x_second_0024, cid, n_boot, boot_seed)
            repro_boot = {"slope_bootstrap_0024": {role: {"ci95": pct(sl24[role]), "n_boot": n_boot, "seed": boot_seed, "mean": round(float(sl24[role].mean()), 6)} for role in ROLES}}
            for a, b_ in (("model", "logistic"), ("model", "depth3_tree")):
                d = sl24[a] - sl24[b_]
                repro_boot["slope_bootstrap_0024"][f"{a}_minus_{b_}"] = {"ci95": pct(d), "paired": True, "share_of_resamples_with_model_ahead": round(float((d > 0).mean()), 4)}
            repro_boot["lead_0024"] = {}
            for k in (N_0024_RUNGS, N_FIRST):
                for a, b_ in (("model", "logistic"), ("model", "depth3_tree")):
                    dv = paired_lead_bootstrap(vec(f"r{k}_{a}"), vec(f"r{k}_{b_}"), cid, n_boot, boot_seed)
                    lo, hi = pct(dv)
                    repro_boot["lead_0024"][f"r{k}_{a}_minus_{b_}"] = {
                        "point": round(readings(f"r{k}_{a}")["ext_real_top1"] - readings(f"r{k}_{b_}")["ext_real_top1"], 4), "ci95": [lo, hi],
                        "n_boot": n_boot, "seed": boot_seed, "share_of_resamples_with_model_ahead": round(float((dv > 0).mean()), 4),
                        "reading": ("MODEL_LEADS" if lo > 0 else "LINEAR_LEADS" if hi < 0 else "NO_SEPARATION") if b_ == "logistic"
                                   else ("MODEL_LEADS" if lo > 0 else "TREE_LEADS" if hi < 0 else "NO_SEPARATION")}
            ref_boot = P.get("reference_bootstrap_0024") or {}
            repro_boot["equals_0024s_banked"] = {
                "slope_bootstrap": bool(ref_boot.get("slope_bootstrap") is not None and all(repro_boot["slope_bootstrap_0024"].get(k) == v for k, v in ref_boot.get("slope_bootstrap", {}).items())),
                "lead_at_top": bool(ref_boot.get("lead_at_top") is not None and all(repro_boot["lead_0024"].get(k) == v for k, v in ref_boot.get("lead_at_top", {}).items()))}
            repro_boot["unit"] = ("0024's verdict intervals recomputed here from this run's vectors under 0024's bootstrap seed over the same "
                                  "scored chunks; they must equal 0024's banked values exactly (a reproduction of the instrument, not a verdict)")
            return repro_boot

        exact_checked = False

        for step in order:
            if step == "null":
                top_rows = rows_all[n_rungs - 1]
                y_sh = y_all.copy()
                sub = y_all[top_rows].copy()
                np.random.default_rng([seed3, NULL_STREAM_WORD]).shuffle(sub)
                y_sh[top_rows] = sub
                partition["null_y_shuffled_sha256"] = _sha(sub)
                partition["null_labels_permuted"] = bool(not np.array_equal(sub, y_all[top_rows]))
                partition["null_labels_same_multiset"] = bool(np.array_equal(np.sort(sub), np.sort(y_all[top_rows])))
                partition["null_rule"] = (f"the top rung's labels, in rung order, permuted by np.random.default_rng([{seed3}, {NULL_STREAM_WORD}]).shuffle; hashed in rung order")
                if not args.smoke and not (partition["null_labels_permuted"] and partition["null_labels_same_multiset"]):
                    raise NotRun("the null control's labels are not a permutation of the top rung's own labels")
                want_null = P.get("null_y_shuffled_sha256_expected")
                if not args.smoke and want_null and partition["null_y_shuffled_sha256"] != want_null:
                    raise NotRun(f"the null control's permuted labels hash to {partition['null_y_shuffled_sha256'][:12]}..., not the sealed "
                                 f"{want_null[:12]}...: the generator state or the label arrays are not the sealed ones")
                rd = fit_role("null", "null", recipes["model"], y_sh, "null", n_rungs)
                del y_sh, sub
                if rd and not args.smoke:
                    tol = float(P["null_tolerance"])
                    if rd["ext_top1"] > chance + tol or rd["builder_eval_top1"] > chance + tol:
                        raise NotRun(f"null control read {rd['ext_top1']} on the extension rows and {rd['builder_eval_top1']} on the sealed evaluation "
                                     f"rows against chance {chance:.6f} + {tol}: the scoring path leaks")
            else:
                k, role = parse_name(step, n_rungs)
                if role not in ALL_ROLES or (k not in (SHIFT4, SHIFT8) and not (1 <= k <= n_rungs)):
                    raise NotRun(f"unknown order step {step!r}")
                stage = ("shift" if k in (SHIFT4, SHIFT8) else "floor" if role in FLOOR_ROLES else "curve" if k > N_0024_RUNGS else "reproduction")
                rd = fit_role(step, role, recipes[role], y_all, stage, k)
                if rd:
                    check_repro(step, k, role, rd)
                if (not args.smoke and not exact_checked
                        and all(f"r{kk}_{r}" in per_ex for kk in range(1, N_0024_RUNGS + 1) for r in ROLES)):
                    exact_checked = True
                    eq = repro_intervals_0024()["equals_0024s_banked"]
                    print(f"[run] 0024's intervals recomputed from this run's rung 1..{N_0024_RUNGS} vectors: {eq}", flush=True)
                    if not (eq["slope_bootstrap"] and eq["lead_at_top"]):
                        raise NotRun(f"after the last reproduction fit ({step}), 0024's banked slope and lead intervals do not recompute exactly "
                                     f"from this run's vectors under 0024's seed ({eq}): the instrument is not 0024's; nothing of rung 8 is fitted")
                if step.endswith("_model") and k in blocks:
                    del blocks[k]
            if step == "null" and n_rungs in blocks and order[order.index(step) + 1].split("_")[0] != f"r{n_rungs}":
                del blocks[n_rungs]
            if step in (f"{SHIFT4}_model", f"{SHIFT8}_model"):
                blocks.pop(SHIFT4 if step.startswith(SHIFT4) else SHIFT8, None)
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
        vec = lambda n: per_ex[n][n_eval:][real_mask]  # noqa: E731
        cid = gx[real_mask]

        def pct(a):
            return [round(float(np.percentile(a, 2.5)), 6), round(float(np.percentile(a, 97.5)), 6)]
        # (a) 0024's intervals, reproduced (the same function the fit loop called before rung 8)
        repro_boot = repro_intervals_0024()
        # (b) this run's intervals: slopes over rungs 4..8 and 1..8 with the same resamples; the fourth-doubling gain and the rung-8 leads, paired
        by_role = {role: [vec(f"r{k}_{role}") for k in range(N_FIRST, n_rungs + 1)] for role in ROLES}
        sl = slope_bootstrap(by_role, log2x_second, cid, n_boot, boot_seed)
        by_role_all = {role: [vec(f"r{k}_{role}") for k in range(1, n_rungs + 1)] for role in ROLES}
        sl_all = slope_bootstrap(by_role_all, log2x, cid, n_boot, boot_seed)
        boot = {role: {"ci95": pct(sl[role]), "n_boot": n_boot, "seed": boot_seed, "mean": round(float(sl[role].mean()), 6)} for role in ROLES}
        for a, b_ in (("model", "logistic"), ("model", "depth3_tree")):
            d = sl[a] - sl[b_]
            boot[f"{a}_minus_{b_}"] = {"ci95": pct(d), "paired": True, "share_of_resamples_with_model_ahead": round(float((d > 0).mean()), 4)}
        boot["both_decades"] = {role: {"ci95": pct(sl_all[role]), "n_boot": n_boot, "seed": boot_seed, "mean": round(float(sl_all[role].mean()), 6)} for role in ROLES}
        boot["unit"] = (f"accuracy on the real-family rows per doubling of plaintexts over the second decade (rungs {N_FIRST}..{n_rungs}) and, under "
                        f"both_decades, over all {n_rungs} rungs; cluster bootstrap over the scored real chunks; informational flags")
        gain = {}
        for role in ROLES:
            dv = paired_lead_bootstrap(vec(f"r{n_rungs}_{role}"), vec(f"r{N_0024_RUNGS}_{role}"), cid, n_boot, boot_seed)
            lo, hi = pct(dv); point = round(readings(f"r{n_rungs}_{role}")["ext_real_top1"] - readings(f"r{N_0024_RUNGS}_{role}")["ext_real_top1"], 4)
            gain[role] = {"point": point, "ci95": [lo, hi], "n_boot": n_boot, "seed": boot_seed,
                          "share_of_resamples_with_a_gain": round(float((dv > 0).mean()), 4), "reading": gain_reading(point, lo, hi, bar_gain)}
        gain["verdict_role"] = "model"; gain["bar"] = bar_gain
        gain["unit"] = (f"accuracy on the real-family rows, rung {n_rungs} minus rung {N_0024_RUNGS}; paired cluster bootstrap over the scored real chunks "
                        "(the same resamples for both rungs); the interval covers the scored chunks only, not the draw of the rung's plaintexts")
        lead = {}
        for k in (n_rungs, N_0024_RUNGS, N_FIRST):
            for a, b_ in (("model", "logistic"), ("model", "depth3_tree")):
                dv = paired_lead_bootstrap(vec(f"r{k}_{a}"), vec(f"r{k}_{b_}"), cid, n_boot, boot_seed)
                lo, hi = pct(dv)
                lead[f"r{k}_{a}_minus_{b_}"] = {
                    "point": round(readings(f"r{k}_{a}")["ext_real_top1"] - readings(f"r{k}_{b_}")["ext_real_top1"], 4), "ci95": [lo, hi],
                    "n_boot": n_boot, "seed": boot_seed, "share_of_resamples_with_model_ahead": round(float((dv > 0).mean()), 4),
                    "reading": ("MODEL_LEADS" if lo > 0 else "LINEAR_LEADS" if hi < 0 else "NO_SEPARATION") if b_ == "logistic"
                               else ("MODEL_LEADS" if lo > 0 else "TREE_LEADS" if hi < 0 else "NO_SEPARATION")}
        # the between-draw comparison: the new shift arm against 0024's, paired
        dv = paired_lead_bootstrap(vec(f"{SHIFT8}_model"), vec(f"{SHIFT4}_model"), cid, n_boot, boot_seed)
        lead["s8_minus_s4_model"] = {"point": round(readings(f"{SHIFT8}_model")["ext_real_top1"] - readings(f"{SHIFT4}_model")["ext_real_top1"], 4),
                                     "ci95": pct(dv), "n_boot": n_boot, "seed": boot_seed, "informational": True}
        lead["unit"] = "accuracy on the real-family rows; paired cluster bootstrap over the scored real chunks, the slope bootstrap's resamples"
        lead["verdict_pair"] = f"r{n_rungs}_model_minus_logistic"
        # (c) seed stability of the two verdict intervals: how many of STABILITY_SEEDS other seeds move a reading
        stab = {"seeds": [boot_seed + 1 + i for i in range(STABILITY_SEEDS)], "gain_readings": {}, "lead_readings": {}}
        for s_ in stab["seeds"]:
            dg = paired_lead_bootstrap(vec(f"r{n_rungs}_model"), vec(f"r{N_0024_RUNGS}_model"), cid, n_boot, s_); lo, hi = pct(dg)
            stab["gain_readings"][str(s_)] = gain_reading(gain["model"]["point"], lo, hi, bar_gain)
            dl = paired_lead_bootstrap(vec(f"r{n_rungs}_model"), vec(f"r{n_rungs}_logistic"), cid, n_boot, s_); lo, hi = pct(dl)
            stab["lead_readings"][str(s_)] = "MODEL_LEADS" if lo > 0 else "LINEAR_LEADS" if hi < 0 else "NO_SEPARATION"
        stab["n_seeds_with_another_gain_reading"] = sum(1 for v in stab["gain_readings"].values() if v != gain["model"]["reading"])
        stab["n_seeds_with_another_lead_reading"] = sum(1 for v in stab["lead_readings"].values() if v != lead[f"r{n_rungs}_model_minus_logistic"]["reading"])
        stab["note"] = ("informational: the sealed readings are read under the sealed seed; this counts how many of the other seeds would have "
                        "read differently, published beside any reading that a single unit of the fourth decimal could flip")
        out = assemble(True, launch_no, ci=ci, boot=boot, lead=lead, repro_boot=repro_boot, gain=gain, stability=stab)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "run", "reason": str(e),
                       "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])}, fh, indent=2)
        return 4
    gm = out["fourth_doubling"]["model"]
    print(f"[run] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; fourth-doubling model gain {gm['point']} "
          f"(paired {gm['ci95']}) -> {gm['reading']}; lead at rung {n_rungs} {out['lead_at_top'][out['lead_at_top']['verdict_pair']]['reading']}; "
          f"model rungs {[p['ext_real_top1'] for p in out['curves']['model']['rungs']]}; 0024 intervals reproduced {out['reproduction_bootstrap_0024']['equals_0024s_banked']}; "
          f"null {out['shuffled_label_accuracy_real']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
