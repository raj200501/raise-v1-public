#!/usr/bin/env python3
"""Hash the rows of a rebuilt data/pivot/realfit2_c4096.npz that make up 0024's sealed SMOKE corpus, against the smoke hashes
prereg/0024-realcurve2-4096.json banks.

0024's smoke corpus was built with --cap-per-family 126: its chunks are the first 126 pool chunks of each family, so it is a row
subset of the full corpus (chunk k < 126, k = (g - 30000000) mod 100000), in the same canonical row order (chunk id, label).
On 2026-10-21 the full rebuild reproduced y, g and fam but not X; this check localises that: if the subset's X hashes to the
banked smoke X, this machine and its libraries reproduce the banked feature bytes for those 629 chunks under all 26
configurations, and the difference lies in the chunks with k >= 126.

    python3 -B tools/prereg_gen/0025/realfit2_smoke_subset_check.py [NPZ]
exit 0 every array matches; 1 any differs.
"""
import hashlib, json, os, sys

import numpy as np

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(R, 'tools', 'pivot'))
sys.dont_write_bytecode = True
from npzmap import npz_memmap  # noqa: E402

NPZ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(R, 'data', 'pivot', 'realfit2_c4096.npz')
sm = json.load(open(os.path.join(R, 'prereg', '0024-realcurve2-4096.json'), encoding='utf-8'))['smoke']['fit2_corpus']['arrays']
sha = lambda a: hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()  # noqa: E731
g = np.asarray(npz_memmap(NPZ, 'g')); k = (g - 30_000_000) % 100_000
idx = np.nonzero(k < 126)[0]
ok = True
for name in ('y', 'g', 'fam', 'X'):
    a = np.array(npz_memmap(NPZ, name)[idx])
    same = sha(a) == sm[name]['sha256']; ok &= same
    print(f"  {'ok  ' if same else 'DIFF'} {name} {list(a.shape)} {sha(a)[:16]} (banked smoke {sm[name]['sha256'][:16]})")
print(f"REALFIT2 SMOKE SUBSET ({len(idx)} rows, chunks k < 126): " + ("IDENTICAL to 0024's banked smoke corpus" if ok else "DIFFERS"))
sys.exit(0 if ok else 1)
