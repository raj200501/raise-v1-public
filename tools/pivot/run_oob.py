#!/usr/bin/env python3
"""Out-of-builder transfer at 4096 (preregistration 0018).

Question. The record's transfer results (0015, 0016, 0017) all stay inside the corpus builder's eight
families. Does the headline recipe - 0014's searched HGB M4 (0.2884 in distribution) - identify the
encoder on content families the builder never produced? Three recipes are fitted ONCE each on 0003's
sealed 800000-row pool (the fit set of 0014 and 0017, hash for hash): 0003's incumbent M1, 0014's
standardised logistic L3 and 0014's searched model M4. Each fit is scored once on the concatenation of
the sealed evaluation set (260000 rows: the reproduction, which must land within 0.005 of the banked
0.2395 / 0.2317 / 0.2884) and the extension corpus (tools/pivot/corpus_ext.py: eight new families,
evaluation only, sealed by array hash). The reading is the accuracy on the extension rows; the clause
is on the headline recipe's count of correct extension rows against chance + 0.05.

Reuses tools/pivot/run_recipe_search.py's machinery (blocks, fits, checkpoints, heartbeat, memory
accounting, launch rules) unchanged. Nothing here searches or selects a recipe, and no extension row is
ever in a fit block.

Stages: one invocation (--stage run). Order: the null control (M4 on the first 20000 pool rows with
shuffled labels, read on the extension rows), then incumbent, logistic_l3, model. Checkpoints resume; a
container restart is recovered by relaunching the identical command.
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

STRUCTURED_TEXT = ["c_src", "py_src", "rfc_txt", "rst_doc", "sql", "xml"]
HIGH_ENTROPY = ["hexdump", "pe_bin"]
REFERENCE_ROLES = ["incumbent", "logistic_l3", "model"]


def _array_sha(path, name):
    arr = npz_memmap(path, name)
    h = hashlib.sha256()
    for i in range(0, len(arr), 20000):
        h.update(np.ascontiguousarray(arr[i:i + 20000]).tobytes())
    return h.hexdigest(), list(arr.shape), str(arr.dtype)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["run"], default="run")
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0018-oob-4096.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "full_c4096.npz"))
    ap.add_argument("--ext", default=os.path.join(REPO, "data", "pivot", "ext_c4096.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "oob_4096_ckpt"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "oob_4096.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot", "oob_4096_scores.json"))
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
        # a real run never shares the machine with another tools/pivot runner (M4 on the pool peaked at 12.19 GB in 0014)
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
    assert families == FAMILIES, "the sealed builder family order must be the corpus family order"
    ext_families = list(P["ext_families"])
    assert ext_families == EXT_FAMILIES, "the sealed extension family order must be corpus_ext's order"
    roles = list(P["roles"])
    if roles != REFERENCE_ROLES or set(recipes) != set(REFERENCE_ROLES):
        print(f"REFUSING: roles must be {REFERENCE_ROLES} with their recipes", file=sys.stderr)
        return 3
    refs = dict(P["reference_top1"])   # banked in-distribution readings the reproductions must reproduce
    env = environment()
    launch_env = {"env": env, "ok": True, "problems": []}
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
    if launch_env["problems"]:
        print("REFUSING TO LAUNCH: " + "; ".join(launch_env["problems"]), file=sys.stderr)
        return 3
    if os.path.exists(not_run_path) and not args.smoke:
        print(f"REFUSING: {os.path.relpath(not_run_path, REPO)} exists; this run was filed NOT RUN", file=sys.stderr)
        return 3

    # [1] corpus A (the builder's) from its cache; y and g are read without touching X, which is memmapped
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
            print(f"REFUSING: cache built at carve {cache_carve}, offset {cache_off}, chunk size {cache_cs}; the "
                  f"preregistration says {P['carve']}, {P['chunk_offset']}, {P['chunk_size']}", file=sys.stderr)
            return 3
        carve_source = "cache metadata written at build time"
    else:
        ident = P.get("cache_identity") or {}
        if ident.get("y_sha256") != cache_y_sha or ident.get("g_sha256") != cache_g_sha:
            print("REFUSING: cache carries no build metadata and its y/g hashes are not the preregistration's sealed "
                  "cache_identity", file=sys.stderr)
            return 3
        cache_carve, cache_off, cache_cs = int(P["carve"]), int(P["chunk_offset"]), int(P["chunk_size"])
        carve_source = "sealed cache identity (sha256 of y and g); the cache carries no build metadata"
    X = npz_memmap(args.cache, "X"); ncols = X.shape[1]
    corpus = {"carve_bytes": cache_carve, "carve_bytes_source": carve_source, "chunk_size": cache_cs, "chunk_offset": cache_off,
              "chunk_id_min": int(g.min()), "chunk_id_max": int(g.max()), "n_source_chunks": int(np.unique(g).size),
              "cache_y_sha256": cache_y_sha, "cache_g_sha256": cache_g_sha, "n_rows": int(len(y)), "n_features": int(ncols)}
    print(f"[1] corpus A: {corpus}", flush=True)

    # [1b] the extension corpus: evaluation only, sealed by array hash (the smoke seals its own tiny build)
    ext_sealed = dict(P["ext_corpus"])
    ext_hashes = {}
    for name in ("X", "y", "g", "fam"):
        h, shape, dtype = _array_sha(args.ext, name)
        ext_hashes[name] = {"sha256": h, "shape": shape, "dtype": dtype}
    mism = [n for n in ext_hashes if ext_hashes[n]["sha256"] != (ext_sealed.get("arrays") or {}).get(n, {}).get("sha256")]
    if mism:
        print(f"REFUSING: extension corpus arrays {mism} do not hash to the preregistration's sealed ext_corpus.arrays",
              file=sys.stderr)
        return 3
    Xx = np.load(_io.BytesIO(_zf.ZipFile(args.ext).read("X.npy"))).astype(np.float32, copy=False)
    with _zf.ZipFile(args.ext) as zf:
        yx = np.load(_io.BytesIO(zf.read("y.npy"))); gx = np.load(_io.BytesIO(zf.read("g.npy")))
        famx = np.load(_io.BytesIO(zf.read("fam.npy")))
        ext_names = [str(s) for s in np.load(_io.BytesIO(zf.read("families.npy")))]
    if ext_names != ext_families or Xx.shape[1] != ncols:
        print("REFUSING: extension corpus family order or feature width differs from the builder's", file=sys.stderr)
        return 3
    fam_x = np.array(ext_families)[famx]
    ext = {"npz": os.path.relpath(args.ext, REPO), "arrays": ext_hashes, "n_rows": int(len(yx)),
           "n_chunks": int(np.unique(gx).size), "families": ext_families,
           "rows_per_family": {f: int((fam_x == f).sum()) for f in ext_families},
           "chunks_per_family": {f: int(np.unique(gx[fam_x == f]).size) for f in ext_families},
           "chunk_id_min": int(gx.min()), "chunk_id_max": int(gx.max()),
           "chunk_ids_disjoint_from_builder": bool(np.intersect1d(np.unique(gx), np.unique(g)).size == 0)}
    print(f"[1b] extension corpus: {ext['n_rows']} rows, {ext['n_chunks']} chunks, {ext['rows_per_family']}", flush=True)

    # [2] the sealed split (0003's by construction): the fit pool and the sealed evaluation set
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam_all = np.array(FAMILIES)[np.asarray(g) % len(FAMILIES)]
    fam_e, fam_t = fam_all[ev], fam_all[tr]
    ev_chunks = np.unique(g[ev])
    if P["fit_rows"] != "all":
        tr = tr[:int(P["fit_rows"])]
    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam_e != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev), "eval_y_sha256": _sha(np.asarray(y[ev])),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_y_sha256": _sha(np.asarray(y[tr])),
                 "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64)),
                 "fit_rows": P["fit_rows"], "families": families,
                 "pool_rows_in_ext": 0, "eval_rows_in_ext": 0}
    if not args.smoke and partition["pool_idx_sha256"] != P["pool_idx_sha256"]:
        print(f"REFUSING: the fit pool hashes to {partition['pool_idx_sha256'][:12]}..., not the sealed "
              f"{P['pool_idx_sha256'][:12]}... (0014's pool)", file=sys.stderr)
        return 3
    nn = min(len(tr), int(P["null_rows"]))
    null_rows = tr[:nn]
    partition["null_rows"] = int(nn); partition["null_sorted_sha256"] = _sha(np.sort(null_rows).astype(np.int64))
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, pool {partition['n_pool_rows']} "
          f"({partition['pool_idx_sha256'][:12]}...), null {nn}", flush=True)

    store = Store(args.workdir)
    proto_sha = sha_obj(prereg["scope"]["protocol"]); recipes_sha = sha_obj(recipes)
    common = {"schema_version": 1, "schema": f"raise-v1/{out_stem}/1", "preregistration": stamp, "smoke": bool(args.smoke),
              "stage": "run", "protocol": prereg["scope"]["protocol"], "protocol_sha256": proto_sha,
              "recipes": recipes, "recipes_sha256": recipes_sha, "corpus": corpus, "ext_corpus": ext, "partition": partition,
              "n_classes": N_CONFIGS, "class_names": CONFIG_NAMES, "chance_accuracy": round(1.0 / N_CONFIGS, 6)}
    names_expected = ["null"] + roles

    started = _utc()
    ge = np.asarray(g[ev]); ye = np.asarray(y[ev]); n_eval = int(len(ev)); n_ext = int(len(yx))
    per_ex: dict[str, np.ndarray] = {}
    records: dict[str, dict] = {}
    r4 = lambda v: round(float(v), 4)  # noqa: E731

    def readings(name):
        """Split one per-example vector into the reproduction (sealed evaluation rows) and the extension reading."""
        v = per_ex.get(name)
        if v is None or len(v) != n_eval + n_ext:
            return None
        rep, ex = v[:n_eval], v[n_eval:]
        out = {"reproduction_top1": r4(rep.mean()), "reproduction_correct": int(rep.sum()),
               "ext_top1": r4(ex.mean()), "ext_correct": int(ex.sum()), "n_ext_rows": n_ext,
               "ext_per_family": {f: r4(ex[fam_x == f].mean()) for f in ext_families},
               "ext_per_family_correct": {f: int(ex[fam_x == f].sum()) for f in ext_families},
               "ext_structured_text_top1": r4(ex[np.isin(fam_x, STRUCTURED_TEXT)].mean()),
               "ext_high_entropy_top1": r4(ex[np.isin(fam_x, HIGH_ENTROPY)].mean()),
               "ext_real_top1": r4(ex[np.isin(fam_x, REAL_FAMILIES)].mean()),
               "ext_synthetic_top1": r4(ex[np.isin(fam_x, SYNTH_FAMILIES)].mean()),
               "reproduction_per_family": {f: r4(rep[fam_e == f].mean()) for f in families}}
        return out

    def assemble(complete, launch_no, ci=None):
        reads = {n: readings(n) for n in names_expected if n in per_ex}
        r6 = lambda a, b: round(a - b, 6) if a is not None and b is not None else None  # noqa: E731
        mc = (reads.get("model") or {}).get("ext_correct"); lc = (reads.get("logistic_l3") or {}).get("ext_correct")
        ic = (reads.get("incumbent") or {}).get("ext_correct")
        doc = dict(common,
                   environment=env, launch_environment=launch_env, launch_number=launch_no,
                   complete=complete, missing_roles=[n for n in names_expected if n not in records],
                   fits={n: records.get(n) for n in names_expected},
                   fit_record_top1_is="accuracy over the CONCATENATED scoring set (sealed evaluation rows then extension rows); "
                                      "informational only - the reproduction and the extension readings are in `readings`",
                   readings=reads,
                   reproduction_top1={r: (reads.get(r) or {}).get("reproduction_top1") for r in roles},
                   reproduction_drift={r: r6((reads.get(r) or {}).get("reproduction_top1"), refs.get(r)) for r in roles},
                   reference_top1=refs,
                   ext_top1={r: (reads.get(r) or {}).get("ext_top1") for r in roles},
                   ext_correct={r: (reads.get(r) or {}).get("ext_correct") for r in roles},
                   ext_top1_model=(reads.get("model") or {}).get("ext_top1"),
                   ext_correct_model=mc,
                   ext_margin_model_over_logistic_l3_exact=(round((mc - lc) / n_ext, 6) if mc is not None and lc is not None else None),
                   ext_margin_model_over_incumbent_exact=(round((mc - ic) / n_ext, 6) if mc is not None and ic is not None else None),
                   ext_per_family={r: (reads.get(r) or {}).get("ext_per_family") for r in roles},
                   null_control=records.get("null"),
                   shuffled_label_accuracy_ext=(reads.get("null") or {}).get("ext_top1"),
                   shuffled_label_accuracy_eval=(reads.get("null") or {}).get("reproduction_top1"),
                   null_rows=int(nn), n_ext_rows=n_ext, n_eval_rows=n_eval,
                   fit_info_by_role={r: (records.get(r) or {}).get("fit_info") for r in roles},
                   cluster_ci95_informational=ci or {},
                   cluster_ci95_note="95% cluster-bootstrap intervals over source chunks (2000 resamples): per extension family, "
                                     "over all extension chunks, and over the sealed evaluation chunks for each reproduction; "
                                     "informational, never a clause",
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
        with open(args.scores_out + ".tmp", "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_scores/1", "preregistration": stamp, "smoke": bool(args.smoke),
                       "n_eval_rows": n_eval, "n_ext_rows": n_ext, "eval_idx_sha256": partition["eval_idx_sha256"],
                       "eval_chunk_ids": ge.tolist(), "ext_chunk_ids": gx.tolist(), "ext_fam": famx.tolist(),
                       "ext_families": ext_families, "ext_arrays_sha256": {k: v["sha256"] for k, v in ext_hashes.items()},
                       "layout": "each per_example vector is [sealed evaluation rows (n_eval_rows)] + [extension rows (n_ext_rows)]",
                       "per_example": {k: v.tolist() for k, v in per_ex.items()}}, fh)
        os.replace(args.scores_out + ".tmp", args.scores_out)
        return doc

    try:
        any_ckpt = any(f.endswith(".json") for f in os.listdir(args.workdir))
        launch_no = store.launches("run", any_ckpt)
        Xs = np.empty((n_eval + n_ext, ncols), np.float32)
        fill_f32(Xs[:n_eval], X, ev, ncols); Xs[n_eval:] = Xx
        del Xx
        ys = np.concatenate([ye, np.asarray(yx)]); fam_s = np.concatenate([fam_e, np.array(["ext:" + f for f in fam_x])])
        print(f"[run] scoring set {n_eval} + {n_ext} rows materialised, anonymous RSS {_rss_gb():.2f} GB "
              f"(total {_rss_total_gb():.2f} GB)", flush=True)

        def fit(name, role, cand, make_block, stage, rows_sha, y_all=None):
            fp = fingerprint(prereg=stamp, seed=seed, role=role, cand=cand, stage=stage, rows=rows_sha,
                             eval=partition["eval_idx_sha256"], ext=ext_hashes["X"]["sha256"])
            block = None if store.load(name, fp) is not None else make_block()
            r, pe = run_fit(store, name, fp, role, cand, seed, block, y_all if y_all is not None else y, g,
                            Xs, ys, fam_s, stage, caps, keep_per_example=True, confirmatory=True)
            del block
            records[name] = r
            if pe is not None:
                per_ex[name] = pe
            rd = readings(name)
            if rd:
                print(f"      {name:<12} reproduction {rd['reproduction_top1']} | extension {rd['ext_top1']} "
                      f"({rd['ext_correct']}/{n_ext}) {rd['ext_per_family']}", flush=True)
            assemble(False, launch_no)
            return r

        pool_holder = {}

        def pool_block():
            if "b" not in pool_holder:
                pool_holder["b"] = Block(X, tr, ncols, "pool")
                print(f"[run] pool {len(tr)} rows materialised, anonymous RSS {_rss_gb():.2f} GB", flush=True)
            return pool_holder["b"]

        for step in P["order"]:
            if step == "null":
                y_sh = np.asarray(y[null_rows]).copy(); rng.shuffle(y_sh)
                y_view = y.copy(); y_view[null_rows] = y_sh
                fit("null", "null", recipes["model"], lambda: Block(X, null_rows, ncols, "null"), "null",
                    partition["null_sorted_sha256"], y_all=y_view)
                del y_view
            elif step in roles:
                fit(step, step, recipes[step], pool_block, "pool", partition["pool_idx_sha256"])
            else:
                raise NotRun(f"unknown order step {step!r}")
        pool_holder.clear()
        ci = {}
        for n in names_expected:
            v = per_ex.get(n)
            if v is None:
                continue
            ex = v[n_eval:]
            ci[f"{n}_ext"] = cluster_ci(ex, gx, seed=seed)
            for f in ext_families:
                m = fam_x == f
                ci[f"{n}_ext_{f}"] = cluster_ci(ex[m], gx[m], seed=seed)
            ci[f"{n}_reproduction"] = cluster_ci(v[:n_eval], ge, seed=seed)
        out = assemble(True, launch_no, ci=ci)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp, "stage": "run", "reason": str(e),
                       "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])}, fh, indent=2)
        return 4
    print(f"[run] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; extension top1 "
          f"{out['ext_top1']} (reproductions {out['reproduction_top1']}, null on extension "
          f"{out['shuffled_label_accuracy_ext']})", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
