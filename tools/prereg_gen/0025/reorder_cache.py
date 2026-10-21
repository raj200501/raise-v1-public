#!/usr/bin/env python3
"""Put a rebuilt builder cache into a documented canonical row order that reproduces the sealed evaluation sequence.

Why. tools/pivot/run_study.py build() writes rows in the order in which Pool(4).imap_unordered(_one, tasks, chunksize=8)
hands back its BATCHES (8 consecutive tasks = 8 consecutive chunk ids starting at chunk_offset + 8k). A batch comes back
whole, its chunks in task order, each chunk's rows in configuration order; but the batches arrive in completion order,
which is timing and cannot be reproduced. A rebuild therefore holds the same rows in another batch order. The sealed
evaluation chunk sequence (scope.eval_chunk_layout) fixes the relative order of the batches that contain evaluation
chunks; nothing banked fixes the order of the batches that contain none. This tool writes the rebuilt rows in the
following order, which is a function of the cache's chunk-id SET and the preregistration alone (so every rebuild whose
per-chunk rows are identical reorders to byte-identical arrays):

  CANONICAL ORDER (batch = (chunk_id - chunk_offset) // 8)
    (i)   every batch is kept whole: its rows are contiguous, in ascending chunk id, and a chunk's rows keep the order
          they have in the input cache (the builder's configuration order);
    (ii)  batches that contain at least one evaluation chunk ("evaluation batches") come in the order of their first
          appearance in the sealed eval_chunk_layout.chunk_ids;
    (iii) every batch with no evaluation chunk is placed immediately after its id-predecessor (the present batch with
          the next lower id): equivalently, each maximal run of consecutive evaluation-free batch ids is placed, ascending,
          directly after the evaluation batch that precedes the run in id order; a run below the lowest evaluation batch
          goes first. Rationale: it is deterministic, needs no information that is not banked, keeps every
          evaluation-free batch next to its id-neighbour (the completion order is near-ascending: no evaluation batch is
          displaced by more than 3 places from ascending order), and on full_c4096 it puts the five batches whose absolute
          positions ARE banked (artifacts/pivot/builder_duplicate_chunks.json pool_row_indices, batches 1750, 2172, 2666,
          5336, 6002) at exactly their banked positions.

Then it ASSERTS, on the in-memory permuted y/g before X is written and again on the file as written, that the runner's
own grouped split (tools/pivot/run_carve.py grouped_split: groups = np.unique(g); rng = default_rng(seed);
rng.shuffle(groups); the first int(len * eval_frac) groups are evaluation; eval rows = np.nonzero(is_ev)[0]) returns
evaluation rows whose chunk ids, run-length encoded, are exactly eval_chunk_layout.chunk_ids / rows_per_chunk, and whose
y and g hash to the sealed eval_y_sha256 / eval_g_sha256 (sha256 of np.ascontiguousarray(a).tobytes()). It also checks,
with an order-invariant fingerprint over (chunk id, ordinal within chunk, row bytes), that the output X is exactly the
input's rows under rule (i).

Output: np.savez's container exactly (ZIP_STORED, zip64, entries X.npy, y.npy, g.npy, build_s.npy in that order, the same
.npy headers), so tools/pivot/npzmap.py maps X in place. X is read with os.preadv at the payload offset npzmap computes
(not through the memory map, whose page faults pull large page-cache folios into RSS) and streamed into the zip entry
block by block: the process holds at most a couple of blocks of X (default 20000 rows = 89 MB each) and writes no
temporary copy; the only extra disk is the output itself (5.76 GB for full_c4096). The output is written to OUT.partial
and renamed only after every assertion has passed.

What it cannot do: the rows' absolute positions in the banked cache are not banked, so the reordered cache's X and g
hashes and every position hash (eval_idx_sha256, pool_idx_sha256, pool_sorted_sha256) differ from the sealed ones and are
printed for re-sealing; y and pool_y_sha256 are order-invariant here (every chunk has 26 rows in label order) and match.

Prints the new X/y/g hashes in tools/pivot/corpus_manifest.py's convention (sha256 of the contiguous array bytes; X
hashed in 20000-row blocks, which is the same digest).

usage: reorder_cache.py CACHE PREREG -o OUT [--repo REPO] [--block-rows N] [--report JSON] [--skip-content-check]
exit:  0 ok; 2 refused (bad input / arguments); 3 an order or content assertion failed (no output left behind)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import zipfile

import numpy as np

BATCH = 8                    # run_study.build(): pool.imap_unordered(_one, tasks, chunksize=8)
ENTRIES = ["X.npy", "y.npy", "g.npy", "build_s.npy"]   # run_study.main(): np.savez(cache, X=X, y=y, g=g, build_s=build_s)
MANIFEST_BLOCK = 20000       # tools/pivot/corpus_manifest.py digest() block


class Refused(Exception):
    pass


class AssertFailed(Exception):
    pass


def check(cond, msg):
    if not cond:
        raise AssertFailed(msg)


def sha(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


# ---------------------------------------------------------------- repo helpers (imported, never modified)
def find_repo(explicit):
    cands = [explicit] if explicit else []
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    for _ in range(6):
        cands.append(d)
        d = os.path.dirname(d)
    cands.append(os.getcwd())
    for c in cands:
        if c and os.path.exists(os.path.join(c, "tools", "pivot", "npzmap.py")):
            return os.path.abspath(c)
    raise Refused("cannot find the repository (tools/pivot/npzmap.py); pass --repo")


def import_repo(repo):
    sys.dont_write_bytecode = True          # never write __pycache__ into the repository
    sys.path.insert(0, os.path.join(repo, "tools", "pivot"))
    from npzmap import npz_memmap          # noqa: E402
    try:
        from run_carve import grouped_split  # noqa: E402  - the runners' function itself
        src = "tools/pivot/run_carve.py grouped_split (imported)"
    except Exception as e:  # noqa: BLE001
        grouped_split = _grouped_split_copy
        src = f"verbatim copy of tools/pivot/run_carve.py grouped_split (import failed: {type(e).__name__}: {e})"
    return npz_memmap, grouped_split, src


def _grouped_split_copy(y, g, seed, eval_frac, cap):
    rng = np.random.default_rng(seed)
    groups = np.unique(g); rng.shuffle(groups)
    ev_groups = set(groups[:max(1, int(len(groups) * eval_frac))].tolist())
    is_ev = np.fromiter((int(v) in ev_groups for v in g), bool, len(g))
    tr = np.nonzero(~is_ev)[0]; rng.shuffle(tr)
    return np.nonzero(is_ev)[0], tr[:min(len(tr), cap)], rng


# ---------------------------------------------------------------- the preregistration
def load_sealed(path):
    pr = json.load(open(path, encoding="utf-8"))
    S = pr.get("scope") or {}
    P = None
    for keys in (("curve", "protocol"), ("roster", "protocol"), ("protocol",)):
        o = S
        for k in keys:
            o = o.get(k) if isinstance(o, dict) else None
        if isinstance(o, dict) and "seed" in o and "eval_frac" in o:
            P = o; ppath = "scope." + ".".join(keys); break
    if P is None:
        raise Refused(f"{path}: no protocol with seed and eval_frac under scope.curve / scope.roster / scope")
    lay = S.get("eval_chunk_layout")
    ev = (S.get("sealed_partition") or {}).get("eval") or {}
    if not lay or "chunk_ids" not in lay or "rows_per_chunk" not in lay:
        raise Refused(f"{path}: no scope.eval_chunk_layout with chunk_ids and rows_per_chunk")
    for k in ("eval_y_sha256", "eval_g_sha256"):
        if k not in ev:
            raise Refused(f"{path}: scope.sealed_partition.eval has no {k}")
    return {"id": pr.get("id"), "protocol_path": ppath,
            "seed": int(P["seed"]), "eval_frac": float(P["eval_frac"]),
            "top_rung": int(P.get("top_rung", 10 ** 12)), "chunk_offset": int(P.get("chunk_offset", 0)),
            "chunk_ids": np.asarray(lay["chunk_ids"], dtype=np.int64),
            "rows_per_chunk": np.asarray(lay["rows_per_chunk"], dtype=np.int64),
            "layout_g_sha256": lay.get("g_sha256"),
            "eval": ev, "pool": (S.get("sealed_partition") or {}).get("pool") or {},
            "cache_identity": P.get("cache_identity") or {}}


# ---------------------------------------------------------------- the order
def rle(a):
    a = np.asarray(a)
    if len(a) == 0:
        return np.empty(0, np.int64), np.empty(0, np.int64)
    starts = np.r_[0, np.nonzero(a[1:] != a[:-1])[0] + 1]
    return a[starts].astype(np.int64), np.diff(np.r_[starts, len(a)]).astype(np.int64)


def check_layout_is_batch_major(chunk_ids, chunk_offset):
    """The sealed sequence must be reproducible by whole batches: each batch's chunks contiguous and ascending."""
    b = (chunk_ids - chunk_offset) // BATCH
    runs, _ = rle(b)
    if len(np.unique(chunk_ids)) != len(chunk_ids):
        raise Refused("the sealed eval_chunk_layout repeats a chunk id")
    if len(runs) != len(np.unique(b)):
        raise Refused("the sealed eval_chunk_layout splits a batch: no batch-preserving order can reproduce it")
    same = b[1:] == b[:-1]
    if not np.all(np.diff(chunk_ids)[same] > 0):
        raise Refused("the sealed eval_chunk_layout has chunks of one batch out of task order")
    d = np.diff(chunk_ids)
    return {"n_eval_chunks": int(len(chunk_ids)), "n_eval_batches": int(len(runs)),
            "n_descents": int((d < 0).sum()), "n_descents_inside_a_batch": int(((d < 0) & same).sum())}


def canonical_batch_order(present, eval_batch_order):
    """present: ascending batch ids in the cache; eval_batch_order: evaluation batches in sealed first-appearance order."""
    is_eval = np.isin(present, eval_batch_order)
    head, tail, last = [], {}, None
    for b, e in zip(present.tolist(), is_eval.tolist()):
        if e:
            last = b; tail[b] = []
        else:
            (head if last is None else tail[last]).append(b)
    order = list(head)
    for e in eval_batch_order.tolist():
        order.append(e); order.extend(tail[e])
    order = np.asarray(order, dtype=np.int64)
    assert len(order) == len(present) and np.array_equal(np.sort(order), present)
    return order, int((~is_eval).sum())


def canonical_permutation(g, sealed):
    off = sealed["chunk_offset"]
    g64 = np.asarray(g, dtype=np.int64)
    if (g64 < off).any():
        raise Refused(f"the cache holds chunk ids below chunk_offset {off}")
    bid = (g64 - off) // BATCH
    present = np.unique(bid)
    seq_b = (sealed["chunk_ids"] - off) // BATCH
    _, first = np.unique(seq_b, return_index=True)
    eval_batch_order = seq_b[np.sort(first)]
    missing = np.setdiff1d(eval_batch_order, present)
    if missing.size:
        raise Refused(f"{missing.size} batches holding sealed evaluation chunks are absent from the cache (e.g. {missing[:5].tolist()})")
    order, n_free = canonical_batch_order(present, eval_batch_order)
    slot_of_present = np.empty(len(present), dtype=np.int64)
    slot_of_present[np.searchsorted(present, order)] = np.arange(len(order))
    row_slot = slot_of_present[np.searchsorted(present, bid)]
    perm = np.lexsort((g64, row_slot))          # stable: rows of one chunk keep their input order
    return perm, order, {"n_batches": int(len(present)), "n_eval_batches": int(len(eval_batch_order)),
                         "n_eval_free_batches": n_free}


def input_shape_report(g, off):
    """Informational: is the input itself batch-major (as the builder writes it)?"""
    b = (np.asarray(g, np.int64) - off) // BATCH
    runs, _ = rle(b)
    gr, _ = rle(g)
    same = b[1:] == b[:-1]
    return {"batch_major": bool(len(runs) == len(np.unique(b))),
            "chunks_contiguous": bool(len(gr) == len(np.unique(g))),
            "chunks_ascending_within_batches": bool(np.all(np.diff(np.asarray(g, np.int64))[same] >= 0))}


# ---------------------------------------------------------------- the assertions
def order_proof(y, g, sealed, grouped_split, where):
    ev, tr, _ = grouped_split(y, g, sealed["seed"], sealed["eval_frac"], sealed["top_rung"])
    ids, counts = rle(np.asarray(g)[ev])
    E = sealed["eval"]
    res = {"n_eval_rows": int(len(ev)),
           "chunk_sequence_equals_sealed": bool(np.array_equal(ids, sealed["chunk_ids"])),
           "rows_per_chunk_equal_sealed": bool(np.array_equal(counts, sealed["rows_per_chunk"])),
           "eval_g_sha256": sha(np.asarray(g)[ev]), "eval_y_sha256": sha(np.asarray(y)[ev])}
    check(res["chunk_sequence_equals_sealed"],
          f"[{where}] evaluation chunk sequence differs from the sealed eval_chunk_layout "
          f"({len(ids)} chunks vs {len(sealed['chunk_ids'])}; first difference at "
          f"{int(np.argmax(ids[:min(len(ids), len(sealed['chunk_ids']))] != sealed['chunk_ids'][:min(len(ids), len(sealed['chunk_ids']))])) if len(ids) and len(sealed['chunk_ids']) else 0})")
    check(res["rows_per_chunk_equal_sealed"], f"[{where}] evaluation rows per chunk differ from the sealed rows_per_chunk")
    check(res["eval_g_sha256"] == E["eval_g_sha256"],
          f"[{where}] eval g hashes to {res['eval_g_sha256'][:16]}..., sealed {E['eval_g_sha256'][:16]}...")
    if sealed["layout_g_sha256"]:
        check(res["eval_g_sha256"] == sealed["layout_g_sha256"], f"[{where}] eval g differs from eval_chunk_layout.g_sha256")
    check(res["eval_y_sha256"] == E["eval_y_sha256"],
          f"[{where}] eval y hashes to {res['eval_y_sha256'][:16]}..., sealed {E['eval_y_sha256'][:16]}...")
    if "n_rows" in E:
        check(len(ev) == int(E["n_rows"]), f"[{where}] {len(ev)} evaluation rows, sealed {E['n_rows']}")
    if "n_chunks" in E:
        check(len(ids) == int(E["n_chunks"]), f"[{where}] {len(ids)} evaluation chunks, sealed {E['n_chunks']}")
    # informational: position-dependent hashes a rebuild cannot reproduce (reported, never asserted)
    P = sealed["pool"]
    info = {"eval_idx_sha256": sha(ev), "pool_idx_sha256": sha(tr), "pool_sorted_sha256": sha(np.sort(tr).astype(np.int64)),
            "pool_y_sha256": sha(np.asarray(y)[tr])}
    info_cmp = {k: (v == (E if k.startswith("eval") else P).get(k)) for k, v in info.items()
                if (E if k.startswith("eval") else P).get(k)}
    return res, info, info_cmp


def chunk_ordinals(g):
    """k[i] = number of earlier rows (in array order) with the same chunk id."""
    g = np.asarray(g)
    s = np.argsort(g, kind="stable")
    gs = g[s]
    starts = np.r_[0, np.nonzero(gs[1:] != gs[:-1])[0] + 1]
    lens = np.diff(np.r_[starts, len(g)])
    k = np.empty(len(g), dtype=np.int64)
    k[s] = np.arange(len(g)) - np.repeat(starts, lens)
    return k


class RowReader:
    """Reads rows of a 2-D array stored in an uncompressed .npz with os.preadv at the offset tools/pivot/npzmap.py computes.

    Reading through the np.memmap instead maps whole large page-cache folios into the process on every fault: measured
    here, 2000 scattered rows of a 0.92 GB file put 0.90 GB of file pages into RSS. pread keeps RSS at the buffers.
    """

    def __init__(self, mm):
        self.path, self.off = mm.filename, int(mm.offset)
        self.shape, self.dtype = tuple(mm.shape), mm.dtype
        self.rowbytes = int(mm.shape[1]) * mm.dtype.itemsize
        self.fd = os.open(self.path, os.O_RDONLY)

    def __len__(self):
        return self.shape[0]

    def close(self):
        os.close(self.fd)

    def _read_into(self, buf, offset):
        mv = memoryview(buf).cast("B"); done = 0
        while done < len(mv):
            n = os.preadv(self.fd, [mv[done:]], offset + done)
            if n <= 0:
                raise IOError(f"{self.path}: short read at {offset + done}")
            done += n

    def block(self, i, j):
        out = np.empty((j - i, self.shape[1]), self.dtype)
        self._read_into(out, self.off + i * self.rowbytes)
        return out

    def gather(self, idx):
        """rows idx (any order) -> array in idx order; consecutive source rows are read in one call."""
        idx = np.asarray(idx, dtype=np.int64)
        o = np.argsort(idx, kind="stable"); s = idx[o]
        got = np.empty((len(idx), self.shape[1]), self.dtype)
        if len(s):
            brk = np.r_[0, np.nonzero(np.diff(s) != 1)[0] + 1, len(s)]
            for a_, b_ in zip(brk[:-1], brk[1:]):
                self._read_into(got[a_:b_], self.off + int(s[a_]) * self.rowbytes)
        out = np.empty_like(got); out[o] = got
        return out


def scan(rd, g, block, want_sha=True, want_fp=True):
    """One sequential pass: sha256 of the contiguous bytes (corpus_manifest convention) and an order-invariant
    fingerprint sum over rows of blake2b-128(chunk id, ordinal within chunk, row bytes)."""
    h = hashlib.sha256() if want_sha else None
    fp = 0
    k = chunk_ordinals(g) if want_fp else None
    g = np.asarray(g)
    for i in range(0, len(rd), block):
        blk = rd.block(i, min(i + block, len(rd)))
        if h is not None:
            h.update(blk)
        if want_fp:
            for j in range(len(blk)):
                d = hashlib.blake2b(digest_size=16)
                d.update(np.int64(g[i + j]).tobytes()); d.update(np.int64(k[i + j]).tobytes()); d.update(blk[j])
                fp += int.from_bytes(d.digest(), "little")
    return (h.hexdigest() if h is not None else None), (fp % (1 << 128) if want_fp else None)


# ---------------------------------------------------------------- the writer (np.savez's container, X streamed)
def write_npz_streamed(out, X, perm, y2, g2, build_s, block):
    """X: a RowReader (or any 2-D array: a test may pass an ndarray)."""
    # Byte-for-byte what np.savez(out, X=X[perm], y=y2, g=g2, build_s=build_s) writes, without materialising X[perm].
    hx = hashlib.sha256()
    n, ncols = len(perm), X.shape[1]
    with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        with zf.open("X.npy", "w", force_zip64=True) as fid:
            np.lib.format.write_array_header_1_0(
                fid, {"descr": np.lib.format.dtype_to_descr(X.dtype), "fortran_order": False, "shape": (n, ncols)})
            for i in range(0, n, block):
                idx = perm[i:i + block]
                blk = X.gather(idx) if isinstance(X, RowReader) else np.ascontiguousarray(X[idx])
                hx.update(blk)
                fid.write(memoryview(blk).cast("B"))
                del blk
        for name, arr in (("y", y2), ("g", g2), ("build_s", np.asanyarray(build_s))):
            with zf.open(name + ".npy", "w", force_zip64=True) as fid:
                np.lib.format.write_array(fid, np.asanyarray(arr), allow_pickle=True, pickle_kwargs=None)
    return hx.hexdigest()


def rss_gb():
    try:
        with open("/proc/self/status") as fh:
            v = {ln.split(":")[0]: int(ln.split()[1]) for ln in fh if ln.startswith(("VmHWM", "VmRSS", "RssAnon"))}
        return {k: round(x / 1e6, 3) for k, x in v.items()}
    except OSError:
        return {}


# ---------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cache", help="rebuilt cache (.npz written by tools/pivot/run_study.py)")
    ap.add_argument("prereg", help="preregistration JSON carrying scope.eval_chunk_layout and scope.sealed_partition.eval")
    ap.add_argument("-o", "--out", required=True, help="output .npz (refused if it exists or is the input)")
    ap.add_argument("--repo", default=None, help="repository root (for tools/pivot/npzmap.py and run_carve.py)")
    ap.add_argument("--block-rows", type=int, default=MANIFEST_BLOCK)
    ap.add_argument("--report", default=None, help="also write the hashes, checks and rule as JSON here")
    ap.add_argument("--skip-content-check", action="store_true",
                    help="skip the two sequential fingerprint passes over X (the order proof is never skipped)")
    a = ap.parse_args(argv)
    t0 = time.perf_counter()
    try:
        if os.path.exists(a.out) or os.path.exists(a.out + ".partial"):
            raise Refused(f"{a.out} (or {a.out}.partial) exists; refusing to overwrite")
        if os.path.realpath(a.out) == os.path.realpath(a.cache):
            raise Refused("the output must not be the input")
        repo = find_repo(a.repo)
        npz_memmap, grouped_split, split_src = import_repo(repo)
        sealed = load_sealed(a.prereg)
        lay_rep = check_layout_is_batch_major(sealed["chunk_ids"], sealed["chunk_offset"])

        with zipfile.ZipFile(a.cache) as zf:
            names = zf.namelist()
            if sorted(names) != sorted(ENTRIES):
                raise Refused(f"{a.cache} holds {names}, not run_study.py's {ENTRIES}")
            if any(zf.getinfo(nm).compress_type != zipfile.ZIP_STORED for nm in names):
                raise Refused(f"{a.cache} has a compressed entry; run_study.py writes stored entries")
            y = np.load(io.BytesIO(zf.read("y.npy")), allow_pickle=False)
            g = np.load(io.BytesIO(zf.read("g.npy")), allow_pickle=False)
            build_s = np.load(io.BytesIO(zf.read("build_s.npy")), allow_pickle=False)
        mm = npz_memmap(a.cache, "X")              # parses the header and locates the payload exactly as the runners do
        if not (mm.ndim == 2 and len(mm) == len(y) == len(g)):
            raise Refused(f"shapes disagree: X {mm.shape}, y {y.shape}, g {g.shape}")
        if (mm.dtype, y.dtype, g.dtype) != (np.dtype(np.float32), np.dtype(np.int16), np.dtype(np.int32)):
            raise Refused(f"dtypes X {mm.dtype}, y {y.dtype}, g {g.dtype}; run_study.py writes float32, int16, int32")
        X = RowReader(mm); del mm
        print(f"[1] {a.cache}: {X.shape[0]} rows x {X.shape[1]} features, {len(np.unique(g))} chunks; "
              f"preregistration {sealed['id']} ({sealed['protocol_path']}: seed {sealed['seed']}, eval_frac {sealed['eval_frac']}, "
              f"top_rung {sealed['top_rung']}, chunk_offset {sealed['chunk_offset']})", flush=True)
        print(f"    sealed layout: {lay_rep}", flush=True)
        in_shape = input_shape_report(g, sealed["chunk_offset"])
        print(f"    input: {in_shape}", flush=True)

        perm, order, ordrep = canonical_permutation(g, sealed)
        y2 = np.ascontiguousarray(y[perm]); g2 = np.ascontiguousarray(g[perm])
        print(f"[2] canonical order: {ordrep}; split = {split_src}", flush=True)
        out_shape = input_shape_report(g2, sealed["chunk_offset"])
        check(out_shape["batch_major"] and out_shape["chunks_contiguous"] and out_shape["chunks_ascending_within_batches"],
              f"the permutation broke batch structure: {out_shape}")
        pre, info, info_cmp = order_proof(y2, g2, sealed, grouped_split, "before writing")
        print(f"    order proof (in memory): {pre}", flush=True)

        fp_in = None
        if not a.skip_content_check:
            sha_in, fp_in = scan(X, g, a.block_rows)
            print(f"[3] input pass: X sha256 {sha_in} (the rebuild as built), fingerprint {fp_in:032x}, "
                  f"{time.perf_counter() - t0:.0f}s, mem {rss_gb()}", flush=True)
        else:
            sha_in = None

        part = a.out + ".partial"
        try:
            sha_written = write_npz_streamed(part, X, perm, y2, g2, build_s, a.block_rows)
            print(f"[4] wrote {part} ({os.path.getsize(part)} bytes), {time.perf_counter() - t0:.0f}s, mem {rss_gb()}", flush=True)
            # ---- re-verify from the file as written
            with zipfile.ZipFile(part) as zf:
                check(zf.namelist() == ENTRIES, f"written entries {zf.namelist()}")
                check(all(i.compress_type == zipfile.ZIP_STORED for i in zf.infolist()), "an entry is compressed")
                yw = np.load(io.BytesIO(zf.read("y.npy"))); gw = np.load(io.BytesIO(zf.read("g.npy")))
                bw = np.load(io.BytesIO(zf.read("build_s.npy")))
            check(np.array_equal(yw, y2) and yw.dtype == y.dtype and np.array_equal(gw, g2) and gw.dtype == g.dtype,
                  "y/g read back differ")
            check(bw.shape == build_s.shape and bw.dtype == build_s.dtype and float(bw) == float(build_s), "build_s read back differs")
            mw = npz_memmap(part, "X")             # the runners' reader must be able to map it
            check(isinstance(mw, np.memmap) and mw.shape == X.shape and mw.dtype == X.dtype, f"X maps as {mw.shape} {mw.dtype}")
            Xw = RowReader(mw); del mw
            post, info2, info_cmp2 = order_proof(yw, gw, sealed, grouped_split, "file as written")
            check(post == pre, "the order proof differs between memory and file")
            sha_x, fp_out = scan(Xw, gw, MANIFEST_BLOCK, True, not a.skip_content_check)
            check(sha_x == sha_written, "X re-read from the file hashes differently from the bytes streamed into it")
            if fp_in is not None:
                check(fp_out == fp_in, "content check: the output's rows are not the input's rows under rule (i)")
            rs = np.sort(np.random.default_rng(0).choice(len(perm), size=min(2000, len(perm)), replace=False))
            check(np.array_equal(Xw.gather(rs), X.gather(perm[rs])), "spot check of X rows failed")
            Xw.close()
        except BaseException:
            if os.path.exists(part):
                os.remove(part)
            raise
        os.replace(part, a.out)

        new = {"X": {"sha256": sha_x, "shape": list(X.shape), "dtype": str(X.dtype)},
               "y": {"sha256": sha(yw), "shape": list(yw.shape), "dtype": str(yw.dtype)},
               "g": {"sha256": sha(gw), "shape": list(gw.shape), "dtype": str(gw.dtype)}}
        ci = sealed["cache_identity"]
        vs_sealed = {k: (new[k]["sha256"] == ci.get(f"{k}_sha256")) for k in ("X", "y", "g") if ci.get(f"{k}_sha256")}
        print(f"[5] wrote {a.out}")
        print(f"    ORDER PROOF PASSED: {post['n_eval_rows']} evaluation rows in the sealed {len(sealed['chunk_ids'])}-chunk "
              f"sequence; eval_y_sha256 {post['eval_y_sha256']}; eval_g_sha256 {post['eval_g_sha256']}")
        print(f"    content check: {'PASSED (fingerprints equal)' if fp_in is not None else 'skipped'}")
        print("    new hashes (corpus_manifest.py convention):")
        for k in ("X", "y", "g"):
            print(f"      {k}: {new[k]['sha256']}  {new[k]['shape']} {new[k]['dtype']}")
        print(f"    vs the preregistration's cache_identity (informational): {vs_sealed}")
        print(f"    position hashes on the reordered cache (informational, a rebuild cannot reproduce these): "
              f"{ {k: (v[:16] + '...', info_cmp2.get(k)) for k, v in info2.items()} }")
        print(f"    {time.perf_counter() - t0:.0f}s, mem {rss_gb()}")
        if a.report:
            rep = {"schema": "raise-v1/reorder_cache/1", "input": os.path.abspath(a.cache), "output": os.path.abspath(a.out),
                   "preregistration": os.path.abspath(a.prereg), "preregistration_id": sealed["id"],
                   "rule": __doc__.split("CANONICAL ORDER")[1].split("Then it ASSERTS")[0].strip(),
                   "split_function": split_src, "sealed_layout": lay_rep, "input_shape": in_shape, "order": ordrep,
                   "input_X_sha256": sha_in, "order_proof": post, "content_check": fp_in is not None,
                   "new_hashes": new, "new_equals_cache_identity": vs_sealed,
                   "position_hashes": info2, "position_hashes_equal_sealed": info_cmp2,
                   "batch_order_sha256": sha(order), "seconds": round(time.perf_counter() - t0, 1), "memory_gb": rss_gb()}
            with open(a.report, "w", encoding="utf-8") as fh:
                json.dump(rep, fh, indent=2, sort_keys=True); fh.write("\n")
        return 0
    except Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    except AssertFailed as e:
        print(f"ASSERTION FAILED: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
