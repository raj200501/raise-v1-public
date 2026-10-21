#!/usr/bin/env python3
"""Pre-freeze check for preregistration 0025 (run before `tools/prereg.py freeze`; committed with the freeze, result
banked in artifacts/verification/prefreeze_0025.json). Exit 1 on any mismatch, 2 once the preregistration is frozen.

What it checks, and why each one exists:
 1. The reader is exactly what the generator produces from the preregistration and the template - no hand edit.
 2. Every sealed literal in the reader equals the preregistration's (protocol and curve hashes, recipes, the references
    of 0021, 0023 and 0024 including 0024's banked intervals, both tolerances, the null-label hash, the partition and the
    eight rungs, both shift arms, the four corpora, the order of 37 fits, the bar with its gain rule and lead rule, the
    bootstrap and the stability seeds).
 3. The corpora on disk hash to the sealed arrays and their blocks are REBUILT BY CALLING the runner's corpus_block();
    the fit block, the eight rungs and both shift arms are REBUILT BY CALLING the runner's rung_partition3() on the three
    fit corpora and must equal the sealed constants hash for hash; the sealed evaluation set, the pool and the null-label
    array are RECOMPUTED from the builder cache and the corpora with the runner's own split and generator
    (OPERATING_RULES 4).
 4. Rungs 1..7 and 0024's shift arm are 0024's hash for hash; the references trace to 0021's, 0023's and 0024's banked
    artifacts; the recipes are 0024's three and three of 0021's four floors (B-tree3 is D1); the fourth-doubling corpus
    is nested on 0024's pool and its manifest is the sealed one; the reference numbers quoted in the prose are banked.
 5. Every key the reader compares is a key the runner writes (the captured fixture), the reader's per-record
    requirements hold against the runner's own banked records, and the fixture is current with the runner in the tree.
 6. Nothing of this run exists yet: no artifact, scores, verdict, NOT RUN file or checkpoints; the preregistration is
    unfrozen and 0024 is the chain head; the smoke block names scratchpad corpora; a real run refuses to start.
 7. The banked mutation report agrees with the coverage map's claim and carries this gate.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
SP = os.environ.get("PREREG_0025_SCRATCH", tempfile.mkdtemp(prefix="prefreeze_0025_"))
os.makedirs(SP, exist_ok=True)
bad = 0


def chk(cond, msg):
    global bad
    print(("ok   " if cond else "BAD  ") + msg)
    if not cond:
        bad += 1


def main() -> int:
    global bad
    pr = json.load(open(f"{REPO}/prereg/0025-realcurve3-4096.json", encoding="utf-8"))
    if pr.get("frozen"):
        print(f"PRE-FREEZE 0025: the preregistration is frozen ({pr.get('frozen_utc')}); this check runs before a freeze "
              f"only. The result it banked then is artifacts/verification/prefreeze_0025.json.", file=sys.stderr)
        return 2
    S = pr["scope"]; CU = S["curve"]; P = CU["protocol"]; RE = CU["recipes"]; sp = S["sealed_partition"]
    canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
    sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

    # 1. the reader is the generated file
    gen = os.environ.get("PREREG_0025_GENERATOR")
    reader_path = f"{REPO}/tools/readers/realcurve3_4096_verdict.py"
    reader = open(reader_path, encoding="utf-8").read()
    if gen and os.path.exists(gen):
        tmp = os.path.join(SP, "regenerated_reader.py")
        rc = subprocess.run([sys.executable, gen, f"{REPO}/prereg/0025-realcurve3-4096.json", tmp], capture_output=True, text=True)
        chk(rc.returncode == 0 and open(tmp, encoding="utf-8").read() == reader,
            "the reader is exactly what the generator produces from this preregistration")
    else:
        chk(False, "PREREG_0025_GENERATOR is not set to the generator script; cannot prove the reader was generated")

    # 2. the reader's sealed literals are the preregistration's
    import importlib.util
    spec = importlib.util.spec_from_file_location("r25", reader_path)
    r25 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r25)
    chk(r25.PREREG == f"{pr['id']}-{pr['slug']}", "the reader is frozen for this preregistration")
    chk(set(CU) == {"protocol", "recipes"}, "the sealed curve spec is exactly {protocol, recipes}")
    chk(r25.PROTOCOL == P and r25.PROTOCOL_SHA256 == sha(P) == S["sealed_hashes"]["protocol_sha256"],
        "the reader's PROTOCOL is the sealed protocol and hashes to the sealed hash")
    chk(r25.CURVE_SHA256 == sha(CU) == S["sealed_hashes"]["curve_sha256"] and r25.RECIPES == RE,
        "the reader's curve hash and recipes are the sealed ones")
    chk(r25.REFERENCE == P["reference_top1"] and r25.REFERENCE_FIRST == P["reference_first_decade"] and r25.REFERENCE_0024 == P["reference_0024"]
        and r25.REFERENCE_SHIFT_0024 == P["reference_shift_arm_0024"] and r25.REFERENCE_BOOT_0024 == P["reference_bootstrap_0024"]
        and r25.REPRO_TOLERANCE == P["reproduction_tolerance"] and r25.REPRO_TOLERANCE_R7 == P["reproduction_tolerance_rung7"] == 0.0005
        and r25.NULL_TOLERANCE == P["null_tolerance"] and r25.NULL_SHA_EXPECTED == P["null_y_shuffled_sha256_expected"]
        and r25.N_REAL == P["n_ext_real_rows"] and r25.N_EXT == P["ext_corpus"]["n_rows"],
        "the reader's references (0021, 0023, 0024 rungs, 0024 shift arm, 0024 intervals), tolerances, null-label hash and row counts are the sealed ones")
    chk(r25.BAR_GAIN == P["bar"]["gain_per_doubling"] == 0.005 and r25.GAIN_RULE == P["bar"]["gain_rule"] and r25.LEAD_RULE == P["bar"]["lead_rule"]
        and r25.N_BOOT == P["bootstrap"]["n_boot"] == 2000 and r25.BOOT_SEED == P["bootstrap"]["seed"] == P["seed2"] == 20260917
        and r25.SEED2 == P["seed2"] == sp["seed2"] and r25.SEED3 == P["seed3"] == sp["seed3"] == 20260923 and r25.STABILITY_SEEDS == P["stability_seeds"] == 20,
        "the reader's bar (gain rule, lead rule), bootstrap (0024's seed), seed3 and stability-seed literals are the sealed ones")
    chk(list(r25.ORDER) == P["order"] and list(r25.ROLES) == P["roles"] == ["depth3_tree", "logistic", "model"]
        and list(r25.FLOOR_ROLES) == P["floor_roles"] == ["floor_majority", "floor_stratified", "floor_feat1"]
        and list(r25.DENOMINATORS) == P["denominators"] == [8, 4, 2, 1] and r25.N_FIRST == P["n_first_decade_rungs"] == 4
        and r25.DOUBLINGS_0024 == P["doublings_0024"] == 3 and r25.DOUBLINGS_0025 == P["doublings_0025"] == 1 and r25.N_RUNGS == 8 and r25.N_0024_RUNGS == 7
        and len(r25.ORDER) == 37 and r25.SHIFT4 == P["shift"] == "s4" and r25.SHIFT8 == P["shift_0025"] == "s8"
        and r25.LOG2X == [r["log2_chunks"] for r in sp["rungs"]] and r25.LOG2X_SECOND == r25.LOG2X[3:] and r25.LOG2X_SECOND_0024 == r25.LOG2X[3:7],
        "the reader's order (37 roles), roles, floors, denominators, doublings, rung counts, shift arm names and log2 abscissae are the sealed ones")
    chk(r25.PARTITION["shift_arm"] == P["shift_arm_hashes"] == sp["shift_arm"] and r25.PARTITION["shift_arm_0025"] == P["shift_arm_0025_hashes"] == sp["shift_arm_0025"],
        "the reader's two shift arms are the sealed ones")
    chk(r25.ENV == P["environment"] and r25.ENV_FULL == dict(P["environment"], threads=P["threads"], nice=P["nice"]), "the reader's environment literals are the sealed ones")
    chk(r25.EXT == P["ext_corpus"] and r25.FIT == P["fit_corpus"] and r25.FIT2 == P["fit2_corpus"] and r25.FIT3 == P["fit3_corpus"], "the reader's four corpus blocks are the sealed ones")
    for k, v in P["fit_block_hashes"].items():
        chk(r25.PARTITION.get(k) == v, f"the reader's PARTITION.{k} is the sealed fit-block hash")
    chk(r25.PARTITION["rungs"] == P["rung_hashes"] == sp["rungs"] and len(sp["rungs"]) == 8, "the reader's PARTITION.rungs is the sealed eight-rung table")
    chk(r25.PARTITION["pool_chunks_with_rows_per_family"] == P["pool_chunks_with_rows_per_family"] == sp["pool_chunks_with_rows_per_family"]
        and r25.PARTITION["pool_chunks_with_rows_per_family_0024"] == P["pool_chunks_with_rows_per_family_0024"] == sp["pool_chunks_with_rows_per_family_0024"]
        and r25.PARTITION["pool_short"] == {}, "the reader's pool counts (0024's and in all) are the sealed ones and pool_short is empty")
    chk(r25.EVAL_CHUNK_IDS == S["eval_chunk_layout"]["chunk_ids"] and r25.EVAL_ROWS_PER_CHUNK == S["eval_chunk_layout"]["rows_per_chunk"]
        and r25.EXT_CHUNK_IDS == S["ext_chunk_layout"]["chunk_ids_with_rows"] and r25.EXT_ROWS_PER_CHUNK == S["ext_chunk_layout"]["rows_per_chunk"],
        "the reader's chunk layouts are the sealed ones")
    chk(r25.MAX_ITER == {r: (RE[r].get("params", {}).get("max_iter") or 0) for r in r25.ROLES}, "the reader's iteration caps are the recipes'")
    paths = [x["json_path"] for x in pr["readings"]]
    chk(all(p.startswith("$.") and p[2:].split(".")[0] in r25.RESULT_KEYS for p in paths), "every sealed reading's json_path names a key the reader writes on every path")

    # 3. the corpora, the fit block, the rungs and both shift arms, rebuilt by calling the runner's own code on the data
    from run_realfit import corpus_block, _array_sha
    import run_realcurve as rc1_
    import run_realcurve2 as rc2_
    import run_realcurve3 as rc_

    def _runner_block(rel, labels):
        d = np.load(f"{REPO}/{rel}", allow_pickle=False)
        names = [str(x) for x in d["families"]]; fam = np.array(names)[d["fam"]]
        h = {n: dict(zip(("sha256", "shape", "dtype"), _array_sha(f"{REPO}/{rel}", n))) for n in ("X", "y", "g", "fam")}
        src = set(str(v) for v in d["meta_src_sha256"])
        return corpus_block(rel, h, d["y"], d["g"], fam, names, labels=labels), d, names, fam, src
    rb_fit, dfit, fit_names, fam_r, fit_src = _runner_block("data/pivot/realfit_c4096.npz", True)
    rb_fit2, dfit2, fit2_names, fam_2, fit2_src = _runner_block("data/pivot/realfit2_c4096.npz", True)
    rb_fit3, dfit3, fit3_names, fam_3, fit3_src = _runner_block("data/pivot/realfit3_c4096.npz", True)
    rb_ext, _, _, _, ext_src = _runner_block("data/pivot/ext_c4096.npz", False)
    chk(P["fit_corpus"] == rb_fit and P["ext_corpus"] == rb_ext and P["fit2_corpus"] == rb_fit2 and P["fit3_corpus"] == rb_fit3,
        "the sealed corpus blocks are what the runner banks from the four npz on disk")
    man3 = json.load(open(f"{REPO}/artifacts/pivot/realfit3_corpus_manifest.json"))
    chk(not (fit3_src & fit_src) and not (fit3_src & ext_src) and not (fit3_src & fit2_src)
        and len(fit3_src) == sp["source_chunks"]["n_fit3_source_chunks"] == rb_fit3["n_chunks"] + len(man3["chunks_without_rows"]),
        "the fourth-doubling corpus shares no source-chunk hash with 0021's block, 0024's corpus or the scored corpus, and its distinct hash count is the sealed one")
    max_id = {f: int(dfit2["meta_chunk_ids"][dfit2["meta_chunk_fam"] == fi].max()) for fi, f in enumerate(fit2_names)}
    bidx = {int(i): int(b) for i, b in zip(dfit3["meta_chunk_ids"], dfit3["meta_blob_chunk_index"])}
    y23 = np.concatenate([np.asarray(dfit2["y"]), np.asarray(dfit3["y"])]); g23 = np.concatenate([np.asarray(dfit2["g"]), np.asarray(dfit3["g"])]); fam_23 = np.concatenate([fam_2, fam_3])
    fit_order, rows_all, RP = rc_.rung_partition3(dfit["y"], dfit["g"], fam_r, fit_names, P["seed"], P["denominators"], y23, g23, fam_23, P["seed2"],
                                                   P["doublings_0024"], P["seed3"], P["doublings_0025"], max_id, bidx, P["n_whole_chunks_in_0024_blob_per_family"])
    chk(max_id == sp["max_chunk_id_0024_per_family"] and all(int(dfit3["meta_chunk_ids"][dfit3["meta_chunk_fam"] == fi].min()) == max_id[f] + 1 for fi, f in enumerate(fit3_names)),
        "0025's chunk ids continue 0024's per family, and the sealed maxima are 0024's")
    chk(RP["shift_arm"] == P["shift_arm_hashes"] and RP["shift_arm_0025"] == P["shift_arm_0025_hashes"] and RP["shift_arm_0025"]["all_chunks_in_the_top_rung"]
        and RP["shift_arm_0025"]["all_chunks_above_0024s_ids"] and RP["shift_arm_0025"]["same_plaintext_count_as_rung_4"]
        and len(rows_all) == RP["n_rungs"] + 2 and len(rows_all[-1]) == RP["shift_arm_0025"]["n_rows"] and len(rows_all[-2]) == RP["shift_arm"]["n_rows"],
        "the sealed shift arms are what rung_partition3() computes: 0024's reproduced, the new one from the top rung's new-file chunks at rung 4's count")
    chk(all(RP[k] == v for k, v in P["fit_block_hashes"].items()), "the sealed fit-block hashes are what the runner's rung_partition3() computes")
    chk(RP["rungs"] == P["rung_hashes"] == sp["rungs"], "the sealed rung table is what the runner's rung_partition3() computes from the three corpora, hash for hash")
    chk(RP["rungs_nested"] and RP["rung_chunks_strictly_increasing"] and RP["rung4_is_fit_block"] and RP["second_decade_exact_doublings"]
        and RP["pool_short"] == {} and RP["doublings_spanned"] == sp["doublings_spanned"] and RP["doublings_spanned_second_decade"] == sp["doublings_spanned_second_decade"] == 4.0
        and RP["fourth_doubling_rule"] == P["fourth_doubling_rule"] == sp["fourth_doubling_rule"] and RP["second_decade_rule"] == P["second_decade_rule"] and RP["rung_rule"] == P["rung_rule"],
        "the rungs are nested, strictly increasing, exact doublings on 0021's block, the pool covers them, and the sealed rules and spans are the runner's")
    chk(all(r25.PARTITION[k] == RP[k] for k in RP if k in r25.PARTITION), "every fit-block, rung, shift-arm and pool key the reader seals equals the runner's recomputation")
    base = RP["fit_chunks_per_family"]
    chk(all(RP["rungs"][3 + d]["chunks_per_family"][f] == base[f] * 2 ** d for d in range(1, 5) for f in fit_names)
        and all(RP["rungs"][3 + d]["n_rows"] == len(rows_all[3 + d]) for d in range(1, 5)),
        "every second-decade rung holds exactly 2^d times rung 4's plaintexts of every family, and its row count is its row set's")
    chk(all(sum(r["chunks_per_family"].values()) == r["n_chunks"] and sum(r["rows_per_family"].values()) == r["n_rows"] for r in RP["rungs"]), "every rung's family counts sum to its totals")
    comp = RP["rungs"][-1]["added_composition_per_family"]
    chk(all(comp[f]["n"] == base[f] * 8 == comp[f]["from_0024_pool"] + comp[f]["from_0024_archives_unused"] + comp[f]["from_new_files"] for f in fit_names)
        and comp["c_src"]["from_new_files"] == 0 and comp["pe_bin"]["from_new_files"] == 0 and comp["py_src"]["from_new_files"] > 0 and comp["rfc_txt"]["from_new_files"] > 0,
        "the fourth doubling's composition per family sums to 8 x n_f, with no new-file chunk for c_src and pe_bin and new-file chunks for py_src and rfc_txt")
    # rungs 1..7 and the shift arm are 0024's, hash for hash; rungs 1..4 are 0023's; the fit block is 0021's
    p24 = json.load(open(f"{REPO}/prereg/0024-realcurve2-4096.json", encoding="utf-8")); P24 = p24["scope"]["curve"]["protocol"]
    a24 = json.load(open(f"{REPO}/artifacts/pivot/realcurve2_4096.json", encoding="utf-8")); v24 = json.load(open(f"{REPO}/artifacts/pivot/realcurve2_4096_verdict.json", encoding="utf-8"))
    keys24 = list(P24["rung_hashes"][0])
    chk([{k: r[k] for k in keys24} for r in RP["rungs"][:7]] == P24["rung_hashes"] and [{k: r[k] for k in keys24} for r in a24["partition"]["rungs"]] == P24["rung_hashes"]
        and RP["shift_arm"] == P24["shift_arm_hashes"] == a24["partition"]["shift_arm"], "rungs 1..7 and the shift arm are 0024's sealed and banked ones, hash for hash")
    p23 = json.load(open(f"{REPO}/prereg/0023-realcurve-4096.json", encoding="utf-8"))
    keys1 = list(p23["scope"]["curve"]["protocol"]["rung_hashes"][0])
    chk([{k: r[k] for k in keys1} for r in RP["rungs"][:4]] == p23["scope"]["curve"]["protocol"]["rung_hashes"], "rungs 1..4 are 0023's sealed rungs, hash for hash")
    a21 = json.load(open(f"{REPO}/artifacts/pivot/realfit_4096_rerun.json", encoding="utf-8")); p21 = json.load(open(f"{REPO}/prereg/0021-realfit-4096-rerun.json", encoding="utf-8"))
    chk(RP["fit_idx_sha256"] == a21["partition"]["fit_idx_sha256"] == p21["scope"]["sealed_partition"]["fit_block"]["idx_sha256"] and RP["rungs"][3]["idx_sha256"] == RP["fit_idx_sha256"],
        "rung 4 is 0021's fit block, row for row (its banked and sealed hashes)")
    # A rebuilt builder cache (CORRECTIONS.md, 2026-10-21) moves the row-POSITION hashes only; amend_cache_0025.py keeps each banked one
    # beside its replacement as *_banked_2026_08. The banked values must be 0024's, and everything else - the labels and chunk ids of the
    # evaluation rows in order, the row and chunk counts - must be 0024's unchanged.
    _MOVABLE = {"X_sha256", "y_sha256", "g_sha256", "eval_idx_sha256", "pool_idx_sha256", "pool_sorted_sha256", "pool_y_sha256"}
    _bk = lambda d: {k[:-len("_banked_2026_08")] if k.endswith("_banked_2026_08") else k: v for k, v in d.items()  # noqa: E731
                     if k.endswith("_banked_2026_08") or f"{k}_banked_2026_08" not in d}
    _banked_keys = []

    def _scan(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if path == "" and k == "amendments_before_freeze":
                    continue
                if k.endswith("_banked_2026_08"):
                    _banked_keys.append((f"{path}.{k}", k[:-len("_banked_2026_08")]))
                _scan(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                _scan(v, f"{path}[{i}]")
    _scan(pr, "")
    chk(all(base in _MOVABLE for _, base in _banked_keys)
        and {p for p, _ in _banked_keys} <= {f".scope.curve.protocol.cache_identity.{k}_banked_2026_08" for k in ("X_sha256", "y_sha256", "g_sha256")}
        | {".scope.sealed_partition.eval.eval_idx_sha256_banked_2026_08"}
        | {f".scope.sealed_partition.pool.{k}_banked_2026_08" for k in ("pool_idx_sha256", "pool_sorted_sha256", "pool_y_sha256")},
        "a banked-beside-the-new value exists only for the seven hashes a rebuilt cache may move, and only where amend_cache_0025.py puts them")
    _pidx = sp["pool"].get("pool_idx_sha256_banked_2026_08", P["pool_idx_sha256"])
    chk(_bk(sp["eval"]) == p24["scope"]["sealed_partition"]["eval"] and _bk(sp["pool"]) == p24["scope"]["sealed_partition"]["pool"] and sp["fit_block"] == p24["scope"]["sealed_partition"]["fit_block"]
        and sp["eval"]["eval_y_sha256"] == p24["scope"]["sealed_partition"]["eval"]["eval_y_sha256"] and sp["eval"]["eval_g_sha256"] == p24["scope"]["sealed_partition"]["eval"]["eval_g_sha256"]
        and _pidx == a21["partition"]["pool_idx_sha256"], "the evaluation set, the pool and the fit block are 0024's sealed ones (0021's before it); a rebuilt cache moves row positions only")
    _rebuilt = bool(_banked_keys)
    _hex64 = lambda v: isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) is not None  # noqa: E731
    chk(all(_hex64(P["cache_identity"][k]) for k in ("X_sha256", "y_sha256", "g_sha256")) and _hex64(P["pool_idx_sha256"])
        and all(_hex64(sp[b][k]) for b, k in (("eval", "eval_idx_sha256"), ("eval", "eval_y_sha256"), ("eval", "eval_g_sha256"),
                                               ("pool", "pool_idx_sha256"), ("pool", "pool_sorted_sha256"), ("pool", "pool_y_sha256"))),
        "every sealed cache and partition hash is a sha256 (an empty X hash would switch the runner's X check off)")
    if _rebuilt:
        _proof_path = f"{REPO}/artifacts/verification/cache_rebuild_0025.json"
        _proof = json.load(open(_proof_path, encoding="utf-8"))
        _am = [a for a in pr.get("amendments_before_freeze", []) if a.get("by") == "tools/prereg_gen/0025/amend_cache_0025.py"]
        _cf = _proof.get("cache_file") or {}
        _sealed_new = {"X": P["cache_identity"]["X_sha256"], "y": P["cache_identity"]["y_sha256"], "g": P["cache_identity"]["g_sha256"],
                       "eval_idx": sp["eval"]["eval_idx_sha256"], "pool_idx": sp["pool"]["pool_idx_sha256"],
                       "pool_sorted": sp["pool"]["pool_sorted_sha256"], "pool_y": sp["pool"]["pool_y_sha256"]}
        chk(_proof.get("passed") is True and _proof.get("mode") == "full" and len(_am) >= 1 and all(_am[-1]["order_proof"].values())
            and _am[-1].get("new") == _sealed_new
            and _am[-1].get("proof_sha256") == hashlib.sha256(open(_proof_path, "rb").read()).hexdigest()
            and _cf.get("X_sha256") == _sealed_new["X"] and _cf.get("y_sha256") == _sealed_new["y"] and _cf.get("g_sha256") == _sealed_new["g"]
            and _proof.get("eval_X_sha256_in_sealed_order") == _am[-1].get("eval_X_sha256_in_sealed_order")
            and P.get("pool_idx_sha256") == sp["pool"]["pool_idx_sha256"] and P["cache_identity"]["X_note"].startswith("REBUILT 2026-10-21"),
            "the rebuilt cache's re-seal is recorded with its order proof, its content proof (0021's recipes reproduce on its evaluation "
            "rows) passed on THIS cache (the proof's cache hashes and evaluation-feature digest are the sealed ones), and the proof file is "
            "the one the re-seal read")
    import io as _io, zipfile as _zf
    from run_recipe_search import grouped_split, _sha as _rsha
    with _zf.ZipFile(f"{REPO}/data/pivot/full_c4096.npz") as zf:
        y_b = np.load(_io.BytesIO(zf.read("y.npy"))); g_b = np.load(_io.BytesIO(zf.read("g.npy")))
    ev, tr, rng = grouped_split(y_b, g_b, P["seed"], P["eval_frac"], P["top_rung"])
    from run_realfit import _array_sha as _xsha
    chk(_rsha(y_b) == P["cache_identity"]["y_sha256"] and _rsha(g_b) == P["cache_identity"]["g_sha256"]
        and _xsha(f"{REPO}/data/pivot/full_c4096.npz", "X")[0] == P["cache_identity"]["X_sha256"]
        and _rsha(np.asarray(y_b[tr])) == sp["pool"]["pool_y_sha256"],
        "the builder cache on disk is the sealed one (y, g and X hashes) and its pool labels hash to the sealed pool_y_sha256")
    chk(_rsha(ev) == r25.PARTITION["eval_idx_sha256"] and _rsha(np.asarray(g_b[ev])) == r25.PARTITION["eval_g_sha256"] and _rsha(np.asarray(y_b[ev])) == r25.PARTITION["eval_y_sha256"]
        and _rsha(tr) == P["pool_idx_sha256"] and _rsha(np.sort(tr).astype(np.int64)) == r25.PARTITION["pool_sorted_sha256"] and int(len(ev)) == r25.PARTITION["n_eval_rows"],
        "the sealed evaluation set and pool hashes are what the runner's grouped_split() computes from the builder cache on disk")
    if _rebuilt:
        # the evaluation rows' features on disk, in the sealed order, are the ones the content proof covered (a hand-written proof
        # or record cannot stand in for them)
        from npzmap import npz_memmap as _nm
        _Xm = _nm(f"{REPO}/data/pivot/full_c4096.npz", "X"); _h = hashlib.sha256()
        for _i in range(0, len(ev), 20000):
            _h.update(np.ascontiguousarray(_Xm[ev[_i:_i + 20000]], dtype=np.float32).tobytes())
        del _Xm
        chk(_h.hexdigest() == _am[-1].get("eval_X_sha256_in_sealed_order") == _proof.get("eval_X_sha256_in_sealed_order"),
            "the evaluation rows' features on disk, in the sealed order, are the ones the content proof covered")
    y_all = np.concatenate([np.asarray(dfit["y"]), y23]); top_rows = rows_all[RP["n_rungs"] - 1]
    sub = y_all[top_rows].copy(); np.random.default_rng([P["seed3"], rc2_.NULL_STREAM_WORD]).shuffle(sub)
    chk(_rsha(sub) == P["null_y_shuffled_sha256_expected"] and not np.array_equal(sub, y_all[top_rows]) and np.array_equal(np.sort(sub), np.sort(y_all[top_rows])),
        "the sealed null-label hash is what the sealed stream (seed3) produces on the top rung's labels, a permutation of them")
    _ci = lambda d: {k[:-len("_banked_2026_08")] if k.endswith("_banked_2026_08") else k: v for k, v in d.items()  # noqa: E731
                     if k != "X_note" and (k.endswith("_banked_2026_08") or f"{k}_banked_2026_08" not in d)}
    _hk = {"cache_X_sha256": "X_sha256", "cache_y_sha256": "y_sha256", "cache_g_sha256": "g_sha256"}
    chk(_ci(P["cache_identity"]) == _ci(p21["scope"]["protocol"]["cache_identity"]) and r25.CORPUS["cache_X_sha256"] == P["cache_identity"]["X_sha256"]
        and all(r25.CORPUS[k] == (P["cache_identity"][_hk[k]] if k in _hk else a21["corpus"][k]) for k in r25.CORPUS)
        and all(a21["corpus"][k] == P["cache_identity"].get(f"{c}_banked_2026_08", P["cache_identity"][c]) for k, c in _hk.items()),
        "the builder cache identity is 0021's (or a rebuilt cache's with 0021's kept beside it), and the reader's CORPUS is 0021's banked block with the sealed cache hashes")
    chk(S["eval_chunk_layout"] == p24["scope"]["eval_chunk_layout"] and S["ext_chunk_layout"] == p24["scope"]["ext_chunk_layout"], "the chunk layouts are 0024's sealed ones")

    # 4. references, recipes, the corpus manifests and the quoted numbers trace to banked artifacts and sealed files
    chk(P["reference_top1"] == P24["reference_top1"] and P["reference_first_decade"] == P24["reference_first_decade"]
        and P["reference_0024"] == {role: [p["ext_real_top1"] for p in v24["curves"][role]["rungs"]] for role in r25.ROLES}
        and P["reference_shift_arm_0024"] == {role: v24["shift_arm"]["readings"][role]["ext_real_top1"] for role in r25.ROLES}
        and P["reference_bootstrap_0024"]["slope_bootstrap"] == {k: v for k, v in v24["slope_bootstrap"].items() if k != "unit"}
        and P["reference_bootstrap_0024"]["lead_at_top"] == {k: v for k, v in v24["lead_at_top"].items() if k not in ("unit", "verdict_pair")}
        and v24["verdict"] == "SECOND_DECADE_RISES_MODEL_LEADS" and v24["reproduction_drift"] == {"depth3_tree": 0.0, "logistic": 0.0, "model": 0.0},
        "the references are 0021's, 0023's and 0024's banked readings and 0024's banked intervals, verbatim")
    chk({r: RE[r] for r in r25.ROLES} == p24["scope"]["curve"]["recipes"] and {r: RE[r] for r in r25.FLOOR_ROLES} == {r: p21["scope"]["recipes"][r] for r in r25.FLOOR_ROLES}
        and p24.get("frozen") is True and P["recipe_ids"]["model"] == "M4" and P["recipe_ids"]["floor_feat1"] == "B-feat1"
        and "floor_tree3" not in RE and p21["scope"]["recipes"]["floor_tree3"]["params"] == RE["depth3_tree"]["params"] == {"max_depth": 3},
        "the recipes are 0024's sealed three (M4, L3, D1) and three of 0021's four floors verbatim; B-tree3 is D1 and is not fitted twice")
    man2 = json.load(open(f"{REPO}/artifacts/pivot/realfit2_corpus_manifest.json", encoding="utf-8"))
    pins3 = json.load(open(f"{REPO}/tools/pivot/ext_source_pins3.json", encoding="utf-8"))
    chk(P["fit3_corpus"]["arrays"] == man3["arrays"] and man3["smoke"] is False and man3["seed"] == P["seed3"] == pins3["seed"] and man3["doublings"] == 4 == pins3["doublings"]
        and man3["nested_on"]["realfit2_arrays"] == man2["arrays"] == P["fit2_corpus"]["arrays"]
        and all(man3["per_family"][f]["pool_prefix_is_0024s_pool"] for f in fit_names)
        and P["fit3_corpus_described"]["manifest_sha256"] == hashlib.sha256(open(f"{REPO}/artifacts/pivot/realfit3_corpus_manifest.json", "rb").read()).hexdigest()
        and S["artifact_identity_at_writing"]["ext_source_pins3_sha256"] == hashlib.sha256(open(f"{REPO}/tools/pivot/ext_source_pins3.json", "rb").read()).hexdigest(),
        "the fourth-doubling corpus block is the banked manifest's, nested on 0024's banked arrays with 0024's pool as its prefix, built with the sealed seed from the pinned sources")
    chk(P["pool_chunks_with_rows_per_family"] == {f: man3["per_family"][f]["n_pool_chunks_with_rows_total"] for f in fit_names}
        and P["pool_chunks_with_rows_per_family_0024"] == {f: man2["per_family"][f]["n_chunks_with_rows"] for f in fit_names}
        and P["n_whole_chunks_in_0024_blob_per_family"] == {f: man3["per_family"][f]["n_whole_chunks_in_0024_blob"] for f in fit_names}
        and all(man3["per_family"][f]["n_candidate_chunks_in_0024_frame"] == man2["per_family"][f]["n_candidate_chunks"] for f in fit_names)
        and man3["exclusion"]["run_overlap"]["run_windows"] * man3["exclusion"]["run_overlap"]["window"] == 1024 and "run_overlap_vs_0024" in man3["exclusion"]
        and P["fit3_corpus_described"]["headroom_per_family"]["rfc_txt"]["new_dropped_run_with_0024"] > 0,
        "the sealed pool counts are the manifests'; 0024's candidates recur unchanged; the two run rules are sealed and the same-family rule removed RFC chunks")
    for flag, msg in (("--check", "IDENTICAL"), ("--disjoint", "shares nothing"), ("--verify-pins", "byte-identical")):
        rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/corpus_realfit3.py", flag], capture_output=True, text=True, cwd=REPO)
        chk(rc.returncode == 0 and msg in rc.stdout, f"corpus_realfit3.py {flag}: {msg}")
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/corpus_realfit2.py", "--check"], capture_output=True, text=True, cwd=REPO)
    chk(rc.returncode == 0 and "IDENTICAL" in rc.stdout, "0024's corpus on disk is still identical to its banked manifest (corpus_realfit2.py --check)")
    rs = P["reference_slopes_informational"]
    chk(rs["second_decade_slope_per_doubling_0024"] == {r: v24["curves"][r]["slope_per_doubling_second_decade"] for r in r25.ROLES}
        and rs["lead_at_rung_7_0024"] == v24["lead_at_top"]["r7_model_minus_logistic"] and rs["rung_to_rung_gains_0024"] == v24["flags"]["rung_to_rung_gains"]
        and rs["paired_half_widths_from_0024s_vectors"]["r7_model_minus_r7_logistic"]["ci95"] == v24["lead_at_top"]["r7_model_minus_logistic"]["ci95"]
        and rs["n_scored_real_chunks"] == 1488 and rs["rung_8_model_reading_below_which_the_eight_rung_slope_fails"] < 0.13,
        "the sealed reference numbers are 0024's banked ones, and the paired interval recomputed from 0024's vectors is 0024's banked lead interval")
    _prose = json.dumps({k: v for k, v in S.items() if k not in ("curve", "sealed_partition", "eval_chunk_layout", "ext_chunk_layout", "sealed_hashes", "artifact_identity_at_writing")})
    chk("seven of the eight points" in S["what_this_is_and_is_not"] and "FOURTH_DOUBLING" in S["expected_outcome_stated_in_advance"] and "NO_SEPARATION" in S["expected_outcome_stated_in_advance"]
        and "iteration cap" in P["bar"]["gain_rule"] and "never 'flat'" in P["bar"]["gain_rule"] and "1.8016 decades, short of 0003's two-decade scope rule" in " ".join(pr["stop_rules"])
        and "one-corpus, one-seed" in " ".join(pr["stop_rules"]) and "fit-side variance" in S["what_this_does_not_cover"] and "twelfth" in S["sealed_set_disclosure"],
        "the sealed text carries the review's clauses: no slope as a clause, the four-way reading, the cap rule, the forward-pointer locations, the scope-rule caveat, the disclosure")
    chk(P["order"][1:7] == [f"r7_{r}" for r in r25.FLOOR_ROLES + r25.ROLES] and P["order"][7:10] == [f"r4_{r}" for r in r25.ROLES]
        and P["order"][-6:] == [f"s4_{r}" for r in r25.ROLES] + [f"s8_{r}" for r in r25.ROLES] and P["order"] == rc_.sealed_order(8),
        "rung 7 is fitted first after the null, every reproduction before rung 8, and the shift arms are last (the runner's sealed_order(8))")
    chk(str(RP["rungs"][-1]["n_chunks"]) in S["one_line"] and str(RP["rungs"][-1]["n_rows"]) in S["one_line"] and str(RP["doublings_spanned"]) in S["one_line"],
        "the one-line scope states the rung sizes and the span")
    # the correction and the compliance filings the sealed file refers to exist
    corr = open(f"{REPO}/CORRECTIONS.md", encoding="utf-8").read(); man_c = json.load(open(f"{REPO}/docs/compliance/sources/MANIFEST.json", encoding="utf-8"))
    chk("## 2026-09-23" in corr and "below 1000" in corr and os.path.exists(f"{REPO}/docs/compliance/EXT_SOURCES3.md")
        and any(e.get("sha256") == pins3["rfc_source"]["sample"]["index_sha256"] for e in man_c["sources"])
        and all(os.path.exists(f"{REPO}/docs/compliance/sources/{n}") for n in ("transformers-5.17.0_LICENSE.txt", "homeassistant-2026.9.3_LICENSE.md.txt", "salt-3008.2_LICENSE.txt")),
        "the RFC-frame correction is filed, the sources document exists, the index is hashed in the compliance manifest and the licence texts are committed")

    # 5. the reader's expectations are keys the runner writes; the fixture is current with the runner in the tree
    fx = json.load(open(f"{REPO}/tests/fixtures/realcurve3_runner_shape.json", encoding="utf-8"))
    shape = fx["artifact"]
    for nm, sealed, blk in (("FIT", r25.FIT, "fit_corpus"), ("FIT2", r25.FIT2, "fit2_corpus"), ("FIT3", r25.FIT3, "fit3_corpus"), ("EXT", r25.EXT, "ext_corpus"),
                            ("PARTITION", r25.PARTITION, "partition"), ("CORPUS", r25.CORPUS, "corpus")):
        chk(set(sealed) <= set(shape[blk]), f"every key the reader's {nm} compares is one the runner writes"
            + (f" (missing {sorted(set(sealed) - set(shape[blk]))})" if not set(sealed) <= set(shape[blk]) else ""))
    chk(set(P) == set(shape["curve_spec"]["protocol"]), "the fixture's protocol has this preregistration's key set (the fixture is current)")
    chk(set(shape["curve_spec"]) == {"protocol", "recipes"} and set(shape["curve_spec"]["recipes"]) == set(RE), "the fixture's curve spec is exactly {protocol, recipes} over the six roles")
    chk(set(shape["fits"]) == set(P["order"]) and len(shape["fits"]) == 37, "the fixture's roles are exactly the sealed order (37)")
    chk({"shift_arm", "shift_arm_0025", "floors", "fourth_doubling", "reproduction_bootstrap_0024", "seed_stability"} <= set(shape)
        and set(shape["partition"]["shift_arm_0025"]) >= set(P["shift_arm_0025_hashes"]) and set(shape["partition"]["rungs"][7]) >= set(P["rung_hashes"][7]),
        "the runner writes the shift arms, the floors, the gain, the reproduced intervals and the stability blocks the reader compares")
    chk(set(shape["bar"]) == {"gain_per_doubling", "gain_rule", "lead_rule", "n_boot", "bootstrap_seed"}
        and set(shape["slope_bootstrap"]) >= {"model", "logistic", "depth3_tree", "model_minus_logistic", "model_minus_depth3_tree", "both_decades", "unit"}
        and set(shape["lead_at_top"]) >= {"r8_model_minus_logistic", "r7_model_minus_logistic", "r4_model_minus_logistic", "s8_minus_s4_model", "unit", "verdict_pair"}
        and set(shape["fourth_doubling"]) >= {"model", "logistic", "depth3_tree", "verdict_role", "bar", "unit"},
        "the fixture's bar, bootstrap, lead and gain blocks carry the keys the reader compares")
    chk(set(shape["curves"]["model"]) >= {"slope_per_doubling_second_decade", "slope_per_doubling_both_decades", "slope_per_doubling_second_decade_0024",
                                          "fourth_doubling_gain", "fourth_doubling_gain_with_rung7_at_reference", "per_family_fourth_doubling_gain"},
        "the fixture's curve blocks carry the gains and slopes the reader recomputes")
    _int = lambda v: isinstance(v, int) and not isinstance(v, bool)  # noqa: E731
    _bad = []
    for _nm, _rec in shape["fits"].items():
        _role = "model" if _nm == "null" else _nm.split("_", 1)[1]
        _fam = RE[_role]["family"]; _inf = _rec.get("fit_info")
        if _rec.get("id") != RE[_role]["id"]:
            _bad.append(f"{_nm}: id {_rec.get('id')!r}")
        if not isinstance(_inf, dict):
            _bad.append(f"{_nm}: fit_info {_inf!r}")
        elif _fam in ("hgb", "logistic") and not _int(_inf.get("n_iter")):
            _bad.append(f"{_nm} ({_fam}): no integer n_iter")
        elif _fam == "tree" and not (_int(_inf.get("depth")) and _int(_inf.get("n_leaves"))):
            _bad.append(f"{_nm} ({_fam}): no integer depth/n_leaves")
        if sorted(_rec["per_family"]) != sorted(r25.FAMILIES + ["ext:" + f for f in r25.EXT_FAMILIES]):
            _bad.append(f"{_nm}: per_family keys")
        if not set(r25.ENV) <= set(_rec.get("environment") or {}):
            _bad.append(f"{_nm}: environment lacks {sorted(set(r25.ENV) - set(_rec.get('environment') or {}))}")
        _head = _nm.split("_", 1)[0]
        _want = 8 if _nm == "null" else (_head if _head in ("s4", "s8") else int(_head[1:]))
        _stage = "null" if _nm == "null" else ("shift" if _want in ("s4", "s8") else "floor" if _role.startswith("floor_") else ("curve" if _want > 7 else "reproduction"))
        if _rec.get("rung") != _want or _rec.get("role") != ("null" if _nm == "null" else _role) or _rec.get("stage") != _stage:
            _bad.append(f"{_nm}: rung/role/stage")
    chk(not _bad, "the reader's per-record requirements hold against the runner's own banked values" + (f" ({'; '.join(_bad[:3])})" if _bad else ""))
    chk("ledger" in shape and any(e.get("event") == "rung_bound" and "rung_sorted_sha256" in e for e in shape["ledger"])
        and [e["name"] for e in shape["ledger"] if e.get("event") == "completed"] == [f"run_{n}" for n in P["order"]],
        "the runner banks a ledger with rung_bound events and completes the roles in the sealed order")
    _src = inspect.getsource(rc_)
    _written = set(re.findall(r'partition\["([a-z0-9_]+)"\]', _src)) | set(re.findall(r'"([a-z0-9_]+)": (?:int|bool|_sha|list|\[|\{)', _src[_src.index("partition = {"):_src.index("t_id = time.perf_counter()")]))
    _rp_src = inspect.getsource(rc_.rung_partition3)
    _written |= set(re.findall(r'"([a-z0-9_]+)":', _rp_src[_rp_src.index("keys.update({"):]))
    chk(_written <= set(shape["partition"]), "every partition key the runner's source writes is in the captured fixture (the fixture is current)"
        + (f" (missing {sorted(_written - set(shape['partition']))})" if not _written <= set(shape["partition"]) else ""))
    import ast as _ast

    def _body_dump(fn):
        node = _ast.parse(inspect.getsource(fn)).body[0]
        body = node.body[1:] if (node.body and isinstance(node.body[0], _ast.Expr) and isinstance(getattr(node.body[0], "value", None), _ast.Constant)
                                 and isinstance(node.body[0].value.value, str)) else node.body
        return [_ast.dump(x) for x in body]
    chk(_body_dump(rc1_.slope_bootstrap) == _body_dump(r25.slope_bootstrap) and _body_dump(rc1_.ols_slope) == _body_dump(r25.ols_slope)
        and _body_dump(rc2_.paired_lead_bootstrap) == _body_dump(r25.paired_lead_bootstrap),
        "the reader's slope_bootstrap, ols_slope and paired_lead_bootstrap are the runners', statement for statement (AST equality below the docstring)")

    # 6. nothing of this run exists yet, and a real run refuses to start on an unfrozen preregistration
    for f in ("realcurve3_4096.json", "realcurve3_4096_scores.json", "realcurve3_4096_verdict.json", "realcurve3_4096_not_run.json"):
        chk(not os.path.exists(f"{REPO}/artifacts/pivot/{f}"), f"artifacts/pivot/{f} does not exist yet")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realcurve3_4096_ckpt"), "no checkpoint directory exists yet")
    chain = [json.loads(l) for l in open(f"{REPO}/prereg/chain.jsonl", encoding="utf-8") if l.strip()]
    chk(chain[-1]["id"] == "0024" and len(chain) == 24, "0024 is the chain head (24 entries)")
    chk(pr["reader"] == "tools/readers/realcurve3_4096_verdict.py" and os.path.exists(reader_path), "the reader exists at the sealed path")
    sm = pr["smoke"]
    chk(all(sm[k]["arrays"]["X"]["sha256"] != P[k]["arrays"]["X"]["sha256"] and sm[k]["npz"].startswith("(scratchpad)") for k in ("ext_corpus", "fit_corpus", "fit2_corpus", "fit3_corpus")),
        "the smoke block names scratchpad corpora whose hashes are not the sealed ones")
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/run_realcurve3.py", "--stage", "run"], capture_output=True, text=True, cwd=REPO,
                        env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    chk(rc.returncode == 3 and "frozen preregistration" in rc.stderr, "a real run refuses to start on an unfrozen preregistration (exit 3)")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realcurve3_4096_ckpt"), "the refused launch created nothing")

    # 7. the banked mutation report agrees with the coverage map and carries this gate
    rep = json.load(open(f"{REPO}/artifacts/verification/mutation_report.json", encoding="utf-8"))
    cov = json.load(open(f"{REPO}/artifacts/verification/coverage.json", encoding="utf-8"))
    claim = next(c for c in cov["claims"] if c["id"] == "mutations-detected")
    chk(rep["detected"] == rep["total_mutations"] == claim["value"] and rep["survived"] == 0,
        f"the banked mutation report ({rep['detected']}/{rep['total_mutations']}) agrees with the coverage claim ({claim['value']})")
    g = rep["by_gate"].get("realcurve3_4096", {})
    chk(g.get("total", 0) >= 140 and g.get("detected") == g.get("total"), f"the report carries the realcurve3_4096 gate ({g})")

    result = {"schema": "raise-v1/prefreeze_0025/1", "preregistration": f"{pr['id']}-{pr['slug']}", "problems": bad,
              "passed": bad == 0, "reader_sha256_at_check": hashlib.sha256(reader.encode()).hexdigest(),
              "prereg_sha256_at_check": hashlib.sha256(open(f"{REPO}/prereg/0025-realcurve3-4096.json", "rb").read()).hexdigest(),
              "rungs": [{k: r[k] for k in ("rung", "decade", "n_chunks", "n_rows")} for r in RP["rungs"]],
              "doublings_spanned": RP["doublings_spanned"], "doublings_spanned_second_decade": RP["doublings_spanned_second_decade"], "decades_spanned": round(RP["doublings_spanned"] * 0.30102999566, 4)}
    os.makedirs(f"{REPO}/artifacts/verification", exist_ok=True)
    with open(f"{REPO}/artifacts/verification/prefreeze_0025.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"PRE-FREEZE 0025: {'PASS' if bad == 0 else 'FAIL'} ({bad} problem(s))")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
