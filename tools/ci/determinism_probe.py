#!/usr/bin/env python3
"""CI determinism probe: prove, on every push, that a corpus slice rebuilds byte-identically.

The full corpora (gigabytes) are banked by content hash in tools/pivot/corpus_manifest.py, but
that proof has only ever been executed on the machine that built them. This probe manufactures a
SMALL corpus slice twice in the CI container - same primitives the real build uses
(tools/pivot/corpus.py chunk_fragments + tools/pivot/features.py features_many) - and fails the
build unless the sha256 of the X, y and g arrays is identical across builds.

It also proves the property the real build's parallelism depends on: run_study.py's build() feeds
a multiprocessing Pool with imap_unordered, so per-chunk generation MUST be order-independent
(chunk i's bytes must depend only on i, never on which chunks were built before it, i.e. no shared
RNG or module state leaking between chunks). Build 3 therefore manufactures the same chunks in
REVERSED order, reassembles them in canonical order, and must reproduce the same hashes.

Scale is deliberately small (~40 chunks) so it finishes in well under 3 minutes on 2 CPUs, and the
chunk offset (900400) is far past any index range used to build training data, so this slice
collides with no banked corpus (chunk index IS the generator seed - see build() in run_study.py).

Exit 0 = deterministic and order-independent; exit 1 = any hash mismatch.
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
    builds are comparable regardless of manufacture order - exactly the invariant that makes the
    real build's imap_unordered pool safe.
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
    print(f"\nDETERMINISM PROBE: PASS ({total:.1f}s) - two rebuilds byte-identical and "
          f"per-chunk generation is order-independent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
