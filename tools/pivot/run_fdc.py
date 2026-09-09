#!/usr/bin/env python3
"""Family-diversity transfer curve (FDC) at one carve size (preregistration 0016 at 4096).

Question. 0015 established that 0003's recipe, fitted on seven content families, does not identify the
encoder on the eighth at chance + 0.05. Is that a matter of how many content types the model has seen?
At a FIXED plaintext budget of C source chunks (every pool row of each chosen chunk: the ~20 encoder
variants the pool holds of it, so the budget counts plaintexts, which is what a corpus costs, not the
manufactured labels), for each held-out family f and each family count k, 0003's fixed recipes (the
incumbent HGB M1, the raw logistic L1, the majority rule U1) are fitted on C/k chunks of each of the k
families that FOLLOW f cyclically in the sealed family order (nested subsets; each family's first C/k
chunks by first appearance in pool order; the union kept in pool order) and scored ONCE on the sealed
evaluation set; the reading for (f, k) is the accuracy on f's evaluation rows. The eight readings at
each k stitch into one leave-one-family-out mixture at that k; the curve is the mixture against
log2(k), and its ordinary-least-squares slope ("accuracy per doubling of families") is what the bar is
read on. Two informational arms separate what the curve entangles: the DEPTH arm fits the single
successor family alone at C/k chunks for k in 2, 4, 7 (family count held at one, per-family depth
varied), and the PREDECESSOR arm refits k = 1 with the family that precedes f (composition sensitivity).

Reuses tools/pivot/run_recipe_search.py's machinery (blocks, fits, checkpoints, heartbeat, memory
accounting, launch rules) unchanged; nothing here searches or selects a recipe.

Stages: one invocation (--stage run). Order: the reproduction control (the incumbent on 0003's 100000-row
rung must reproduce 0003's banked 0.1965), the null control, then per family in sealed order: the four
fixed-budget folds, the three depth folds, the predecessor fold; majority / logistic / model within each.
Checkpoints resume; a container restart is recovered by relaunching the identical command.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run_recipe_search import (  # noqa: E402
    REPO, _sha, sha_obj, _utc, fingerprint, environment, npz_memmap, fill_f32, Block, run_fit, Store,
    NotRun, cluster_ci, _rss_gb, _rss_total_gb, grouped_split, FAMILIES, N_CONFIGS, CONFIG_NAMES)

STRUCTURED = ["code", "csv", "json", "log"]


def following_families(f: str, k: int, families: list[str]) -> list[str]:
    """The k families that follow f cyclically in the sealed family order (nested in k)."""
    i = families.index(f)
    return [families[(i + j) % len(families)] for j in range(1, k + 1)]


def preceding_family(f: str, families: list[str]) -> str:
    return families[(families.index(f) - 1) % len(families)]


def ols_slope(xs, ys):
    """Ordinary least squares slope of ys on xs; None if any y is None."""
    if any(v is None for v in ys) or len(xs) < 2:
        return None
    xb = sum(xs) / len(xs); yb = sum(ys) / len(ys)
    sxx = sum((x - xb) ** 2 for x in xs)
    if sxx == 0:
        return None
    return sum((x - xb) * (y - yb) for x, y in zip(xs, ys)) / sxx


def bits(v: np.ndarray) -> str:
    """A per-example 0/1 vector as a string of '0'/'1' characters (260000 rows -> 260 KB, not 800 KB of JSON ints)."""
    return "".join("1" if int(x) else "0" for x in v.tolist())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["run"], default="run")
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0016-fdc-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "fdc_4096_ckpt"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "fdc_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "fdc_4096_scores.json"))
    ap.add_argument("--smoke", action="store_true", help="tiny rows, scratchpad outputs only; the reader voids it")
    args = ap.parse_args()
    out_stem = os.path.splitext(os.path.basename(args.out))[0]
    art = os.path.join(REPO, "artifacts") + os.sep
    outputs = {"--workdir": args.workdir, "--out": args.out, "--scores-out": args.scores_out}
    under = {k: os.path.abspath(v).startswith(art) for k, v in outputs.items()}
    if args.smoke and any(under.values()):
        print(f"REFUSING: --smoke with an output path under artifacts/: {[k for k, v in under.items() if v]}",
              file=sys.stderr)
        return 3
    if not args.smoke and not all(under.values()):
        print(f"REFUSING: a real run must write every output under artifacts/: "
              f"{[k for k, v in under.items() if not v]}", file=sys.stderr)
        return 3
    t_all = time.perf_counter()
    not_run_path = args.out[:-5] + "_not_run.json"

    prereg = json.load(open(args.prereg_file, encoding="utf-8"))
    P = dict(prereg["scope"]["protocol"]); recipes = prereg["scope"]["recipes"]
    if args.smoke:
        P.update(prereg.get("smoke", {}))
    stamp = f"{prereg['id']}-{prereg['slug']}"
    seed = int(P["seed"]); eval_frac = float(P["eval_frac"]); top_rung = int(P["top_rung"]); caps = P["caps"]
    families = list(P["families"])
    assert families == FAMILIES, "the sealed family order must be the corpus family order"
    roles = list(P["roles"])
    assert set(roles) == set(recipes) == {"majority", "logistic", "model"}
    ks = [int(k) for k in P["family_counts"]]
    C = int(P["budget_chunks"])
    assert ks[0] == 1 and all(C % k == 0 for k in ks), "the chunk budget must divide exactly by every family count, and k starts at 1"
    assert P["subset_rule"] == "following_cyclic_nested_by_chunk"
    depth_sizes = [C // k for k in ks[1:]]           # the depth arm: one family at C/k chunks, k > 1
    repro_rows = int(P["repro_rows"])
    env = environment()
    launch_env = {"env": env, "ok": True, "problems": []}
    if env["threads"] != P["threads"]:
        launch_env["problems"].append(f"threads {env['threads']} != preregistered {P['threads']} (all three "
                                      f"of OMP/OPENBLAS/MKL_NUM_THREADS must be set to it)")
    if env["nice"] != P["nice"]:
        launch_env["problems"].append(f"nice {env['nice']} != preregistered {P['nice']}")
    for k, v in (P.get("environment") or {}).items():
        # the reader voids every record on a version mismatch; refusing here costs nothing and saves hours (0016 review)
        if env.get(k) != v:
            launch_env["problems"].append(f"{k} {env.get(k)!r} != preregistered {v!r}")
    if (env["disk_free_gb"] or 0) < P["launch"]["min_disk_free_gb"]:
        launch_env["problems"].append(f"disk free {env['disk_free_gb']} GB < {P['launch']['min_disk_free_gb']}")
    if (env["mem_available_gb"] or 0) < P["launch"]["min_mem_available_gb"]:
        launch_env["problems"].append(f"MemAvailable {env['mem_available_gb']} GB < {P['launch']['min_mem_available_gb']}")
    if launch_env["problems"]:
        print("REFUSING TO LAUNCH: " + "; ".join(launch_env["problems"]), file=sys.stderr)
        return 3
    if os.path.exists(not_run_path) and not args.smoke:
        print(f"REFUSING: {os.path.relpath(not_run_path, REPO)} exists; this run was filed NOT RUN", file=sys.stderr)
        return 3

    # [1] corpus A from its cache; y and g are read without touching X, which is memmapped
    import io as _io, zipfile as _zf
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
            print(f"REFUSING: cache built at carve {cache_carve}, offset {cache_off}, chunk size {cache_cs}; "
                  f"the preregistration says {P['carve']}, {P['chunk_offset']}, {P['chunk_size']}", file=sys.stderr)
            return 3
        carve_source = "cache metadata written at build time"
    else:
        ident = P.get("cache_identity") or {}
        if ident.get("y_sha256") != cache_y_sha or ident.get("g_sha256") != cache_g_sha:
            print("REFUSING: cache carries no build metadata and its y/g hashes are not the preregistration's "
                  "sealed cache_identity", file=sys.stderr)
            return 3
        cache_carve, cache_off, cache_cs = int(P["carve"]), int(P["chunk_offset"]), int(P["chunk_size"])
        carve_source = "sealed cache identity (sha256 of y and g); the cache carries no build metadata"
    X = npz_memmap(args.cache, "X"); ncols = X.shape[1]
    corpus = {"carve_bytes": cache_carve, "carve_bytes_source": carve_source,
              "chunk_size": cache_cs, "chunk_offset": cache_off, "chunk_id_min": int(g.min()),
              "chunk_id_max": int(g.max()), "n_source_chunks": int(np.unique(g).size),
              "cache_y_sha256": cache_y_sha, "cache_g_sha256": cache_g_sha, "n_rows": int(len(y)), "n_features": int(ncols)}
    print(f"[1] corpus A: {corpus}", flush=True)

    # [2] the sealed split (0003's by construction), the reproduction rung, the null block, the folds
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e, fam_t = fam_all[ev], fam_all[tr]
    g_t = np.asarray(g[tr])
    ev_chunks = np.unique(g[ev])
    if repro_rows > len(tr):
        raise SystemExit(f"REFUSING: repro_rows {repro_rows} exceeds the pool ({len(tr)})")
    rep = tr[:repro_rows]
    nn = min(len(tr), int(P["null_rows"]))
    null_rows = tr[:nn]
    # per family: its pool positions (in pool order) and its chunks ordered by first appearance in the pool
    fam_pos = {f: np.nonzero(fam_t == f)[0] for f in families}
    fam_chunks = {}
    for f in families:
        ch = g_t[fam_pos[f]]
        _, first = np.unique(ch, return_index=True)
        fam_chunks[f] = ch[np.sort(first)]

    def block_rows(chosen, n_chunks):
        """Every pool row of the first n_chunks chunks (by first appearance) of each chosen family, in pool order."""
        sel = []
        for c in chosen:
            if len(fam_chunks[c]) < n_chunks:
                raise SystemExit(f"REFUSING: family {c} has {len(fam_chunks[c])} pool chunks, fewer than {n_chunks}")
            want = fam_chunks[c][:n_chunks]
            p = fam_pos[c]
            sel.append(p[np.isin(g_t[p], want)])
        return tr[np.sort(np.concatenate(sel))]

    def seal(idx, f, chosen, n_chunks):
        fi = fam_all[idx]; gi = np.asarray(g[idx])
        return {"families": list(chosen), "chunks_per_family": int(n_chunks),
                "n_train_rows": int(len(idx)), "train_idx_sha256": _sha(idx),
                "train_sorted_sha256": _sha(np.sort(idx).astype(np.int64)), "n_train_chunks": int(np.unique(gi).size),
                "train_rows_per_family": {c: int((fi == c).sum()) for c in families},
                "train_chunks_per_family": {c: int(np.unique(gi[fi == c]).size) for c in families},
                "train_rows_of_heldout_family": int((fi == f).sum()),
                "train_rows_outside_chosen_families": int((~np.isin(fi, chosen)).sum()),
                "train_chunks_shared_with_eval": int(np.intersect1d(np.unique(gi), ev_chunks).size),
                "train_rows_in_eval": int(np.intersect1d(idx, ev).size)}

    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam_e != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev), "eval_y_sha256": _sha(np.asarray(y[ev])),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_y_sha256": _sha(np.asarray(y[tr])),
                 "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64)),
                 "pool_rows_per_family": {f: int(len(fam_pos[f])) for f in families},
                 "pool_chunks_per_family": {f: int(len(fam_chunks[f])) for f in families},
                 "repro_rows": int(len(rep)), "repro_idx_sha256": _sha(rep),
                 "repro_sorted_sha256": _sha(np.sort(rep).astype(np.int64)),
                 "null_rows": int(nn), "null_sorted_sha256": _sha(np.sort(null_rows).astype(np.int64)),
                 "budget_chunks": C, "family_counts": ks, "depth_chunks": [C] + depth_sizes,
                 "subset_rule": P["subset_rule"], "families": families, "folds": {}}
    folds: dict[str, dict[str, np.ndarray]] = {}
    for f in families:
        ev_f = ev[fam_e == f]
        succ = following_families(f, len(families) - 1, families); pred = preceding_family(f, families)
        folds[f] = {}
        pf = {"n_eval_rows": int(len(ev_f)), "eval_idx_sha256": _sha(ev_f), "n_eval_chunks": int(np.unique(g[ev_f]).size),
              "by_k": {}, "depth": {}, "pred_k1": None}
        for k in ks:
            idx = block_rows(succ[:k], C // k); folds[f][f"k{k}"] = idx
            pf["by_k"][str(k)] = seal(idx, f, succ[:k], C // k)
        for n in depth_sizes:
            idx = block_rows(succ[:1], n); folds[f][f"c{n}"] = idx
            pf["depth"][str(n)] = seal(idx, f, succ[:1], n)
        idx = block_rows([pred], C); folds[f]["pred"] = idx
        pf["pred_k1"] = seal(idx, f, [pred], C)
        partition["folds"][f] = pf
    leak = 0
    for f in families:
        pf = partition["folds"][f]
        for e in list(pf["by_k"].values()) + list(pf["depth"].values()) + [pf["pred_k1"]]:
            leak += sum(e[c] for c in ("train_rows_of_heldout_family", "train_chunks_shared_with_eval", "train_rows_in_eval",
                                       "train_rows_outside_chosen_families"))
    # every block must carry all N_CONFIGS classes in its first 90% of rows (the incumbent's fit rows; the last 10% is its
    # early-stopping validation split) and in that split: HGB refuses a validation label it never saw, and a block too small
    # to cover the classes is a size problem to refuse here, before any fit, not a crash hours in (found by a smoke run)
    short = []
    for f in families:
        for key, idx in folds[f].items():
            k90 = len(idx) - len(idx) // 10
            for part_name, sl in (("fit_rows", idx[:k90]), ("validation_rows", idx[k90:])):
                n_cls = int(np.unique(np.asarray(y[sl])).size)
                if n_cls != N_CONFIGS:
                    short.append(f"{f}/{key}/{part_name}: {n_cls} of {N_CONFIGS} classes")
    if short:
        raise SystemExit(f"REFUSING: {len(short)} blocks do not carry every class in both fit and validation rows: {short[:6]}")
    partition["every_block_carries_all_classes_in_fit_and_validation_rows"] = True
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, pool "
          f"{partition['n_pool_rows']}, repro {partition['repro_rows']}, null {nn}; budget {C} chunks at k in {ks}, depth "
          f"sizes {depth_sizes}, predecessor at k=1; leakage counts sum {leak}", flush=True)

    store = Store(args.workdir)
    proto_sha = sha_obj(prereg["scope"]["protocol"]); recipes_sha = sha_obj(recipes)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "stage": "run", "protocol": prereg["scope"]["protocol"], "protocol_sha256": proto_sha,
              "recipes": recipes, "recipes_sha256": recipes_sha, "corpus": corpus, "partition": partition,
              "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES, "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    fold_names = []
    for f in families:
        fold_names += [f"fold_{f}_k{k}_{r}" for k in ks for r in roles]
        fold_names += [f"depth_{f}_c{n}_{r}" for n in depth_sizes for r in roles]
        fold_names += [f"pred_{f}_k1_{r}" for r in roles]
    names_expected = ["repro_100k", "null"] + fold_names

    started = _utc()
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev])
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}
    log2k = [math.log2(k) for k in ks]

    def stitch(vec_names):
        """Stitch eight per-example vectors: row i is read from the vector named for i's family."""
        vecs = {f: per_ex.get(vec_names[f]) for f in families}
        if any(v is None for v in vecs.values()):
            return None
        mix = np.empty(len(ev), np.int8)
        for f in families:
            m = fam_e == f
            mix[m] = vecs[f][m]
        struct = np.isin(fam_e, STRUCTURED)
        return {"mixture_top1": round(float(mix.mean()), 4),
                "mixture_top1_non_gutenberg": round(float(mix[fam_e != "gutenberg"].mean()), 4),
                "structured_four_top1": round(float(mix[struct].mean()), 4),
                "per_family": {f: round(float(mix[fam_e == f].mean()), 4) for f in families}}, mix

    def mixtures(role):
        """All stitched mixtures for a role: the fixed-budget curve by k, the depth arm by chunks, the predecessor k=1."""
        out = {"fdc": {}, "depth": {}, "pred": None}; vecs = {}
        for k in ks:
            m = stitch({f: f"fold_{f}_k{k}_{role}" for f in families})
            if m is not None:
                out["fdc"][str(k)], vecs[f"fdc_mixture_k{k}_{role}"] = m
        if str(ks[0]) in out["fdc"]:
            out["depth"][str(C)] = dict(out["fdc"][str(ks[0])])       # the k=1 fold is the depth arm's C-chunk point
        for n in depth_sizes:
            m = stitch({f: f"depth_{f}_c{n}_{role}" for f in families})
            if m is not None:
                out["depth"][str(n)], vecs[f"depth_mixture_c{n}_{role}"] = m
        m = stitch({f: f"pred_{f}_k1_{role}" for f in families})
        if m is not None:
            out["pred"], vecs[f"pred_mixture_k1_{role}"] = m
        return out, vecs

    def curve(role):
        mx, vecs = mixtures(role)
        ys = [mx["fdc"].get(str(k), {}).get("mixture_top1") for k in ks]
        slope = ols_slope(log2k, ys)
        dsizes = [C] + depth_sizes
        dys = [mx["depth"].get(str(n), {}).get(  "mixture_top1") for n in dsizes]
        pred_m = (mx["pred"] or {}).get("mixture_top1")
        r6 = lambda a, b: round(a - b, 6) if a is not None and b is not None else None  # noqa: E731
        out = {"by_k": mx["fdc"], "family_counts": ks, "log2_family_counts": [round(x, 6) for x in log2k],
               "mixture_top1_by_k": ys,
               "slope_per_doubling": round(slope, 6) if slope is not None else None,
               "end_difference": r6(ys[-1], ys[0]),
               "structured_four_by_k": [mx["fdc"].get(str(k), {}).get("structured_four_top1") for k in ks],
               "non_gutenberg_by_k": [mx["fdc"].get(str(k), {}).get("mixture_top1_non_gutenberg") for k in ks],
               "per_family_by_k": {f: [mx["fdc"].get(str(k), {}).get("per_family", {}).get(f) for k in ks] for f in families},
               "depth": {"by_chunks": mx["depth"], "chunks": dsizes, "mixture_top1_by_chunks": dys,
                         "per_family_by_chunks": {f: [mx["depth"].get(str(n), {}).get("per_family", {}).get(f) for n in dsizes]
                                                  for f in families},
                         "row_effect_within_family": r6(dys[0], dys[-1]),
                         "row_effect_per_doubling_of_chunks": (round((dys[0] - dys[-1]) / math.log2(dsizes[0] / dsizes[-1]), 6)
                                                               if dys[0] is not None and dys[-1] is not None else None)},
               "pred_k1": mx["pred"],
               "family_effect_at_matched_depth": {str(k): r6(mx["fdc"].get(str(k), {}).get("mixture_top1"),
                                                             mx["depth"].get(str(C // k), {}).get("mixture_top1")) for k in ks[1:]},
               "composition_spread_k1": r6(ys[0], pred_m)}
        return out, vecs

    def assemble(complete, launch_no, ci=None):
        curves = {}; mix_vecs = {}
        for r in roles:
            curves[r], mix_vecs[r] = curve(r)
        model_slope = curves["model"]["slope_per_doubling"]; logi_slope = curves["logistic"]["slope_per_doubling"]
        doc = dict(common,
                   environment=env, launch_environment=launch_env, launch_number=launch_no,
                   complete=complete, missing_roles=[n for n in names_expected if n not in records],
                   reproduction={"model_100k": records.get("repro_100k")},
                   incumbent_100k_refit_top1=(records.get("repro_100k") or {}).get("top1"),
                   null_control=records.get("null"), shuffled_label_accuracy=(records.get("null") or {}).get("top1"),
                   null_rows=int(nn),
                   folds={f: {"by_k": {str(k): {r: records.get(f"fold_{f}_k{k}_{r}") for r in roles} for k in ks},
                              "depth": {str(n): {r: records.get(f"depth_{f}_c{n}_{r}") for r in roles} for n in depth_sizes},
                              "pred_k1": {r: records.get(f"pred_{f}_k1_{r}") for r in roles}} for f in families},
                   fdc=curves,
                   fdc_slope_per_doubling=model_slope,
                   fdc_mixture_top1_by_k=curves["model"]["mixture_top1_by_k"],
                   fdc_end_difference=curves["model"]["end_difference"],
                   fdc_slope_model_minus_logistic=(round(model_slope - logi_slope, 6)
                                                   if model_slope is not None and logi_slope is not None else None),
                   cluster_ci95_informational=ci or {},
                   cluster_ci95_note=f"95% cluster-bootstrap intervals over the held-out family's evaluation chunks "
                                     f"(2000 resamples) for each fit and role, and over all {partition['n_eval_chunks']} "
                                     f"chunks for each mixture; informational, never a clause",
                   ledger=store.ledger(),
                   cost={"wall_seconds_this_invocation": round(time.perf_counter() - t_all, 1),
                         "seconds_by_name": {k: v.get("seconds") for k, v in records.items()},
                         "interruptions_by_name": {k: v.get("interruptions_before_this_fit") for k, v in records.items()},
                         "banked_fit_seconds_total": round(sum((v.get("seconds") or 0) for v in records.values()), 1),
                         "checkpoints": os.path.relpath(args.workdir, REPO)},
                   run_started_utc=started, run_finished_utc=_utc() if complete else None)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out + ".tmp", "w") as fh:
            json.dump(doc, fh, indent=2, sort_keys=True); fh.write("\n")
        os.replace(args.out + ".tmp", args.out)
        vec = {k: bits(v) for k, v in per_ex.items()}
        for r, d in mix_vecs.items():
            vec.update({k: bits(v) for k, v in d.items()})
        with open(args.scores_out + ".tmp", "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_scores/1", "preregistration": stamp, "smoke": bool(args.smoke),
                       "eval_idx_sha256": partition["eval_idx_sha256"], "eval_chunk_ids": ge.tolist(),
                       "families": families, "encoding": "each per-example vector is a string of '0'/'1' characters, "
                       "one per evaluation row in eval order (1 = top-1 correct)", "per_example": vec}, fh)
        os.replace(args.scores_out + ".tmp", args.scores_out)
        return doc

    try:
        any_ckpt = any(f.endswith(".json") for f in os.listdir(args.workdir))
        launch_no = store.launches("run", any_ckpt)
        Xe = fill_f32(np.empty((len(ev), ncols), np.float32), X, ev, ncols)
        print(f"[run] eval {len(ev)} rows materialised, anonymous RSS {_rss_gb():.2f} GB "
              f"(total {_rss_total_gb():.2f} GB)", flush=True)

        def fit(name, role, cand, make_block, stage, rows_sha, y_all=None, keep=True):
            """make_block is called only when the fit is not already checkpointed: a resume never gathers a
            block it will not use."""
            fp = fingerprint(prereg=stamp, seed=seed, role=role, cand=cand, stage=stage,
                             rows=rows_sha, eval=partition["eval_idx_sha256"])
            block = None if store.load(name, fp) is not None else make_block()
            r, pe = run_fit(store, name, fp, role, cand, seed, block, y_all if y_all is not None else y, g,
                            Xe, ye, fam_e, stage, caps, keep_per_example=keep, confirmatory=True)
            del block
            records[name] = r
            if pe is not None:
                per_ex[name] = pe
            assemble(False, launch_no)
            return r

        def run_fold(name_fmt, stage, idx, rows_sha):
            holder = {}

            def make_block():
                if "b" not in holder:
                    holder["b"] = Block(X, idx, ncols, stage)
                    print(f"[run] {stage}: {len(idx)} training rows materialised, anonymous RSS {_rss_gb():.2f} GB", flush=True)
                return holder["b"]

            for r in roles:
                fit(name_fmt.format(r=r), r, recipes[r], make_block, stage, rows_sha)
            holder.clear()

        for step in P["order"]:
            if step == "reproduction_100k":
                fit("repro_100k", "model", recipes["model"], lambda: Block(X, rep, ncols, "repro100k"), "reproduction",
                    partition["repro_idx_sha256"])
            elif step == "null":
                # the label shuffle is drawn from the split's generator whether or not the fit is checkpointed, so
                # the generator's state downstream does not depend on resume history (nothing downstream uses it)
                y_sh = np.asarray(y[null_rows]).copy(); rng.shuffle(y_sh)
                y_view = y.copy(); y_view[null_rows] = y_sh
                fit("null", "null", recipes["model"], lambda: Block(X, null_rows, ncols, "null"), "null",
                    partition["null_sorted_sha256"], y_all=y_view, keep=False)
                del y_view
            elif step == "folds":
                for f in families:
                    pf = partition["folds"][f]
                    for k in ks:
                        run_fold(f"fold_{f}_k{k}_{{r}}", f"fdc:{f}:k{k}", folds[f][f"k{k}"], pf["by_k"][str(k)]["train_idx_sha256"])
                    for n in depth_sizes:
                        run_fold(f"depth_{f}_c{n}_{{r}}", f"depth:{f}:c{n}", folds[f][f"c{n}"], pf["depth"][str(n)]["train_idx_sha256"])
                    run_fold(f"pred_{f}_k1_{{r}}", f"pred:{f}:k1", folds[f]["pred"], pf["pred_k1"]["train_idx_sha256"])
            else:
                raise NotRun(f"unknown order step {step!r}")
        ci = {}
        for f in families:
            m = fam_e == f
            for nm in fold_names:
                if nm.split("_")[1] == f and per_ex.get(nm) is not None:
                    ci[nm] = cluster_ci(per_ex[nm][m], ge[m], seed=seed)
        for r in roles:
            _, vecs = mixtures(r)
            for k, v in vecs.items():
                ci[k] = cluster_ci(v, ge, seed=seed)
        if per_ex.get("repro_100k") is not None:
            ci["repro_100k"] = cluster_ci(per_ex["repro_100k"], ge, seed=seed)
        out = assemble(True, launch_no, ci=ci)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "run",
                       "reason": str(e), "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])},
                      fh, indent=2)
        return 4
    print(f"[run] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; model mixture "
          f"by k {out['fdc_mixture_top1_by_k']} slope/doubling {out['fdc_slope_per_doubling']}; depth "
          f"{out['fdc']['model']['depth']['mixture_top1_by_chunks']}; predecessor k=1 "
          f"{(out['fdc']['model']['pred_k1'] or {}).get('mixture_top1')}; logistic by k "
          f"{out['fdc']['logistic']['mixture_top1_by_k']} slope {out['fdc']['logistic']['slope_per_doubling']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
