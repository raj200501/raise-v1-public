#!/usr/bin/env python3
"""Pre-freeze check for preregistration 0024 (run before `tools/prereg.py freeze`; committed with the freeze, result
banked in artifacts/verification/prefreeze_0024.json). Exit 1 on any mismatch, 2 once the preregistration is frozen.

What it checks, and why each one exists:
 1. The reader is exactly what the generator produces from the preregistration and the template - no hand edit.
 2. Every sealed literal in the reader equals the preregistration's (protocol and curve hashes, recipes, references of
    both decades, tolerances, the null-label hash, the partition and the seven rungs, the three corpora, the order, the
    bar with its lead rule, the bootstrap).
 3. The corpora on disk hash to the sealed arrays and their blocks are REBUILT BY CALLING the runner's corpus_block();
    the fit block and the seven rungs are REBUILT BY CALLING the runner's rung_partition2() on the two fit corpora and
    must equal the sealed constants hash for hash; the sealed evaluation set, the pool and the null-label array are
    RECOMPUTED from the builder cache and the corpora with the runner's own split and generator (OPERATING_RULES 4).
 4. Rungs 1..4 are 0023's rungs hash for hash; the references trace to 0021's and 0023's banked artifacts; the recipes are
    0023's; the second-decade corpus is disjoint by construction and its manifest is the sealed one; the reference numbers
    quoted in the prose are banked numbers.
 5. Every key the reader compares is a key the runner writes (the captured fixture), the reader's per-record
    requirements hold against the runner's own banked records, and the fixture is current with the runner in the tree.
 6. Nothing of this run exists yet: no artifact, scores, verdict, NOT RUN file or checkpoints; the preregistration is
    unfrozen and 0023 is the chain head; the smoke block names scratchpad corpora; a real run refuses to start.
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
SP = os.environ.get("PREREG_0024_SCRATCH", tempfile.mkdtemp(prefix="prefreeze_0024_"))
os.makedirs(SP, exist_ok=True)
bad = 0


def chk(cond, msg):
    global bad
    print(("ok   " if cond else "BAD  ") + msg)
    if not cond:
        bad += 1


def main() -> int:
    global bad
    pr = json.load(open(f"{REPO}/prereg/0024-realcurve2-4096.json", encoding="utf-8"))
    if pr.get("frozen"):
        print(f"PRE-FREEZE 0024: the preregistration is frozen ({pr.get('frozen_utc')}); this check runs before a freeze "
              f"only. The result it banked then is artifacts/verification/prefreeze_0024.json.", file=sys.stderr)
        return 2
    S = pr["scope"]; CU = S["curve"]; P = CU["protocol"]; RE = CU["recipes"]; sp = S["sealed_partition"]
    canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
    sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

    # 1. the reader is the generated file
    gen = os.environ.get("PREREG_0024_GENERATOR")
    reader_path = f"{REPO}/tools/readers/realcurve2_4096_verdict.py"
    reader = open(reader_path, encoding="utf-8").read()
    if gen and os.path.exists(gen):
        tmp = os.path.join(SP, "regenerated_reader.py")
        rc = subprocess.run([sys.executable, gen, f"{REPO}/prereg/0024-realcurve2-4096.json", tmp], capture_output=True, text=True)
        chk(rc.returncode == 0 and open(tmp, encoding="utf-8").read() == reader,
            "the reader is exactly what the generator produces from this preregistration")
    else:
        chk(False, "PREREG_0024_GENERATOR is not set to the generator script; cannot prove the reader was generated")

    # 2. the reader's sealed literals are the preregistration's
    import importlib.util
    spec = importlib.util.spec_from_file_location("r24", reader_path)
    r24 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r24)
    chk(r24.PREREG == f"{pr['id']}-{pr['slug']}", "the reader is frozen for this preregistration")
    chk(set(CU) == {"protocol", "recipes"}, "the sealed curve spec is exactly {protocol, recipes}")
    chk(r24.PROTOCOL == P and r24.PROTOCOL_SHA256 == sha(P) == S["sealed_hashes"]["protocol_sha256"],
        "the reader's PROTOCOL is the sealed protocol and hashes to the sealed hash")
    chk(r24.CURVE_SHA256 == sha(CU) == S["sealed_hashes"]["curve_sha256"] and r24.RECIPES == RE,
        "the reader's curve hash and recipes are the sealed ones")
    chk(r24.REFERENCE == P["reference_top1"] and r24.REFERENCE_FIRST == P["reference_first_decade"]
        and r24.REPRO_TOLERANCE == P["reproduction_tolerance"] and r24.NULL_TOLERANCE == P["null_tolerance"]
        and r24.NULL_SHA_EXPECTED == P["null_y_shuffled_sha256_expected"]
        and r24.N_REAL == P["n_ext_real_rows"] and r24.N_EXT == P["ext_corpus"]["n_rows"],
        "the reader's references of both decades, tolerances, null-label hash and row counts are the sealed ones")
    chk(r24.BAR_SLOPE == P["bar"]["slope_per_doubling"] == 0.005 and r24.BOOT_LB == P["bar"]["bootstrap_lower_bound_gt"] == 0.0
        and r24.LEAD_RULE == P["bar"]["lead_rule"] and r24.N_BOOT == P["bootstrap"]["n_boot"] == 2000
        and r24.BOOT_SEED == P["bootstrap"]["seed"] == P["seed2"] and r24.SEED2 == P["seed2"] == sp["seed2"]
        and r24.REF_FIRST_DECADE_SLOPE == P["reference_slopes_informational"]["first_decade_slope_per_doubling_0023"]["model"],
        "the reader's bar (with its lead rule), bootstrap, seed2 and 0023 reference-slope literals are the sealed ones")
    chk(list(r24.ORDER) == P["order"] and list(r24.ROLES) == P["roles"] == ["depth3_tree", "logistic", "model"]
        and list(r24.DENOMINATORS) == P["denominators"] == [8, 4, 2, 1] and r24.N_FIRST == P["n_first_decade_rungs"] == 4
        and r24.DOUBLINGS == P["doublings"] == 3 and r24.N_RUNGS == 7 and len(r24.ORDER) == 25 and r24.SHIFT == P["shift"] == "s4"
        and r24.LOG2X == [r["log2_chunks"] for r in sp["rungs"]] and r24.LOG2X_SECOND == r24.LOG2X[3:],
        "the reader's order (25 roles), roles, denominators, doublings, rung count, shift arm name and log2 abscissae are the sealed ones")
    chk(r24.PARTITION["shift_arm"] == P["shift_arm_hashes"] == sp["shift_arm"], "the reader's shift arm is the sealed one")
    chk(r24.ENV == P["environment"] and r24.ENV_FULL == dict(P["environment"], threads=P["threads"], nice=P["nice"]),
        "the reader's environment literals are the sealed ones")
    chk(r24.EXT == P["ext_corpus"] and r24.FIT == P["fit_corpus"] and r24.FIT2 == P["fit2_corpus"], "the reader's three corpus blocks are the sealed ones")
    for k, v in P["fit_block_hashes"].items():
        chk(r24.PARTITION.get(k) == v, f"the reader's PARTITION.{k} is the sealed fit-block hash")
    chk(r24.PARTITION["rungs"] == P["rung_hashes"] == sp["rungs"] and len(sp["rungs"]) == 7, "the reader's PARTITION.rungs is the sealed seven-rung table")
    chk(r24.PARTITION["pool_chunks_with_rows_per_family"] == P["pool_chunks_with_rows_per_family"] == sp["pool_chunks_with_rows_per_family"]
        and r24.PARTITION["pool_short"] == {}, "the reader's pool counts are the sealed ones and pool_short is empty")
    chk(r24.EVAL_CHUNK_IDS == S["eval_chunk_layout"]["chunk_ids"] and r24.EVAL_ROWS_PER_CHUNK == S["eval_chunk_layout"]["rows_per_chunk"]
        and r24.EXT_CHUNK_IDS == S["ext_chunk_layout"]["chunk_ids_with_rows"] and r24.EXT_ROWS_PER_CHUNK == S["ext_chunk_layout"]["rows_per_chunk"],
        "the reader's chunk layouts are the sealed ones")
    chk(r24.MAX_ITER == {r: (RE[r].get("params", {}).get("max_iter") or 0) for r in r24.ROLES}, "the reader's iteration caps are the recipes'")
    paths = [x["json_path"] for x in pr["readings"]]
    chk(all(p.startswith("$.") and p[2:].split(".")[0] in r24.RESULT_KEYS for p in paths),
        "every sealed reading's json_path names a key the reader writes on every path")

    # 3. the corpora, the fit block and the rungs, rebuilt by calling the runner's own code on the data
    from run_realfit import corpus_block, _array_sha
    import run_realcurve as rc1_
    import run_realcurve2 as rc_

    def _runner_block(rel, labels):
        d = np.load(f"{REPO}/{rel}", allow_pickle=False)
        names = [str(x) for x in d["families"]]; fam = np.array(names)[d["fam"]]
        h = {n: dict(zip(("sha256", "shape", "dtype"), _array_sha(f"{REPO}/{rel}", n))) for n in ("X", "y", "g", "fam")}
        src = set(str(v) for v in d["meta_src_sha256"])
        return corpus_block(rel, h, d["y"], d["g"], fam, names, labels=labels), d, names, fam, src
    rb_fit, dfit, fit_names, fam_r, fit_src = _runner_block("data/pivot/realfit_c4096.npz", True)
    rb_fit2, dfit2, fit2_names, fam_2, fit2_src = _runner_block("data/pivot/realfit2_c4096.npz", True)
    rb_ext, _, _, _, ext_src = _runner_block("data/pivot/ext_c4096.npz", False)
    chk(P["fit_corpus"] == rb_fit and P["ext_corpus"] == rb_ext and P["fit2_corpus"] == rb_fit2,
        "the sealed corpus blocks are what the runner banks from the three npz on disk")
    chk(not (fit2_src & fit_src) and not (fit2_src & ext_src) and len(fit2_src) == sp["source_chunks"]["n_fit2_source_chunks"] == rb_fit2["n_chunks"] + len(
        json.load(open(f"{REPO}/artifacts/pivot/realfit2_corpus_manifest.json"))["chunks_without_rows"]),
        "the second-decade corpus shares no source-chunk hash with 0021's block or the scored corpus, and its distinct hash count is the sealed one")
    fit_order, rows_all, RP = rc_.rung_partition2(dfit["y"], dfit["g"], fam_r, fit_names, P["seed"], P["denominators"],
                                                   dfit2["y"], dfit2["g"], fam_2, P["seed2"], P["doublings"])
    chk(RP["shift_arm"] == P["shift_arm_hashes"] and RP["shift_arm"]["same_chunks_as_rung_5s_new_chunks"] and RP["shift_arm"]["same_plaintext_count_as_rung_4"]
        and len(rows_all) == RP["n_rungs"] + 1 and len(rows_all[-1]) == RP["shift_arm"]["n_rows"] and RP["shift_arm"]["n_chunks"] == RP["rungs"][3]["n_chunks"],
        "the sealed shift arm is what rung_partition2() computes: rung 5's new chunks alone, rung 4's plaintext count, its own row set")
    chk(all(RP[k] == v for k, v in P["fit_block_hashes"].items()), "the sealed fit-block hashes are what the runner's rung_partition2() computes")
    chk(RP["rungs"] == P["rung_hashes"] == sp["rungs"], "the sealed rung table is what the runner's rung_partition2() computes from the two corpora, hash for hash")
    chk(RP["rungs_nested"] and RP["rung_chunks_strictly_increasing"] and RP["rung4_is_fit_block"] and RP["second_decade_exact_doublings"]
        and RP["pool_short"] == {} and RP["doublings_spanned"] == sp["doublings_spanned"]
        and RP["doublings_spanned_second_decade"] == sp["doublings_spanned_second_decade"] == 3.0
        and RP["second_decade_rule"] == P["second_decade_rule"] == sp["second_decade_rule"] and RP["rung_rule"] == P["rung_rule"],
        "the rungs are nested, strictly increasing, exact doublings on 0021's block, the pool covers them, and the sealed rules and spans are the runner's")
    chk(all(r24.PARTITION[k] == RP[k] for k in RP if k in r24.PARTITION), "every fit-block, rung and pool key the reader seals equals the runner's recomputation")
    base = RP["fit_chunks_per_family"]
    chk(all(RP["rungs"][3 + d]["chunks_per_family"][f] == base[f] * 2 ** d for d in range(1, 4) for f in fit_names)
        and all(RP["rungs"][3 + d]["n_rows"] == len(rows_all[3 + d]) for d in range(1, 4)),
        "every second-decade rung holds exactly 2^d times rung 4's plaintexts of every family, and its row count is its row set's")
    chk(all(sum(r["chunks_per_family"].values()) == r["n_chunks"] and sum(r["rows_per_family"].values()) == r["n_rows"] for r in RP["rungs"]),
        "every rung's family counts sum to its totals")
    # rungs 1..4 are 0023's, hash for hash, and the fit block is 0021's
    p23 = json.load(open(f"{REPO}/prereg/0023-realcurve-4096.json", encoding="utf-8"))
    a23 = json.load(open(f"{REPO}/artifacts/pivot/realcurve_4096.json", encoding="utf-8"))
    v23 = json.load(open(f"{REPO}/artifacts/pivot/realcurve_4096_verdict.json", encoding="utf-8"))
    keys1 = list(p23["scope"]["curve"]["protocol"]["rung_hashes"][0])
    chk([{k: r[k] for k in keys1} for r in RP["rungs"][:4]] == p23["scope"]["curve"]["protocol"]["rung_hashes"]
        and [{k: r[k] for k in keys1} for r in a23["partition"]["rungs"]] == p23["scope"]["curve"]["protocol"]["rung_hashes"],
        "rungs 1..4 are 0023's sealed and banked rungs, hash for hash")
    a21 = json.load(open(f"{REPO}/artifacts/pivot/realfit_4096_rerun.json", encoding="utf-8"))
    p21 = json.load(open(f"{REPO}/prereg/0021-realfit-4096-rerun.json", encoding="utf-8"))
    chk(RP["fit_idx_sha256"] == a21["partition"]["fit_idx_sha256"] == p21["scope"]["sealed_partition"]["fit_block"]["idx_sha256"]
        and RP["fit_sorted_sha256"] == a21["partition"]["fit_sorted_sha256"] and RP["rungs"][3]["idx_sha256"] == RP["fit_idx_sha256"],
        "rung 4 is 0021's fit block, row for row (its banked and sealed hashes)")
    chk(sp["eval"] == p23["scope"]["sealed_partition"]["eval"] and sp["pool"] == p23["scope"]["sealed_partition"]["pool"]
        and sp["fit_block"] == p23["scope"]["sealed_partition"]["fit_block"] and P["pool_idx_sha256"] == a21["partition"]["pool_idx_sha256"],
        "the evaluation set, the pool and the fit block are 0023's sealed ones (0021's before it)")
    import io as _io, zipfile as _zf
    from run_recipe_search import grouped_split, _sha as _rsha
    with _zf.ZipFile(f"{REPO}/data/pivot/full_c4096.npz") as zf:
        y_b = np.load(_io.BytesIO(zf.read("y.npy"))); g_b = np.load(_io.BytesIO(zf.read("g.npy")))
    ev, tr, rng = grouped_split(y_b, g_b, P["seed"], P["eval_frac"], P["top_rung"])
    chk(_rsha(ev) == r24.PARTITION["eval_idx_sha256"] and _rsha(np.asarray(g_b[ev])) == r24.PARTITION["eval_g_sha256"]
        and _rsha(np.asarray(y_b[ev])) == r24.PARTITION["eval_y_sha256"] and _rsha(tr) == P["pool_idx_sha256"]
        and _rsha(np.sort(tr).astype(np.int64)) == r24.PARTITION["pool_sorted_sha256"] and int(len(ev)) == r24.PARTITION["n_eval_rows"]
        and int(len(tr)) == r24.PARTITION["n_pool_rows"],
        "the sealed evaluation set and pool hashes are what the runner's grouped_split() computes from the builder cache on disk")
    y_all = np.concatenate([np.asarray(dfit["y"]), np.asarray(dfit2["y"])]); top_rows = rows_all[RP["n_rungs"] - 1]
    sub = y_all[top_rows].copy(); np.random.default_rng([P["seed2"], rc_.NULL_STREAM_WORD]).shuffle(sub)
    chk(_rsha(sub) == P["null_y_shuffled_sha256_expected"] and not np.array_equal(sub, y_all[top_rows])
        and np.array_equal(np.sort(sub), np.sort(y_all[top_rows])),
        "the sealed null-label hash is what the sealed stream produces on the top rung's labels, a permutation of them")
    _ci = lambda d: {k: v for k, v in d.items() if k != "X_note"}  # noqa: E731
    chk(_ci(P["cache_identity"]) == _ci(p21["scope"]["protocol"]["cache_identity"]) and r24.CORPUS["cache_X_sha256"] == P["cache_identity"]["X_sha256"]
        and r24.CORPUS == {k: a21["corpus"][k] for k in r24.CORPUS}, "the builder cache identity is 0021's, X hash included, and the reader's CORPUS is 0021's banked block")
    chk(S["eval_chunk_layout"] == p23["scope"]["eval_chunk_layout"] and S["ext_chunk_layout"] == p23["scope"]["ext_chunk_layout"],
        "the chunk layouts are 0023's sealed ones")

    # 4. references, recipes, the corpus manifest and the quoted numbers trace to banked artifacts and sealed files
    chk(P["reference_top1"] == p23["scope"]["curve"]["protocol"]["reference_top1"]
        == {"model": a21["ext_real_top1"]["real_model"], "logistic": a21["ext_real_top1"]["real_logistic"], "depth3_tree": a21["ext_real_top1"]["floor_tree3"]},
        "the rung-4 references are 0021's banked readings, as 0023 sealed them")
    chk(P["reference_first_decade"] == {role: [p["ext_real_top1"] for p in v23["curves"][role]["rungs"]] for role in r24.ROLES}
        and all(P["reference_first_decade"][r][-1] == P["reference_top1"][r] for r in r24.ROLES) and v23["verdict"] == "REAL_CURVE_RISES"
        and a23["reproduction_drift"] == {"depth3_tree": 0.0, "logistic": 0.0, "model": 0.0},
        "the first-decade references are 0023's banked rung readings per role, ending at 0021's; 0023 reproduced 0021 with drift 0.0")
    chk(RE == p23["scope"]["curve"]["recipes"] and p23.get("frozen") is True and P["recipe_ids"] == {"model": "M4", "logistic": "L3", "depth3_tree": "D1"},
        "the recipes are 0023's sealed recipes (M4, L3, D1), verbatim")
    man2 = json.load(open(f"{REPO}/artifacts/pivot/realfit2_corpus_manifest.json", encoding="utf-8"))
    pins2 = json.load(open(f"{REPO}/tools/pivot/ext_source_pins2.json", encoding="utf-8"))
    chk(P["fit2_corpus"]["arrays"] == man2["arrays"] and man2["smoke"] is False and man2["seed"] == P["seed2"] == pins2["seed"]
        and man2["doublings"] == P["doublings"] == pins2["doublings"]
        and P["fit2_corpus_described"]["manifest_sha256"] == hashlib.sha256(open(f"{REPO}/artifacts/pivot/realfit2_corpus_manifest.json", "rb").read()).hexdigest()
        and S["artifact_identity_at_writing"]["ext_source_pins2_sha256"] == hashlib.sha256(open(f"{REPO}/tools/pivot/ext_source_pins2.json", "rb").read()).hexdigest(),
        "the second-decade corpus block is the banked manifest's, built with the sealed seed and doublings from the pinned sources")
    chk(P["pool_chunks_with_rows_per_family"] == {f: man2["per_family"][f]["n_chunks_with_rows"] for f in fit_names}
        and all(man2["per_family"][f]["n_dropped_byte_identical_to_0018"] == 0 for f in fit_names)
        and man2["exclusion"]["n_distinct_chunk_hashes_of_0018_pinned_blobs"] == 2534 and man2["exclusion"]["n_whole_chunks_of_0018_pinned_blobs"] == 2537
        and man2["exclusion"]["run_overlap"]["run_windows"] * man2["exclusion"]["run_overlap"]["window"] == 1024
        and P["fit2_corpus_described"]["dropped_sharing_a_run_with_0018"] == {f: man2["per_family"][f]["n_dropped_sharing_a_run_with_0018"] for f in fit_names}
        and sum(P["fit2_corpus_described"]["dropped_sharing_a_run_with_0018"].values()) > 0,
        "the sealed pool counts are the manifest's chunks with rows; nothing was byte-identical to 0018's pinned chunks; the exclusion set is the "
        "2534 distinct hashes of the 2537 whole chunks of those blobs plus the 1024-byte run rule, whose per-family drops are sealed and non-zero")
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/corpus_realfit2.py", "--check"], capture_output=True, text=True, cwd=REPO)
    chk(rc.returncode == 0 and "IDENTICAL" in rc.stdout, "the second-decade corpus on disk is identical to its banked manifest (corpus_realfit2.py --check)")
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/corpus_realfit2.py", "--disjoint"], capture_output=True, text=True, cwd=REPO)
    chk(rc.returncode == 0 and "shares nothing" in rc.stdout, "the second-decade corpus shares nothing with anything scored or fitted before (corpus_realfit2.py --disjoint)")
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/corpus_realfit2.py", "--verify-pins"], capture_output=True, text=True, cwd=REPO)
    chk(rc.returncode == 0 and "byte-identical" in rc.stdout, "every pinned second-decade source file is present and byte-identical")
    rs = P["reference_slopes_informational"]
    chk(rs["first_decade_slope_per_doubling_0023"] == {r: v23["curves"][r]["slope_per_doubling"] for r in r24.ROLES}
        and rs["first_decade_model_minus_logistic_0023"] == v23["flags"]["slope_model_minus_logistic"]
        and rs["top_rung_if_0023s_lines_continued"] == {r: round(P["reference_top1"][r] + rs["first_decade_slope_per_doubling_0023"][r] * 3.0, 4) for r in r24.ROLES},
        "the sealed reference slopes and the informational extrapolation are 0023's banked numbers and arithmetic on them")
    _prose = json.dumps({k: v for k, v in S.items() if k not in ("curve", "sealed_partition", "eval_chunk_layout", "ext_chunk_layout", "sealed_hashes", "artifact_identity_at_writing")})
    chk(all(str(rs["first_decade_slope_per_doubling_0023"][r]) in S["why_this_preregistration_exists"] for r in ("model", "logistic"))
        and all(str(v) not in _prose for v in rs["top_rung_if_0023s_lines_continued"].values()),
        "the prose quotes 0023's banked slopes and NOT the sealed extrapolation (informational only; review finding)")
    chk("iteration cap" in P["bar"]["lead_rule"] and "lowered the model's reading" in pr["stop_rules"][0] and "0.9031" in " ".join(pr["stop_rules"])
        and "CONFOUNDS" in S["what_this_is_and_is_not"] and "shift arm" in S["what_this_is_and_is_not"],
        "the sealed text carries the review's clauses: the cap clause in the lead rule, the falling-decade sentence, the decade statement, the confound")
    chk(P["order"][1:13] == [f"r{k}_{r}" for k in (4, 1, 2, 3) for r in r24.ROLES] and P["order"][-3:] == [f"s4_{r}" for r in r24.ROLES],
        "every reproduction is fitted before any new plaintext, and the shift arm is last")
    chk("SECOND_DECADE_RISES" in S["expected_outcome_stated_in_advance"] and "more likely than not" in S["expected_outcome_stated_in_advance"]
        and "LINEAR_LEADS" in S["expected_outcome_stated_in_advance"], "the expected outcome is stated in advance for both questions")
    chk(P["order"] == rc_.sealed_order(7) and len(P["order"]) == 25, "the sealed order is the runner's sealed_order(7), 25 roles")
    chk(str(RP["rungs"][0]["n_chunks"]) in S["one_line"] and str(RP["rungs"][-1]["n_rows"]) in S["one_line"]
        and str(RP["doublings_spanned"]) in S["one_line"], "the one-line scope states the rung sizes and the span")

    # 5. the reader's expectations are keys the runner writes; the fixture is current with the runner in the tree
    fx = json.load(open(f"{REPO}/tests/fixtures/realcurve2_runner_shape.json", encoding="utf-8"))
    shape = fx["artifact"]
    for nm, sealed, blk in (("FIT", r24.FIT, "fit_corpus"), ("FIT2", r24.FIT2, "fit2_corpus"), ("EXT", r24.EXT, "ext_corpus"),
                            ("PARTITION", r24.PARTITION, "partition"), ("CORPUS", r24.CORPUS, "corpus")):
        chk(set(sealed) <= set(shape[blk]), f"every key the reader's {nm} compares is one the runner writes"
            + (f" (missing {sorted(set(sealed) - set(shape[blk]))})" if not set(sealed) <= set(shape[blk]) else ""))
    chk(set(P) == set(shape["curve_spec"]["protocol"]), "the fixture's protocol has this preregistration's key set (the fixture is current)")
    chk(set(shape["curve_spec"]) == {"protocol", "recipes"} and set(shape["curve_spec"]["recipes"]) == set(RE),
        "the fixture's curve spec is exactly {protocol, recipes} over the three roles")
    chk(set(shape["fits"]) == set(P["order"]) and len(shape["fits"]) == 25, "the fixture's roles are exactly the sealed order (25)")
    chk("shift_arm" in shape and {"arm", "readings", "difference_from_rung_4", "difference_from_rung_5", "note"} <= set(shape["shift_arm"])
        and set(shape["partition"]["shift_arm"]) >= set(P["shift_arm_hashes"]), "the runner writes the shift arm block and partition entry the reader compares")
    chk(set(shape["partition"]["rungs"][0]) >= set(P["rung_hashes"][0]) and set(shape["partition"]["rungs"][6]) >= set(P["rung_hashes"][6]),
        "every sealed rung key of both decades is one the runner writes per rung")
    chk(set(shape["bar"]) == {"slope_per_doubling", "bootstrap_lower_bound_gt", "n_boot", "bootstrap_seed", "lead_rule"}
        and set(shape["slope_bootstrap"]) >= {"model", "logistic", "depth3_tree", "model_minus_logistic", "model_minus_depth3_tree", "unit"}
        and set(shape["lead_at_top"]) >= {"r7_model_minus_logistic", "r7_model_minus_depth3_tree", "r4_model_minus_logistic", "r4_model_minus_depth3_tree", "unit", "verdict_pair"},
        "the fixture's bar, bootstrap and lead blocks carry the keys the reader compares")
    chk(set(shape["curves"]["model"]) >= {"slope_per_doubling_second_decade", "slope_per_doubling_first_decade", "slope_per_doubling_both_decades",
                                          "rung_to_rung_gains", "per_family_slope_per_doubling_second_decade"},
        "the fixture's curve blocks carry the two-decade slopes the reader recomputes")
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
        if sorted(_rec["per_family"]) != sorted(r24.FAMILIES + ["ext:" + f for f in r24.EXT_FAMILIES]):
            _bad.append(f"{_nm}: per_family keys")
        if not set(r24.ENV) <= set(_rec.get("environment") or {}):
            _bad.append(f"{_nm}: environment lacks {sorted(set(r24.ENV) - set(_rec.get('environment') or {}))}")
        _want = 7 if _nm == "null" else ("s4" if _nm.startswith("s4_") else int(_nm[1:_nm.index('_')]))
        _stage = "null" if _nm == "null" else ("shift" if _want == "s4" else ("curve" if _want > 4 else "reproduction"))
        if _rec.get("rung") != _want or _rec.get("role") != ("null" if _nm == "null" else _role) or _rec.get("stage") != _stage:
            _bad.append(f"{_nm}: rung/role/stage")
    chk(not _bad, "the reader's per-record requirements hold against the runner's own banked values" + (f" ({'; '.join(_bad[:3])})" if _bad else ""))
    chk("ledger" in shape and any(e.get("event") == "rung_bound" and "rung_sorted_sha256" in e for e in shape["ledger"])
        and [e["name"] for e in shape["ledger"] if e.get("event") == "completed"] == [f"run_{n}" for n in P["order"]],
        "the runner banks a ledger with rung_bound events and completes the roles in the sealed order")
    _src = inspect.getsource(rc_)
    _written = set(re.findall(r'partition\["([a-z0-9_]+)"\]', _src)) | set(re.findall(r'"([a-z0-9_]+)": (?:int|bool|_sha|list|\[|\{)', _src[_src.index("partition = {"):_src.index("t_id = time.perf_counter()")]))
    _rp_src = inspect.getsource(rc_.rung_partition2)
    _written |= set(re.findall(r'"([a-z0-9_]+)":', _rp_src[_rp_src.index("keys = {"):]))
    chk(_written <= set(shape["partition"]), "every partition key the runner's source writes is in the captured fixture (the fixture is current)"
        + (f" (missing {sorted(_written - set(shape['partition']))})" if not _written <= set(shape["partition"]) else ""))
    import ast as _ast

    def _body_dump(fn):
        node = _ast.parse(inspect.getsource(fn)).body[0]
        body = node.body[1:] if (node.body and isinstance(node.body[0], _ast.Expr) and isinstance(getattr(node.body[0], "value", None), _ast.Constant)
                                 and isinstance(node.body[0].value.value, str)) else node.body
        return [_ast.dump(x) for x in body]
    chk(_body_dump(rc1_.slope_bootstrap) == _body_dump(r24.slope_bootstrap) and _body_dump(rc1_.ols_slope) == _body_dump(r24.ols_slope)
        and _body_dump(rc_.paired_lead_bootstrap) == _body_dump(r24.paired_lead_bootstrap),
        "the reader's slope_bootstrap, ols_slope and paired_lead_bootstrap are the runners', statement for statement (AST equality below the docstring)")

    # 6. nothing of this run exists yet, and a real run refuses to start on an unfrozen preregistration
    for f in ("realcurve2_4096.json", "realcurve2_4096_scores.json", "realcurve2_4096_verdict.json", "realcurve2_4096_not_run.json"):
        chk(not os.path.exists(f"{REPO}/artifacts/pivot/{f}"), f"artifacts/pivot/{f} does not exist yet")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realcurve2_4096_ckpt"), "no checkpoint directory exists yet")
    chain = [json.loads(l) for l in open(f"{REPO}/prereg/chain.jsonl", encoding="utf-8") if l.strip()]
    chk(chain[-1]["id"] == "0023" and len(chain) == 23, "0023 is the chain head (23 entries)")
    chk(pr["reader"] == "tools/readers/realcurve2_4096_verdict.py" and os.path.exists(reader_path), "the reader exists at the sealed path")
    sm = pr["smoke"]
    chk(all(sm[k]["arrays"]["X"]["sha256"] != P[k]["arrays"]["X"]["sha256"] and sm[k]["npz"].startswith("(scratchpad)")
            for k in ("ext_corpus", "fit_corpus", "fit2_corpus")),
        "the smoke block names scratchpad corpora whose hashes are not the sealed ones")
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/run_realcurve2.py", "--stage", "run"], capture_output=True, text=True, cwd=REPO,
                        env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    chk(rc.returncode == 3 and "frozen preregistration" in rc.stderr, "a real run refuses to start on an unfrozen preregistration (exit 3)")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realcurve2_4096_ckpt"), "the refused launch created nothing")

    # 7. the banked mutation report agrees with the coverage map and carries this gate
    rep = json.load(open(f"{REPO}/artifacts/verification/mutation_report.json", encoding="utf-8"))
    cov = json.load(open(f"{REPO}/artifacts/verification/coverage.json", encoding="utf-8"))
    claim = next(c for c in cov["claims"] if c["id"] == "mutations-detected")
    chk(rep["detected"] == rep["total_mutations"] == claim["value"] and rep["survived"] == 0,
        f"the banked mutation report ({rep['detected']}/{rep['total_mutations']}) agrees with the coverage claim ({claim['value']})")
    g = rep["by_gate"].get("realcurve2_4096", {})
    chk(g.get("total", 0) >= 140 and g.get("detected") == g.get("total"), f"the report carries the realcurve2_4096 gate ({g})")

    result = {"schema": "raise-v1/prefreeze_0024/1", "preregistration": f"{pr['id']}-{pr['slug']}", "problems": bad,
              "passed": bad == 0, "reader_sha256_at_check": hashlib.sha256(reader.encode()).hexdigest(),
              "prereg_sha256_at_check": hashlib.sha256(open(f"{REPO}/prereg/0024-realcurve2-4096.json", "rb").read()).hexdigest(),
              "rungs": [{k: r[k] for k in ("rung", "decade", "n_chunks", "n_rows")} for r in RP["rungs"]],
              "doublings_spanned": RP["doublings_spanned"], "doublings_spanned_second_decade": RP["doublings_spanned_second_decade"]}
    os.makedirs(f"{REPO}/artifacts/verification", exist_ok=True)
    with open(f"{REPO}/artifacts/verification/prefreeze_0024.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"PRE-FREEZE 0024: {'PASS' if bad == 0 else 'FAIL'} ({bad} problem(s))")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
