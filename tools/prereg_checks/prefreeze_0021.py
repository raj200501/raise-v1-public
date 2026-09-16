#!/usr/bin/env python3
"""Pre-freeze check for preregistration 0021 (run before `tools/prereg.py freeze`; committed with the freeze, result
banked in artifacts/verification/prefreeze_0021.json). Exit 1 on any mismatch, 2 once the preregistration is frozen.

What it checks, and why each one exists:
 1. The reader is exactly what the generator produces from the preregistration and the template - no hand edit.
 2. Every sealed literal in the reader equals the preregistration's (protocol hash, recipes, partition, corpora, clause).
 3. The fit corpus on disk hashes to the sealed arrays, is disjoint from the scored corpora
    by index, by chunk id and by source-chunk hash.
 4. The three fit blocks are RECOMPUTED FROM THE DATA with the runner's own split and permutation, not copied from the
    preregistration - two copies of one wrong literal agree with each other (docs/OPERATING_RULES.md section 4, and the
    0018 null-block defect filed in CORRECTIONS.md 2026-09-10).
 5. The clause arithmetic, the reproduction reference and the chunk layout trace to banked artifacts.
 6. Nothing of this run exists yet: no artifact, no scores, no verdict; the preregistration is unfrozen and 0019 is the
    chain head; the smoke block names scratchpad corpora rather than the sealed ones.
 7. The banked mutation report agrees with the coverage map's claim.
"""
from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
SP = os.environ.get("PREREG_0021_SCRATCH", tempfile.mkdtemp(prefix="prefreeze_0021_"))
bad = 0


def chk(cond, msg):
    global bad
    print(("ok   " if cond else "BAD  ") + msg)
    if not cond:
        bad += 1


def main() -> int:
    global bad
    pr = json.load(open(f"{REPO}/prereg/0021-realfit-4096-rerun.json", encoding="utf-8"))
    if pr.get("frozen"):
        print(f"PRE-FREEZE 0021: the preregistration is frozen ({pr.get('frozen_utc')}); this check runs before a freeze "
              f"only. The result it banked then is artifacts/verification/prefreeze_0021.json.", file=sys.stderr)
        return 2
    S = pr["scope"]; P = S["protocol"]; sp = S["sealed_partition"]
    canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
    sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

    # 1. the reader is the generated file
    gen = os.environ.get("PREREG_0021_GENERATOR")
    reader_path = f"{REPO}/tools/readers/realfit4096_rerun_verdict.py"
    reader = open(reader_path, encoding="utf-8").read()
    if gen and os.path.exists(gen):
        tmp = os.path.join(SP, "regenerated_reader.py")
        rc = subprocess.run([sys.executable, gen, f"{REPO}/prereg/0021-realfit-4096-rerun.json", tmp],
                            capture_output=True, text=True)
        chk(rc.returncode == 0 and open(tmp, encoding="utf-8").read() == reader,
            "the reader is exactly what the generator produces from this preregistration")
    else:
        chk(False, "PREREG_0021_GENERATOR is not set to the generator script; cannot prove the reader was generated")

    # 2. the reader's sealed literals are the preregistration's
    import importlib.util
    spec = importlib.util.spec_from_file_location("r20", reader_path)
    r20 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r20)
    chk(r20.PREREG == f"{pr['id']}-{pr['slug']}", "the reader is frozen for this preregistration")
    chk(r20.PROTOCOL == P and r20.PROTOCOL_SHA256 == sha(P) == S["sealed_hashes"]["protocol_sha256"],
        "the reader's PROTOCOL is the sealed protocol and hashes to the sealed hash")
    chk(r20.RECIPES == S["recipes"] and r20.RECIPES_SHA256 == sha(S["recipes"]) == S["sealed_hashes"]["recipes_sha256"],
        "the reader's recipes are 0018's three, hash for hash")
    chk(r20.MIN_CORRECT_REAL == P["min_correct_real"] and r20.N_REAL == P["n_ext_real_rows"]
        and r20.BAR == P["bar"]["real_model_correct_over_n_real_minus_chance"],
        f"the reader's clause is {P['min_correct_real']} of {P['n_ext_real_rows']} at chance + "
        f"{P['bar']['real_model_correct_over_n_real_minus_chance']}")
    chk(r20.REPRO_REFERENCE == P["reference_top1"]["repro"] and r20.REPRO_TOLERANCE == P["reproduction_tolerance"]
        and r20.NULL_TOLERANCE == P["null_tolerance"], "the reader's control references and tolerances are the sealed ones")
    chk(r20.ORDER == P["order"] and r20.RECIPE_OF == P["recipe_of"], "the reader's arm order and recipe map are sealed")
    # NOT just the array hashes. 0021's pre-freeze review found four fit_corpus values sealed from the manifest's
    # BUILT counts where the runner measures the with-rows counts, and this check compared two copies of the same
    # literal for exactly those fields. Both blocks are now rebuilt by CALLING the runner's own corpus_block().
    from run_realfit import corpus_block, _array_sha

    def _runner_block(rel, labels):
        d = np.load(f"{REPO}/{rel}", allow_pickle=False)
        names = [str(x) for x in d["families"]]; fam = np.array(names)[d["fam"]]
        h = {n: dict(zip(("sha256", "shape", "dtype"), _array_sha(f"{REPO}/{rel}", n))) for n in ("X", "y", "g", "fam")}
        return corpus_block(rel, h, d["y"], d["g"], fam, names, labels=labels)
    rb_fit = _runner_block("data/pivot/realfit_c4096.npz", True)
    rb_ext = _runner_block("data/pivot/ext_c4096.npz", False)
    chk(r20.FIT == rb_fit, "the reader's FIT block is what the runner banks, key for key, from the npz on disk")
    chk(r20.EXT == rb_ext, "the reader's EXT block is what the runner banks, key for key, from the npz on disk")
    chk(P["fit_corpus"] == rb_fit and P["ext_corpus"] == rb_ext,
        "the sealed corpus blocks are the runner's own, not the manifest's built counts")

    # (b) every key the reader compares must be a key the runner actually writes, taken from the captured fixture
    shape = json.load(open(f"{REPO}/tests/fixtures/realfit_runner_shape.json", encoding="utf-8"))["artifact"]
    for nm, sealed, blk in (("FIT", r20.FIT, "fit_corpus"), ("EXT", r20.EXT, "ext_corpus"),
                            ("PARTITION", r20.PARTITION, "partition"), ("CORPUS", r20.CORPUS, "corpus")):
        chk(set(sealed) <= set(shape[blk]),
            f"every key the reader's {nm} compares is one the runner writes"
            + (f" (missing {sorted(set(sealed) - set(shape[blk]))})" if not set(sealed) <= set(shape[blk]) else ""))
    chk(set(r20.ORDER) == set(shape["fits"]), "the reader's arms are the arms the runner banks")
    # ... and one level deeper, at the VALUES, not only the key sets. The reader demanded an integer fit_info.n_iter
    # of all eleven arms; sklearn's DummyClassifier and DecisionTreeClassifier produce none, so an honest run voided
    # on four clauses behind a green gate (0021 pre-freeze review, instrument lens, findings H1 and H3).
    _int = lambda v: isinstance(v, int) and not isinstance(v, bool)  # noqa: E731
    _bad = []
    for _nm in r20.ORDER:
        _rec = shape["fits"][_nm]; _fam = r20.RECIPES[r20.RECIPE_OF[_nm]]["family"]
        _inf = _rec.get("fit_info")
        if not isinstance(_inf, dict):
            _bad.append(f"{_nm}: fit_info {_inf!r}")
        elif _fam in ("hgb", "logistic") and not _int(_inf.get("n_iter")):
            _bad.append(f"{_nm} ({_fam}): no integer n_iter, banked {_inf!r}")
        elif _fam == "tree" and not (_int(_inf.get("depth")) and _int(_inf.get("n_leaves"))):
            _bad.append(f"{_nm} ({_fam}): no integer depth/n_leaves, banked {_inf!r}")
        elif _fam == "dummy" and _inf:
            _bad.append(f"{_nm} (dummy): banked {_inf!r}, expected {{}}")
        if not set(r20.ENV) <= set(_rec.get("environment") or {}):
            _bad.append(f"{_nm}: record environment lacks {sorted(set(r20.ENV) - set(_rec.get('environment') or {}))}")
    chk(not _bad, "the reader's per-record requirements hold against the runner's own banked values"
                  + (f" ({'; '.join(_bad[:3])})" if _bad else ""))
    chk("ledger" in shape, "the runner banks a ledger, which the reader requires one completion per arm from")

    # (c) the fixture is CURRENT: captured from the runner in the tree, not an older one
    import inspect as _inspect
    import run_realfit as _rr
    _src = _inspect.getsource(_rr)
    _written = set(re.findall(r'partition\["([a-z0-9_]+)"\]', _src))
    _blk = _src[_src.index("partition = {"):]
    _written |= set(re.findall(r'"([a-z0-9_]+)":', _blk[:_blk.index("\n\n")]))
    chk(_written <= set(shape["partition"]),
        "the captured runner-shape fixture is current with the runner"
        + (f" (runner writes {sorted(_written - set(shape['partition']))} which the fixture lacks)"
           if not _written <= set(shape["partition"]) else ""))
    chk(r20.PARTITION["fit_idx_sha256"] == sp["fit_block"]["idx_sha256"]
        and r20.PARTITION["fit_sorted_sha256"] == sp["fit_block"]["sorted_sha256"]
        and r20.PARTITION["repro_sorted_sha256"] == sp["repro_block"]["sorted_sha256"]
        and r20.PARTITION["matched_sorted_sha256"] == sp["matched_block"]["sorted_sha256"]
        and r20.PARTITION["chunk_matched_sorted_sha256"] == sp["chunk_matched_block"]["sorted_sha256"]
        and r20.PARTITION["eval_g_sha256"] == sp["eval"]["eval_g_sha256"],
        "the reader's four fit-block hashes and the evaluation g digest are the sealed ones")
    chk(r20.EXT_CHUNK_IDS == S["ext_chunk_layout"]["chunk_ids_with_rows"]
        and r20.EXT_ROWS_PER_CHUNK == S["ext_chunk_layout"]["rows_per_chunk"], "the reader carries the sealed chunk layout")

    # 3. the fit corpus on disk is the sealed one and is disjoint from everything scored
    for args, label in (( ["--check"], "fit corpus on disk hashes to its banked manifest"),
                        (["--disjoint"], "fit and sealed corpora share no chunk index, chunk id or source-chunk hash")):
        rc = subprocess.run([sys.executable, "tools/pivot/corpus_realfit.py", *args], cwd=REPO, capture_output=True, text=True)
        chk(rc.returncode == 0, label + (f" ({rc.stdout.strip().splitlines()[-1] if rc.stdout.strip() else rc.returncode})"
                                         if rc.returncode else ""))
    man = json.load(open(f"{REPO}/artifacts/pivot/realfit_corpus_manifest.json", encoding="utf-8"))
    chk({k: {kk: v[kk] for kk in ("sha256", "shape", "dtype")} for k, v in man["arrays"].items()} == P["fit_corpus"]["arrays"],
        "the sealed fit_corpus arrays are the manifest's")
    chk(man["n_rows"] == P["fit_corpus"]["n_rows"] == sp["fit_block"]["n_rows"] == P["matched_rows"],
        f"the fit corpus's row count {man['n_rows']} is the sealed one and the matched arm's budget")

    # 4. the three fit blocks, recomputed from the data with the runner's own code
    from run_recipe_search import grouped_split, _sha
    with zipfile.ZipFile(f"{REPO}/data/pivot/full_c4096.npz") as zf:
        y = np.load(io.BytesIO(zf.read("y.npy"))); g = np.load(io.BytesIO(zf.read("g.npy")))
    ev, tr, _ = grouped_split(y, g, P["seed"], P["eval_frac"], P["top_rung"])
    chk(_sha(tr) == P["pool_idx_sha256"] == sp["pool"]["pool_idx_sha256"], "the recomputed pool is 0003's sealed pool")
    chk(_sha(ev) == sp["eval"]["eval_idx_sha256"], "the recomputed evaluation set is 0003's sealed evaluation set")
    chk(_sha(np.sort(tr[:P["repro_rows"]]).astype(np.int64)) == sp["repro_block"]["sorted_sha256"]
        and _sha(tr[:P["repro_rows"]]) == sp["repro_block"]["idx_sha256"],
        f"the recomputed {P['repro_rows']}-row reproduction block is the sealed one")
    chk(_sha(np.sort(tr[:P["matched_rows"]]).astype(np.int64)) == sp["matched_block"]["sorted_sha256"]
        and _sha(tr[:P["matched_rows"]]) == sp["matched_block"]["idx_sha256"],
        f"the recomputed {P['matched_rows']}-row builder-matched block is the sealed one")
    perm = np.random.default_rng(P["seed"]).permutation(man["n_rows"])
    chk(_sha(perm) == sp["fit_block"]["idx_sha256"] and _sha(np.sort(perm).astype(np.int64)) == sp["fit_block"]["sorted_sha256"],
        "the recomputed fit-row permutation is the sealed one")

    # 4b. THE CLAUSE THAT REFUSED 0020. The sealed expected collision counts are recomputed from the data here, with
    # the runner's own blocks and the runner's own digest, so the preregistration cannot seal a number nobody measured.
    # 0020 sealed a blanket zero for all four blocks and refused at launch on repro 8 and matched 2.
    import importlib.util as _ilu
    _sp = _ilu.spec_from_file_location("_rr", f"{REPO}/tools/pivot/run_realfit.py")
    _rr = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_rr)
    dx = np.load(f"{REPO}/data/pivot/ext_c4096.npz", allow_pickle=False)
    Xx = dx["X"]
    Xc = _rr.npz_memmap(f"{REPO}/data/pivot/full_c4096.npz", "X"); ncols = Xc.shape[1]
    _H = lambda r: hashlib.blake2b(np.ascontiguousarray(r, dtype=np.float32).tobytes(), digest_size=16).digest()
    scored = {_H(Xx[i]) for i in range(len(Xx))}
    _evs = np.sort(ev)
    for i in range(0, len(_evs), 20000):
        _b = np.ascontiguousarray(Xc[_evs[i:i + 20000], :ncols], dtype=np.float32)
        for j in range(len(_b)):
            scored.add(_H(_b[j]))

    def _hits(rows):
        o = np.sort(np.asarray(rows)); n = 0
        for i in range(0, len(o), 20000):
            _b = np.ascontiguousarray(Xc[o[i:i + 20000], :ncols], dtype=np.float32)
            n += sum(1 for j in range(len(_b)) if _H(_b[j]) in scored)
        return int(n)
    _gp = g[tr]; _seen, _ord = set(), []
    for _v in _gp:
        _v = int(_v)
        if _v not in _seen:
            _seen.add(_v); _ord.append(_v)
            if len(_ord) >= P["chunk_matched_chunks"]:
                break
    _cm = tr[np.fromiter((int(v) in set(_ord) for v in _gp), bool, len(tr))]
    _Xr = np.load(f"{REPO}/data/pivot/realfit_c4096.npz", allow_pickle=False)["X"]
    measured = {"fit_block": int(sum(1 for i in range(len(_Xr)) if _H(_Xr[i]) in scored)),
                "repro_block": _hits(tr[:P["repro_rows"]]),
                "matched_block": _hits(tr[:P["matched_rows"]]),
                "chunk_matched_block": _hits(_cm)}
    exp = P["expected_rows_identical_to_a_scored_row"]
    chk(measured == exp, f"the sealed expected collision counts are what the data gives: measured {measured}, "
                         f"sealed {exp}")
    chk(exp["fit_block"] == 0, "the clause's own corpus shares no feature row with anything scored")
    chk(r20.EXPECTED_COLLISIONS == exp, "the reader carries the sealed expected collision counts")
    dupman = json.load(open(f"{REPO}/artifacts/pivot/builder_duplicate_chunks.json", encoding="utf-8"))
    chk(sum(p["collisions_repro_block_vs_eval"] for p in dupman["duplicate_chunk_pairs"]) == exp["repro_block"]
        and sum(p["collisions_matched_block_vs_eval"] for p in dupman["duplicate_chunk_pairs"]) == exp["matched_block"],
        "the sealed counts are accounted for, pair by pair, by the banked duplicate-chunk table")

    # 5. the clause arithmetic and the references trace to banked artifacts
    import math
    ext_man = json.load(open(f"{REPO}/artifacts/pivot/ext_corpus_manifest.json", encoding="utf-8"))
    p18 = json.load(open(f"{REPO}/prereg/0018-oob-4096.json", encoding="utf-8"))["scope"]
    curve = json.load(open(f"{REPO}/artifacts/pivot/deflate_curve.json", encoding="utf-8"))
    fdc = json.load(open(f"{REPO}/artifacts/pivot/fdc_4096.json", encoding="utf-8"))
    v19 = json.load(open(f"{REPO}/artifacts/pivot/oob_4096_reread_verdict.json", encoding="utf-8"))
    n_real = sum(ext_man["per_family"][f]["n_rows"] for f in ext_man["real_families"])
    chk(n_real == P["n_ext_real_rows"] == 38452, f"the five real families carry {n_real} rows, the sealed count")
    chk(P["min_correct_real"] == math.ceil(n_real * (1 / 26 + P["bar"]["real_model_correct_over_n_real_minus_chance"]) - 1e-9)
        == p18["protocol"]["min_correct_real"], "the clause count is the arithmetic and is 0018's, so the two are comparable")
    rung = {r["n_units"]: r["accuracy"] for r in curve["rungs"]}
    chk(P["reference_top1"]["repro"] == rung[P["repro_rows"]] == fdc.get("incumbent_100k_refit_top1"),
        f"the reproduction reference {P['reference_top1']['repro']} is 0003's banked rung and 0016's reproduction of it")
    chk(r20.OOB_MODEL_REAL_CORRECT == v19["ext_real_correct_model"] and r20.OOB_MODEL_REAL_TOP1 == v19["ext_real_top1_model"],
        "the 0018 comparison literals in the reader are 0019's banked readings")
    chk(S["ext_chunk_layout"]["chunk_ids_with_rows"] == ext_man["chunk_ids_with_rows"]
        == p18["ext_chunk_layout"]["chunk_ids_with_rows"], "the sealed chunk layout is the manifest's and 0018's")

    # 6. nothing of this run exists yet
    for f in ("realfit_4096_rerun.json", "realfit_4096_rerun_scores.json", "realfit_4096_rerun_verdict.json", "realfit_4096_rerun_not_run.json"):
        chk(not os.path.exists(f"{REPO}/artifacts/pivot/{f}"), f"no {f} exists before the freeze")
    chk(pr.get("frozen") is False and pr["reader"] == "tools/readers/realfit4096_rerun_verdict.py", "prereg unfrozen, reader named")
    chain = [json.loads(l) for l in open(f"{REPO}/prereg/chain.jsonl", encoding="utf-8") if l.strip()]
    chk(chain[-1]["seq"] == 20 and chain[-1]["id"] == "0020", "the chain head is 0020; this freeze is seq 21")
    chk(subprocess.run([sys.executable, "tools/prereg.py", "verify"], cwd=REPO, capture_output=True).returncode == 0,
        "the chain verifies")
    smoke = pr.get("smoke") or {}
    # On absent keys the previous form evaluated None != <hash> -> True and could never fail, which is what
    # OPERATING_RULES section 4 forbids; and with no smoke corpora at all the documented smoke invocation could not
    # run against the committed preregistration.
    _sfx = (smoke.get("fit_corpus") or {}).get("arrays", {}).get("X", {}).get("sha256")
    _sex = (smoke.get("ext_corpus") or {}).get("arrays", {}).get("X", {}).get("sha256")
    chk(bool(_sfx) and bool(_sex) and _sfx != P["fit_corpus"]["arrays"]["X"]["sha256"]
        and _sex != P["ext_corpus"]["arrays"]["X"]["sha256"],
        "the smoke block names scratchpad corpora - present, and not the sealed ones")

    # the sealed-set ordinal equals one plus the number of predecessors it lists (CORRECTIONS, 2026-09-10)
    _d = S["sealed_set_disclosure"]
    _ord = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
            "ninth": 9, "tenth": 10}
    _said = next((v for k, v in _ord.items() if f"the {k} preregistration" in _d), None)
    _listed = len(re.findall(r"00\d\d ", _d[_d.index("("):_d.index(")")])) if "(" in _d else 0
    chk(_said is not None and _said == _listed + 1,
        f"the sealed-set ordinal ({_said}) is one plus the {_listed} predecessors it lists")
    chk("FILL IN" not in json.dumps(pr), "no FILL IN left")

    # 7. the banked mutation report agrees with the coverage map
    mr = json.load(open(f"{REPO}/artifacts/verification/mutation_report.json", encoding="utf-8"))
    cov = json.load(open(f"{REPO}/artifacts/verification/coverage.json", encoding="utf-8"))
    claimed = next(c["value"] for c in cov["claims"] if c["id"] == "mutations-detected")
    chk(mr["total_mutations"] == mr["detected"] == claimed and mr["survived"] == 0,
        f"mutation report {mr['total_mutations']}/{mr['detected']} == coverage claim {claimed}, 0 survived")
    chk("realfit4096" in mr["by_gate"], "the realfit4096 gate is in the banked mutation report")

    res = {"schema": "raise-v1/prefreeze_check/1", "preregistration": "0021-realfit-4096-rerun",
           "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "reader_sha256_checked": hashlib.sha256(reader.encode()).hexdigest(),
           "prereg_sha256_checked": hashlib.sha256(open(f"{REPO}/prereg/0021-realfit-4096-rerun.json", "rb").read()).hexdigest(),
           "fit_corpus_X_sha256": P["fit_corpus"]["arrays"]["X"]["sha256"],
           "mutation_report_total": mr["total_mutations"], "realfit4096_cases": mr["by_gate"].get("realfit4096"),
           "checks_failed": bad, "result": "PASS" if bad == 0 else f"FAIL ({bad})"}
    os.makedirs(f"{REPO}/artifacts/verification", exist_ok=True)
    with open(f"{REPO}/artifacts/verification/prefreeze_0021.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"\nresult banked in artifacts/verification/prefreeze_0021.json at {res['utc']}")
    print("PRE-FREEZE 0021:", res["result"])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
