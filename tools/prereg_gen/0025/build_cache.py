"""Rebuild data/pivot/full_c4096.npz (the builder cache: 50000 source chunks of 32768 bytes, carve 4096) with run_study.build(),
the function run_study.py --cache uses, and save it exactly as run_study.py does; no model is trained and no artifact is written."""
import os, sys, time
import numpy as np
REPO = '/home/user/raise-v1'; sys.path.insert(0, os.path.join(REPO, 'tools', 'pivot'))
import run_study as rs
out = os.path.join(REPO, 'data', 'pivot', 'full_c4096.npz')
assert not os.path.exists(out), 'refusing to overwrite an existing cache'
t = time.time()
X, y, g, build_s = rs.build(50000, 32768, 4096, os.path.join(REPO, 'data', 'pivot', 'src'), 4, 0, 0)
np.savez(out, X=X, y=y, g=g, build_s=build_s)
print(f'cached {out}: X {X.shape} {X.dtype}, build_s {build_s}, wall {round(time.time() - t, 1)} s', flush=True)
