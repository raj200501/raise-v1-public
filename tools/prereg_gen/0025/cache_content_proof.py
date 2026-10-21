#!/usr/bin/env python3
"""Prove that a builder cache's sealed EVALUATION ROWS carry the banked FEATURE CONTENT, by refitting banked fits.

Why. data/pivot/full_c4096.npz is rebuilt on a fresh container and reordered so that the sealed evaluation rows
(grouped_split(y, g, seed, eval_frac, top_rung) with 0025's scope.curve.protocol constants) come out in the banked
order. The evaluation y and g hashes prove that ORDER; they say nothing about the FEATURES, and no banked number is a
hash of the evaluation rows' features. What IS banked: the per-example 0/1 correctness vectors of deterministic fits -
0021's recipes on 0021's fit block (rung 4 of 0023/0024/0025, row for row) - over [the sealed evaluation rows] +
[the extension corpus], and those vectors agree hash for hash across 0021, 0022, 0023 and 0024. So this script refits
the same recipes on the same block with the repository's OWN code (run_recipe_search.run_fit -> fit_one ->
build_estimator / InPlaceScaled, Block / fill_f64, fill_f32, predict_chunked), scores them on [THIS cache's
evaluation rows] + [ext_c4096.npz] laid out exactly as the runners lay out their scoring set (one float32 array, the
same 50000-row prediction chunks), and compares the vectors with the banked ones.

How to read the result.
  * The EXTENSION part is the CONTROL: those rows are sealed bytes (their array hashes are checked here), so an
    identical extension part says this environment and this fitting path reproduce the banked fit.
  * The EVALUATION part is the TEST: with the fit reproduced, a differing evaluation row means that row's features
    differ from the banked ones (its label and position are excluded first by the y/g checks).
  * L3 (standardised logistic) reads all 1108 features of every row through a dense linear map, so an identical L3
    evaluation part is the strong statement: a content change would have to leave the argmax of all 260000 rows
    untouched to escape it. B-feat1 reads one feature and D1 at most seven: cheap early warnings. M4 is optional
    (minutes). Each full vector's sha256 is compared with the per_example_sha256 its run artifact banked.

Usage
    OMP_NUM_THREADS=3 python3 -B tools/prereg_gen/0025/cache_content_proof.py data/pivot/full_c4096.npz [--with-m4]
    OMP_NUM_THREADS=3 python3 -B tools/prereg_gen/0025/cache_content_proof.py --ext-only        # before the cache exists: control part only
    OMP_NUM_THREADS=3 python3 -B tools/prereg_gen/0025/cache_content_proof.py CACHE --check-only  # every check, no fit

Threads come from OMP_NUM_THREADS (3 if unset - every banked run used 3) and are copied to OPENBLAS_NUM_THREADS and
MKL_NUM_THREADS before numpy loads (run_recipe_search.environment() reports threads only when all three agree); the
process renices itself to 10, the banked runs' nice. Every corpus is memory-mapped (npzmap.npz_memmap); the one
materialised array is the float32 scoring set (1.42 GB), as in the runners. Expected peak anonymous RSS is about
3.3 GB (the L3 scoring transient); it is sampled and reported. Nothing is written under the repository by default:
bytecode writing is off, run_fit's throwaway checkpoint store is refused there, and the report goes there only with
--allow-repo-out (tools/prereg_gen/0025/amend_cache_0025.py reads artifacts/verification/cache_rebuild_0025.json and
requires its top-level "passed": true, which only a full-mode run that includes L3, hashes the cache and finds every
vector identical can set).

Exit status: 0 every compared part identical; 1 a compared part differs; 3 refused (a sealed hash, the evaluation
order, a banked file's integrity or the environment).
"""
from __future__ import annotations

import os
import sys

sys.dont_write_bytecode = True        # importing the repository's modules must never write its __pycache__

_THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
BANKED_THREADS = 3
BANKED_NICE = 10


def _pin_threads():
    """Thread count from OMP_NUM_THREADS, copied to the BLAS variables. Must run before numpy is imported."""
    notes = []
    omp = os.environ.get("OMP_NUM_THREADS")
    if not (omp and omp.isdigit() and int(omp) > 0):
        notes.append(f"OMP_NUM_THREADS was {omp!r}; set to {BANKED_THREADS}, the value every banked run used")
        omp = str(BANKED_THREADS)
    for k in _THREAD_VARS:
        if os.environ.get(k) not in (None, omp):
            notes.append(f"{k} was {os.environ.get(k)!r}; set to OMP_NUM_THREADS={omp}")
        os.environ[k] = omp
    return int(omp), notes


THREADS, THREAD_NOTES = _pin_threads()

import argparse  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import resource  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import zipfile  # noqa: E402

# scratch outside the repository: the report and run_fit's throwaway checkpoint store never land in the tree by default
SCRIPT_DIR = os.environ.get("RAISE_SCRATCH") or __import__("tempfile").gettempdir()
DEFAULT_REPO = os.environ.get("RAISE_REPO", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
ALLOWED_ENV = {"python": ("3.11.15", "3.11.17"), "numpy": ("2.4.6",), "sklearn": ("1.9.0",), "scipy": ("1.17.1",)}

ROLE_ORDER = ["B-feat1", "D1", "L3", "M4"]          # cheapest first
# recipe_0021: the key in prereg 0021 scope.recipes; curve: the key in 0024/0025 scope.curve.recipes (cross-checked);
# banked: the per-example key of the SAME fit (0021's recipe on 0021's fit block) in each banked scores file.
ROLE_SPEC = {
    "B-feat1": {"recipe_0021": "floor_feat1", "curve": {"0025": "floor_feat1"},
                "banked": {"0021": "floor_feat1", "0022": "best_single_feat"}},
    "D1": {"recipe_0021": "floor_tree3", "curve": {"0024": "depth3_tree", "0025": "depth3_tree"},
           "banked": {"0021": "floor_tree3", "0024": "r4_depth3_tree", "0023": "r4_depth3_tree", "0022": "repro_d1"}},
    "L3": {"recipe_0021": "logistic_l3", "curve": {"0024": "logistic", "0025": "logistic"},
           "banked": {"0021": "real_logistic", "0024": "r4_logistic", "0023": "r4_logistic", "0022": "repro_l3"}},
    "M4": {"recipe_0021": "model", "curve": {"0024": "model", "0025": "model"},
           "banked": {"0021": "real_model", "0024": "r4_model", "0023": "r4_model", "0022": "repro_m4"}},
}
SOURCES = {   # run artifact (fits[key].per_example_sha256), scores file (per_example[key])
    "0021": ("artifacts/pivot/realfit_4096_rerun.json", "artifacts/pivot/realfit_4096_rerun_scores.json"),
    "0022": ("artifacts/pivot/realsearch_4096.json", "artifacts/pivot/realsearch_4096_scores.json"),
    "0023": ("artifacts/pivot/realcurve_4096.json", "artifacts/pivot/realcurve_4096_scores.json"),
    "0024": ("artifacts/pivot/realcurve2_4096.json", "artifacts/pivot/realcurve2_4096_scores.json"),
}
PREREGS = {"0021": "prereg/0021-realfit-4096-rerun.json", "0024": "prereg/0024-realcurve2-4096.json",
           "0025": "prereg/0025-realcurve3-4096.json"}


class Refuse(Exception):
    pass


# --------------------------------------------------------------------------------------------- small utilities
def _proc_status_gb(field):
    try:
        with open("/proc/self/status") as fh:
            for ln in fh:
                if ln.startswith(field + ":"):
                    return int(ln.split()[1]) / 1e6
    except OSError:
        pass
    return float("nan")


class PeakRss:
    """Samples anonymous RSS (RssAnon: what a container's memory ceiling counts) every `interval` seconds."""

    def __init__(self, interval=0.2):
        self.interval, self.peak, self.where = interval, 0.0, "start"
        self.phase = "start"
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def sample(self):
        v = _proc_status_gb("RssAnon")
        if v == v and v > self.peak:
            self.peak, self.where = v, self.phase
        return v

    def _run(self):
        while not self._stop.wait(self.interval):
            self.sample()

    def stop(self):
        self._stop.set(); self.sample()


def _under(path, root):
    path, root = os.path.realpath(path), os.path.realpath(root)
    return path == root or path.startswith(root + os.sep)


def _utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _say(msg):
    print(msg, flush=True)


def _write_json(path, doc):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True); fh.write("\n")
    os.replace(tmp, path)


def _git(repo, *a):
    try:
        r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def module_provenance(repo, mods):
    """sha256 and git blob id of every repository module the fits run through, against HEAD (read-only git)."""
    out = {}
    for m in mods:
        path = os.path.abspath(m.__file__); rel = os.path.relpath(path, repo)
        data = open(path, "rb").read()
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        head = _git(repo, "rev-parse", f"HEAD:{rel}")
        out[rel] = {"sha256": hashlib.sha256(data).hexdigest(), "git_blob": blob, "head_blob": head,
                    "unmodified_vs_HEAD": (blob == head) if head else None}
    return out


# --------------------------------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cache", nargs="?", help="the builder cache (uncompressed .npz with X, y, g); omitted with --ext-only")
    ap.add_argument("--ext-only", action="store_true",
                    help="no cache: the evaluation slots of the scoring set are zero rows (same geometry), and only the "
                         "extension part is compared - tests the environment and the fitting path")
    ap.add_argument("--check-only", action="store_true", help="every sealed-hash, order and integrity check; no fit")
    ap.add_argument("--roles", default="B-feat1,D1,L3", help=f"comma list from {ROLE_ORDER}; run in cheapness order")
    ap.add_argument("--with-m4", action="store_true", help="add M4 (about 5-6 minutes of fit at 3 threads, plus scoring)")
    ap.add_argument("--banked", default="0021,0024",
                    help=f"banked sources to compare with, from {sorted(SOURCES)} (0022 and 0023 bank the same vectors)")
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--ext", default=None, help="default: REPO/data/pivot/ext_c4096.npz")
    ap.add_argument("--realfit", default=None, help="default: REPO/data/pivot/realfit_c4096.npz")
    ap.add_argument("--out", default=os.path.join(SCRIPT_DIR, "cache_content_proof_report.json"))
    ap.add_argument("--workdir-root", default=SCRIPT_DIR, help="where run_fit's throwaway checkpoint store is created")
    ap.add_argument("--keep-workdir", action="store_true")
    ap.add_argument("--nice", type=int, default=BANKED_NICE)
    ap.add_argument("--no-hash-cache", action="store_true",
                    help="skip hashing the whole cache X (about 5.8 GB read). The hash binds the proof to the cache file, "
                         "so a report made without it never has passed=true")
    ap.add_argument("--allow-env-mismatch", action="store_true",
                    help="run even if threads, nice or library versions differ from the banked runs' (recorded)")
    ap.add_argument("--allow-repo-out", action="store_true",
                    help="permit --out under the repository (e.g. artifacts/verification/cache_rebuild_0025.json, which "
                         "tools/prereg_gen/0025/amend_cache_0025.py reads); the checkpoint store is never put there")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    ext_path = os.path.abspath(args.ext or os.path.join(repo, "data", "pivot", "ext_c4096.npz"))
    realfit_path = os.path.abspath(args.realfit or os.path.join(repo, "data", "pivot", "realfit_c4096.npz"))
    if args.ext_only and args.cache:
        ap.error("--ext-only takes no cache argument")
    if not args.ext_only and not args.cache:
        ap.error("a cache path is required (or --ext-only)")
    if _under(args.workdir_root, repo):
        ap.error(f"--workdir-root {args.workdir_root} is under the repository {repo}; run_fit's store never goes there")
    if _under(args.out, repo) and not args.allow_repo_out:
        ap.error(f"--out {args.out} is under the repository {repo}; pass --allow-repo-out to write the report there")
    roles = [r.strip() for r in args.roles.split(",") if r.strip()]
    if args.with_m4 and "M4" not in roles:
        roles.append("M4")
    bad = [r for r in roles if r not in ROLE_SPEC]
    if bad:
        ap.error(f"unknown roles {bad}; choose from {ROLE_ORDER}")
    roles = [r for r in ROLE_ORDER if r in roles]
    sources = [s.strip() for s in args.banked.split(",") if s.strip()]
    if not sources or any(s not in SOURCES for s in sources):
        ap.error(f"--banked must name sources from {sorted(SOURCES)}")
    mode = "ext_only" if args.ext_only else "full"

    # nice before any work; the banked runs ran at nice 10
    cur = os.nice(0)
    if cur < args.nice:
        os.nice(args.nice - cur)

    t_all = time.perf_counter()
    mem = PeakRss()
    report = {"schema": "cache_content_proof/1", "started_utc": _utc(), "mode": mode, "roles_requested": roles,
              "banked_sources": sources, "cache": os.path.abspath(args.cache) if args.cache else None,
              "ext": ext_path, "realfit": realfit_path, "repo": repo, "thread_notes": THREAD_NOTES,
              "argv": sys.argv[1:], "proof_script": os.path.abspath(__file__),
              "proof_script_sha256": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest(),
              "passed": False,
              "passed_means": ("full mode on a named cache whose whole-cache hashes are recorded below; every sealed-hash, "
                               "order and banked-integrity check passed; L3 was among the fits; and every fitted role's "
                               "per-example vector equals every selected banked vector on the evaluation part AND the "
                               "extension part, its sha256 equal to the banked per_example_sha256"),
              "checks": {}, "roles": {}, "status": "running"}

    def save():
        report["peak_rss_anon_gb"] = round(mem.peak, 3); report["peak_rss_anon_phase"] = mem.where
        report["vmhwm_gb_includes_mapped_file_pages"] = round(_proc_status_gb("VmHWM"), 3)
        report["wall_seconds"] = round(time.perf_counter() - t_all, 1)
        _write_json(args.out, report)

    try:
        rc = _run(args, repo, ext_path, realfit_path, roles, sources, mode, report, mem, save)
    except Refuse as e:
        report["status"] = "REFUSED"; report["refusal"] = str(e)
        mem.stop(); save()
        _say(f"\nREFUSED: {e}\nreport: {args.out}")
        return 3
    mem.stop(); save()
    _say(f"\nreport: {args.out}  (peak anonymous RSS {mem.peak:.2f} GB during '{mem.where}'; "
         f"wall {report['wall_seconds']} s)")
    return rc


def _run(args, repo, ext_path, realfit_path, roles, sources, mode, report, mem, save) -> int:
    ext_only = mode == "ext_only"
    pivot = os.path.join(repo, "tools", "pivot")
    sys.path.insert(0, pivot)
    mem.phase = "imports"
    import numpy as np
    import scipy
    import sklearn
    import sklearn.ensemble  # noqa: F401  (loads the OpenMP runtime so threadpool_info sees it)
    import sklearn.linear_model  # noqa: F401
    import sklearn.tree  # noqa: F401
    import threadpoolctl
    import npzmap
    import run_recipe_search as rrs
    import run_carve
    import run_study
    import run_realfit
    import run_realsearch   # installs score_by_family as run_recipe_search.score (0022-0025's scorer; same vector)
    import run_realcurve
    import run_realcurve2
    import corpus_ext
    import corpus_realfit
    from run_recipe_search import (_sha, sha_obj, fingerprint, environment, npz_memmap, fill_f32, Block, run_fit,
                                   Store, grouped_split, build_estimator, FAMILIES)
    from run_realfit import _array_sha
    from run_realcurve import rung_partition
    from corpus_ext import REAL_FAMILIES

    def check(name, ok, detail=None, fatal=True):
        report["checks"][name] = {"ok": bool(ok), "fatal": bool(fatal), "detail": detail}
        tag = "ok" if ok else ("FAIL" if fatal else "warn")
        _say(f"  [{tag}] {name}" + (f": {detail}" if detail is not None else ""))
        if fatal and not ok:
            save()
            raise Refuse(f"{name}: {detail}")

    def small(path, name):
        with zipfile.ZipFile(path) as zf:
            return np.load(io.BytesIO(zf.read(name + ".npy")), allow_pickle=False)

    # ---------------------------------------------------------------------------------------- environment
    _say(f"[env] mode {mode}; roles {roles}; banked sources {sources}")
    env = environment()
    env["scipy"] = scipy.__version__
    env["threadpools"] = [{k: d.get(k) for k in ("user_api", "internal_api", "num_threads", "version")}
                          for d in threadpoolctl.threadpool_info()]
    report["environment"] = env
    problems = []
    if env["threads"] != BANKED_THREADS:
        problems.append(f"threads {env['threads']} (from OMP_NUM_THREADS) != the banked runs' {BANKED_THREADS}")
    if env["nice"] != BANKED_NICE:
        problems.append(f"nice {env['nice']} != the banked runs' {BANKED_NICE}")
    for k, allowed in ALLOWED_ENV.items():
        if env.get(k) not in allowed:
            problems.append(f"{k} {env.get(k)} not in {list(allowed)}")
    pools = [p for p in env["threadpools"] if p.get("num_threads") != THREADS]
    if pools:
        problems.append(f"thread pools not at {THREADS}: {pools}")
    for n in THREAD_NOTES:
        _say(f"  note: {n}")
    _say(f"  python {env['python']} numpy {env['numpy']} sklearn {env['sklearn']} scipy {env['scipy']} threads "
         f"{env['threads']} nice {env['nice']} pools {[(p['internal_api'], p['num_threads']) for p in env['threadpools']]}")
    check("environment matches the banked runs", not problems, problems or "threads 3, nice 10, allowed versions",
          fatal=not args.allow_env_mismatch)
    mods = [npzmap, rrs, run_carve, run_study, run_realfit, run_realsearch, run_realcurve, run_realcurve2,
            corpus_ext, corpus_realfit]
    prov = module_provenance(repo, mods)
    report["module_provenance"] = prov
    report["repo_head"] = _git(repo, "rev-parse", "HEAD")
    dirty = [k for k, v in prov.items() if v["unmodified_vs_HEAD"] is False]
    check("repository modules used by the fits are unmodified vs HEAD", not dirty,
          dirty or f"{len(prov)} modules at HEAD {str(report['repo_head'])[:12]}", fatal=False)

    # ------------------------------------------------------------------------ sealed constants (preregistrations)
    mem.phase = "sealed constants"
    _say("[sealed] preregistrations")
    pr = {k: json.load(open(os.path.join(repo, v), encoding="utf-8")) for k, v in PREREGS.items()}
    P21 = pr["0021"]["scope"]["protocol"]; S21 = pr["0021"]["scope"]["sealed_partition"]
    R21 = pr["0021"]["scope"]["recipes"]
    C24 = pr["0024"]["scope"]["curve"]; C25 = pr["0025"]["scope"]["curve"]
    P24 = C24["protocol"]; P25 = C25["protocol"]
    seed, eval_frac, top_rung = int(P25["seed"]), float(P25["eval_frac"]), int(P25["top_rung"])
    denominators = [int(d) for d in P25["denominators"]]
    n_first = int(run_realcurve2.N_FIRST)
    check("0025 split constants equal 0021's", (seed, eval_frac, top_rung) == (int(P21["seed"]), float(P21["eval_frac"]),
          int(P21["top_rung"])), {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung})
    check("0025 denominators and first-decade rung count are 0023's", denominators == [int(d) for d in P24["denominators"]]
          and int(P25.get("n_first_decade_rungs", n_first)) == n_first and denominators[n_first - 1] == 1,
          {"denominators": denominators, "N_FIRST": n_first})
    sealed_rec = pr["0021"]["scope"]["sealed_hashes"]["recipe_sha256"]
    for role in roles:
        k21 = ROLE_SPEC[role]["recipe_0021"]; cand = R21[k21]
        check(f"{role}: 0021 recipe '{k21}' hashes to its sealed recipe_sha256", sha_obj(cand) == sealed_rec[k21],
              cand.get("id"))
        p_ref = build_estimator(cand, seed).get_params()
        for src, ck in ROLE_SPEC[role]["curve"].items():
            other = (C24 if src == "0024" else C25)["recipes"][ck]
            same = (build_estimator(other, seed).get_params() == p_ref
                    and bool(other.get("scaled", False)) == bool(cand.get("scaled", False))
                    and (cand["family"] != "hgb" or other.get("val", "frag") == cand.get("val", "frag")))
            check(f"{role}: {src}'s '{ck}' ({other.get('id')}) builds the identical estimator", same, None)

    # ------------------------------------------------------------------------------- 0021's fit corpus and block
    mem.phase = "fit block"
    _say("[fit block] 0021's fit corpus and its block (rung 4 of 0023/0024/0025)")
    sealed_fit = P21["fit_corpus"]["arrays"]
    for name in ("X", "y", "g", "fam"):
        h, shape, dtype = _array_sha(realfit_path, name)
        check(f"fit corpus {name} hashes to the sealed array", h == sealed_fit[name]["sha256"]
              and shape == sealed_fit[name]["shape"] and dtype == sealed_fit[name]["dtype"], f"{h[:16]} {shape} {dtype}")
    check("0025's fit_corpus arrays are 0021's", {k: v["sha256"] for k, v in P25["fit_corpus"]["arrays"].items()}
          == {k: v["sha256"] for k, v in sealed_fit.items()}, None)
    Xr = npz_memmap(realfit_path, "X"); ncols = int(Xr.shape[1])
    yr = small(realfit_path, "y"); gr = small(realfit_path, "g"); famr = small(realfit_path, "fam")
    fit_names = [str(s) for s in small(realfit_path, "families")]
    check("fit corpus family order is the sealed one", fit_names == list(P21["fit_families"]), fit_names)
    fam_r = np.array(fit_names)[famr]
    fit_order, rung_rows, _rep_rows, rk = rung_partition(yr, gr, fam_r, fit_names, seed, denominators)
    rung4 = np.asarray(rung_rows[n_first - 1])
    inline_0021 = np.random.default_rng(seed).permutation(len(yr))     # run_realfit.py's own (inline) expression
    fbh21, fbh25 = P21["fit_block_hashes"], P25["fit_block_hashes"]
    r4_25 = P25["rung_hashes"][n_first - 1]; r4_24 = P24["rung_hashes"][n_first - 1]
    check("fit block idx/sorted hashes are 0021's sealed fit_idx_sha256/fit_sorted_sha256",
          rk["fit_idx_sha256"] == fbh21["fit_idx_sha256"] and rk["fit_sorted_sha256"] == fbh21["fit_sorted_sha256"],
          {"fit_idx_sha256": rk["fit_idx_sha256"], "fit_sorted_sha256": rk["fit_sorted_sha256"]})
    check("... and 0025's fit_block_hashes", rk["fit_idx_sha256"] == fbh25["fit_idx_sha256"]
          and rk["fit_sorted_sha256"] == fbh25["fit_sorted_sha256"], None)
    check("rung 4 is the fit block row for row (0023's top_rung_is_fit_block, and element-wise)",
          bool(rk["top_rung_is_fit_block"]) and np.array_equal(rung4, fit_order), {"n_rows": int(len(rung4))})
    check("rung 4 hashes are 0024's and 0025's sealed rung_hashes[3]",
          all(_sha(rung4) == r["idx_sha256"] and _sha(np.sort(rung4).astype(np.int64)) == r["sorted_sha256"]
              and int(r["n_rows"]) == len(rung4) for r in (r4_24, r4_25)), None)
    check("0021 runner's inline permutation is the same block", np.array_equal(inline_0021, fit_order), None)
    del inline_0021, rung_rows, _rep_rows

    # --------------------------------------------------------------------------------------- extension corpus
    mem.phase = "extension corpus"
    _say("[ext] the sealed extension corpus")
    sealed_ext = P21["ext_corpus"]["arrays"]; ext_hashes = {}
    for name in ("X", "y", "g", "fam"):
        h, shape, dtype = _array_sha(ext_path, name); ext_hashes[name] = h
        check(f"extension {name} hashes to the sealed array", h == sealed_ext[name]["sha256"]
              and shape == sealed_ext[name]["shape"] and dtype == sealed_ext[name]["dtype"], f"{h[:16]} {shape} {dtype}")
    Xx = npz_memmap(ext_path, "X")
    yx = small(ext_path, "y"); gx = small(ext_path, "g"); famx = small(ext_path, "fam")
    ext_names = [str(s) for s in small(ext_path, "families")]
    check("extension family order is the sealed one", ext_names == list(P21["ext_families"]), ext_names)
    check("extension width equals the fit corpus's", int(Xx.shape[1]) == ncols, int(Xx.shape[1]))
    fam_x = np.array(ext_names)[famx]; real_mask = np.isin(fam_x, REAL_FAMILIES)
    n_ext = int(len(yx))

    # --------------------------------------------------------------------------------------- banked vectors
    mem.phase = "banked vectors"
    _say("[banked] scores files and run artifacts")
    banked, banked_meta = {}, {}
    eval_chunk_ids_banked = None
    for src in sources:
        art_rel, sc_rel = SOURCES[src]
        art = json.load(open(os.path.join(repo, art_rel), encoding="utf-8"))
        sc = json.load(open(os.path.join(repo, sc_rel), encoding="utf-8"))
        eci = np.asarray(sc["eval_chunk_ids"], np.int32)
        lay_ok = (sc.get("smoke") is False and art.get("complete") is True and art.get("smoke") is False
                  and int(sc["n_eval_rows"]) == int(S21["eval"]["n_rows"]) and int(sc["n_ext_rows"]) == n_ext
                  and _sha(eci) == S21["eval"]["eval_g_sha256"]
                  and np.array_equal(np.asarray(sc["ext_chunk_ids"], np.int32), gx)
                  and np.array_equal(np.asarray(sc["ext_fam"], np.int8), famx)
                  and sc.get("ext_arrays_sha256") == ext_hashes
                  and sc.get("fit_arrays_sha256") == {k: v["sha256"] for k, v in sealed_fit.items()}
                  and sc.get("eval_idx_sha256") == S21["eval"]["eval_idx_sha256"])
        check(f"banked {src}: complete, not smoke, the sealed layout (260000 eval rows by sealed g, the extension rows, "
              f"the sealed corpora)", lay_ok, sc_rel)
        if eval_chunk_ids_banked is None:
            eval_chunk_ids_banked = eci
        for role in roles:
            key = ROLE_SPEC[role]["banked"].get(src)
            if key is None:
                continue
            vec = np.asarray(sc["per_example"][key], np.int8)
            rec = (art.get("fits") or {}).get(key) or {}
            vsha = hashlib.sha256(vec.tobytes()).hexdigest()
            check(f"banked {src}:{key} vector hashes to its artifact's per_example_sha256", vsha == rec.get("per_example_sha256")
                  and len(vec) == int(sc["n_eval_rows"]) + n_ext, vsha[:16])
            check(f"banked {src}:{key} was fitted on the fit block", rec.get("fit_rows_sha256") == rk["fit_idx_sha256"]
                  and rec.get("fit_rows_sorted_sha256") == rk["fit_sorted_sha256"], rec.get("id"))
            banked[(role, src)] = vec
            rd = (art.get("readings") or {}).get(key) or {}
            banked_meta[(role, src)] = {"key": key, "id": rec.get("id"), "per_example_sha256": rec.get("per_example_sha256"),
                                        "fit_info": rec.get("fit_info"), "seconds": rec.get("seconds"),
                                        "environment": {k: v for k, v in (rec.get("environment") or {}).items()
                                                        if k != "standardiser_probe"},
                                        "builder_eval_top1": rd.get("builder_eval_top1"), "ext_top1": rd.get("ext_top1"),
                                        "ext_real_top1": rd.get("ext_real_top1")}
        del sc, art
    for role in roles:   # the banked sources must agree with each other (they do: same fit, four runs)
        vs = [banked[(role, s)] for s in sources if (role, s) in banked]
        if not vs:
            raise Refuse(f"{role} has no banked vector in the selected sources {sources}; it is banked in "
                         f"{sorted(ROLE_SPEC[role]['banked'])}")
        check(f"{role}: banked sources agree with each other", all(np.array_equal(vs[0], v) for v in vs[1:]),
              [banked_meta[(role, s)]["key"] for s in sources if (role, s) in banked])

    # ------------------------------------------------------------------------------- the cache's evaluation rows
    n_eval = int(S21["eval"]["n_rows"])
    if ext_only:
        _say("[cache] --ext-only: no cache; the evaluation slots are zero rows (the runners' scoring-set geometry kept)")
        ge = eval_chunk_ids_banked; fam_e = np.array(FAMILIES)[ge % len(FAMILIES)]
        ye = np.full(n_eval, -1, np.int16)
        X = ev = None
    else:
        mem.phase = "cache order"
        cache = os.path.abspath(args.cache)
        _say(f"[cache] {cache}")
        if not os.path.exists(cache):
            raise Refuse(f"{cache} does not exist")
        st = os.stat(cache)
        report["cache_file"] = {"path": cache, "size_bytes": int(st.st_size),
                                "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))}
        with zipfile.ZipFile(cache) as zf:
            names = zf.namelist()
            y = np.load(io.BytesIO(zf.read("y.npy"))); g = np.load(io.BytesIO(zf.read("g.npy")))
            meta = None
            if "carve.npy" in names:
                meta = tuple(int(np.load(io.BytesIO(zf.read(f"{k}.npy")))) for k in ("carve", "chunk_offset", "chunk_size"))
        if meta is not None:
            check("cache build metadata is carve 4096, offset 0, chunk size 32768",
                  meta == (int(P21["carve"]), int(P21["chunk_offset"]), int(P21["chunk_size"])), meta)
        try:
            X = npz_memmap(cache, "X")
        except Exception as e:  # noqa: BLE001
            raise Refuse(f"cannot memory-map {cache}:X ({e})")
        ident = P21["cache_identity"]
        check("cache X width and dtype are the sealed ones", int(X.shape[1]) == ncols == int(ident["X_shape"][1])
              and str(X.dtype) == ident["X_dtype"], f"{list(X.shape)} {X.dtype}")
        report["cache_file"].update({"y_sha256": _sha(y), "g_sha256": _sha(g), "X_shape": [int(v) for v in X.shape],
                                     "X_dtype": str(X.dtype), "build_metadata": list(meta) if meta else None})
        same_y, same_g = _sha(y) == ident["y_sha256"], _sha(g) == ident["g_sha256"]
        check("whole-cache y and g are the sealed cache_identity (informational: false after a reorder of non-evaluation rows)",
              same_y and same_g, {"y": same_y, "g": same_g, "n_rows": int(len(y))}, fatal=False)
        ev, tr, _rng = grouped_split(y, g, seed, eval_frac, top_rung)
        del tr, _rng
        ge = np.asarray(g[ev]); ye = np.asarray(y[ev]); fam_e = np.array(FAMILIES)[ge % len(FAMILIES)]
        check("evaluation row count is the sealed one", len(ev) == n_eval
              and np.unique(ge).size == int(S21["eval"]["n_chunks"]), {"rows": int(len(ev)), "chunks": int(np.unique(ge).size)})
        check("evaluation y is the sealed eval_y_sha256 (order and labels)", _sha(ye) == S21["eval"]["eval_y_sha256"], _sha(ye)[:16])
        check("evaluation g is the sealed eval_g_sha256 (order and chunks)", _sha(ge) == S21["eval"]["eval_g_sha256"], _sha(ge)[:16])
        check("evaluation g equals the banked scores file's eval_chunk_ids element-wise",
              np.array_equal(ge.astype(np.int32), eval_chunk_ids_banked), None)
        check("evaluation (chunk, label) pairs identify rows uniquely, so the y/g hashes pin each row's identity",
              np.unique(ge.astype(np.int64) * 64 + ye).size == n_eval, None, fatal=False)
        check("evaluation index hash is the sealed eval_idx_sha256 (informational: positions may move in a reordered cache)",
              _sha(ev) == S21["eval"]["eval_idx_sha256"], _sha(ev)[:16], fatal=False)
        check("no extension chunk id is an evaluation chunk id", np.intersect1d(np.unique(ge), np.unique(gx)).size == 0, None)
        del y, g
        if not args.no_hash_cache:
            mem.phase = "whole-cache X hash"
            t = time.perf_counter()
            hx, _, _ = _array_sha(cache, "X")
            decisive = same_y and same_g
            check("whole-cache X hashes to the sealed cache_identity X_sha256"
                  + ("" if decisive else " (informational: the row order differs from the sealed cache, so a mismatch "
                                         "is expected)"), hx == ident["X_sha256"],
                  f"{hx[:16]} in {time.perf_counter() - t:.0f}s", fatal=False)
            report["cache_file"]["X_sha256"] = hx
            report["whole_cache_X_hash_is_decisive"] = bool(decisive)

    # ---------------------------------------------------------------------- the scoring set, as the runners build it
    mem.phase = "scoring set"
    if args.check_only:
        report["status"] = "CHECKED"
        report["conclusion"] = "CHECKS_ONLY"
        save()
        _say("[done] --check-only: every check passed; nothing fitted")
        return 0
    t = time.perf_counter()
    if ext_only:
        Xs = np.zeros((n_eval + n_ext, ncols), np.float32)    # untouched zero pages cost no memory
    else:
        Xs = np.empty((n_eval + n_ext, ncols), np.float32)
        fill_f32(Xs[:n_eval], X, ev, ncols)
    Xs[n_eval:] = Xx
    ys = np.concatenate([ye, np.asarray(yx)])
    fam_s = np.concatenate([fam_e, np.array(["ext:" + f for f in fam_x])])
    if not ext_only:
        h = hashlib.sha256()
        for i in range(0, n_eval, 20000):
            h.update(Xs[i:i + 20000])
        report["eval_X_sha256_in_sealed_order"] = h.hexdigest()
        report["eval_X_sha256_note"] = ("sha256 of the evaluation rows' float32 features, C order, in the sealed evaluation "
                                        "order; nothing banked to compare it with - bank it beside a passing proof")
        report["eval_y_sha256"] = _sha(ye); report["eval_g_sha256"] = _sha(ge)
    _say(f"[scoring set] {n_eval} + {n_ext} rows materialised in {time.perf_counter() - t:.0f}s, anonymous RSS "
         f"{mem.sample():.2f} GB")

    # ---------------------------------------------------------------------------------------------- the fits
    caps = dict(P25["caps"])
    store_dir = tempfile.mkdtemp(prefix="ccp_store_", dir=args.workdir_root)
    if _under(store_dir, repo):
        raise Refuse(f"checkpoint store {store_dir} is under the repository")
    store = Store(store_dir)
    report["store_dir"] = store_dir
    ctx = {"ge": ge, "fam_e": fam_e, "fam_x": fam_x, "real_mask": real_mask}

    def compare(ours, theirs):
        out = {}
        d = np.flatnonzero(ours[n_eval:] != theirs[n_eval:])
        out["ext_identical"] = bool(d.size == 0); out["ext_n_diff"] = int(d.size)
        if d.size:
            out["ext_n_diff_real_families"] = int(ctx["real_mask"][d].sum())
            u, c = np.unique(ctx["fam_x"][d], return_counts=True)
            out["ext_diff_per_family"] = {str(a): int(b) for a, b in zip(u, c)}
            out["ext_first_diff_rows"] = d[:10].tolist()
        if ext_only:
            out["eval_identical"] = None; out["eval_n_diff"] = None
            return out
        d = np.flatnonzero(ours[:n_eval] != theirs[:n_eval])
        out["eval_identical"] = bool(d.size == 0); out["eval_n_diff"] = int(d.size)
        if d.size:
            ch = np.unique(ctx["ge"][d])
            out["eval_n_diff_chunks"] = int(ch.size); out["eval_diff_chunks_first20"] = ch[:20].tolist()
            u, c = np.unique(ctx["fam_e"][d], return_counts=True)
            out["eval_diff_per_family"] = {str(a): int(b) for a, b in zip(u, c)}
            out["eval_first_diff_rows"] = d[:10].tolist()
            out["eval_correct_ours_minus_banked"] = int(ours[:n_eval].sum()) - int(theirs[:n_eval].sum())
        return out

    any_diff = False
    try:
        for role in roles:
            cand = R21[ROLE_SPEC[role]["recipe_0021"]]
            exp = banked_meta.get((role, sources[0])) or next(v for (r, _), v in banked_meta.items() if r == role)
            _say(f"[fit] {role} ({cand['id']}, {cand['family']} {cand.get('params')}) on the {len(fit_order)}-row fit block; "
                 f"banked fit took {exp.get('seconds')} s")
            mem.phase = f"fit {role}"
            fp = fingerprint(proof="cache_content_proof", mode=mode, role=role, cand=cand, seed=seed,
                             rows=rk["fit_sorted_sha256"], ext=ext_hashes["X"])
            block = Block(Xr, fit_order, ncols, role)
            rec, pe = run_fit(store, f"proof_{role}", fp, role, cand, seed, block, yr, gr, Xs, ys, fam_s,
                              "cache_content_proof", caps, keep_per_example=True, confirmatory=True)
            del block
            if pe is None:
                raise Refuse(f"{role}: run_fit returned no per-example vector (status {rec.get('status')!r})")
            pe = np.asarray(pe, np.int8)
            full_sha = hashlib.sha256(pe.tobytes()).hexdigest()
            ext_sha = hashlib.sha256(pe[n_eval:].tobytes()).hexdigest()
            ev_sha = None if ext_only else hashlib.sha256(pe[:n_eval].tobytes()).hexdigest()
            ex = pe[n_eval:]
            rr = {"recipe": cand, "status": rec.get("status"), "fit_seconds": rec.get("seconds"),
                  "fit_info": rec.get("fit_info"), "fit_rows_sha256": rec.get("fit_rows_sha256"),
                  "fit_rows_sorted_sha256": rec.get("fit_rows_sorted_sha256"), "rss_gb": rec.get("rss_gb"),
                  "heartbeat_max_rss_gb": rec.get("heartbeat_max_rss_gb"), "block_refills": rec.get("block_refills"),
                  "vector_sha256": None if ext_only else full_sha, "eval_part_sha256": ev_sha, "ext_part_sha256": ext_sha,
                  "readings": {"ext_top1": round(float(ex.mean()), 4), "ext_real_top1": round(float(ex[real_mask].mean()), 4),
                               "ext_real_correct": int(ex[real_mask].sum()),
                               "builder_eval_top1": None if ext_only else round(float(pe[:n_eval].mean()), 4)},
                  "vs_banked": {}}
            ok = True
            for src in sources:
                if (role, src) not in banked:
                    continue
                b = banked[(role, src)]; m = banked_meta[(role, src)]
                c = compare(pe, b)
                c["banked_key"] = m["key"]; c["banked_id"] = m["id"]
                c["banked_per_example_sha256"] = m["per_example_sha256"]
                c["banked_ext_part_sha256"] = hashlib.sha256(b[n_eval:].tobytes()).hexdigest()
                c["full_sha256_equal"] = None if ext_only else bool(full_sha == m["per_example_sha256"])
                c["fit_info_equal"] = rec.get("fit_info") == m["fit_info"]
                c["banked_fit_info"] = m["fit_info"]
                c["banked_readings"] = {k: m[k] for k in ("builder_eval_top1", "ext_top1", "ext_real_top1")}
                c["banked_environment"] = m["environment"]
                rr["vs_banked"][f"{src}:{m['key']}"] = c
                ok = ok and c["ext_identical"] and (ext_only or (c["eval_identical"] and c["full_sha256_equal"]))
                if ext_only:
                    line = (f"ext part {'IDENTICAL' if c['ext_identical'] else 'DIFFERS'} ({c['ext_n_diff']} rows differ); "
                            f"ext sha {ext_sha[:16]} vs banked {c['banked_ext_part_sha256'][:16]}")
                else:
                    line = (f"eval part {'IDENTICAL' if c['eval_identical'] else 'DIFFERS'} ({c['eval_n_diff']} rows differ"
                            + (f", {c.get('eval_n_diff_chunks')} chunks" if c['eval_n_diff'] else "") + "); "
                            f"ext part {'IDENTICAL' if c['ext_identical'] else 'DIFFERS'} ({c['ext_n_diff']} rows differ); "
                            f"vector sha {full_sha[:16]} {'==' if c['full_sha256_equal'] else '!='} banked "
                            f"{str(m['per_example_sha256'])[:16]}")
                _say(f"      vs {src}:{m['key']:<17} {line}; fit_info {rec.get('fit_info')} "
                     f"{'==' if c['fit_info_equal'] else '!='} banked {m['fit_info']}")
            rr["verdict"] = ("EXT_PART_IDENTICAL" if ok else "EXT_PART_DIFFERS") if ext_only else ("IDENTICAL" if ok else "DIFFERS")
            any_diff = any_diff or not ok
            report["roles"][role] = rr
            _say(f"      {role}: {rr['verdict']}  readings {rr['readings']}")
            save()
    finally:
        if not args.keep_workdir:
            shutil.rmtree(store_dir, ignore_errors=True)

    # ------------------------------------------------------------------------------------------- conclusion
    done = [r for r in roles if r in report["roles"]]
    ext_all = all(all(c["ext_identical"] for c in report["roles"][r]["vs_banked"].values()) for r in done)
    if ext_only:
        concl = ("EXT_PART_REPRODUCED: this environment and the repository's fitting path reproduce the banked extension "
                 f"parts of {done}") if ext_all else \
            "EXT_PART_DIFFERS: this environment or fitting path does not reproduce the banked fit; do not run the proof here"
    else:
        eval_all = all(all(c["eval_identical"] and c["full_sha256_equal"] for c in report["roles"][r]["vs_banked"].values())
                       for r in done)
        if ext_all and eval_all and "L3" in done:
            concl = ("EVAL_CONTENT_PROVEN: every vector is the banked one hash for hash; L3 reads all 1108 features of every "
                     "evaluation row, so the evaluation rows carry the banked content and this environment reproduces "
                     "0021's fits")
        elif ext_all and eval_all:
            concl = (f"EVAL_IDENTICAL_WITHOUT_L3: {done} are the banked vectors hash for hash, but none of them reads every "
                     "feature; run L3 for the proof")
        elif ext_all:
            concl = ("EVAL_CONTENT_DIFFERS: the extension parts (the control) are identical, so the fit is reproduced, and "
                     "the evaluation parts differ: some evaluation rows' features are not the banked ones")
        else:
            concl = ("ENVIRONMENT_DOES_NOT_REPRODUCE: an extension part (the control) differs, so the evaluation comparison is "
                     "inconclusive here")
    report["conclusion"] = concl
    report["status"] = "DIFFERS" if any_diff else "IDENTICAL"
    report["passed"] = bool(not ext_only and not any_diff and concl.startswith("EVAL_CONTENT_PROVEN")
                            and (report.get("cache_file") or {}).get("X_sha256") is not None)
    save()
    _say("\n[summary]")
    for r in done:
        rr = report["roles"][r]
        for k, c in rr["vs_banked"].items():
            ev_txt = ("n/a" if c["eval_identical"] is None
                      else "identical" if c["eval_identical"] else "%d rows differ" % c["eval_n_diff"])
            ex_txt = "identical" if c["ext_identical"] else "%d rows differ" % c["ext_n_diff"]
            sha_txt = ("n/a (ext-only)" if c["full_sha256_equal"] is None
                       else "== banked" if c["full_sha256_equal"] else "!= banked")
            _say(f"  {r:<8} vs {k:<22} eval {ev_txt:<18} ext {ex_txt:<16} vector sha {sha_txt}")
    _say(f"  CONCLUSION: {concl}")
    return 1 if any_diff else 0


if __name__ == "__main__":
    raise SystemExit(main())
