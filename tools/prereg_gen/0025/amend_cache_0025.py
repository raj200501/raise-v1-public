#!/usr/bin/env python3
"""Re-seal preregistration 0025's builder-cache identity to the cache rebuilt on 2026-10-21 (UNFROZEN file only).

Why. The banked data/pivot/full_c4096.npz was lost with the old container. tools/pivot/run_study.py build() writes rows in the
order its Pool.imap_unordered(chunksize=8) batches finish, so a rebuild holds the same rows in another order, and the banked
X and g hashes (and every row-position hash derived from them) cannot be reproduced (CORRECTIONS.md, 2026-10-21). 0025 scores
the cache's sealed EVALUATION rows only (its fits are on the real-content corpora), so what must be preserved is the
evaluation rows' order and content, not the positions of rows nobody reads. tools/prereg_gen/0025/reorder_cache.py puts the
rebuilt cache in a documented order in which the evaluation rows come out in exactly the banked sequence; this script then

  * proves the ORDER: the runner's own grouped_split() on the reordered cache gives evaluation rows whose label and chunk-id
    hashes (eval_y_sha256, eval_g_sha256) and row count equal the sealed ones, and whose chunk sequence and rows per chunk equal
    the sealed eval_chunk_layout;
  * requires the CONTENT proof (artifacts/verification/cache_rebuild_0025.json, written by cache_content_proof.py: 0021's
    recipes refitted on 0021's fit block reproduce their banked per-example vectors on these evaluation rows) to have passed;
  * re-seals only what a rebuild legitimately changes: cache_identity's X and g hashes (y if it moved), the evaluation-row
    position hash, the pool position hashes - and replaces each old literal wherever it stands in the file, listing the paths;
  * recomputes the sealed hashes and records the change under amendments_before_freeze. Idempotent; refuses on a frozen file.
"""
import argparse, copy, hashlib, json, os, sys

import numpy as np

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(R, 'tools', 'pivot'))
from run_recipe_search import grouped_split, _sha  # noqa: E402
from run_realfit import _array_sha  # noqa: E402
from npzmap import npz_memmap  # noqa: E402

canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
shao = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cache', default=os.path.join(R, 'data', 'pivot', 'full_c4096.npz'))
    ap.add_argument('--prereg', default=os.path.join(R, 'prereg', '0025-realcurve3-4096.json'))
    ap.add_argument('--proof', default=os.path.join(R, 'artifacts', 'verification', 'cache_rebuild_0025.json'))
    a = ap.parse_args()
    pr = json.load(open(a.prereg, encoding='utf-8')); assert pr.get('frozen') is False, 'refusing: frozen'
    S = pr['scope']; P = S['curve']['protocol']; sp = S['sealed_partition']
    # an edit made without rehashing would otherwise be laundered by the recomputation at the end
    assert shao(P) == S['sealed_hashes']['protocol_sha256'] and shao(S['curve']) == S['sealed_hashes']['curve_sha256'], \
        'refusing: the sealed hashes are stale (the file was edited without recomputing them)'
    proof = json.load(open(a.proof, encoding='utf-8'))
    assert proof.get('passed') is True and proof.get('mode') == 'full', f'refusing: the cache content proof has not passed ({a.proof})'
    proof_sha = hashlib.sha256(open(a.proof, 'rb').read()).hexdigest()

    import zipfile, io
    with zipfile.ZipFile(a.cache) as zf:
        names = set(zf.namelist())
        y = np.load(io.BytesIO(zf.read('y.npy'))); g = np.load(io.BytesIO(zf.read('g.npy')))
    assert not ({'carve.npy', 'chunk_offset.npy', 'chunk_size.npy'} & names), 'the runner treats a cache with build metadata differently'
    ev, tr, _ = grouped_split(y, g, P['seed'], P['eval_frac'], P['top_rung'])
    # ---- the order proof
    lay = S['eval_chunk_layout']; ids = np.asarray(g[ev])
    runs_ids = [int(ids[0])]; runs_n = [0]
    for c in ids:
        if int(c) != runs_ids[-1]:
            runs_ids.append(int(c)); runs_n.append(0)
        runs_n[-1] += 1
    order_ok = {"eval_y_sha256": _sha(np.asarray(y[ev])) == sp['eval']['eval_y_sha256'],
                "eval_g_sha256": _sha(ids) == sp['eval']['eval_g_sha256'],
                "n_eval_rows": int(len(ev)) == sp['eval']['n_rows'],
                "chunk_sequence": runs_ids == list(lay['chunk_ids']) and runs_n == list(lay['rows_per_chunk'])}
    print('order proof:', order_ok)
    assert all(order_ok.values()), 'refusing: the reordered cache does not give the banked evaluation rows in the banked order'

    x_sha, x_shape, x_dtype = _array_sha(a.cache, 'X')
    # the proof must have been made on THIS cache: its recorded whole-cache hashes and its digest of the evaluation rows' features
    # in the sealed order (float32, C order - as cache_content_proof.py computes it) are recomputed here
    Xm = npz_memmap(a.cache, 'X'); hx = hashlib.sha256()
    for i in range(0, len(ev), 20000):
        hx.update(np.ascontiguousarray(Xm[ev[i:i + 20000]], dtype=np.float32).tobytes())
    eval_x = hx.hexdigest(); del Xm
    cf = proof.get('cache_file') or {}
    bound = {"X": cf.get('X_sha256') == x_sha, "y": cf.get('y_sha256') == _sha(y), "g": cf.get('g_sha256') == _sha(g),
             "eval_X_sha256_in_sealed_order": proof.get('eval_X_sha256_in_sealed_order') == eval_x}
    print('proof bound to this cache:', bound)
    assert all(bound.values()), 'refusing: the content proof was not made on this cache'
    new = {'X': x_sha, 'y': _sha(y), 'g': _sha(g), 'eval_idx': _sha(ev), 'pool_idx': _sha(tr), 'pool_sorted': _sha(np.sort(tr).astype(np.int64)),
           'pool_y': _sha(np.asarray(y[tr]))}
    ci = P['cache_identity']
    old = {'X': ci.get('X_sha256_banked_2026_08', ci['X_sha256']), 'y': ci.get('y_sha256_banked_2026_08', ci['y_sha256']),
           'g': ci.get('g_sha256_banked_2026_08', ci['g_sha256']), 'eval_idx': sp['eval'].get('eval_idx_sha256_banked_2026_08', sp['eval']['eval_idx_sha256']),
           'pool_idx': sp['pool'].get('pool_idx_sha256_banked_2026_08', sp['pool']['pool_idx_sha256']),
           'pool_sorted': sp['pool'].get('pool_sorted_sha256_banked_2026_08', sp['pool']['pool_sorted_sha256']),
           'pool_y': sp['pool'].get('pool_y_sha256_banked_2026_08', sp['pool']['pool_y_sha256'])}
    assert list(x_shape) == list(ci['X_shape']) and x_dtype == ci['X_dtype'], (x_shape, x_dtype)
    # a second run with a DIFFERENT rebuilt cache must not pass as 'unchanged' and leave the first cache's hashes sealed
    cur = {'X': ci['X_sha256'], 'y': ci['y_sha256'], 'g': ci['g_sha256'], 'eval_idx': sp['eval']['eval_idx_sha256'],
           'pool_idx': sp['pool']['pool_idx_sha256'], 'pool_sorted': sp['pool']['pool_sorted_sha256'], 'pool_y': sp['pool']['pool_y_sha256']}
    assert all(cur[k] in (old[k], new[k]) for k in cur), 'refusing: a different rebuilt cache is already sealed in this file'

    before = copy.deepcopy(pr)
    replaced = []

    def walk(o, path):
        if isinstance(o, dict):
            for k in list(o):
                # the banked values and the amendment records (whose 'banked' block holds them) are history, never rewritten
                if k.endswith('_banked_2026_08') or k == 'amendments_before_freeze':
                    continue
                if isinstance(o[k], str):
                    for key in old:
                        if o[k] == old[key] and old[key] != new[key]:
                            o[k] = new[key]; replaced.append(f'{path}.{k}')
                else:
                    walk(o[k], f'{path}.{k}')
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str):
                    for key in old:
                        if v == old[key] and old[key] != new[key]:
                            o[i] = new[key]; replaced.append(f'{path}[{i}]')
                else:
                    walk(v, f'{path}[{i}]')
    walk(pr, '')
    # keep the banked values beside the new ones, named for what they are
    for k, key in (('X_sha256', 'X'), ('y_sha256', 'y'), ('g_sha256', 'g')):
        if old[key] != new[key]:
            ci.setdefault(f'{k}_banked_2026_08', old[key])
    for blk, k, key in (('eval', 'eval_idx_sha256', 'eval_idx'), ('pool', 'pool_idx_sha256', 'pool_idx'), ('pool', 'pool_sorted_sha256', 'pool_sorted'),
                        ('pool', 'pool_y_sha256', 'pool_y')):
        if old[key] != new[key]:
            sp[blk].setdefault(f'{k}_banked_2026_08', old[key])
    note = ("REBUILT 2026-10-21: the banked cache (0021's identity, kept beside each hash as *_banked_2026_08) was lost with a container and "
            "its row order - the build's parallel batch-completion order - cannot be reproduced; this is the rebuilt cache put in a documented "
            "order (tools/prereg_gen/0025/reorder_cache.py) in which the sealed evaluation rows come out in the banked order (eval_y_sha256, "
            "eval_g_sha256 and eval_chunk_layout unchanged) with banked content (artifacts/verification/cache_rebuild_0025.json); the X and g "
            "hashes and the row-position hashes are this cache's (CORRECTIONS.md, 2026-10-21)")
    ci['X_note'] = note
    S['sealed_hashes']['protocol_sha256'] = shao(P); S['sealed_hashes']['curve_sha256'] = shao(S['curve'])
    # a proof re-run after the re-seal (new bytes, same cache) must be recordable: append a record instead of printing 'unchanged'
    _last = [r for r in before.get('amendments_before_freeze', []) if r.get('by') == 'tools/prereg_gen/0025/amend_cache_0025.py']
    changed = pr != before or bool(_last and (_last[-1].get('proof_sha256'), _last[-1].get('eval_X_sha256_in_sealed_order')) != (proof_sha, eval_x))
    if changed:
        pr.setdefault('amendments_before_freeze', []).append({
            "date": "2026-10-21", "by": "tools/prereg_gen/0025/amend_cache_0025.py",
            "source": "CORRECTIONS.md 2026-10-21 (the builder cache's row order cannot be rebuilt); artifacts/verification/cache_rebuild_0025.json",
            "changes": [{"where": p, "why": "the rebuilt cache's identity or row-position hash replaces the banked one"} for p in sorted(set(replaced))]
                       + [{"where": "scope.curve.protocol.cache_identity.X_note", "why": "states what the cache is now"}],
            "order_proof": order_ok, "new": new, "banked": old, "eval_X_sha256_in_sealed_order": eval_x, "proof_sha256": proof_sha})
        with open(a.prereg, 'w', encoding='utf-8') as fh:
            json.dump(pr, fh, indent=2, ensure_ascii=False); fh.write('\n')
    print(f"{'amended' if changed else 'unchanged'}: {len(set(replaced))} literal(s) replaced at {sorted(set(replaced))}")
    print('new:', {k: v[:12] for k, v in new.items()})


if __name__ == '__main__':
    main()
