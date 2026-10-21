#!/usr/bin/env python3
"""CI determinism probe: per-chunk determinism of the corpus primitives, and the real build()'s rows as a SET.

This probe does not execute the manifest proof (tools/pivot/corpus_manifest.py --check) and compares nothing with a banked
hash: it compares builds made in the same container with each other. It manufactures a SMALL slice three times with the
per-chunk primitives the real build uses (tools/pivot/corpus.py chunk_fragments + tools/pivot/features.py features_many) and
fails unless the sha256 of the X, y and g arrays is identical across those builds. A fourth build calls run_study.py's real
build() itself (Pool and imap_unordered, 2 processes) on the same slice and fails unless its rows, sorted by chunk id and
label, are byte-identical to the canonical assembly: the property the real build does have. Whether its rows came out in
canonical order is printed, never required (CORRECTIONS.md 2026-10-21: the CI-probe entry).

It also proves that per-chunk generation is order-independent: chunk i's bytes depend only on i,
never on which chunks were built before it (no shared RNG or module state leaking between chunks).
Build 3 therefore manufactures the same chunks in REVERSED order, reassembles them in canonical
order, and must reproduce the same hashes.

What it does NOT prove: that the real build's ROW ORDER is reproducible. It is not. run_study.py's
build() feeds a multiprocessing Pool with imap_unordered (chunksize 8) and writes each finished
batch at the next free row, and nothing sorts the rows before the cache is saved, so the row order
of a cache it builds (full_c4096, and carve_c1024/carve_c2048 through run_carve.py) depends on
worker scheduling; order-independence makes the SET of rows reproducible, not their order. The
canonical-order assembly below is this probe's own, not the real build's. build() is deliberately
left as it is: a different behaviour would make the banked corpora impossible to reason about
(cold-clone audit D1).

Scale is deliberately small (~40 chunks) so it finishes in well under 3 minutes on 2 CPUs, and the
chunk offset (900400) is far past any index range used to build training data, so this slice
collides with no banked corpus (chunk index IS the generator seed - see build() in run_study.py).

Exit 0 = deterministic, order-independent, and the real build's rows equal the canonical rows as a set; 1 = any mismatch.
"""
from __future__ import annotations

import hashlib
import os
import sys
import time

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools", "pivot"))
from corpus import FAMILIES, chunk_fragments, load_real  # noqa: E402
from features import N_FEATURES, features_many  # noqa: E402

N_CHUNKS = 40
CHUNK_SIZE = 32768
CARVE_LEN = 4096
CHUNK_OFFSET = 900400  # past every index range used for banked corpora: collides with no training data
SRC_DIR = os.path.join(REPO, "data", "pivot", "src")


def build_slice(order: list[int], real: bytes):
    """Manufacture the chunks in the given order, then assemble in CANONICAL (index) order.

    Same per-chunk primitives as run_study.py's build(); assembly is sorted by chunk index so two
    builds are comparable regardless of manufacture order. The real build does NOT sort: it keeps
    imap_unordered's completion order (see the module docstring), so this establishes per-chunk
    order-independence only, not a reproducible row order for the real caches.
    """
    blocks = {}
    for idx in order:
        family = FAMILIES[idx % len(FAMILIES)]  # same family assignment as build() in run_study.py
        frags, labels, _ = chunk_fragments(idx, family, real, CHUNK_SIZE, CARVE_LEN)
        if frags:
            blocks[idx] = (features_many(frags),
                           np.asarray(labels, dtype=np.int16),
                           np.full(len(labels), idx, dtype=np.int32))
    keys = sorted(blocks)
    X = np.concatenate([blocks[k][0] for k in keys]).astype(np.float32, copy=False)
    y = np.concatenate([blocks[k][1] for k in keys])
    g = np.concatenate([blocks[k][2] for k in keys])
    return X, y, g


def hashes(X, y, g):
    return {name: hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()
            for name, arr in (("X", X), ("y", y), ("g", g))}


def main() -> int:
    t0 = time.perf_counter()
    real = load_real(SRC_DIR)
    if len(real) == 0:
        # With no source bytes corpus.py silently substitutes synthetic json for the gutenberg
        # family (make_chunk), so a "pass" here would have tested seven families and quietly
        # relabelled the eighth. Found by the 2026-09-03 board review; refuse rather than pretend.
        print("DETERMINISM PROBE: REFUSED - data/pivot/src holds no source bytes, so the gutenberg "
              "family would be silently replaced by synthetic json. Run tools/pivot/fetch_sources.sh "
              "first (it pins the banked edition).", file=sys.stderr)
        return 2
    canonical = list(range(CHUNK_OFFSET, CHUNK_OFFSET + N_CHUNKS))
    print(f"determinism probe: {N_CHUNKS} chunks x {CHUNK_SIZE} B, carve {CARVE_LEN} B, "
          f"offset {CHUNK_OFFSET}, {N_FEATURES} features, "
          f"{len(real)} real source bytes", flush=True)

    builds = [
        ("build 1 (canonical order)", canonical),
        ("build 2 (canonical order, fresh)", canonical),
        ("build 3 (REVERSED manufacture order)", list(reversed(canonical))),
    ]
    results = []
    for name, order in builds:
        t = time.perf_counter()
        X, y, g = build_slice(order, real)
        h = hashes(X, y, g)
        results.append((name, h, X.shape, len(y)))
        print(f"  {name}: {len(y)} fragments, X{X.shape}  ({time.perf_counter()-t:.1f}s)")
        for k in ("X", "y", "g"):
            print(f"    {k} sha256 {h[k]}")

    # build 4: the real build() - Pool, imap_unordered, no sort - on the same slice; its rows must be the canonical rows as a set
    import run_study  # noqa: E402
    t = time.perf_counter()
    X4, y4, g4, _ = run_study.build(N_CHUNKS, CHUNK_SIZE, CARVE_LEN, SRC_DIR, 2, 0, CHUNK_OFFSET)
    order = np.lexsort((y4, g4))
    in_canonical_order = bool(np.array_equal(order, np.arange(len(order))))
    h4 = hashes(np.ascontiguousarray(X4[order]), np.ascontiguousarray(y4[order]), np.ascontiguousarray(g4[order]))
    name4 = "build 4 (run_study.build(), 2 processes; rows sorted by chunk id and label)"
    results.append((name4, h4, X4.shape, len(y4)))
    print(f"  {name4}: {len(y4)} fragments, X{X4.shape}  ({time.perf_counter()-t:.1f}s); "
          f"its own row order {'was' if in_canonical_order else 'was NOT'} canonical (informational)")
    for k in ("X", "y", "g"):
        print(f"    {k} sha256 {h4[k]}")

    ref = results[0][1]
    failed = False
    for name, h, _, _ in results[1:]:
        for k in ("X", "y", "g"):
            if h[k] != ref[k]:
                print(f"MISMATCH: {k} differs between '{results[0][0]}' and '{name}'")
                failed = True
    total = time.perf_counter() - t0
    if failed:
        print(f"\nDETERMINISM PROBE: FAIL ({total:.1f}s) - rebuild is NOT byte-identical")
        return 1
    print(f"\nDETERMINISM PROBE: PASS ({total:.1f}s) - two rebuilds byte-identical, per-chunk generation "
          f"order-independent, and the real build()'s rows equal the canonical rows as a set (not their order)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
