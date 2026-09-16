#!/usr/bin/env python3
"""Pre-freeze check for preregistration 0020 (run before `tools/prereg.py freeze`; committed with the freeze, result
banked in artifacts/verification/prefreeze_0020.json). Exit 1 on any mismatch, 2 once the preregistration is frozen.

What it checks, and why each one exists:
 1. The reader is exactly what the generator produces from the preregistration and the template - no hand edit.
 2. Every sealed literal in the reader equals the preregistration's (protocol hash, recipes, partition, corpora, clause).
 3. The fit corpus on disk hashes to the sealed arrays, rebuilds identically, and is disjoint from the scored corpora
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
import subprocess
import sys
import tempfile
import zipfile

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
SP = os.environ.get("PREREG_0020_SCRATCH", tempfile.mkdtemp(prefix="prefreeze_0020_"))
bad = 0


def chk(cond, msg):
    global bad
    print(("ok   " if cond else "BAD  ") + msg)
    if not cond:
        bad += 1


def main() -> int:
    global bad
    pr = json.load(open(f"{REPO}/prereg/0020-realfit-4096.json", encoding="utf-8"))
    if pr.get("frozen"):
        print(f"PRE-FREEZE 0020: the preregistration is frozen ({pr.get('frozen_utc')}); this check runs before a freeze "
              f"only. The result it banked then is artifacts/verification/prefreeze_0020.json.", file=sys.stderr)
        return 2
    S = pr["scope"]; P = S["protocol"]; sp = S["sealed_partition"]
    canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
    sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

    # 1. the reader is the generated file
    gen = os.environ.get("PREREG_0020_GENERATOR")
    reader_path = f"{REPO}/tools/readers/realfit4096_verdict.py"
    reader = open(reader_path, encoding="utf-8").read()
    if gen and os.path.exists(gen):
        tmp = os.path.join(SP, "regenerated_reader.py")
        rc = subprocess.run([sys.executable, gen, f"{REPO}/prereg/0020-realfit-4096.json", tmp],
                            capture_output=True, text=True)
        chk(rc.returncode == 0 and open(tmp, encoding="utf-8").read() == reader,
            "the reader is exactly what the generator produces from this preregistration")
    else:
        chk(False, "PREREG_0020_GENERATOR is not set to the generator script; cannot prove the reader was generated")

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
    chk(r20.FIT["arrays"] == P["fit_corpus"]["arrays"] and r20.EXT["arrays"] == P["ext_corpus"]["arrays"],
        "the reader's corpus array hashes are the sealed ones")
    chk(r20.PARTITION["fit_idx_sha256"] == sp["fit_block"]["idx_sha256"]
        and r20.PARTITION["fit_sorted_sha256"] == sp["fit_block"]["sorted_sha256"]
        and r20.PARTITION["repro_sorted_sha256"] == sp["repro_block"]["sorted_sha256"]
        and r20.PARTITION["matched_sorted_sha256"] == sp["matched_block"]["sorted_sha256"],
        "the reader's three fit-block hashes are the sealed ones")
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
    for f in ("realfit_4096.json", "realfit_4096_scores.json", "realfit_4096_verdict.json", "realfit_4096_not_run.json"):
        chk(not os.path.exists(f"{REPO}/artifacts/pivot/{f}"), f"no {f} exists before the freeze")
    chk(pr.get("frozen") is False and pr["reader"] == "tools/readers/realfit4096_verdict.py", "prereg unfrozen, reader named")
    chain = [json.loads(l) for l in open(f"{REPO}/prereg/chain.jsonl", encoding="utf-8") if l.strip()]
    chk(chain[-1]["seq"] == 19 and chain[-1]["id"] == "0019", "the chain head is 0019; this freeze is seq 20")
    chk(subprocess.run([sys.executable, "tools/prereg.py", "verify"], cwd=REPO, capture_output=True).returncode == 0,
        "the chain verifies")
    smoke = pr.get("smoke") or {}
    chk((smoke.get("fit_corpus") or {}).get("arrays", {}).get("X", {}).get("sha256") != P["fit_corpus"]["arrays"]["X"]["sha256"]
        and (smoke.get("ext_corpus") or {}).get("arrays", {}).get("X", {}).get("sha256")
        != P["ext_corpus"]["arrays"]["X"]["sha256"], "the smoke block names scratchpad corpora, not the sealed ones")
    chk("FILL IN" not in json.dumps(pr), "no FILL IN left")

    # 7. the banked mutation report agrees with the coverage map
    mr = json.load(open(f"{REPO}/artifacts/verification/mutation_report.json", encoding="utf-8"))
    cov = json.load(open(f"{REPO}/artifacts/verification/coverage.json", encoding="utf-8"))
    claimed = next(c["value"] for c in cov["claims"] if c["id"] == "mutations-detected")
    chk(mr["total_mutations"] == mr["detected"] == claimed and mr["survived"] == 0,
        f"mutation report {mr['total_mutations']}/{mr['detected']} == coverage claim {claimed}, 0 survived")
    chk("realfit4096" in mr["by_gate"], "the realfit4096 gate is in the banked mutation report")

    res = {"schema": "raise-v1/prefreeze_check/1", "preregistration": "0020-realfit-4096",
           "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "reader_sha256_checked": hashlib.sha256(reader.encode()).hexdigest(),
           "prereg_sha256_checked": hashlib.sha256(open(f"{REPO}/prereg/0020-realfit-4096.json", "rb").read()).hexdigest(),
           "fit_corpus_X_sha256": P["fit_corpus"]["arrays"]["X"]["sha256"],
           "mutation_report_total": mr["total_mutations"], "realfit4096_cases": mr["by_gate"].get("realfit4096"),
           "checks_failed": bad, "result": "PASS" if bad == 0 else f"FAIL ({bad})"}
    os.makedirs(f"{REPO}/artifacts/verification", exist_ok=True)
    with open(f"{REPO}/artifacts/verification/prefreeze_0020.json", "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, sort_keys=True); fh.write("\n")
    print(f"\nresult banked in artifacts/verification/prefreeze_0020.json at {res['utc']}")
    print("PRE-FREEZE 0020:", res["result"])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
