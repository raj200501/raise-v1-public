#!/usr/bin/env python3
"""Pre-freeze check for preregistration 0023 (run before `tools/prereg.py freeze`; committed with the freeze, result
banked in artifacts/verification/prefreeze_0023.json). Exit 1 on any mismatch, 2 once the preregistration is frozen.

What it checks, and why each one exists:
 1. The reader is exactly what the generator produces from the preregistration and the template - no hand edit.
 2. Every sealed literal in the reader equals the preregistration's (protocol and curve hashes, recipes, references,
    tolerances, the null-label hash, the partition and the rungs, the corpora, the order, the bar, the bootstrap).
 3. The corpora on disk hash to the sealed arrays and their blocks are REBUILT BY CALLING the runner's corpus_block();
    the fit block, the four rungs and the replicate are REBUILT BY CALLING the runner's rung_partition() on the data and
    must equal the sealed constants hash for hash; the sealed evaluation set, pool and null-label array are RECOMPUTED from
    the builder cache and the fit corpus with the runner's own split and generator, not compared copy to copy
    (docs/OPERATING_RULES.md section 4; CORRECTIONS.md 2026-09-16 and 2026-09-17; 0023 pre-freeze review, condition lens).
 4. The references, the null-label hash and the recipes trace to 0021's and 0022's banked artifacts and sealed files; the
    reference slopes quoted in the prose are the banked numbers converted; no projection is sealed.
 5. Every key the reader compares is a key the runner writes (the captured fixture), the reader's per-record
    requirements hold against the runner's own banked records, and the fixture is current with the runner in the tree.
 6. Nothing of this run exists yet: no artifact, scores, verdict, NOT RUN file or checkpoints; the preregistration is
    unfrozen and 0022 is the chain head; the smoke block names scratchpad corpora; a real run refuses to start.
 7. The banked mutation report agrees with the coverage map's claim and carries this gate.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
SP = os.environ.get("PREREG_0023_SCRATCH", tempfile.mkdtemp(prefix="prefreeze_0023_"))
os.makedirs(SP, exist_ok=True)
bad = 0


def chk(cond, msg):
    global bad
    print(("ok   " if cond else "BAD  ") + msg)
    if not cond:
        bad += 1


def main() -> int:
    global bad
    pr = json.load(open(f"{REPO}/prereg/0023-realcurve-4096.json", encoding="utf-8"))
    if pr.get("frozen"):
        print(f"PRE-FREEZE 0023: the preregistration is frozen ({pr.get('frozen_utc')}); this check runs before a freeze "
              f"only. The result it banked then is artifacts/verification/prefreeze_0023.json.", file=sys.stderr)
        return 2
    S = pr["scope"]; CU = S["curve"]; P = CU["protocol"]; RE = CU["recipes"]; sp = S["sealed_partition"]
    canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
    sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

    # 1. the reader is the generated file
    gen = os.environ.get("PREREG_0023_GENERATOR")
    reader_path = f"{REPO}/tools/readers/realcurve4096_verdict.py"
    reader = open(reader_path, encoding="utf-8").read()
    if gen and os.path.exists(gen):
        tmp = os.path.join(SP, "regenerated_reader.py")
        rc = subprocess.run([sys.executable, gen, f"{REPO}/prereg/0023-realcurve-4096.json", tmp], capture_output=True, text=True)
        chk(rc.returncode == 0 and open(tmp, encoding="utf-8").read() == reader,
            "the reader is exactly what the generator produces from this preregistration")
    else:
        chk(False, "PREREG_0023_GENERATOR is not set to the generator script; cannot prove the reader was generated")

    # 2. the reader's sealed literals are the preregistration's
    import importlib.util
    spec = importlib.util.spec_from_file_location("r23", reader_path)
    r23 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r23)
    chk(r23.PREREG == f"{pr['id']}-{pr['slug']}", "the reader is frozen for this preregistration")
    chk(set(CU) == {"protocol", "recipes"}, "the sealed curve spec is exactly {protocol, recipes}")
    chk(r23.PROTOCOL == P and r23.PROTOCOL_SHA256 == sha(P) == S["sealed_hashes"]["protocol_sha256"],
        "the reader's PROTOCOL is the sealed protocol and hashes to the sealed hash")
    chk(r23.CURVE_SHA256 == sha(CU) == S["sealed_hashes"]["curve_sha256"] and r23.RECIPES == RE,
        "the reader's curve hash and recipes are the sealed ones")
    chk(r23.REFERENCE == P["reference_top1"] and r23.REPRO_TOLERANCE == P["reproduction_tolerance"]
        and r23.NULL_TOLERANCE == P["null_tolerance"] and r23.NULL_SHA_EXPECTED == P["null_y_shuffled_sha256_expected"]
        and r23.N_REAL == P["n_ext_real_rows"] and r23.N_EXT == P["ext_corpus"]["n_rows"],
        "the reader's references, tolerances, null-label hash and row counts are the sealed ones")
    chk(r23.BAR_SLOPE == P["bar"]["slope_per_doubling"] == 0.005 and r23.BOOT_LB == P["bar"]["bootstrap_lower_bound_gt"] == 0.0
        and r23.N_BOOT == P["bootstrap"]["n_boot"] == 2000 and r23.BOOT_SEED == P["bootstrap"]["seed"] == P["seed"]
        and "projection" not in P and r23.REF_BUILDER_SLOPE == P["reference_slopes_informational"]["builder_per_plaintext_slope_per_doubling"],
        "the reader's bar and bootstrap literals are the sealed ones, no projection is sealed, and the builder reference slope is the sealed one")
    chk(list(r23.ORDER) == P["order"] and list(r23.ROLES) == P["roles"] == ["depth3_tree", "logistic", "model"]
        and list(r23.DENOMINATORS) == P["denominators"] == [8, 4, 2, 1] and r23.N_RUNGS == 4 and len(r23.ORDER) == 16
        and r23.REPLICATE == P["replicate"] == "rep1" and r23.LOG2X == [r["log2_chunks"] for r in sp["rungs"]],
        "the reader's order (16 roles), roles, denominators, rung count, replicate name and log2 abscissae are the sealed ones")
    chk(r23.ENV == P["environment"] and r23.ENV_FULL == dict(P["environment"], threads=P["threads"], nice=P["nice"]),
        "the reader's environment literals are the sealed ones")
    chk(r23.EXT == P["ext_corpus"] and r23.FIT == P["fit_corpus"], "the reader's corpus blocks are the sealed ones")
    for k, v in P["fit_block_hashes"].items():
        chk(r23.PARTITION.get(k) == v, f"the reader's PARTITION.{k} is the sealed fit-block hash")
    chk(r23.PARTITION["rungs"] == P["rung_hashes"] == sp["rungs"], "the reader's PARTITION.rungs is the sealed rung table")
    chk(r23.PARTITION["replicate_rung_1"] == P["replicate_rung_1_hashes"] == sp["replicate_rung_1"], "the reader's replicate rung is the sealed one")
    chk(r23.EVAL_CHUNK_IDS == S["eval_chunk_layout"]["chunk_ids"] and r23.EVAL_ROWS_PER_CHUNK == S["eval_chunk_layout"]["rows_per_chunk"]
        and r23.EXT_CHUNK_IDS == S["ext_chunk_layout"]["chunk_ids_with_rows"] and r23.EXT_ROWS_PER_CHUNK == S["ext_chunk_layout"]["rows_per_chunk"],
        "the reader's chunk layouts are the sealed ones")
    chk(r23.MAX_ITER == {r: (RE[r].get("params", {}).get("max_iter") or 0) for r in r23.ROLES}, "the reader's iteration caps are the recipes'")
    # every reading's json_path resolves to a key of the reader's result (the exception path writes the same keys)
    paths = [x["json_path"] for x in pr["readings"]]
    chk(all(p.startswith("$.") and p[2:].split(".")[0] in r23.RESULT_KEYS for p in paths),
        "every sealed reading's json_path names a key the reader writes on every path")

    # 3. the corpora, the fit block and the rungs, rebuilt by calling the runner's own code on the data
    from run_realfit import corpus_block, _array_sha
    import run_realcurve as rc_

    def _runner_block(rel, labels):
        d = np.load(f"{REPO}/{rel}", allow_pickle=False)
        names = [str(x) for x in d["families"]]; fam = np.array(names)[d["fam"]]
        h = {n: dict(zip(("sha256", "shape", "dtype"), _array_sha(f"{REPO}/{rel}", n))) for n in ("X", "y", "g", "fam")}
        return corpus_block(rel, h, d["y"], d["g"], fam, names, labels=labels), d, names, fam
    rb_fit, dfit, fit_names, fam_r = _runner_block("data/pivot/realfit_c4096.npz", True)
    rb_ext, _, _, _ = _runner_block("data/pivot/ext_c4096.npz", False)
    chk(P["fit_corpus"] == rb_fit and P["ext_corpus"] == rb_ext, "the sealed corpus blocks are what the runner banks from the npz on disk")
    fit_order, rung_rows, rep_rows, RP = rc_.rung_partition(dfit["y"], dfit["g"], fam_r, fit_names, P["seed"], P["denominators"])
    chk(RP["replicate_rung_1"] == P["replicate_rung_1_hashes"] and RP["replicate_rung_1"]["n_chunks"] == RP["rungs"][0]["n_chunks"]
        and RP["replicate_rung_1"]["idx_sha256"] != RP["rungs"][0]["idx_sha256"] and len(rep_rows) == RP["replicate_rung_1"]["n_rows"],
        "the sealed replicate rung is what rung_partition() computes: rung 1's size under the second nesting, not rung 1's rows")
    chk(all(RP[k] == v for k, v in P["fit_block_hashes"].items()), "the sealed fit-block hashes are what the runner's rung_partition() computes")
    chk([{k: r[k] for k in P["rung_hashes"][0]} for r in RP["rungs"]] == P["rung_hashes"] == sp["rungs"],
        "the sealed rung table is what the runner's rung_partition() computes from the fit corpus, hash for hash")
    chk(RP["rungs_nested"] and RP["rung_chunks_strictly_increasing"] and RP["top_rung_is_fit_block"]
        and RP["doublings_spanned"] == sp["doublings_spanned"] and RP["rung_rule"] == P["rung_rule"] == sp["rung_rule"],
        "the rungs are nested, strictly increasing, topped by the whole fit block, and the sealed rule and span are the runner's")
    chk(all(r23.PARTITION[k] == RP[k] for k in RP if k in r23.PARTITION), "every fit-block and rung key the reader seals equals the runner's recomputation")
    chk(all(sum(r["chunks_per_family"].values()) == r["n_chunks"] and sum(r["rows_per_family"].values()) == r["n_rows"]
            and all(v >= 1 for v in r["chunks_per_family"].values()) for r in RP["rungs"]),
        "every rung's family counts sum to its totals and every family has at least one plaintext in the smallest rung")
    chk(RP["rungs"][-1]["n_rows"] == rb_fit["n_rows"] and RP["rungs"][-1]["n_chunks"] == rb_fit["n_chunks"] and len(fit_order) == rb_fit["n_rows"],
        "the top rung is the whole fit corpus")
    a21 = json.load(open(f"{REPO}/artifacts/pivot/realfit_4096_rerun.json", encoding="utf-8"))
    p21 = json.load(open(f"{REPO}/prereg/0021-realfit-4096-rerun.json", encoding="utf-8"))
    chk(RP["fit_idx_sha256"] == a21["partition"]["fit_idx_sha256"] == p21["scope"]["sealed_partition"]["fit_block"]["idx_sha256"]
        and RP["fit_sorted_sha256"] == a21["partition"]["fit_sorted_sha256"],
        "the fit block is 0021's fit block, row for row (its banked and sealed hashes)")
    chk(sp["eval"] == p21["scope"]["sealed_partition"]["eval"] and sp["pool"] == p21["scope"]["sealed_partition"]["pool"]
        and P["pool_idx_sha256"] == a21["partition"]["pool_idx_sha256"] and r23.PARTITION["eval_idx_sha256"] == a21["partition"]["eval_idx_sha256"]
        and r23.PARTITION["eval_g_sha256"] == a21["partition"]["eval_g_sha256"] and r23.PARTITION["eval_y_sha256"] == a21["partition"]["eval_y_sha256"],
        "the evaluation set and the pool are 0021's sealed and banked ones")
    # recomputed from the data with the runner's own split and generator, never copy to copy (condition lens, finding 2)
    import io as _io, zipfile as _zf
    from run_recipe_search import grouped_split, _sha as _rsha
    with _zf.ZipFile(f"{REPO}/data/pivot/full_c4096.npz") as zf:
        y_b = np.load(_io.BytesIO(zf.read("y.npy"))); g_b = np.load(_io.BytesIO(zf.read("g.npy")))
    ev, tr, rng = grouped_split(y_b, g_b, P["seed"], P["eval_frac"], P["top_rung"])
    y_sh = np.asarray(dfit["y"]).copy(); rng.shuffle(y_sh)
    chk(_rsha(ev) == r23.PARTITION["eval_idx_sha256"] and _rsha(np.asarray(g_b[ev])) == r23.PARTITION["eval_g_sha256"]
        and _rsha(np.asarray(y_b[ev])) == r23.PARTITION["eval_y_sha256"] and _rsha(tr) == P["pool_idx_sha256"]
        and _rsha(np.sort(tr).astype(np.int64)) == r23.PARTITION["pool_sorted_sha256"] and int(len(ev)) == r23.PARTITION["n_eval_rows"]
        and int(len(tr)) == r23.PARTITION["n_pool_rows"],
        "the sealed evaluation set and pool hashes are what the runner's grouped_split() computes from the builder cache on disk")
    chk(_rsha(y_sh) == P["null_y_shuffled_sha256_expected"] and not np.array_equal(y_sh, np.asarray(dfit["y"])),
        "the sealed null-label hash is what the split's generator produces on the fit corpus's labels as its first draw")
    _ci = lambda d: {k: v for k, v in d.items() if k != "X_note"}  # noqa: E731  (the note is restated for what it is; the hashes are 0021's)
    chk(_ci(P["cache_identity"]) == _ci(p21["scope"]["protocol"]["cache_identity"]) and r23.CORPUS["cache_X_sha256"] == P["cache_identity"]["X_sha256"]
        and r23.CORPUS == {k: a21["corpus"][k] for k in r23.CORPUS}, "the builder cache identity is 0021's, X hash included, and the reader's CORPUS is 0021's banked block")
    chk(S["eval_chunk_layout"] == p21["scope"]["eval_chunk_layout"] and S["ext_chunk_layout"] == p21["scope"]["ext_chunk_layout"],
        "the chunk layouts are 0021's sealed ones")

    # 4. references, null hash, recipes, target and quoted numbers trace to banked artifacts and sealed files
    er = a21["ext_real_top1"]
    p22 = json.load(open(f"{REPO}/prereg/0022-realsearch-4096.json", encoding="utf-8"))
    a22 = json.load(open(f"{REPO}/artifacts/pivot/realsearch_4096.json", encoding="utf-8"))
    v22 = json.load(open(f"{REPO}/artifacts/pivot/realsearch_4096_verdict.json", encoding="utf-8"))
    chk(P["reference_top1"] == {"model": er["real_model"], "logistic": er["real_logistic"], "depth3_tree": er["floor_tree3"]}
        == {"model": v22["reproduction_top1"]["repro_m4"], "logistic": v22["reproduction_top1"]["repro_l3"], "depth3_tree": v22["reproduction_top1"]["repro_d1"]},
        "the three references are 0021's banked readings, which 0022 reproduced with drift 0.0")
    chk(P["null_y_shuffled_sha256_expected"] == a21["partition"]["null_y_shuffled_sha256"] == a22["partition"]["null_y_shuffled_sha256"],
        "the sealed null-label hash is 0021's banked one, which 0022 matched")
    rr = p22["scope"]["recipes_reference"]; r21 = p21["scope"]["recipes"]
    chk(RE == {"model": rr["model"], "logistic": rr["logistic_l3"], "depth3_tree": rr["depth3"]} and p22.get("frozen") is True,
        "the recipes are 0022's sealed recipes_reference (M4, L3, D1), verbatim")
    chk(RE["model"]["params"] == r21["model"]["params"] and RE["logistic"]["params"] == r21["logistic_l3"]["params"]
        and bool(RE["logistic"].get("scaled")) == bool(r21["logistic_l3"].get("scaled")) and RE["depth3_tree"]["params"] == r21["floor_tree3"]["params"],
        "the recipes are 0021's recipes parameter for parameter")
    chk(P["recipe_ids"] == {"model": "M4", "logistic": "L3", "depth3_tree": "D1"} and all(RE[r]["id"] == P["recipe_ids"][r] for r in RE),
        "the sealed recipe ids are M4, L3, D1")
    c03 = json.load(open(f"{REPO}/artifacts/pivot/deflate_curve.json", encoding="utf-8"))
    chk(str(round(c03["slope"] / math.log2(10), 6)) in S["why_this_preregistration_exists"], "the 0003 slope per doubling quoted in the prose is the banked slope converted")
    rs = P["reference_slopes_informational"]; rd = a21["readings"]; pa = a21["partition"]
    pfc = json.load(open(f"{REPO}/artifacts/pivot/per_family_curves.json", encoding="utf-8"))
    chk(rs["builder_per_plaintext_slope_per_doubling"] == round((c03["top_rung_accuracy"] - rd["builder_chunk_matched"]["builder_eval_top1"])
                                                                / math.log2(pa["n_pool_chunks"] / pa["chunk_matched_block_chunks"]), 6)
        and rs["builder_fixed_rows_plaintext_slope_per_doubling"] == round((rd["builder_matched"]["builder_eval_top1"] - rd["builder_chunk_matched"]["builder_eval_top1"])
                                                                            / math.log2(pa["matched_block_chunks"] / pa["chunk_matched_block_chunks"]), 6)
        and rs["builder_mixed_family_slope_per_doubling"] == round(pfc["families"]["mixed"]["slope"] * math.log10(2), 6)
        and rs["builder_mixture_slope_per_doubling_of_fragments"] == round(c03["slope"] / math.log2(10), 6),
        "the sealed reference slopes are the banked numbers converted (0021's matched arms, 0003's top rung, the mixed family's curve)")
    chk(all(str(rs[k]) in S["expected_outcome_stated_in_advance"] for k in ("builder_per_plaintext_slope_per_doubling",
                                                                            "builder_fixed_rows_plaintext_slope_per_doubling",
                                                                            "builder_mixed_family_slope_per_doubling")),
        "the expected outcome quotes the sealed reference slopes")
    chk("REAL_CURVE_RISES" in S["expected_outcome_stated_in_advance"] and "more likely than not" in S["expected_outcome_stated_in_advance"]
        and "COULD NOT VERIFY" in S["expected_outcome_stated_in_advance"], "the expected outcome is stated in advance with its direction and its unknowns")
    for k in ("pool_idx_sha256", "n_ext_real_rows"):
        chk(P[k] == p21["scope"]["protocol"][k], f"protocol.{k} is 0021's")
    chk(P["order"] == rc_.sealed_order(4), "the sealed order is the runner's sealed_order(4)")
    chk(str(RP["rungs"][0]["n_chunks"]) in S["one_line"] and str(RP["rungs"][-1]["n_rows"]) in S["one_line"]
        and str(RP["doublings_spanned"]) in S["one_line"], "the one-line scope states the rung sizes and the span")

    # 5. the reader's expectations are keys the runner writes; the fixture is current with the runner in the tree
    fx = json.load(open(f"{REPO}/tests/fixtures/realcurve_runner_shape.json", encoding="utf-8"))
    shape = fx["artifact"]
    for nm, sealed, blk in (("FIT", r23.FIT, "fit_corpus"), ("EXT", r23.EXT, "ext_corpus"), ("PARTITION", r23.PARTITION, "partition"),
                            ("CORPUS", r23.CORPUS, "corpus")):
        chk(set(sealed) <= set(shape[blk]), f"every key the reader's {nm} compares is one the runner writes"
            + (f" (missing {sorted(set(sealed) - set(shape[blk]))})" if not set(sealed) <= set(shape[blk]) else ""))
    chk(set(P) == set(shape["curve_spec"]["protocol"]), "the fixture's protocol has this preregistration's key set (the fixture is current)")
    chk(set(shape["curve_spec"]) == {"protocol", "recipes"} and set(shape["curve_spec"]["recipes"]) == set(RE),
        "the fixture's curve spec is exactly {protocol, recipes} over the three roles")
    chk(set(shape["fits"]) == set(P["order"]) and len(shape["fits"]) == 16, "the fixture's roles are exactly the sealed order (16)")
    chk(set(shape["partition"]["replicate_rung_1"]) >= set(P["replicate_rung_1_hashes"]) and "replicate_rung_1" in shape
        and {"readings", "difference_from_rung_1", "slope_with_replicate_at_rung_1", "note", "rung"} <= set(shape["replicate_rung_1"]),
        "the runner writes the replicate rung and the replicate block the reader compares")
    chk("projection_informational" not in shape and set(shape["curves"]["model"]) >= {"rung_to_rung_gains", "slope_with_top_rung_at_reference"},
        "the fixture is current: no projection, and the curve blocks carry the gains and the sensitivity slope")
    chk(set(shape["partition"]["rungs"][0]) >= set(P["rung_hashes"][0]), "every sealed rung key is one the runner writes per rung")
    chk(set(shape["bar"]) == {"slope_per_doubling", "bootstrap_lower_bound_gt", "n_boot", "bootstrap_seed"}
        and set(shape["slope_bootstrap"]) >= {"model", "logistic", "depth3_tree", "model_minus_logistic", "model_minus_depth3_tree", "unit"},
        "the fixture's bar and bootstrap blocks carry the keys the reader compares")
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
        if sorted(_rec["per_family"]) != sorted(r23.FAMILIES + ["ext:" + f for f in r23.EXT_FAMILIES]):
            _bad.append(f"{_nm}: per_family keys")
        if not set(r23.ENV) <= set(_rec.get("environment") or {}):
            _bad.append(f"{_nm}: environment lacks {sorted(set(r23.ENV) - set(_rec.get('environment') or {}))}")
        _want = 4 if _nm == "null" else (r23.REPLICATE if _nm.startswith(r23.REPLICATE + "_") else int(_nm[1:_nm.index('_')]))
        if _rec.get("rung") != _want or _rec.get("role") != ("null" if _nm == "null" else _role):
            _bad.append(f"{_nm}: rung/role")
    chk(not _bad, "the reader's per-record requirements hold against the runner's own banked values" + (f" ({'; '.join(_bad[:3])})" if _bad else ""))
    chk("ledger" in shape and all(e.get("event") in ("rung_bound", "started", "completed", "heartbeat", "resumed", "killed", "infeasible") for e in shape["ledger"])
        and any(e.get("event") == "rung_bound" and "rung_sorted_sha256" in e for e in shape["ledger"]),
        "the runner banks a ledger with rung_bound events carrying the rung's sorted hash")
    _src = inspect.getsource(rc_)
    _written = set(re.findall(r'partition\["([a-z0-9_]+)"\]', _src)) | set(re.findall(r'"([a-z0-9_]+)": (?:int|bool|_sha|list|\[|\{)', _src[_src.index("partition = {"):_src.index("t_id = time.perf_counter()")]))
    _rp_src = inspect.getsource(rc_.rung_partition)
    _written |= set(re.findall(r'"([a-z0-9_]+)":', _rp_src[_rp_src.index("keys = {"):]))
    chk(_written <= set(shape["partition"]), "every partition key the runner's source writes is in the captured fixture (the fixture is current)"
        + (f" (missing {sorted(_written - set(shape['partition']))})" if not _written <= set(shape["partition"]) else ""))
    import ast as _ast

    def _body_dump(fn):
        node = _ast.parse(inspect.getsource(fn)).body[0]
        body = node.body[1:] if (node.body and isinstance(node.body[0], _ast.Expr) and isinstance(getattr(node.body[0], "value", None), _ast.Constant)
                                 and isinstance(node.body[0].value.value, str)) else node.body
        return [_ast.dump(x) for x in body]
    chk(_body_dump(rc_.slope_bootstrap) == _body_dump(r23.slope_bootstrap) and _body_dump(rc_.ols_slope) == _body_dump(r23.ols_slope),
        "the reader's slope_bootstrap and ols_slope are the runner's, statement for statement (AST equality below the docstring)")

    # 6. nothing of this run exists yet, and a real run refuses to start on an unfrozen preregistration
    for f in ("realcurve_4096.json", "realcurve_4096_scores.json", "realcurve_4096_verdict.json", "realcurve_4096_not_run.json"):
        chk(not os.path.exists(f"{REPO}/artifacts/pivot/{f}"), f"artifacts/pivot/{f} does not exist yet")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realcurve_4096_ckpt"), "no checkpoint directory exists yet")
    chain = [json.loads(l) for l in open(f"{REPO}/prereg/chain.jsonl", encoding="utf-8") if l.strip()]
    chk(chain[-1]["id"] == "0022" and len(chain) == 22, "0022 is the chain head (22 entries)")
    chk(pr["reader"] == "tools/readers/realcurve4096_verdict.py" and os.path.exists(reader_path), "the reader exists at the sealed path")
    sm = pr["smoke"]
    chk(sm["ext_corpus"]["arrays"]["X"]["sha256"] != P["ext_corpus"]["arrays"]["X"]["sha256"]
        and sm["fit_corpus"]["arrays"]["X"]["sha256"] != P["fit_corpus"]["arrays"]["X"]["sha256"]
        and sm["ext_corpus"]["npz"].startswith("(scratchpad)") and sm["fit_corpus"]["npz"].startswith("(scratchpad)"),
        "the smoke block names scratchpad corpora whose hashes are not the sealed ones")
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/run_realcurve.py", "--stage", "run"], capture_output=True, text=True, cwd=REPO,
                        env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    chk(rc.returncode == 3 and "frozen preregistration" in rc.stderr, "a real run refuses to start on an unfrozen preregistration (exit 3)")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realcurve_4096_ckpt"), "the refused launch created nothing")

    # 7. the banked mutation report agrees with the coverage map and carries this gate
    rep = json.load(open(f"{REPO}/artifacts/verification/mutation_report.json", encoding="utf-8"))
    cov = json.load(open(f"{REPO}/artifacts/verification/coverage.json", encoding="utf-8"))
    claim = next(c for c in cov["claims"] if c["id"] == "mutations-detected")
    chk(rep["detected"] == rep["total_mutations"] == claim["value"] and rep["survived"] == 0,
        f"the banked mutation report ({rep['detected']}/{rep['total_mutations']}) agrees with the coverage claim ({claim['value']})")
    g = rep["by_gate"].get("realcurve4096", {})
    chk(g.get("total", 0) >= 95 and g.get("detected") == g.get("total"), f"the report carries the realcurve4096 gate ({g})")

    result = {"schema": "raise-v1/prefreeze_0023/1", "preregistration": f"{pr['id']}-{pr['slug']}", "problems": bad,
              "passed": bad == 0, "reader_sha256_at_check": hashlib.sha256(reader.encode()).hexdigest(),
              "prereg_sha256_at_check": hashlib.sha256(open(f"{REPO}/prereg/0023-realcurve-4096.json", "rb").read()).hexdigest(),
              "rungs": [{k: r[k] for k in ("rung", "denominator", "n_chunks", "n_rows")} for r in RP["rungs"]],
              "replicate_rung_1": {k: RP["replicate_rung_1"][k] for k in ("n_chunks", "n_rows", "chunks_shared_with_rung_1")},
              "doublings_spanned": RP["doublings_spanned"]}
    os.makedirs(f"{REPO}/artifacts/verification", exist_ok=True)
    with open(f"{REPO}/artifacts/verification/prefreeze_0023.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"PRE-FREEZE 0023: {'PASS' if bad == 0 else 'FAIL'} ({bad} problem(s))")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
