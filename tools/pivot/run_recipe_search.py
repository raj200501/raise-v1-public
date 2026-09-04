#!/usr/bin/env python3
"""A budgeted, SYMMETRIC recipe search at one carve size (preregistration 0012 at 2048; 0014 at 4096).

Question. 0011 measured the incumbent recipe at 2048 and returned CARVE_FAILS with the frozen-set
margin 0.0025 short of the bar (0.1741 against logistic 0.1266) and the expanded margin +0.0294
(against the depth-16 tree 0.1447). VERDICT.md names the next question in its own words: a gap that
small "is exactly the gap a per-head recipe search might close", and "a training recipe tuned under
one architecture is not architecture-neutral, and freezing it privileges the incumbent". So the
search here is symmetric: every HEAD - the model and each baseline family with a hyperparameter -
is an enumerated roster of the same size in the preregistration's SEALED scope, selected by the
same rule on the same chunk-rule holdout, and each head's selected recipe is fitted ONCE on the
same training pool the reproduced run used (0011's 500000 rows at 2048; 0003's 800000 at 4096) and
scored ONCE on that run's sealed evaluation set.

Two invocations, so that selection can be shown never to have held an evaluation row:

  --stage select   gathers the holdout and the stage blocks only (every gather is intersected
                   with the evaluation index and the count banked), runs every roster through the
                   stages, and writes the --selection-out file.
  --stage confirm  refuses without that file; gathers the evaluation block and the pool once;
                   fits the roles in the PREREGISTERED ORDER - the incumbent and the fixed-recipe logistic
                   reproductions, the knob-free heads, the searched baseline heads, the null
                   control, and the model's selected recipe LAST - and re-assembles the artifact
                   after every role, so an abandoned stage reads VOID rather than vanishing.

Everything the script does is read from prereg["scope"]["roster"] (sealed by the chain): the heads
and their rosters, the holdout rule, the stages, the caps, the fit order. It banks what it actually
did - row counts, index hashes, measured overlaps, per-candidate records with status, the
append-only attempt ledger, the environment - and the frozen reader compares those against the
constants sealed in it.

Partition (all derived from the cache's y and g arrays; the script recomputes and banks hashes):
  eval        grouped_split(seed, eval_frac, cap) held-out chunks - the reproduced run's sealed set
              (130000 rows / 5000 chunks at 2048; 260000 rows / 10000 chunks at 4096)
  pool        the `cap` training rows grouped_split returns, in its order - the top rung's rows
              (500000 at 2048; 800000 at 4096)
  holdout     pool rows whose chunk id satisfies the preregistered rule (a rule, not a draw)
  fit pool    the other pool rows, in pool order
  stage k     the first stage.rows of the fit pool ("all" = the whole fit pool)

Selection per head: stage 1 fits every candidate on the stage-1 block and scores it on the holdout;
the top `keep` advance (ties at 4 decimals go to the LOWER roster index, so a tie can only favour
the recipe listed first, and every roster lists the reproduced run's recipe first); the last stage's winner is
the head's recipe. Fit seconds are banked for cost and never decide eligibility. A candidate whose
fit raises MemoryError, or that was killed while its last heartbeat showed the process at or above
the preregistered memory threshold, is banked infeasible_memory and is ineligible; it is never
silently dropped. A fit killed for any other reason (a container restart) is retried without bound
and the count is banked.

Blocks are float64 arrays gathered from the memmap. A scaled candidate standardises its block IN
PLACE and the block is refilled afterwards; a group-validation candidate has its block refilled in
[fit rows, validation rows] order so both halves are contiguous views, then refilled canonically.
Every refill is probe-checked against the block's first materialisation (sha256 of every 7813th
row) and the result banked; a probe mismatch aborts the run.

Digest convention, for every hash banked here: sha256 of np.ascontiguousarray(a).tobytes(); index
arrays are the int64 arrays grouped_split / np.nonzero return, in their order; y is the stored int16,
g the stored int32; chunk-id sets and sorted sets are np.sort(...).astype(np.int64).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import shutil
import sys
import threading
import time

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import CONFIG_NAMES, FAMILIES, N_CONFIGS  # noqa: E402
from npzmap import fill_f32, fill_f64, npz_memmap  # noqa: E402
from run_carve import grouped_split  # noqa: E402
from run_study import _rss_gb as _rss_total_gb, predict_chunked  # noqa: E402


def _rss_gb():
    """Anonymous resident memory (RssAnon) in GB - what the container's memory ceiling counts.
    VmRSS also counts the file-backed pages of the memory-mapped cache (5.77 GB for corpus A),
    which the kernel drops under pressure; a VmRSS threshold would be crossed by an idle process
    sitting on the pool plus the mapping. Both figures are banked; this one is the threshold's."""
    try:
        anon = rss_file = rss = None
        with open("/proc/self/status") as fh:
            for ln in fh:
                if ln.startswith("RssAnon:"):
                    anon = int(ln.split()[1])
                elif ln.startswith("RssFile:"):
                    rss_file = int(ln.split()[1])
                elif ln.startswith("VmRSS:"):
                    rss = int(ln.split()[1])
        if anon is not None:
            return anon / 1e6
        if rss is not None and rss_file is not None:
            return (rss - rss_file) / 1e6
    except OSError:
        pass
    return float("nan")

PROBE_STRIDE = 7813


# ------------------------------------------------------------------------------------- utilities
def _sha(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha_obj(obj) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def fingerprint(**parts) -> str:
    return sha_obj(parts)[:16]


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _threads():
    vals = [os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")]
    if all(v and v.isdigit() for v in vals) and len(set(vals)) == 1:
        return int(vals[0])
    return None


def environment():
    env = {"threads": _threads(), "cpu_cores": os.cpu_count(), "gpu": "none", "nice": os.nice(0),
           "python": platform.python_version(), "sklearn": __import__("sklearn").__version__,
           "numpy": np.__version__, "disk_free_gb": round(shutil.disk_usage(REPO).free / 1e9, 2),
           "mem_available_gb": None, "cgroup_memory_limit": "not visible"}
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                env["mem_available_gb"] = round(int(line.split()[1]) / 1e6, 2)
    except OSError:
        pass
    for p in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        if os.path.exists(p):
            v = open(p).read().strip()
            env["cgroup_memory_limit"] = v if v == "max" else (
                round(int(v) / 1e9, 2) if int(v) < 1 << 60 else "unlimited")
            break
    return env


_PROBE = {}


def standardiser_probe(rows=20000, ncols=1108):
    """Fit InPlaceScaled on a synthetic block under tracemalloc and bank the peak extra allocation
    as a fraction of the block. The guard against a pool-sized temporary creeping back into the
    standardiser (numpy's std(axis=0) allocates one; at 800000 x 1108 float64 that is 7.09 GB).
    Computed once per process and banked with every record's environment."""
    key = (rows, ncols)
    if key not in _PROBE:
        import tracemalloc
        A = np.random.default_rng(0).normal(size=(rows, ncols))
        tracemalloc.start()
        base = tracemalloc.get_traced_memory()[0]
        tracemalloc.reset_peak()
        # rows_per_pass is set to a tenth of the probe block so the probe can tell a chunked
        # standardiser (one pass-sized transient: fraction about 0.1) from one that materialises the
        # whole block (about 1.0); production uses the default 20000-row pass, banked as an absolute.
        InPlaceScaled(None).fit_inplace(A, lambda est: None, rows_per_pass=max(1, rows // 10))
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        _PROBE[key] = {"rows": rows, "ncols": ncols, "block_gb": round(A.nbytes / 1e9, 3),
                       "probe_rows_per_pass": max(1, rows // 10),
                       "peak_extra_fraction_of_block": round(max(0.0, peak - base) / A.nbytes, 4),
                       "production_rows_per_pass": 20000,
                       "production_transient_gb": round(20000 * ncols * 8 / 1e9, 3)}
        del A
    return dict(_PROBE[key])


def record_env():
    return {"threads": _threads(), "nice": os.nice(0), "sklearn": __import__("sklearn").__version__,
            "numpy": np.__version__, "python": platform.python_version(),
            "standardiser_probe": standardiser_probe()}


# ------------------------------------------------------------------------------- recipe factories
def build_estimator(cand: dict, seed: int):
    fam = cand["family"]; p = dict(cand.get("params", {}))
    if fam == "hgb":
        from sklearn.ensemble import HistGradientBoostingClassifier
        base = dict(max_iter=200, learning_rate=0.15, max_leaf_nodes=63, early_stopping=True,
                    n_iter_no_change=10, random_state=seed)
        base.update(p); return HistGradientBoostingClassifier(**base)
    if fam == "logistic":
        from sklearn.linear_model import LogisticRegression
        base = dict(max_iter=400); base.update(p); return LogisticRegression(**base)
    if fam == "tree":
        from sklearn.tree import DecisionTreeClassifier
        base = dict(random_state=0); base.update(p); return DecisionTreeClassifier(**base)
    if fam == "dummy":
        from sklearn.dummy import DummyClassifier
        base = dict(random_state=0); base.update(p); return DummyClassifier(**base)
    raise ValueError(f"unknown family {fam!r}")


class InPlaceScaled:
    """Standardise the float64 block IN PLACE (mean/std of the fitting rows, zero-variance columns
    get scale 1), fit the inner estimator, standardise scoring chunks on the fly. No second copy of
    the block is made; the caller refills the block afterwards."""

    def __init__(self, est):
        self.est = est

    def fit_inplace(self, Xtr, fit_fn, rows_per_pass=20000):
        # Column mean and (population) standard deviation accumulated over row blocks. numpy's
        # std(axis=0) materialises a full-size (Xtr - mean) temporary: at 800000 x 1108 float64 that
        # is a second 7.09 GB copy beside the block (0012 banked it as +4.3 GB of ru_maxrss on the
        # scaled logistic at 500000 rows). Two passes, transients of rows_per_pass rows only.
        n = int(Xtr.shape[0])
        self.mean_ = Xtr.mean(axis=0)
        ss = np.zeros(Xtr.shape[1], np.float64)
        buf = np.empty((min(rows_per_pass, n), Xtr.shape[1]), np.float64)  # the one transient
        for i in range(0, n, rows_per_pass):
            d = buf[:min(rows_per_pass, n - i)]
            np.subtract(Xtr[i:i + rows_per_pass], self.mean_, out=d)
            np.multiply(d, d, out=d)
            ss += d.sum(axis=0)
        del buf, d
        sd = np.sqrt(ss / n); sd[sd == 0] = 1.0; self.scale_ = sd
        Xtr -= self.mean_; Xtr /= self.scale_
        fit_fn(self.est)
        return self

    def predict(self, Xc):
        return self.est.predict((Xc - self.mean_) / self.scale_)


class Block:
    """A float64 gather of `rows` from the memmap, with probe-checked refills."""

    def __init__(self, X, rows, ncols, name):
        self.X, self.rows, self.ncols, self.name = X, rows, ncols, name
        self.A = fill_f64(np.empty((len(rows), ncols), np.float64), X, rows, ncols)
        self.probe = self._probe(); self.refills = []
        self.order = None

    def _probe(self):
        return hashlib.sha256(np.ascontiguousarray(self.A[::PROBE_STRIDE]).tobytes()).hexdigest()

    def refill(self, order=None):
        """Refill canonically (order None) or in the given permutation of the block's rows."""
        rows = self.rows if order is None else self.rows[order]
        fill_f64(self.A, self.X, rows, self.ncols)
        self.order = order
        ok = order is not None or self._probe() == self.probe
        self.refills.append({"utc": _utc(), "order": "canonical" if order is None else "reordered",
                             "probe_ok": bool(ok)})
        if not ok:
            raise RuntimeError(f"block {self.name}: probe checksum mismatch after refill; the pool is not the pool")


def fit_one(cand, seed, block, y_all, g_all):
    """Fit a candidate on the block. HGB 'frag': the last 10% of rows are the explicit validation
    split (the incumbent's rule, 0003/0007/0011). HGB 'group': every row of 10% of the block's
    CHUNKS, chosen by a permutation seeded with seed + 1, is the validation split; the block is
    refilled in [fit rows, validation rows] order so both are contiguous views, and refilled
    canonically afterwards. Returns (estimator, needs_refill)."""
    rows = block.rows
    ytr = np.asarray(y_all[rows]); gtr = np.asarray(g_all[rows])
    inner = build_estimator(cand, seed)
    reordered = False
    if cand["family"] == "hgb" and cand.get("val", "frag") == "group":
        chunks = np.sort(np.unique(gtr))
        perm = np.random.default_rng(seed + 1).permutation(chunks)
        val_chunks = set(perm[:max(1, int(len(chunks) * 0.1))].tolist())
        is_val = np.fromiter((int(v) in val_chunks for v in gtr), bool, len(gtr))
        order = np.concatenate([np.nonzero(~is_val)[0], np.nonzero(is_val)[0]])
        block.refill(order); reordered = True
        ytr = ytr[order]; k = int((~is_val).sum())
    else:
        k = max(1, int(len(ytr) * 0.9))

    def do_fit(est):
        if cand["family"] == "hgb":
            est.fit(block.A[:k], ytr[:k], X_val=block.A[k:], y_val=ytr[k:])
        else:
            est.fit(block.A, ytr)

    if cand.get("scaled"):
        est = InPlaceScaled(inner).fit_inplace(block.A, do_fit)
        return est, True
    do_fit(inner)
    return inner, reordered


def score(est, Xs32, ys, fam_s):
    correct = (predict_chunked(est, Xs32) == ys).astype(np.int8)
    return {"top1": round(float(correct.mean()), 4),
            "top1_non_gutenberg": round(float(correct[fam_s != "gutenberg"].mean()), 4),
            "per_family": {f: round(float(correct[fam_s == f].mean()), 4) for f in FAMILIES}}, correct


def fit_info(est):
    inner = est.est if isinstance(est, InPlaceScaled) else est
    info = {}
    if hasattr(inner, "n_iter_"):
        n = np.asarray(inner.n_iter_); info["n_iter"] = int(n.max()) if n.ndim else int(n)
    if hasattr(inner, "get_depth"):
        info["depth"] = int(inner.get_depth())
    if hasattr(inner, "get_n_leaves"):
        info["n_leaves"] = int(inner.get_n_leaves())
    return info


def cluster_ci(correct, chunk_ids, n_boot=2000, seed=0):
    """Informational 95% interval on a mean accuracy under a cluster bootstrap over source chunks.
    Never a clause."""
    _, inv = np.unique(chunk_ids, return_inverse=True)
    sums = np.bincount(inv, weights=correct.astype(np.float64)); counts = np.bincount(inv).astype(np.float64)
    rng = np.random.default_rng(seed); n = len(sums); means = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n); means[b] = sums[idx].sum() / counts[idx].sum()
    return [round(float(np.percentile(means, 2.5)), 4), round(float(np.percentile(means, 97.5)), 4)]


# ----------------------------------------------------------------------------------- checkpoints
class NotRun(Exception):
    pass


class Store:
    """One JSON file per completed fit, an append-only ledger (started / completed / memory_error /
    infeasible_stamped), a heartbeat file per running fit with its RSS, and a launches file."""

    def __init__(self, workdir):
        self.dir = workdir; os.makedirs(workdir, exist_ok=True)
        self.ledger_path = os.path.join(workdir, "ledger.jsonl")

    def path(self, name): return os.path.join(self.dir, f"{name}.json")

    def ledger(self):
        out = []
        if os.path.exists(self.ledger_path):
            for line in open(self.ledger_path):
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        out.append({"event": "unparseable", "raw": line[:200]})
        return out

    def log(self, name, fp, event, **extra):
        with open(self.ledger_path, "a") as fh:
            fh.write(json.dumps({"name": name, "fingerprint": fp, "event": event, "utc": _utc(),
                                 "rss_gb": round(_rss_gb(), 2), "pid": os.getpid(), **extra}) + "\n")
            fh.flush(); os.fsync(fh.fileno())

    def load(self, name, fp):
        p = self.path(name)
        if not os.path.exists(p):
            return None
        try:
            d = json.load(open(p))
        except Exception:  # noqa: BLE001
            return None
        return d if d.get("fingerprint") == fp else None

    def open_attempts(self, name, fp):
        n, last_hb = 0, None
        for e in self.ledger():
            if e.get("name") != name or e.get("fingerprint") != fp:
                continue
            if e["event"] == "started":
                n += 1
            elif e["event"] in ("completed", "memory_error", "infeasible_stamped"):
                n = 0
        hb = self.path(name) + ".hb"
        if os.path.exists(hb):
            try:
                last_hb = json.load(open(hb))
            except Exception:  # noqa: BLE001
                last_hb = None
        return n, last_hb

    def completed_before(self, name, fp):
        return any(e.get("name") == name and e.get("fingerprint") == fp and e.get("event") == "completed"
                   for e in self.ledger())

    def heartbeat(self, name, stop, box):
        hb = self.path(name) + ".hb"
        while not stop.wait(30):
            try:
                r = round(_rss_gb(), 2); box["max"] = max(box.get("max", 0.0), r)
                with open(hb + ".tmp", "w") as fh:
                    json.dump({"utc": _utc(), "rss_gb": r, "rss_total_gb": round(_rss_total_gb(), 2),
                               "rss_gb_is": "anonymous (RssAnon)"}, fh)
                os.replace(hb + ".tmp", hb)
            except Exception:  # noqa: BLE001
                pass

    def save(self, name, fp, record, per_example=None):
        tmp = self.path(name) + ".tmp"
        with open(tmp, "w") as fh:
            json.dump({"fingerprint": fp, "record": record,
                       "per_example": per_example.tolist() if per_example is not None else None}, fh)
        os.replace(tmp, self.path(name))
        hb = self.path(name) + ".hb"
        if os.path.exists(hb):
            os.remove(hb)

    def banked_seconds(self, prefix):
        total = 0.0
        for f in os.listdir(self.dir):
            if f.startswith(prefix) and f.endswith(".json"):
                try:
                    total += float(json.load(open(os.path.join(self.dir, f)))["record"].get("seconds") or 0)
                except Exception:  # noqa: BLE001
                    pass
        return total

    def launches(self, stage, any_eval_checkpoint):
        """Append this launch; NOT RUN if the last three launches of this stage produced no new
        checkpoint - and only while no evaluation-touching checkpoint exists."""
        path = os.path.join(self.dir, "launches.jsonl")
        n_ckpt = len([f for f in os.listdir(self.dir) if f.endswith(".json")])
        prior = []
        if os.path.exists(path):
            for line in open(path):
                try:
                    e = json.loads(line)
                    if e.get("stage") == stage:
                        prior.append(e)
                except json.JSONDecodeError:
                    pass
        with open(path, "a") as fh:
            fh.write(json.dumps({"utc": _utc(), "stage": stage, "n_checkpoints_at_launch": n_ckpt,
                                 "launch": len(prior) + 1}) + "\n")
        counts = [p.get("n_checkpoints_at_launch") for p in prior[-3:]] + [n_ckpt]
        if not any_eval_checkpoint and len(counts) == 4 and len(set(counts)) == 1:
            raise NotRun(f"three consecutive {stage} launches produced no new checkpoint (count {n_ckpt})")
        return len(prior) + 1


def run_fit(store, name, fp, head, cand, seed, block, y_all, g_all, Xs, ys, fam_s, stage, caps,
            keep_per_example=False, confirmatory=False):
    """Fit-or-resume one candidate on a block, scored on (Xs, ys). Returns (record, per_example)."""
    hit = store.load(name, fp)
    if hit is not None:
        r = hit["record"]
        if not store.completed_before(name, fp):
            # Store.save writes the checkpoint and only then appends the 'completed' event; a restart
            # inside that window leaves a banked record with no completion event, which the reader
            # counts as zero completions. Reconstruct the event from the checkpoint, marked as such.
            store.log(name, fp, "completed", seconds=r.get("seconds"), reconstructed_on_resume=True)
        print(f"      {name:<30} resumed: {r['status']} top1={r.get('top1')}", flush=True)
        pe = np.asarray(hit["per_example"], np.int8) if hit.get("per_example") is not None else None
        return r, pe
    if confirmatory and store.completed_before(name, fp):
        raise NotRun(f"{name}: the ledger shows a completed confirmatory record that is no longer on disk; "
                     f"one evaluation scoring per role - refusing to refit")
    if not confirmatory:
        total = store.banked_seconds("sel")
        if total > caps["selection_fit_seconds"]:
            raise NotRun(f"{name}: banked selection fit seconds {total:.0f} exceed the preregistered cap "
                         f"{caps['selection_fit_seconds']}")
    prior, last_hb = store.open_attempts(name, fp)
    base = {"id": cand["id"], "head": head, "family": cand["family"], "params": cand.get("params", {}),
            "scaled": bool(cand.get("scaled", False)), "val": cand.get("val"), "seed": seed,
            "params_sha256": sha_obj(cand), "stage": stage, "n_fit_rows": int(len(block.rows)),
            "fit_rows_sha256": _sha(block.rows), "fit_rows_sorted_sha256": _sha(np.sort(block.rows).astype(np.int64)),
            "environment": record_env(), "interruptions_before_this_fit": prior,
            "last_heartbeat_rss_gb_before_this_fit": (last_hb or {}).get("rss_gb"), "utc": _utc()}
    if prior > 0 and last_hb and (last_hb.get("rss_gb") or 0) >= caps["memory_kill_gb"]:
        rec = dict(base, status="infeasible_memory", seconds=None, top1=None, top1_non_gutenberg=None,
                   per_family=None, evidence=f"killed with anonymous RSS {last_hb['rss_gb']} GB at the last heartbeat, "
                                             f"at or above the preregistered {caps['memory_kill_gb']} GB")
        store.log(name, fp, "infeasible_stamped", evidence=rec["evidence"]); store.save(name, fp, rec)
        print(f"      {name:<30} {rec['status']} ({rec['evidence']})", flush=True)
        return rec, None
    store.log(name, fp, "started", attempt=prior + 1)
    stop = threading.Event(); box = {"max": round(_rss_gb(), 2)}
    threading.Thread(target=store.heartbeat, args=(name, stop, box), daemon=True).start()
    t = time.perf_counter()
    try:
        est, needs_refill = fit_one(cand, seed, block, y_all, g_all)
    except MemoryError:
        stop.set()
        rec = dict(base, status="infeasible_memory", seconds=round(time.perf_counter() - t, 1), top1=None,
                   top1_non_gutenberg=None, per_family=None, rss_gb=round(_rss_gb(), 2),
                   evidence="MemoryError raised by the fit")
        store.log(name, fp, "memory_error", rss_gb=rec["rss_gb"]); store.save(name, fp, rec)
        block.refill()
        print(f"      {name:<30} {rec['status']}", flush=True)
        return rec, None
    secs = round(time.perf_counter() - t, 1)
    sc, correct = score(est, Xs, ys, fam_s)
    stop.set()
    if needs_refill:
        block.refill()
    rec = dict(base, status="fit", seconds=secs, rss_gb=round(_rss_gb(), 2),
               rss_total_gb=round(_rss_total_gb(), 2), rss_gb_is="anonymous (RssAnon)",
               heartbeat_max_rss_gb=box.get("max"),
               ru_maxrss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2),
               fit_info=fit_info(est), block_refills=list(block.refills), **sc)
    store.save(name, fp, rec, correct if keep_per_example else None)
    store.log(name, fp, "completed", seconds=secs)
    print(f"      {name:<30} fit: top1 {sc['top1']:.4f} (ng {sc['top1_non_gutenberg']:.4f}, {secs}s, "
          f"RSS {rec['rss_gb']} GB, {rec['fit_info']})", flush=True)
    return rec, (correct if keep_per_example else None)


def ranked_ids(records):
    """Ids of status-'fit' records by descending top1; ties at 4 decimals to the record listed first."""
    pool = [r for r in records if r.get("status") == "fit" and r.get("top1") is not None]
    out = []
    while pool:
        best = None
        for r in pool:
            if best is None or r["top1"] > best["top1"] + 1e-12:
                best = r
        out.append(best["id"]); pool = [r for r in pool if r is not best]
    return out


# ------------------------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["select", "confirm"], required=True)
    ap.add_argument("--prereg-file", default=os.path.join(REPO, "prereg", "0012-recipe-search-2048.json"))
    ap.add_argument("--cache", default=os.path.join(REPO, "data", "pivot", "carve_c2048.npz"))
    ap.add_argument("--workdir", default=os.path.join(REPO, "artifacts", "pivot", "recipe_search_2048_ckpt"))
    ap.add_argument("--selection-out", default=os.path.join(REPO, "artifacts", "pivot",
                                                            "recipe_search_2048_selection.json"))
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "pivot", "recipe_search_2048.json"))
    ap.add_argument("--scores-out", default=os.path.join(REPO, "artifacts", "pivot",
                                                         "recipe_search_2048_scores.json"))
    ap.add_argument("--smoke", action="store_true",
                    help="override the protocol with the prereg file's 'smoke' block; every output is "
                         "stamped smoke=true and the reader VOIDs it")
    args = ap.parse_args()
    out_stem = os.path.splitext(os.path.basename(args.out))[0]  # recipe_search_2048 / recipe_search_4096
    # Smoke runs write only to the scratchpad; real runs write only under artifacts/. Enforced, not
    # promised: a smoke launched with the defaults would otherwise overwrite a chain-referenced
    # banked artifact, and a smoke at the sealed paths would plant a smoke-stamped selection file
    # that the real --stage select then refuses.
    art = os.path.join(REPO, "artifacts") + os.sep
    outputs = {"--workdir": args.workdir, "--selection-out": args.selection_out, "--out": args.out,
               "--scores-out": args.scores_out}
    under = {k: os.path.abspath(v).startswith(art) for k, v in outputs.items()}
    if args.smoke and any(under.values()):
        print("REFUSING: --smoke with an output path under artifacts/: "
              f"{[k for k, v in under.items() if v]}", file=sys.stderr)
        return 3
    if not args.smoke and not all(under.values()):
        print("REFUSING: a real run must write every output under artifacts/: "
              f"{[k for k, v in under.items() if not v]}", file=sys.stderr)
        return 3
    t_all = time.perf_counter()
    not_run_path = args.out[:-5] + "_not_run.json"

    prereg = json.load(open(args.prereg_file, encoding="utf-8"))
    roster = prereg["scope"]["roster"]
    P = dict(roster["protocol"]); heads = roster["heads"]
    if args.smoke:
        P.update(prereg.get("smoke", {}))
    stamp = f"{prereg['id']}-{prereg['slug']}"
    seed = int(P["seed"]); eval_frac = float(P["eval_frac"]); top_rung = int(P["top_rung"]); caps = P["caps"]
    by_id = {c["id"]: c for h in heads for c in h["candidates"]}
    assert len(by_id) == sum(len(h["candidates"]) for h in heads), "candidate ids must be unique"
    model_head = next(h for h in heads if h["side"] == "model")
    assert model_head["candidates"][0]["id"] == P["incumbent_id"], "the incumbent must lead the model roster"
    env = environment()
    launch_env = {"env": env, "ok": True, "problems": []}
    if env["threads"] != P["threads"]:
        launch_env["problems"].append(f"threads {env['threads']} != preregistered {P['threads']} (all three "
                                      f"of OMP/OPENBLAS/MKL_NUM_THREADS must be set to it)")
    if env["nice"] != P["nice"]:
        launch_env["problems"].append(f"nice {env['nice']} != preregistered {P['nice']}")
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

    # [1] corpus C from its cache, refusing a cache whose build metadata disagrees with the protocol
    # y and g are read without touching X (np.load would read the whole X array); X is memmapped.
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
        # A cache built before build metadata was written (corpus A, 0003) is identified by the
        # sha256 of its y and g arrays, which the preregistration seals; anything else is refused.
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
    print(f"[1] corpus C: {corpus}", flush=True)

    # [2] the sealed split - the reproduced run's by construction (same function, seed, fraction, cap)
    ev, tr, rng = grouped_split(y, g, seed, eval_frac, top_rung)
    fam = lambda idx: np.array([FAMILIES[int(v) % len(FAMILIES)] for v in g[idx]])  # noqa: E731
    ev_chunks = np.unique(g[ev])
    partition = {"seed": seed, "eval_frac": eval_frac, "top_rung": top_rung,
                 "split_is_grouped_by_source": bool(np.intersect1d(ev_chunks, np.unique(g[tr])).size == 0),
                 "n_eval_rows": int(len(ev)), "n_eval_chunks": int(ev_chunks.size),
                 "n_eval_non_gutenberg": int((fam(ev) != "gutenberg").sum()),
                 "eval_idx_sha256": _sha(ev),
                 "n_pool_rows": int(len(tr)), "n_pool_chunks": int(np.unique(g[tr]).size),
                 "pool_idx_sha256": _sha(tr), "pool_y_sha256": _sha(y[tr]),
                 "pool_sorted_sha256": _sha(np.sort(tr).astype(np.int64))}
    rule = P["holdout"]
    if rule["rule"] != "chunk_id_mod":
        raise ValueError(f"unknown holdout rule {rule['rule']!r}")
    in_hold = (g[tr] % int(rule["modulus"])) == int(rule["residue"])
    hold = tr[in_hold]; fitpool = tr[~in_hold]
    stages = []
    for k, st in enumerate(P["stages"]):
        n = len(fitpool) if st["rows"] == "all" else int(st["rows"])
        if n > len(fitpool):
            print(f"REFUSING: stage {k + 1} wants {n} rows, fit pool has {len(fitpool)}", file=sys.stderr); return 3
        stages.append({"rows": fitpool[:n], "keep": int(st["keep"]), "n": n})
    partition.update({
        "holdout_rule": f"chunk_id % {rule['modulus']} == {rule['residue']}",
        "n_holdout_rows": int(len(hold)), "n_holdout_chunks": int(np.unique(g[hold]).size),
        "holdout_idx_sha256": _sha(hold), "holdout_chunks_sha256": _sha(np.sort(np.unique(g[hold])).astype(np.int64)),
        "holdout_chunks_per_family": {f: int(sum(1 for c in np.unique(g[hold]) if FAMILIES[int(c) % 8] == f))
                                      for f in FAMILIES},
        "n_fitpool_rows": int(len(fitpool)), "n_fitpool_chunks": int(np.unique(g[fitpool]).size),
        "fitpool_idx_sha256": _sha(fitpool), "fitpool_chunks_sha256": _sha(np.sort(np.unique(g[fitpool])).astype(np.int64)),
        "stage_rows": [s["n"] for s in stages], "stage_keep": [s["keep"] for s in stages],
        "stage_chunks": [int(np.unique(g[s["rows"]]).size) for s in stages],
        "stage_idx_sha256": [_sha(s["rows"]) for s in stages],
        "stage_sorted_sha256": [_sha(np.sort(s["rows"]).astype(np.int64)) for s in stages],
        "n_chunks_holdout_and_eval": int(np.intersect1d(np.unique(g[hold]), ev_chunks).size),
        "n_chunks_holdout_and_fitpool": int(np.intersect1d(np.unique(g[hold]), np.unique(g[fitpool])).size),
        "n_chunks_fitpool_and_eval": int(np.intersect1d(np.unique(g[fitpool]), ev_chunks).size),
        "n_eval_rows_in_holdout": int(np.intersect1d(hold, ev).size),
        "n_eval_rows_in_fitpool": int(np.intersect1d(fitpool, ev).size),
    })
    print(f"[2] partition: eval {partition['n_eval_rows']}/{partition['n_eval_chunks']} chunks, pool "
          f"{partition['n_pool_rows']}, holdout {partition['n_holdout_rows']}/{partition['n_holdout_chunks']} "
          f"chunks, stages {partition['stage_rows']}; overlaps "
          f"{partition['n_chunks_holdout_and_eval']}/{partition['n_chunks_holdout_and_fitpool']}/"
          f"{partition['n_chunks_fitpool_and_eval']}", flush=True)

    store = Store(args.workdir)
    roster_sha = sha_obj(roster)
    common = {"schema_version": 1, "preregistration": stamp, "smoke": bool(args.smoke), "roster_sha256": roster_sha,
              "roster": roster, "corpus": corpus, "partition": partition, "n_classes": N_CONFIGS,
              "class_names": CONFIG_NAMES, "chance_accuracy": round(1.0 / N_CONFIGS, 6)}

    # ================================================================================ stage select
    if args.stage == "select":
        if os.path.exists(args.selection_out) and not args.smoke:
            print(f"REFUSING: {os.path.relpath(args.selection_out, REPO)} exists; selection is done once",
                  file=sys.stderr)
            return 3
        gathers = []

        def gather_f32(name, rows):
            gathers.append({"name": name, "n_rows": int(len(rows)), "idx_sha256": _sha(rows),
                            "n_eval_rows": int(np.intersect1d(rows, ev).size)})
            return fill_f32(np.empty((len(rows), ncols), np.float32), X, rows, ncols)

        def gather_block(name, rows):
            gathers.append({"name": name, "n_rows": int(len(rows)), "idx_sha256": _sha(rows),
                            "n_eval_rows": int(np.intersect1d(rows, ev).size)})
            return Block(X, rows, ncols, name)

        started = _utc()
        try:
            launch_no = store.launches("select", False)
            Xh = gather_f32("holdout", hold); yh = np.asarray(y[hold]); fam_h = fam(hold)
            selection = {h["id"]: {"side": h["side"], "stages": [], "selected_id": None} for h in heads}
            for si, st in enumerate(stages):
                block = gather_block(f"stage{si + 1}", st["rows"])
                rows_sha = partition["stage_idx_sha256"][si]
                for h in heads:
                    hid = h["id"]; entry = selection[hid]
                    if len(h["candidates"]) == 1:
                        continue      # knob-free heads are fitted only at the confirmatory stage
                    survivors = list(h["candidates"]) if si == 0 else \
                        [c for c in h["candidates"] if c["id"] in entry["stages"][-1]["advanced_ids"]]
                    recs = []
                    for c in survivors:
                        fp = fingerprint(prereg=stamp, seed=seed, head=hid, cand=c, stage=si + 1, rows=rows_sha,
                                         holdout=partition["holdout_idx_sha256"])
                        r, _ = run_fit(store, f"sel{si + 1}_{hid}_{c['id']}", fp, hid, c, seed, block, y, g,
                                       Xh, yh, fam_h, f"selection-{si + 1}", caps)
                        recs.append(r)
                    ranked = ranked_ids(recs)
                    entry["stages"].append({"stage": si + 1, "n_fit_rows": st["n"], "fit_rows_sha256": rows_sha,
                                            "records": recs, "eligible_ranked_ids": ranked,
                                            "advanced_ids": ranked[:st["keep"]]})
                del block
            for hid, entry in selection.items():
                if entry["stages"]:
                    last = entry["stages"][-1]
                    entry["selected_id"] = last["advanced_ids"][0] if last["advanced_ids"] else None
                else:                 # knob-free head: its single candidate is its recipe
                    entry["selected_id"] = next(h for h in heads if h["id"] == hid)["candidates"][0]["id"]
                print(f"      head {hid:<18} selected {entry['selected_id']}", flush=True)
            sel_secs = {hid: round(sum((r.get("seconds") or 0) for st in e["stages"] for r in st["records"]), 1)
                        for hid, e in selection.items()}
            out = dict(common, stage="select", gathers=gathers,
                       eval_rows_gathered_in_selection=int(sum(gt["n_eval_rows"] for gt in gathers)),
                       environment=env, launch_environment=launch_env, launch_number=launch_no,
                       selection=selection, selected_ids={hid: e["selected_id"] for hid, e in selection.items()},
                       ledger=store.ledger(),
                       cost={"selection_seconds_by_head": sel_secs,
                             "selection_seconds_total": round(sum(sel_secs.values()), 1),
                             "wall_seconds_this_invocation": round(time.perf_counter() - t_all, 1),
                             "interruptions_by_head": {hid: sum((r.get("interruptions_before_this_fit") or 0)
                                                                for st in e["stages"] for r in st["records"])
                                                       for hid, e in selection.items()}},
                       selection_started_utc=started, selection_finished_utc=_utc())
        except NotRun as e:
            print(f"NOT RUN: {e}", file=sys.stderr)
            with open(not_run_path, "w") as fh:
                json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp,
                           "stage": "select", "reason": str(e), "utc": _utc(), "smoke": bool(args.smoke),
                           "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])},
                          fh, indent=2)
            return 4
        os.makedirs(os.path.dirname(args.selection_out), exist_ok=True)
        with open(args.selection_out, "w", encoding="utf-8") as fh:
            fh.write(canon(out))
        print(f"[select] wrote {os.path.relpath(args.selection_out, REPO)} in "
              f"{out['cost']['wall_seconds_this_invocation']}s; eval rows gathered: "
              f"{out['eval_rows_gathered_in_selection']}", flush=True)
        return 0

    # =============================================================================== stage confirm
    if not os.path.exists(args.selection_out):
        print(f"REFUSING: {os.path.relpath(args.selection_out, REPO)} absent; run --stage select first",
              file=sys.stderr)
        return 3
    sel_bytes = open(args.selection_out, "rb").read()
    selection_sha = hashlib.sha256(sel_bytes).hexdigest()
    sel_doc = json.loads(sel_bytes)
    if sel_doc.get("roster_sha256") != roster_sha or sel_doc.get("preregistration") != stamp \
            or bool(sel_doc.get("smoke")) != bool(args.smoke):
        print("REFUSING: the selection file was not produced under this preregistration's sealed roster",
              file=sys.stderr)
        return 3
    for e in store.ledger():
        if e.get("name", "").startswith("confirm_") and e.get("selection_sha256") not in (None, selection_sha):
            print("REFUSING: an earlier confirmatory ledger entry carries a different selection hash",
                  file=sys.stderr)
            return 3
    selected = sel_doc["selected_ids"]
    # the winners are READ from the selection file, never re-selected here; they are re-derived
    # only to refuse a tampered file
    for hid, entry in sel_doc["selection"].items():
        if entry["stages"]:
            last = entry["stages"][-1]
            if ranked_ids(last["records"])[:1] != ([entry["selected_id"]] if entry["selected_id"] else []):
                print(f"REFUSING: head {hid}'s selected id is not the rule's winner from its own records",
                      file=sys.stderr)
                return 3

    def assemble(final, per_ex, null_rec, incumbent, l1_rep, complete, missing, launch_no, ci=None):
        def best_over(sides, key):
            floors = P["floors" if key == "top1" else "floors_non_gutenberg"]
            vals = []
            for h in heads:
                if h["side"] in sides and final.get(h["id"], {}).get("status") == "fit":
                    v = final[h["id"]].get(key)
                    if v is not None:
                        vals.append((max(v, floors.get(h["id"], 0.0)), v, h["id"]))
            if not vals:
                return None, None, None
            b = max(vals); return b[0], b[1], b[2]
        fb, fbs, fbh = best_over({"frozen"}, "top1"); fbn, fbns, fbnh = best_over({"frozen"}, "top1_non_gutenberg")
        eb, ebs, ebh = best_over({"frozen", "expanded"}, "top1")
        ebn, ebns, ebnh = best_over({"frozen", "expanded"}, "top1_non_gutenberg")
        fm = final.get(model_head["id"], {})
        out = dict(common, stage="confirm", selection_sha256=selection_sha, selection=sel_doc,
                   selected_ids=selected, selected_model_id=selected.get(model_head["id"]),
                   environment=env, launch_environment=launch_env, launch_number=launch_no,
                   complete=complete, missing_roles=missing, final=final,
                   final_top1=fm.get("top1"), final_top1_non_gutenberg=fm.get("top1_non_gutenberg"),
                   final_per_family=fm.get("per_family"), final_status=fm.get("status"),
                   best_frozen_for_bar=fb, best_frozen_searched=fbs, best_frozen_head=fbh,
                   best_frozen_non_gutenberg_for_bar=fbn, best_frozen_non_gutenberg_searched=fbns,
                   best_expanded_for_bar=eb, best_expanded_searched=ebs, best_expanded_head=ebh,
                   best_expanded_non_gutenberg_for_bar=ebn, best_expanded_non_gutenberg_searched=ebns,
                   best_expanded_non_gutenberg_head=ebnh,
                   incumbent_refit=incumbent, incumbent_refit_top1=(incumbent or {}).get("top1"),
                   logistic_l1_refit=l1_rep, logistic_l1_refit_top1=(l1_rep or {}).get("top1"),
                   null_control=null_rec, shuffled_label_accuracy=(null_rec or {}).get("top1"),
                   null_rows=int(min(len(tr), int(P["null_rows"]))),
                   cluster_ci95_informational=ci or {},
                   cluster_ci95_note=f"95% cluster-bootstrap intervals over the {partition['n_eval_chunks']} "
                                     "evaluation chunks (2000 resamples) on each confirmatory accuracy; "
                                     "informational, never a clause",
                   ledger=store.ledger(),
                   cost={"wall_seconds_this_invocation": round(time.perf_counter() - t_all, 1),
                         "selection_seconds_total": sel_doc["cost"]["selection_seconds_total"],
                         "confirmatory_seconds_by_role": {k: v.get("seconds") for k, v in final.items()},
                         "incumbent_refit_seconds": (incumbent or {}).get("seconds"),
                         "logistic_l1_refit_seconds": (l1_rep or {}).get("seconds"),
                         "null_seconds": (null_rec or {}).get("seconds"),
                         "confirmatory_interruptions": {k: v.get("interruptions_before_this_fit") for k, v in final.items()},
                         "banked_fit_seconds_total": round(store.banked_seconds("sel") + store.banked_seconds("confirm"), 1),
                         "checkpoints": os.path.relpath(args.workdir, REPO)},
                   confirmatory_started_utc=started)
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out + ".tmp", "w") as fh:
            json.dump(out, fh, indent=2, sort_keys=True); fh.write("\n")
        os.replace(args.out + ".tmp", args.out)
        with open(args.scores_out + ".tmp", "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_scores/1", "preregistration": stamp,
                       "smoke": bool(args.smoke), "eval_idx_sha256": partition["eval_idx_sha256"],
                       "eval_chunk_ids": g[ev].tolist(),
                       "per_example": {k: v.tolist() for k, v in per_ex.items()}}, fh)
        os.replace(args.scores_out + ".tmp", args.scores_out)
        return out

    started = _utc()
    try:
        any_conf = any(f.startswith("confirm_") and f.endswith(".json") for f in os.listdir(args.workdir))
        launch_no = store.launches("confirm", any_conf)
        Xe = fill_f32(np.empty((len(ev), ncols), np.float32), X, ev, ncols)
        ye = np.asarray(y[ev]); fam_e = fam(ev)
        partition["eval_y_sha256"] = _sha(ye)
        pool = Block(X, tr, ncols, "pool")
        print(f"[confirm] pool {len(tr)} rows and eval {len(ev)} rows materialised, anonymous RSS "
              f"{_rss_gb():.2f} GB (total {_rss_total_gb():.2f} GB)",
              flush=True)
        final, per_ex = {}, {}
        roles_done = []

        def confirm(name, hid, c, block=None):
            fp = fingerprint(prereg=stamp, seed=seed, head=hid, cand=c, stage="confirm",
                             rows=partition["pool_idx_sha256"], eval=partition["eval_idx_sha256"],
                             selection=selection_sha)
            store.log(name, fp, "selection_bound", selection_sha256=selection_sha)
            r, pe = run_fit(store, name, fp, hid, c, seed, block or pool, y, g, Xe, ye, fam_e, "confirmatory",
                            caps, keep_per_example=True, confirmatory=True)
            roles_done.append(name)
            return r, pe

        inc = by_id[P["incumbent_id"]]; l1 = by_id[P["logistic_l1_id"]]
        mh = model_head["id"]; lh = P["logistic_head_id"]
        order = P["confirm_order"]
        incumbent = l1_rep = null_rec = None
        for role in order:
            if role == "incumbent":
                if selected.get(mh) == inc["id"]:
                    continue                      # the model's own fit doubles as the reproduction
                incumbent, pe = confirm("confirm_incumbent", "incumbent", inc)
                per_ex["incumbent"] = pe
            elif role == "logistic_l1":
                if selected.get(lh) == l1["id"]:
                    continue
                l1_rep, pe = confirm("confirm_logistic_l1", "logistic_l1", l1)
                per_ex["logistic_l1"] = pe
            elif role == "null":
                nn = min(len(tr), int(P["null_rows"]))
                y_sh = np.asarray(y[tr[:nn]]).copy(); rng.shuffle(y_sh)
                c_sel = by_id[selected[mh]]
                null_block = Block(X, tr[:nn], ncols, "null")
                y_view = y.copy(); y_view[tr[:nn]] = y_sh       # shuffled labels for the null block only
                fp = fingerprint(prereg=stamp, seed=seed, head="null", cand=c_sel, stage="null",
                                 rows=partition["pool_idx_sha256"], n=nn, eval=partition["eval_idx_sha256"],
                                 selection=selection_sha)
                store.log("confirm_null", fp, "selection_bound", selection_sha256=selection_sha)
                null_rec, _ = run_fit(store, "confirm_null", fp, "null", c_sel, seed, null_block, y_view, g,
                                      Xe, ye, fam_e, "null", caps, confirmatory=True)
                del null_block, y_view
                roles_done.append("confirm_null")
            elif role == "model":
                final[mh], pe = confirm(f"confirm_{mh}", mh, by_id[selected[mh]])
                per_ex[mh] = pe
                if incumbent is None:
                    incumbent = dict(final[mh])
            else:                                  # a baseline head
                h = next(x for x in heads if x["id"] == role)
                cid = selected.get(role)
                if cid is None:
                    final[role] = {"status": "no_eligible_candidate", "id": None}
                else:
                    final[role], pe = confirm(f"confirm_{role}", role, by_id[cid])
                    per_ex[role] = pe
                    if role == lh and cid == l1["id"]:
                        l1_rep = dict(final[role])
            missing = [r for r in order if (f"confirm_{r}" not in roles_done)
                       and not (r == "incumbent" and selected.get(mh) == inc["id"])
                       and not (r == "logistic_l1" and selected.get(lh) == l1["id"])]
            assemble(final, per_ex, null_rec, incumbent, l1_rep, complete=False, missing=missing,
                     launch_no=launch_no)
        ge = np.asarray(g[ev])
        ci = {k: cluster_ci(v, ge, seed=seed) for k, v in per_ex.items() if v is not None}
        out = assemble(final, per_ex, null_rec, incumbent, l1_rep, complete=True, missing=[],
                       launch_no=launch_no, ci=ci)
    except NotRun as e:
        print(f"NOT RUN: {e}", file=sys.stderr)
        with open(not_run_path, "w") as fh:
            json.dump({"schema": f"raise-v1/{out_stem}_not_run/1", "preregistration": stamp,
                       "stage": "confirm", "reason": str(e), "utc": _utc(), "smoke": bool(args.smoke),
                       "n_checkpoints": len([f for f in os.listdir(args.workdir) if f.endswith(".json")])},
                      fh, indent=2)
        return 4
    print(f"[confirm] wrote {os.path.relpath(args.out, REPO)} in {out['cost']['wall_seconds_this_invocation']}s; "
          f"model {out['selected_model_id']} {out['final_top1']} vs bars frozen {out['best_frozen_for_bar']} / "
          f"expanded {out['best_expanded_for_bar']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
