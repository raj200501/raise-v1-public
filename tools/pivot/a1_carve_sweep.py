#!/usr/bin/env python3
"""A1 for carve size: how much information survives a shorter window, measured on the INPUT.

Run BEFORE preregistration 0007 is frozen and before any model is trained at a shorter carve. If
two encoders produce byte-identical windows far more often at 1024 than at 4096, there is an
information CEILING that no volume of manufactured data can pass, and that has to be known before
spending hours measuring against it. This measures the input, never the outcome.

Source chunk seeds 900000..900399 are disjoint from every corpus used for training, so nothing
here touches data a model will later be evaluated on.

Writes after EVERY carve size rather than at the end: the first attempt at this was lost to a
container restart with two of four sizes already computed.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import FAMILIES, N_CONFIGS, chunk_fragments, load_real  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "artifacts", "pivot", "carve_channel_capacity.json")
CARVES = (4096, 2048, 1024, 512)
N_CHUNKS = 400
FIRST_SEED = 900000


def main() -> int:
    real = load_real(os.path.join(REPO, "data", "pivot", "src"))
    out = {"schema": "raise-v1/carve_channel_capacity/1",
           "why": __doc__.strip().split("\n\n")[1],
           "n_chunks_sampled": N_CHUNKS, "chunk_size": 32768, "n_configs": N_CONFIGS,
           "source_chunk_seeds": f"{FIRST_SEED}..{FIRST_SEED + N_CHUNKS - 1}, disjoint from every "
                                 f"corpus used for training",
           "by_carve": {}}
    for carve in CARVES:
        t = time.perf_counter()
        tot = dsum = n = 0
        for i in range(N_CHUNKS):
            frags, _, _ = chunk_fragments(FIRST_SEED + i, FAMILIES[i % len(FAMILIES)], real,
                                          32768, carve)
            if not frags:
                continue
            dsum += len({hashlib.sha256(f).digest() for f in frags})
            tot += len(frags)
            n += 1
        out["by_carve"][str(carve)] = {
            "mean_distinct_streams_of_26": round(dsum / max(n, 1), 4),
            "collision_rate": round(1 - (dsum / max(tot, 1)), 4),
            "chunks_used": n, "seconds": round(time.perf_counter() - t, 1)}
        d = out["by_carve"][str(carve)]
        print(f"  carve {carve:>5}: {d['mean_distinct_streams_of_26']:.2f} distinct of "
              f"{N_CONFIGS}, collision rate {d['collision_rate']:.4f}   ({d['seconds']}s)",
              flush=True)
        with open(OUT, "w", encoding="utf-8") as fh:      # written after EVERY size, not at the end
            json.dump(out, fh, indent=2, sort_keys=True)
            fh.write("\n")
    print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
