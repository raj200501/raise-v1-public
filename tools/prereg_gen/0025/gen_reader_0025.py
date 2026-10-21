#!/usr/bin/env python3
"""Generate tools/readers/realcurve3_4096_verdict.py from prereg/0025-realcurve3-4096.json and the template.
Every literal in the reader comes from the preregistration or from a banked artifact; none is typed here."""
import json, hashlib, pprint, sys, os, re
canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731
R = '/home/user/raise-v1'; SP = os.path.dirname(os.path.abspath(__file__))
prereg_path = sys.argv[1] if len(sys.argv) > 1 else f'{R}/prereg/0025-realcurve3-4096.json'
out_path = sys.argv[2] if len(sys.argv) > 2 else f'{R}/tools/readers/realcurve3_4096_verdict.py'
pr = json.load(open(prereg_path)); S = pr['scope']; CU = S['curve']; P = CU['protocol']; RE = CU['recipes']; sp = S['sealed_partition']
a21 = json.load(open(f'{R}/artifacts/pivot/realfit_4096_rerun.json'))
assert set(CU) == {"protocol", "recipes"}, sorted(CU)
CORPUS = {k: a21['corpus'][k] for k in ("carve_bytes", "carve_bytes_source", "chunk_size", "chunk_offset", "chunk_id_min", "chunk_id_max",
                                        "n_source_chunks", "cache_y_sha256", "cache_g_sha256", "n_rows", "n_features", "cache_X_sha256")}
assert CORPUS["cache_X_sha256"] == P['cache_identity']['X_sha256'] and CORPUS["cache_y_sha256"] == P['cache_identity']['y_sha256']
EXT = dict(P['ext_corpus']); FIT = dict(P['fit_corpus']); FIT2 = dict(P['fit2_corpus']); FIT3 = dict(P['fit3_corpus'])
assert EXT['families'] == P['ext_families'] and FIT['families'] == P['fit_families'] == FIT2['families'] == FIT3['families']
N_FIRST = int(P['n_first_decade_rungs']); D2 = int(P['doublings_0024']); D3 = int(P['doublings_0025']); N_RUNGS = N_FIRST + D2 + D3; N24 = int(P['n_0024_rungs'])
assert sp['n_rungs'] == N_RUNGS == len(sp['rungs']) == len(P['rung_hashes']) and N24 == N_FIRST + D2
PARTITION = {"seed": P['seed'], "eval_frac": P['eval_frac'], "top_rung": P['top_rung'], "split_is_grouped_by_source": True,
 "n_eval_rows": sp['eval']['n_rows'], "n_eval_chunks": sp['eval']['n_chunks'], "n_eval_non_gutenberg": sp['eval']['n_non_gutenberg'],
 "eval_idx_sha256": sp['eval']['eval_idx_sha256'], "eval_y_sha256": sp['eval']['eval_y_sha256'], "eval_g_sha256": sp['eval']['eval_g_sha256'],
 "n_pool_rows": sp['pool']['n_rows'], "n_pool_chunks": sp['pool']['n_chunks'],
 "pool_idx_sha256": sp['pool']['pool_idx_sha256'], "pool_sorted_sha256": sp['pool']['pool_sorted_sha256'],
 "families": P['families'],
 "fit_rows": sp['fit_block']['n_rows'], "fit_idx_sha256": sp['fit_block']['idx_sha256'], "fit_sorted_sha256": sp['fit_block']['sorted_sha256'],
 "fit_order_rule": sp['fit_block']['order_rule'], "fit_block_chunks": FIT['n_chunks'],
 "fit_chunks_per_family": sp['fit_block']['chunks_with_rows_per_family'],
 "rung_rule": sp['rung_rule'], "second_decade_rule": sp['second_decade_rule'], "fourth_doubling_rule": sp['fourth_doubling_rule'],
 "denominators": sp['denominators'], "doublings": D2 + D3, "doublings_0024": D2, "doublings_0025": D3, "seed2": P['seed2'], "seed3": P['seed3'],
 "n_first_decade_rungs": N_FIRST, "n_rungs": N_RUNGS, "rungs": sp['rungs'],
 "pool_chunks_with_rows_per_family": sp['pool_chunks_with_rows_per_family'], "pool_chunks_with_rows_per_family_0024": sp['pool_chunks_with_rows_per_family_0024'],
 "pool_short": {}, "rungs_nested": True, "rung_chunks_strictly_increasing": True, "rung4_is_fit_block": True, "second_decade_exact_doublings": True,
 "doublings_spanned": sp['doublings_spanned'], "doublings_spanned_second_decade": sp['doublings_spanned_second_decade'], "doublings_spanned_0024": sp['doublings_spanned_0024'],
 "n_fit_rows_total": sp['n_fit_rows_total'],
 "shift_arm": sp['shift_arm'], "shift_arm_0025": sp['shift_arm_0025'],
 "max_chunk_id_0024_per_family": sp['max_chunk_id_0024_per_family'],
 "n_fit_source_chunks": sp['source_chunks']['n_fit_source_chunks'], "n_ext_source_chunks": sp['source_chunks']['n_ext_source_chunks'],
 "n_fit2_source_chunks": sp['source_chunks']['n_fit2_source_chunks'], "n_fit3_source_chunks": sp['source_chunks']['n_fit3_source_chunks']}
for k, v in P['fit_block_hashes'].items():
    assert PARTITION[k] == v, k
assert PARTITION['rungs'] == P['rung_hashes'] and PARTITION['fit_idx_sha256'] == a21['partition']['fit_idx_sha256']
assert sp['rungs'][N_FIRST - 1]['idx_sha256'] == PARTITION['fit_idx_sha256'] and sp['rungs'][N_FIRST - 1]['n_rows'] == PARTITION['fit_rows']
assert PARTITION['shift_arm'] == P['shift_arm_hashes'] and PARTITION['shift_arm_0025'] == P['shift_arm_0025_hashes']
assert P['shift'] == sp['shift_arm']['rung'] and P['shift_0025'] == sp['shift_arm_0025']['rung'] and len(P['order']) == 37
ROLES = list(P['roles']); FLOORS = list(P['floor_roles']); assert ROLES == ["depth3_tree", "logistic", "model"] and set(RE) == set(ROLES + FLOORS)
MAX_ITER = {r: (RE[r].get('params', {}).get('max_iter') or 0) for r in ROLES}
LOG2X = [r['log2_chunks'] for r in sp['rungs']]
REF_FIRST = {r: list(P['reference_first_decade'][r]) for r in ROLES}; REF24 = {r: list(P['reference_0024'][r]) for r in ROLES}
assert all(REF_FIRST[r][-1] == P['reference_top1'][r] and REF24[r][:N_FIRST] == REF_FIRST[r] and len(REF24[r]) == N24 for r in ROLES)
_tpl = open(f'{SP}/reader_0025_template.py').read()
_body = _tpl[_tpl.index('    result = {\n        "schema"'):]
_body = _body[:_body.index('\n    }\n')]
RESULT_KEYS = sorted(set(re.findall(r'^\s{8}"([a-z0-9_]+)":', _body, re.M)))
assert {'verdict', 'bar_applied', 'flags', 'curves', 'lead_at_top', 'verdict_components', 'fourth_doubling', 'floors', 'shift_arm_0025',
        'reproduction_bootstrap_0024', 'seed_stability', 'gain_reading', 'lead_reading'} <= set(RESULT_KEYS) and len(RESULT_KEYS) > 40, RESULT_KEYS
fmt = lambda o: pprint.pformat(o, width=112, sort_dicts=False)  # noqa: E731
out = _tpl % dict(
    fam=json.dumps(P['families']), ext_fam=json.dumps(P['ext_families']), real_fam=json.dumps(P['subsets']['real']),
    synth_fam=json.dumps(P['subsets']['synthetic']), fit_fam=json.dumps(P['fit_families']),
    structured=json.dumps(P['subsets']['structured_text']), high_entropy=json.dumps(P['subsets']['high_entropy']),
    corpus=fmt(CORPUS), proto=fmt(P), proto_sha=sha(P), curve_sha=sha(CU), recipes=fmt(RE), roles=json.dumps(ROLES), floor_roles=json.dumps(FLOORS),
    order=json.dumps(P['order']), denominators=json.dumps(P['denominators']), n_first=N_FIRST, doublings_0024=D2, doublings_0025=D3, n_rungs=N_RUNGS,
    n_0024_rungs=N24, partition=fmt(PARTITION), ext=fmt(EXT), fit=fmt(FIT), fit2=fmt(FIT2), fit3=fmt(FIT3),
    ext_chunk_ids=json.dumps(S['ext_chunk_layout']['chunk_ids_with_rows']), ext_rows_per_chunk=json.dumps(S['ext_chunk_layout']['rows_per_chunk']),
    eval_chunk_ids=json.dumps(S['eval_chunk_layout']['chunk_ids']), eval_rows_per_chunk=json.dumps(S['eval_chunk_layout']['rows_per_chunk']),
    seed=P['seed'], seed2=P['seed2'], seed3=P['seed3'], chance=round(1 / 26, 6), n_ext=EXT['n_rows'], n_real=P['n_ext_real_rows'],
    reference=fmt(P['reference_top1']), reference_first=fmt(REF_FIRST), reference_0024=fmt(REF24), reference_shift_0024=fmt(P['reference_shift_arm_0024']),
    reference_boot_0024=fmt(P['reference_bootstrap_0024']),
    repro_tol=P['reproduction_tolerance'], repro_tol_r7=P['reproduction_tolerance_rung7'], null_tol=P['null_tolerance'],
    null_sha=P['null_y_shuffled_sha256_expected'], env=fmt(P['environment']), threads=P['threads'], nice=P['nice'],
    bar_gain=P['bar']['gain_per_doubling'], gain_rule=json.dumps(P['bar']['gain_rule']), lead_rule=json.dumps(P['bar']['lead_rule']),
    n_boot=P['bootstrap']['n_boot'], boot_seed=P['bootstrap']['seed'], stability_seeds=P['stability_seeds'], log2x=json.dumps(LOG2X),
    max_iter=fmt(MAX_ITER), decades=sp['decades_spanned'], shift4=P['shift'], shift8=P['shift_0025'], result_keys=fmt(RESULT_KEYS))
assert sha(P) == S['sealed_hashes']['protocol_sha256'] and sha(CU) == S['sealed_hashes']['curve_sha256']
open(out_path, 'w').write(out)
print("wrote", out_path, len(out), "bytes;", len(RESULT_KEYS), "result keys")
