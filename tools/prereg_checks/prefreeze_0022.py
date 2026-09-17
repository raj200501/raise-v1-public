#!/usr/bin/env python3
"""Pre-freeze check for preregistration 0022 (run before `tools/prereg.py freeze`; committed with the freeze, result
banked in artifacts/verification/prefreeze_0022.json). Exit 1 on any mismatch, 2 once the preregistration is frozen.

What it checks, and why each one exists:
 1. The reader is exactly what the generator produces from the preregistration and the template - no hand edit.
 2. Every sealed literal in the reader equals the preregistration's (protocol and roster hashes, floors, references,
    tolerances, the null-label hash, the partition, the corpora, the order, the heads).
 3. The corpora on disk hash to the sealed arrays and their blocks are REBUILT BY CALLING the runner's corpus_block();
    the fit block, the holdout, the fit pool and the stage are REBUILT BY CALLING the runner's fit_block_partition()
    on the data, and must equal the sealed constants hash for hash (docs/OPERATING_RULES.md section 4: two copies of
    one wrong literal agree with each other; CORRECTIONS.md 2026-09-16 and 2026-09-17).
 4. The floors, the reproduction references and the null-label hash trace to 0021's banked artifact; the roster heads
    are 0014's sealed heads verbatim; the reference recipes are 0021's recipes parameter for parameter.
 5. Every key the reader compares is a key the runner writes (the captured fixture), the reader's per-record
    requirements hold against the runner's own banked records, and the fixture is current with the runner in the tree.
 6. Nothing of this run exists yet: no selection file, artifact, scores or verdict; the preregistration is unfrozen and
    0021 is the chain head; the smoke block names scratchpad corpora; a real run refuses to start on an unfrozen file.
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
SP = os.environ.get("PREREG_0022_SCRATCH", tempfile.mkdtemp(prefix="prefreeze_0022_"))
os.makedirs(SP, exist_ok=True)
bad = 0


def chk(cond, msg):
    global bad
    print(("ok   " if cond else "BAD  ") + msg)
    if not cond:
        bad += 1


def main() -> int:
    global bad
    pr = json.load(open(f"{REPO}/prereg/0022-realsearch-4096.json", encoding="utf-8"))
    if pr.get("frozen"):
        print(f"PRE-FREEZE 0022: the preregistration is frozen ({pr.get('frozen_utc')}); this check runs before a freeze "
              f"only. The result it banked then is artifacts/verification/prefreeze_0022.json.", file=sys.stderr)
        return 2
    S = pr["scope"]; RO = S["roster"]; P = RO["protocol"]; sp = S["sealed_partition"]
    canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
    sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

    # 1. the reader is the generated file
    gen = os.environ.get("PREREG_0022_GENERATOR")
    reader_path = f"{REPO}/tools/readers/realsearch4096_verdict.py"
    reader = open(reader_path, encoding="utf-8").read()
    if gen and os.path.exists(gen):
        tmp = os.path.join(SP, "regenerated_reader.py")
        rc = subprocess.run([sys.executable, gen, f"{REPO}/prereg/0022-realsearch-4096.json", tmp], capture_output=True, text=True)
        chk(rc.returncode == 0 and open(tmp, encoding="utf-8").read() == reader,
            "the reader is exactly what the generator produces from this preregistration")
    else:
        chk(False, "PREREG_0022_GENERATOR is not set to the generator script; cannot prove the reader was generated")

    # 2. the reader's sealed literals are the preregistration's
    import importlib.util
    spec = importlib.util.spec_from_file_location("r22", reader_path)
    r22 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r22)
    chk(r22.PREREG == f"{pr['id']}-{pr['slug']}", "the reader is frozen for this preregistration")
    chk(set(RO) == {"protocol", "heads"}, "the sealed roster is exactly {protocol, heads}")
    chk(r22.PROTOCOL == P and r22.PROTOCOL_SHA256 == sha(P) == S["sealed_hashes"]["protocol_sha256"],
        "the reader's PROTOCOL is the sealed protocol and hashes to the sealed hash")
    chk(r22.ROSTER_SHA256 == sha(RO) == S["sealed_hashes"]["roster_sha256"] and r22.HEADS == RO["heads"],
        "the reader's roster hash and heads are the sealed ones")
    p14 = json.load(open(f"{REPO}/prereg/0014-recipe-search-4096.json", encoding="utf-8"))
    chk(RO["heads"] == p14["scope"]["roster"]["heads"] and p14.get("frozen") is True,
        "the roster heads are 0014's sealed heads, verbatim")
    chk(r22.FLOORS == P["floors"] and r22.REFERENCE == P["reference_top1"] and r22.MARGIN == P["bar"]["margin"] == 0.05
        and r22.REPRO_TOLERANCE == P["reproduction_tolerance"] and r22.NULL_TOLERANCE == P["null_tolerance"]
        and r22.NULL_SHA_EXPECTED == P["null_y_shuffled_sha256_expected"] and r22.N_REAL == P["n_ext_real_rows"],
        "the reader's floors, references, margin, tolerances, null-label hash and real-row count are the sealed ones")
    chk(list(r22.CONFIRM_ORDER) == P["confirm_order"] and list(r22.FROZEN_HEADS) == P["frozen_heads"]
        and list(r22.EXPANDED_HEADS) == P["expanded_heads"]
        and {a: [h, P[k]] for a, (h, k) in {"repro_m1": ("model", "incumbent_id"), "repro_m4": ("model", "model_reference_id"),
                                             "repro_l3": ("logistic", "logistic_reference_id"),
                                             "repro_d1": ("depth3_tree", "tree_reference_id")}.items()} == {a: list(v) for a, v in r22.REPRO_ARMS.items()},
        "the reader's order, head sets and reproduction arms are the sealed ones")
    chk(r22.ENV == P["environment"] and r22.ENV_FULL == dict(P["environment"], threads=P["threads"], nice=P["nice"]),
        "the reader's environment literals are the sealed ones")
    chk(r22.EXT == P["ext_corpus"] and r22.FIT == P["fit_corpus"], "the reader's corpus blocks are the sealed ones")
    for k, v in P["fit_block_hashes"].items():
        chk(r22.PARTITION.get(k) == v, f"the reader's PARTITION.{k} is the sealed fit-block hash")
    chk(r22.EVAL_CHUNK_IDS == S["eval_chunk_layout"]["chunk_ids"] and r22.EVAL_ROWS_PER_CHUNK == S["eval_chunk_layout"]["rows_per_chunk"]
        and r22.EXT_CHUNK_IDS == S["ext_chunk_layout"]["chunk_ids_with_rows"] and r22.EXT_ROWS_PER_CHUNK == S["ext_chunk_layout"]["rows_per_chunk"],
        "the reader's chunk layouts are the sealed ones")

    # 3. the corpora and the partition, rebuilt by calling the runner's own code on the data
    from run_realfit import corpus_block, _array_sha
    import run_realsearch as rs

    def _runner_block(rel, labels):
        d = np.load(f"{REPO}/{rel}", allow_pickle=False)
        names = [str(x) for x in d["families"]]; fam = np.array(names)[d["fam"]]
        h = {n: dict(zip(("sha256", "shape", "dtype"), _array_sha(f"{REPO}/{rel}", n))) for n in ("X", "y", "g", "fam")}
        return corpus_block(rel, h, d["y"], d["g"], fam, names, labels=labels), d, names, fam
    rb_fit, dfit, fit_names, fam_r = _runner_block("data/pivot/realfit_c4096.npz", True)
    rb_ext, _, _, _ = _runner_block("data/pivot/ext_c4096.npz", False)
    chk(P["fit_corpus"] == rb_fit and P["ext_corpus"] == rb_ext, "the sealed corpus blocks are what the runner banks from the npz on disk")
    fit_order, hold, fitpool, stage_rows, FP = rs.fit_block_partition(dfit["y"], dfit["g"], fam_r, fit_names, P["seed"], P["holdout"], P["stages"][0])
    chk(all(FP[k] == v for k, v in P["fit_block_hashes"].items()),
        "the sealed fit-block hashes are what the runner's fit_block_partition() computes from the fit corpus")
    chk(FP["holdout_rule"] == sp["holdout"]["rule"] and FP["n_holdout_rows"] == sp["holdout"]["n_rows"]
        and FP["n_holdout_chunks"] == sp["holdout"]["n_chunks"] and FP["holdout_rows_per_family"] == sp["holdout"]["rows_per_family"]
        and FP["holdout_chunks_per_family"] == sp["holdout"]["chunks_per_family"] and FP["n_fitpool_rows"] == sp["fit_pool"]["n_rows"]
        and FP["n_fitpool_chunks"] == sp["fit_pool"]["n_chunks"] and FP["fitpool_rows_per_family"] == sp["fit_pool"]["rows_per_family"]
        and FP["stage_rows"] == sp["stage"]["rows"] and FP["stage_keep"] == sp["stage"]["keep"] and FP["stage_chunks"] == sp["stage"]["chunks"]
        and FP["fit_order_rule"] == sp["fit_block"]["order_rule"],
        "the sealed holdout, fit pool and stage counts and rules are the runner's")
    chk(all(r22.PARTITION[k] == FP[k] for k in FP if k in r22.PARTITION and k not in ("n_chunks_holdout_and_fitpool", "n_holdout_rows_in_fitpool")),
        "every fit-block key the reader seals equals the runner's recomputation")
    chk(FP["n_holdout_rows"] + FP["n_fitpool_rows"] == FP["fit_rows"] == rb_fit["n_rows"] and FP["stage_rows"] == [FP["n_fitpool_rows"]]
        and FP["n_chunks_holdout_and_fitpool"] == 0 and FP["n_holdout_rows_in_fitpool"] == 0,
        "the holdout and the fit pool partition the fit block, share nothing, and the single stage is the whole fit pool")
    chk(all(FP["holdout_chunks_per_family"][f] >= 1 for f in fit_names), "every real family has at least one holdout chunk")
    a21 = json.load(open(f"{REPO}/artifacts/pivot/realfit_4096_rerun.json", encoding="utf-8"))
    p21 = json.load(open(f"{REPO}/prereg/0021-realfit-4096-rerun.json", encoding="utf-8"))
    chk(FP["fit_idx_sha256"] == a21["partition"]["fit_idx_sha256"] == p21["scope"]["sealed_partition"]["fit_block"]["idx_sha256"]
        and FP["fit_sorted_sha256"] == a21["partition"]["fit_sorted_sha256"],
        "the fit block is 0021's fit block, row for row (its banked and sealed hashes)")
    chk(sp["eval"] == p21["scope"]["sealed_partition"]["eval"] and sp["pool"] == p21["scope"]["sealed_partition"]["pool"]
        and P["pool_idx_sha256"] == a21["partition"]["pool_idx_sha256"] and r22.PARTITION["eval_idx_sha256"] == a21["partition"]["eval_idx_sha256"]
        and r22.PARTITION["eval_g_sha256"] == a21["partition"]["eval_g_sha256"] and r22.PARTITION["eval_y_sha256"] == a21["partition"]["eval_y_sha256"],
        "the evaluation set and the pool are 0021's sealed and banked ones")
    chk(P["cache_identity"] == p21["scope"]["protocol"]["cache_identity"] and r22.CORPUS["cache_X_sha256"] == P["cache_identity"]["X_sha256"]
        and r22.CORPUS == {k: a21["corpus"][k] for k in r22.CORPUS}, "the builder cache identity is 0021's, X hash included, and the reader's CORPUS is 0021's banked block")
    chk(S["eval_chunk_layout"] == p21["scope"]["eval_chunk_layout"] and S["ext_chunk_layout"] == p21["scope"]["ext_chunk_layout"],
        "the chunk layouts are 0021's sealed ones")

    # 4. floors, references and the null hash trace to 0021's banked artifact; the reference recipes are 0021's
    er = a21["ext_real_top1"]
    chk(P["floors"] == {"majority": er["floor_majority"], "stratified": er["floor_stratified"], "depth3_tree": er["floor_tree3"],
                        "logistic": er["real_logistic"], "best_single_feat": er["floor_feat1"], "deep_tree": 0.0},
        "the floors are 0021's banked real-family readings of each head's reference recipe (deep_tree floored at 0)")
    chk(P["reference_top1"] == {"repro_m1": er["real_incumbent"], "repro_m4": er["real_model"], "repro_l3": er["real_logistic"],
                                "repro_d1": er["floor_tree3"]}, "the four reproduction references are 0021's banked readings")
    chk(P["null_y_shuffled_sha256_expected"] == a21["partition"]["null_y_shuffled_sha256"], "the sealed null-label hash is 0021's banked one")
    by_id = {c["id"]: c for h in RO["heads"] for c in h["candidates"]}
    r21 = p21["scope"]["recipes"]
    chk(by_id["M1"]["params"] == r21["incumbent"]["params"] and by_id["M4"]["params"] == r21["model"]["params"]
        and by_id["L3"]["params"] == r21["logistic_l3"]["params"] and bool(by_id["L3"].get("scaled")) == bool(r21["logistic_l3"].get("scaled"))
        and by_id["D1"]["params"] == r21["floor_tree3"]["params"] and by_id["U3"]["params"] == r21["floor_feat1"]["params"]
        and by_id["U1"]["params"] == r21["floor_majority"]["params"] and by_id["U2"]["params"] == r21["floor_stratified"]["params"],
        "the reference recipes M1, M4, L3, D1 and the knob-free U1, U2, U3 are 0021's recipes parameter for parameter")
    chk(P["incumbent_id"] == "M1" == RO["heads"][0]["candidates"][0]["id"] and RO["heads"][0]["side"] == "model",
        "the incumbent leads the model roster")
    v21 = json.load(open(f"{REPO}/artifacts/pivot/realfit_4096_rerun_verdict.json", encoding="utf-8"))
    chk(v21["verdict"] == "REAL_FIT_FAILS" and v21["ext_real_top1_model"] == P["reference_top1"]["repro_m4"]
        and r22.REF_0021_MODEL_CORRECT == v21["ext_real_correct_model"], "the 0021 comparison numbers are the banked verdict's")
    need_unsearched = int(np.ceil(P["n_ext_real_rows"] * (max(P["floors"][h] for h in P["frozen_heads"]) + 0.05) - 1e-9))
    chk(str(need_unsearched) in S["the_bar_and_why_the_logistic_is_in_it"], f"the scope states the unsearched frozen bar's row count ({need_unsearched})")
    chk("REAL_RECIPE_FAILS" in S["expected_outcome_stated_in_advance"] and "more likely than not" in S["expected_outcome_stated_in_advance"],
        "the expected outcome is stated in advance with its direction")
    for k in ("pool_idx_sha256", "n_ext_real_rows"):
        chk(P[k] == p21["scope"]["protocol"][k], f"protocol.{k} is 0021's")

    # 5. the reader's expectations are keys the runner writes; the fixture is current with the runner in the tree
    fx = json.load(open(f"{REPO}/tests/fixtures/realsearch_runner_shape.json", encoding="utf-8"))
    shape, sel_shape = fx["artifact"], fx["selection"]
    for nm, sealed, blk in (("FIT", r22.FIT, "fit_corpus"), ("EXT", r22.EXT, "ext_corpus"), ("PARTITION", r22.PARTITION, "partition"),
                            ("CORPUS", r22.CORPUS, "corpus")):
        chk(set(sealed) <= set(shape[blk]), f"every key the reader's {nm} compares is one the runner writes"
            + (f" (missing {sorted(set(sealed) - set(shape[blk]))})" if not set(sealed) <= set(shape[blk]) else ""))
    chk(set(r22.SEL_PARTITION) <= set(sel_shape["partition"]), "every key the reader compares in the selection partition is one the runner writes there")
    chk(set(P) == set(shape["roster"]["protocol"]), "the fixture's protocol has this preregistration's key set (the fixture is current)")
    chk(set(shape["roster"]) == set(sel_shape["roster"]) == {"protocol", "heads"}, "the fixture's roster is exactly {protocol, heads} in both files")
    chk(shape["roster_sha256"] == sel_shape["roster_sha256"] == sha(RO) == r22.ROSTER_SHA256,
        "the fixture was captured under the sealed roster (its banked roster_sha256 is the sealed one: the fixture is current)")
    chk(set(shape["fits"]) <= set(P["confirm_order"]) and "repro_m4" in shape["fits"], "the fixture's roles are roles of the sealed order")
    _int = lambda v: isinstance(v, int) and not isinstance(v, bool)  # noqa: E731
    _bad = []
    for _nm, _rec in shape["fits"].items():
        _fam = by_id[_rec["id"]]["family"]; _inf = _rec.get("fit_info")
        if not isinstance(_inf, dict):
            _bad.append(f"{_nm}: fit_info {_inf!r}")
        elif _fam in ("hgb", "logistic") and not _int(_inf.get("n_iter")):
            _bad.append(f"{_nm} ({_fam}): no integer n_iter")
        elif _fam == "tree" and not (_int(_inf.get("depth")) and _int(_inf.get("n_leaves"))):
            _bad.append(f"{_nm} ({_fam}): no integer depth/n_leaves")
        elif _fam == "dummy" and _inf:
            _bad.append(f"{_nm} (dummy): banked {_inf!r}")
        if sorted(_rec["per_family"]) != sorted(r22.FAMILIES + ["ext:" + f for f in r22.EXT_FAMILIES]):
            _bad.append(f"{_nm}: per_family keys")
        if not set(r22.ENV) <= set(_rec.get("environment") or {}):
            _bad.append(f"{_nm}: environment lacks {sorted(set(r22.ENV) - set(_rec.get('environment') or {}))}")
    for _hid, _e in sel_shape["selection"].items():
        for _st in _e["stages"]:
            for _rec in _st["records"]:
                if _rec["status"] == "fit" and sorted(_rec["per_family"]) != sorted(r22.FIT_FAMILIES):
                    _bad.append(f"selection {_hid}/{_rec['id']}: per_family keys {sorted(_rec['per_family'])}")
    chk(not _bad, "the reader's per-record requirements hold against the runner's own banked values" + (f" ({'; '.join(_bad[:3])})" if _bad else ""))
    chk("ledger" in shape and "ledger" in sel_shape, "the runner banks a ledger in both files")
    _src = inspect.getsource(rs)
    _written = set(re.findall(r'partition\["([a-z0-9_]+)"\]', _src)) | set(re.findall(r'"([a-z0-9_]+)": (?:int|bool|_sha|list|\[|\{)', _src[_src.index("partition = {"):_src.index("# Row identity")]))
    _fp_src = inspect.getsource(rs.fit_block_partition)
    _written |= set(re.findall(r'"([a-z0-9_]+)":', _fp_src[_fp_src.index("keys = {"):]))
    chk(_written <= set(shape["partition"]), "every partition key the runner's source writes is in the captured fixture (the fixture is current)"
        + (f" (missing {sorted(_written - set(shape['partition']))})" if not _written <= set(shape["partition"]) else ""))

    # 6. nothing of this run exists yet, and a real run refuses to start on an unfrozen preregistration
    for f in ("realsearch_4096_selection.json", "realsearch_4096.json", "realsearch_4096_scores.json", "realsearch_4096_verdict.json",
              "realsearch_4096_not_run.json"):
        chk(not os.path.exists(f"{REPO}/artifacts/pivot/{f}"), f"artifacts/pivot/{f} does not exist yet")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realsearch_4096_ckpt"), "no checkpoint directory exists yet")
    chain = [json.loads(l) for l in open(f"{REPO}/prereg/chain.jsonl", encoding="utf-8") if l.strip()]
    chk(chain[-1]["id"] == "0021" and len(chain) == 21, "0021 is the chain head (21 entries)")
    chk(pr["reader"] == "tools/readers/realsearch4096_verdict.py" and os.path.exists(reader_path), "the reader exists at the sealed path")
    sm = pr["smoke"]
    chk(sm["ext_corpus"]["arrays"]["X"]["sha256"] != P["ext_corpus"]["arrays"]["X"]["sha256"]
        and sm["fit_corpus"]["arrays"]["X"]["sha256"] != P["fit_corpus"]["arrays"]["X"]["sha256"]
        and sm["ext_corpus"]["npz"].startswith("(scratchpad)") and sm["fit_corpus"]["npz"].startswith("(scratchpad)"),
        "the smoke block names scratchpad corpora whose hashes are not the sealed ones")
    # the probe can never pass the launch check even if this file is run against a frozen preregistration from a shell that
    # exports the sealed thread count: threads are forced to 1 here (0022 pre-freeze review, runner lens, finding 7)
    rc = subprocess.run([sys.executable, f"{REPO}/tools/pivot/run_realsearch.py", "--stage", "select"], capture_output=True, text=True, cwd=REPO,
                        env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    chk(rc.returncode == 3 and "frozen preregistration" in rc.stderr, "a real run refuses to start on an unfrozen preregistration (exit 3)")
    chk(not os.path.exists(f"{REPO}/artifacts/pivot/realsearch_4096_ckpt"), "the refused launch created nothing")

    # 7. the banked mutation report agrees with the coverage map and carries this gate
    rep = json.load(open(f"{REPO}/artifacts/verification/mutation_report.json", encoding="utf-8"))
    cov = json.load(open(f"{REPO}/artifacts/verification/coverage.json", encoding="utf-8"))
    claim = next(c for c in cov["claims"] if c["id"] == "mutations-detected")
    chk(rep["detected"] == rep["total_mutations"] == claim["value"] and rep["survived"] == 0,
        f"the banked mutation report ({rep['detected']}/{rep['total_mutations']}) agrees with the coverage claim ({claim['value']})")
    chk(rep["by_gate"].get("realsearch4096", {}).get("total", 0) >= 70 and rep["by_gate"].get("realsearch4096", {}).get("detected") == rep["by_gate"].get("realsearch4096", {}).get("total"),
        f"the report carries the realsearch4096 gate ({rep['by_gate'].get('realsearch4096')})")

    result = {"schema": "raise-v1/prefreeze_0022/1", "preregistration": f"{pr['id']}-{pr['slug']}", "problems": bad,
              "passed": bad == 0, "reader_sha256_at_check": hashlib.sha256(reader.encode()).hexdigest(),
              "prereg_sha256_at_check": hashlib.sha256(open(f"{REPO}/prereg/0022-realsearch-4096.json", "rb").read()).hexdigest(),
              "holdout": {k: FP[k] for k in ("n_holdout_rows", "n_holdout_chunks", "holdout_rows_per_family")},
              "unsearched_frozen_bar_rows": need_unsearched}
    os.makedirs(f"{REPO}/artifacts/verification", exist_ok=True)
    with open(f"{REPO}/artifacts/verification/prefreeze_0022.json", "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"PRE-FREEZE 0022: {'PASS' if bad == 0 else 'FAIL'} ({bad} problem(s))")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
