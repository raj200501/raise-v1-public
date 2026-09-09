#!/usr/bin/env python3
"""The searched logistic under leave-one-family-out transfer (preregistration 0017 at 4096).

Question. 0015 found that under transfer the raw logistic L1 (0.0928) beat the incumbent HGB M1
(0.0859), both near chance + 0.05, while L1 hit its 400-iteration cap in every fold. Does 0014's
searched, standardised logistic L3 - the converged linear rule the record has - beat the incumbent
under transfer by the same 0.05 margin the incumbent had to beat the linear baselines by
in-distribution? For each family f, L3 is fitted on 0015's sealed fold (every pool row of the OTHER
seven families, in pool order) and scored ONCE on the sealed evaluation set; the reading for f is the
accuracy on f's evaluation rows; the LOFO mixture stitches the eight readings as 0015 did. The bar is
the mixture against 0015's banked incumbent mixture plus 0.05.

Reuses tools/pivot/run_recipe_search.py's machinery (blocks, fits, checkpoints, heartbeat, memory
accounting, launch rules) unchanged and 0015's sealed folds hash for hash; nothing here searches or
selects a recipe.

Stages: one invocation (--stage run). Order: the reproduction control on the full pool (L3 must
reproduce 0014's 0.2317), the null control (L3 on 0015's null block with shuffled labels), then the
eight folds in the sealed family order. Checkpoints resume; a container restart is recovered by
relaunching the identical command.
"""
from __future__ import annotations

import argparse
import json
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["run"], default="run")
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0017-lofo-l3-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "lofo_l3_4096_ckpt"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "lofo_l3_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "lofo_l3_4096_scores.json"))
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
    if not args.smoke and prereg.get("frozen") is not True:
        print("REFUSING: a real run needs a frozen preregistration (the reader's literals are generated from it)", file=sys.stderr)
        return 3
    if not args.smoke:
        # a real run never shares the machine with another tools/pivot runner (memory: this run peaks near 9.4 GB)
        others = []
        for pid in os.listdir("/proc"):
            if not pid.isdigit() or int(pid) == os.getpid():
                continue
            try:
                parts = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
            except OSError:
                continue
            # a runner is an interpreter process whose own arguments name a tools/pivot/run_ script; a shell whose
            # command text merely mentions one (an operator's grep) is not (first launch attempt, 18:03 UTC)
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
    assert families == FAMILIES, "the sealed family order must be the corpus family order"
    roles = list(P["roles"])
    if roles != ["logistic_l3"] or set(recipes) != {"logistic_l3"}:
        print("REFUSING: the only role is logistic_l3 with its recipe", file=sys.stderr)
        return 3
    ref15 = dict(P["reference_0015"])   # 0015's banked mixtures, sealed: the margin's other side
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

    # [2] the sealed split (0003's by construction) and the eight folds
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e, fam_t = fam_all[ev], fam_all[tr]
    ev_chunks = np.unique(g[ev])
    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam_e != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev), "eval_y_sha256": _sha(np.asarray(y[ev])),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_y_sha256": _sha(np.asarray(y[tr])),
                 "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64)),
                 "fold_rows": P["fold_rows"], "families": families, "folds": {}}
    folds = {}
    for f in families:
        ev_f = ev[fam_e == f]; tr_f = tr[fam_t != f]
        if P["fold_rows"] != "all":
            tr_f = tr_f[:int(P["fold_rows"])]
        folds[f] = tr_f
        partition["folds"][f] = {
            "n_eval_rows": int(len(ev_f)), "eval_idx_sha256": _sha(ev_f), "n_eval_chunks": int(np.unique(g[ev_f]).size),
            "n_train_rows": int(len(tr_f)), "train_idx_sha256": _sha(tr_f),
            "train_sorted_sha256": _sha(np.sort(tr_f).astype(np.int64)), "n_train_chunks": int(np.unique(g[tr_f]).size),
            "train_rows_of_heldout_family": int((fam_all[tr_f] == f).sum()),
            "train_chunks_shared_with_eval": int(np.intersect1d(np.unique(g[tr_f]), ev_chunks).size),
            "train_rows_in_eval": int(np.intersect1d(tr_f, ev).size)}
    nn = min(len(folds[families[0]]), int(P["null_rows"]))
    null_rows = folds[families[0]][:nn]
    partition["null_rows"] = int(nn); partition["null_sorted_sha256"] = _sha(np.sort(null_rows).astype(np.int64))
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, pool "
          f"{partition['n_pool_rows']}; folds "
          f"{ {f: (partition['folds'][f]['n_train_rows'], partition['folds'][f]['n_eval_rows']) for f in families} }; "
          f"held-out rows in training {sum(partition['folds'][f]['train_rows_of_heldout_family'] for f in families)}, "
          f"shared chunks {sum(partition['folds'][f]['train_chunks_shared_with_eval'] for f in families)}", flush=True)

    store = Store(args.workdir)
    proto_sha = sha_obj(prereg["scope"]["protocol"]); recipes_sha = sha_obj(recipes)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "stage": "run", "protocol": prereg["scope"]["protocol"], "protocol_sha256": proto_sha,
              "recipes": recipes, "recipes_sha256": recipes_sha, "corpus": corpus, "partition": partition,
              "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES, "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    names_expected = ["repro_l3", "null"] + [f"fold_{f}_{r}" for f in families for r in roles]

    started = _utc()
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev])
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}

    def mixture(role):
        """Stitch the eight LOFO per-example vectors: row i is read from the fold that held out i's family."""
        vecs = {f: per_ex.get(f"fold_{f}_{role}") for f in families}
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
                "per_family": {f: round(float(mix[fam_e == f].mean()), 4) for f in families},
                "mixture_vector_key": f"lofo_mixture_{role}"}, mix

    def assemble(complete, launch_no, ci=None):
        lofo = {}; mix_vecs = {}
        for r in roles:
            m = mixture(r)
            if m is not None:
                lofo[r], mix_vecs[r] = m
        l3_mix = (lofo.get("logistic_l3") or {}).get("mixture_top1")
        r6 = lambda a, b: round(a - b, 6) if a is not None and b is not None else None  # noqa: E731
        l3_correct = int(mix_vecs["logistic_l3"].sum()) if "logistic_l3" in mix_vecs else None
        n_iter_by_fold = {f: ((records.get(f"fold_{f}_logistic_l3") or {}).get("fit_info") or {}).get("n_iter") for f in families}
        doc = dict(common,
                   environment=env, launch_environment=launch_env, launch_number=launch_no,
                   complete=complete, missing_roles=[n for n in names_expected if n not in records],
                   reproduction={"logistic_l3": records.get("repro_l3")},
                   logistic_l3_refit_top1=(records.get("repro_l3") or {}).get("top1"),
                   null_control=records.get("null"), shuffled_label_accuracy=(records.get("null") or {}).get("top1"),
                   null_rows=int(nn),
                   folds={f: {r: records.get(f"fold_{f}_{r}") for r in roles} for f in families},
                   lofo=lofo,
                   lofo_mixture_top1=l3_mix,
                   reference_0015=ref15,
                   lofo_correct_l3=l3_correct,
                   lofo_margin_l3_over_0015_model_exact=(round((l3_correct - ref15["model_correct"]) / len(ev), 6)
                                                         if l3_correct is not None else None),
                   lofo_margin_l3_over_0015_model=r6(l3_mix, ref15["model_mixture_top1"]),
                   n_iter_by_fold=n_iter_by_fold,
                   any_fold_at_iteration_cap=(any(v is not None and v >= recipes["logistic_l3"]["params"]["max_iter"] for v in n_iter_by_fold.values())
                                              if all(v is not None for v in n_iter_by_fold.values()) else None),
                   lofo_margin_l3_over_0015_logistic=r6(l3_mix, ref15["logistic_mixture_top1"]),
                   lofo_per_family_margin_over_0015_model={f: r6((lofo.get("logistic_l3") or {}).get("per_family", {}).get(f),
                                                                 ref15["model_per_family"].get(f)) for f in families},
                   cluster_ci95_informational=ci or {},
                   cluster_ci95_note=f"95% cluster-bootstrap intervals over the held-out family's evaluation chunks "
                                     f"(2000 resamples) for each fold and role, and over all {partition['n_eval_chunks']} "
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
        vec = {k: v.tolist() for k, v in per_ex.items()}
        vec.update({f"lofo_mixture_{r}": v.tolist() for r, v in mix_vecs.items()})
        with open(args.scores_out + ".tmp", "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_scores/1", "preregistration": stamp, "smoke": bool(args.smoke),
                       "eval_idx_sha256": partition["eval_idx_sha256"], "eval_chunk_ids": ge.tolist(),
                       "families": families, "per_example": vec}, fh)
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
            block it will not use (a pool gather is 7.09 GB and about two minutes from a cold cache)."""
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

        for step in P["order"]:
            if step == "reproduction_l3":
                fit("repro_l3", "logistic_l3", recipes["logistic_l3"], lambda: Block(X, tr, ncols, "pool"), "reproduction",
                    partition["pool_idx_sha256"])
            elif step == "null":
                # the label shuffle is drawn from the split's generator whether or not the fit is checkpointed, so
                # the generator's state downstream does not depend on resume history (nothing downstream uses it)
                y_sh = np.asarray(y[null_rows]).copy(); rng.shuffle(y_sh)
                y_view = y.copy(); y_view[null_rows] = y_sh
                fit("null", "null", recipes["logistic_l3"], lambda: Block(X, null_rows, ncols, "null"), "null",
                    partition["null_sorted_sha256"], y_all=y_view, keep=False)
                del y_view
            elif step == "folds":
                for f in families:
                    holder = {}

                    def make_fold_block(f=f, holder=holder):
                        if "b" not in holder:
                            holder["b"] = Block(X, folds[f], ncols, f"fold_{f}")
                            print(f"[run] fold {f}: {len(folds[f])} training rows materialised, anonymous RSS "
                                  f"{_rss_gb():.2f} GB", flush=True)
                        return holder["b"]

                    for r in roles:
                        fit(f"fold_{f}_{r}", r, recipes[r], make_fold_block, f"lofo:{f}",
                            partition["folds"][f]["train_idx_sha256"])
                    holder.clear()
            else:
                raise NotRun(f"unknown order step {step!r}")
        ci = {}
        for f in families:
            m = fam_e == f
            for r in roles:
                v = per_ex.get(f"fold_{f}_{r}")
                if v is not None:
                    ci[f"fold_{f}_{r}"] = cluster_ci(v[m], ge[m], seed=seed)
        for r in roles:
            mres = mixture(r)
            if mres is not None:
                ci[f"lofo_mixture_{r}"] = cluster_ci(mres[1], ge, seed=seed)
        if per_ex.get("repro_l3") is not None:
            ci["repro_l3"] = cluster_ci(per_ex["repro_l3"], ge, seed=seed)
        out = assemble(True, launch_no, ci=ci)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "run",
                       "reason": str(e), "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])},
                      fh, indent=2)
        return 4
    print(f"[run] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; LOFO mixture "
          f"L3 {out['lofo_mixture_top1']} vs 0015 incumbent {ref15['model_mixture_top1']} (margin "
          f"{out['lofo_margin_l3_over_0015_model']}) and 0015 logistic {ref15['logistic_mixture_top1']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
