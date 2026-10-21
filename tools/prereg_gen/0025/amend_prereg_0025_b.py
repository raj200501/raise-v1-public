#!/usr/bin/env python3
"""Second pre-freeze amendment of the UNFROZEN preregistration 0025: the cost block restated from the sealed-run cost audit and
the bin-mapper check of 2026-10-21 (both from banked numbers and the installed scikit-learn's source). Same mechanics as
amend_prereg_0025.py: every edit is an exact replacement asserted to occur once (or already applied), the sealed hashes are
recomputed with the reader generator's canonical serialisation, everything outside the edited fields is asserted unchanged, and
the changes are recorded under amendments_before_freeze. Refuses on a frozen file; a second run changes nothing."""
import copy, hashlib, json, os

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PATH = os.path.join(R, 'prereg', '0025-realcurve3-4096.json')
canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

pr = json.load(open(PATH, encoding='utf-8'))
assert pr.get('frozen') is False, 'refusing: the preregistration is frozen'
S = pr['scope']; P = S['curve']['protocol']
assert sha(P) == S['sealed_hashes']['protocol_sha256'] and sha(S['curve']) == S['sealed_hashes']['curve_sha256'], 'refusing: stale sealed hashes'
before = copy.deepcopy(pr)
a24 = json.load(open(os.path.join(R, 'artifacts', 'pivot', 'realcurve2_4096.json'), encoding='utf-8'))

# ---- banked inputs (asserted, never typed into the sentence by hand)
bound = {e['name']: e['rss_gb'] for e in a24['ledger'] if e.get('event') == 'rung_bound'}
RB7, RBS4 = bound['run_r7_depth3_tree'], bound['run_s4_depth3_tree']
TREE7_HB = a24['fits']['r7_depth3_tree']['heartbeat_max_rss_gb']; MODEL7_HB = a24['fits']['r7_model']['heartbeat_max_rss_gb']
ROWS8 = S['sealed_partition']['rungs'][-1]['n_rows']; ROWS7 = S['sealed_partition']['rungs'][-2]['n_rows']; N_FIT3 = P['fit3_corpus']['n_rows']
NCOLS = 1108
BLOCK8 = round(ROWS8 * NCOLS * 8 / 1e9, 2); F3 = round(N_FIT3 * NCOLS * 4 / 1e9, 2); TREECOPY = round(BLOCK8 / 2, 2)
SUB = 200000; SUBCOPY = round(SUB * NCOLS * 8 / 1e9, 2)
TRAIN8, TRAIN7 = int(0.9 * ROWS8), int(0.9 * ROWS7)
PEAK_TREE = round(RB7 + F3 + BLOCK8 + TREECOPY, 1); PEAK_TREE_S4 = round(RBS4 + F3 + BLOCK8 + TREECOPY, 1)
PEAK_MODEL = round(RB7 + F3 + BLOCK8 + SUBCOPY, 1)
assert (RB7, RBS4, TREE7_HB, MODEL7_HB, BLOCK8, F3, SUBCOPY, TRAIN8, TRAIN7) == (3.59, 3.89, 6.33, 6.15, 3.73, 0.97, 1.77, 378913, 189675), \
    (RB7, RBS4, TREE7_HB, MODEL7_HB, BLOCK8, F3, SUBCOPY, TRAIN8, TRAIN7)

changes = []
old_mem = S['cost']['memory']
new_mem = (f"from 0024's banked ledger and heartbeats: anonymous RSS at rung 7's rung_bound (before its block) was {RB7} GB, and at "
           f"its shift arm's rung_bound {RBS4} GB; 0024's r7_depth3_tree heartbeat peaked at {TREE7_HB} GB and r7_model's at {MODEL7_HB} GB, "
           f"the tree's rise over its start being the float32 copy sklearn's trees make of the float64 block. For rung 8: {RB7} GB + the "
           f"third fit corpus in float32 ({F3} GB) + rung 8's float64 block ({BLOCK8} GB) + the trees' float32 copy of it ({TREECOPY} GB) "
           f"gives about {PEAK_TREE} GB anonymous at r8_floor_feat1 and r8_depth3_tree ({PEAK_TREE_S4} GB on the shift arm's base). "
           f"r8_model and the null train on {TRAIN8} rows, above the {SUB}-row subsample threshold of scikit-learn 1.9.0's histogram "
           f"bin mapper (sklearn/ensemble/_hist_gradient_boosting/binning.py: subsample=int(2e5), and X.take() of the subsample after "
           f"the cast to float64), which 0024's largest model fit ({TRAIN7} rows) never crossed: a float64 copy of {SUB} rows x {NCOLS} "
           f"features ({SUBCOPY} GB) for the binning step, so about {PEAK_MODEL} GB at r8_model, tying the trees' peak, and possibly "
           f"between two 30 s heartbeats. Against the sealed memory_kill_gb of {P['caps']['memory_kill_gb']} on a 15 GB machine whose "
           f"shell memory cgroup read 14343688192 bytes on 2026-10-21 (the runner's environment block reads the root cgroup file, "
           f"which reports 'unlimited'), the launch requires {P['launch']['min_mem_available_gb']} GB available and nothing else heavy in "
           f"the same cgroup (the runner refuses to start beside another runner, a corpus builder or the mutation suite). Earlier "
           f"versions of this sentence projected about 9.0 GB from a line through post-fit readings, then omitted the bin mapper's "
           f"subsample copy (pre-freeze instrument review; sealed-run cost audit, 2026-10-21). COULD NOT VERIFY until run.")
if old_mem != new_mem:
    S['cost']['memory'] = new_mem
    changes.append({"where": "scope.cost.memory", "why": "the bin mapper's float64 subsample copy at rung 8 (378913 training rows, above "
                    "sklearn 1.9.0's 200000-row threshold) and the shift arm's higher base are counted; the cgroup reading is stated as "
                    "read, not as banked (sealed-run cost audit and bin-mapper check, 2026-10-21)"})

FL_OLD = "the floors are seconds each (about 60 s in all)"
FL_NEW = "the floors are seconds each (the totals below allow 120.4 s for them)"
est = S['cost']['estimate_stated_in_advance']
if FL_OLD in est:
    assert est.count(FL_OLD) == 1
    lo = 5374.2 + 353.2 + 4354 + 892 + 70 + 446 + 353.2; hi = 5374.2 + 353.2 + 7675 + 1119 + 70 + 446 + 353.2
    assert round(11963 - lo, 1) == round(15511 - hi, 1) == 120.4, (11963 - lo, 15511 - hi)
    S['cost']['estimate_stated_in_advance'] = est.replace(FL_OLD, FL_NEW)
    changes.append({"where": "scope.cost.estimate_stated_in_advance", "why": "the sentence said the floors cost about 60 s in all while "
                    "its own totals (11963 and 15511 s) allow 120.4 s for them; the sentence now states what the totals count"})

S['sealed_hashes']['protocol_sha256'] = sha(P)
S['sealed_hashes']['curve_sha256'] = sha(S['curve'])


def strip(d):
    d = copy.deepcopy(d); s = d['scope']
    s['cost'].pop('memory'); s['cost']['estimate_stated_in_advance'] = s['cost']['estimate_stated_in_advance'].replace(FL_NEW, FL_OLD)
    s.pop('sealed_hashes'); d.pop('amendments_before_freeze', None)
    return d


assert strip(pr) == strip(before), 'an edit touched something outside its field'
if changes:
    pr.setdefault('amendments_before_freeze', []).append({
        "date": "2026-10-21", "by": "tools/prereg_gen/0025/amend_prereg_0025_b.py",
        "source": "the sealed-run cost audit and the bin-mapper check of 2026-10-21 (banked 0024 ledger, scikit-learn 1.9.0 source)",
        "changes": changes})
    with open(PATH, 'w', encoding='utf-8') as fh:
        json.dump(pr, fh, indent=2, ensure_ascii=False); fh.write('\n')
print(f"{len(changes)} change(s); protocol {S['sealed_hashes']['protocol_sha256'][:12]} curve {S['sealed_hashes']['curve_sha256'][:12]}")
for c in changes:
    print(' -', c['where'])
