#!/usr/bin/env python3
"""Publish preregistration 0025's verdict across the record, at the size every other outcome would have had.

Written BEFORE the sealed run was read, so it serves every one of the twelve verdict strings
FOURTH_DOUBLING_{RISES|BELOW_RATE|NOT_RESOLVED|FALLS}_{MODEL_LEADS|LINEAR_LEADS|NO_SEPARATION} with the same sentences at the
same size, and REFUSES on VOID or NOT RUN (published by another path) before anything is written. Every number is read from the
banked verdict, run, sealed, manifest and 0024 files and asserted against its other banked copies or recomputed from them; none is
typed. The pre-committed words (BELOW_RATE's, NOT_RESOLVED's, FALLS's, the floors', the cap notes', the forward pointer's) are
the sealed file's or the reader's.

Sites, each written idempotently (a second run changes no byte; a stale 0025 unit or pointer is replaced, never duplicated):
  artifacts/pivot/engineering_log_0025.json   run_record, status
  VERDICT.md                                  the 0025 block (replacing the in-flight paragraph), a table row, the claim counts
  README.md                                   the 0025 paragraph (replacing the in-flight paragraph)
  outbound/ONE_PAGER.md                       a paragraph after 0024's; the claim count
  outbound/EVIDENCE_BRIEF.md                  a paragraph after 0024's and a findings bullet after 0024's
  outbound/NARRATIVE.md                       a blockquote paragraph after 0024's; the claim count
  docs/DILIGENCE.md                           a Q&A before "Who buys it?"
  artifacts/verification/coverage.json        primary-verifiable claims on artifacts/pivot/realcurve3_4096_verdict.json
  tools/render/evidence_page.py               the forward pointer and the lead bound in 0024's panel, read from 0025's verdict at
                                              render time (guarded), then outbound/evidence_page.html re-rendered
The stop rules' forward pointers and bounds, each site touched once (VERDICT.md, README.md, outbound/*.md, docs/DILIGENCE.md;
never CORRECTIONS.md, a ledger, nor a plan under docs/strategy, which is named in a NOTE), anchored on the documents' wording after
the 2026-10-22 honesty pass:
  every "1.8016 decades, short of 0003's two-decade scope rule"  -> the sealed pointer sentence, verbatim
  on BELOW_RATE, NOT_RESOLVED, FALLS, in the documents the stop rule names (VERDICT.md, README.md): 0024's "other files of the same
      kinds keep buying the recipe the record's rate ... through 8232 plaintexts" (VERDICT.md now: "keep raising the recipe's
      accuracy ... at or above the record's bar ..., through 8232 plaintexts") -> bounded, with the rung-8 gain, its reading and
      the lead part beside it
  on FALLS, in VERDICT.md and DILIGENCE.md: 0023's "the record's scaling thesis holds on real files" (now, in both, "this does
      not establish the record's scaling thesis, which 0003's scope rule ties to two decades ... (this curve spans 0.8985 of a
      decade)") -> a forward pointer
  on LINEAR_LEADS, NO_SEPARATION: every published MODEL_LEADS of 0024 (each sentence that states its top-rung lead of 0.0039 or
      its `MODEL_LEADS` after the interval [0.0001, 0.0077], once per sentence; the one-pager's headline) -> bounded to 8232
      plaintexts with the rung-8 reading beside it
A keep or thesis site that no longer carries the stop rule's own words is bounded all the same and named in a NOTE.

Environment: PUBLISH_0025_ROOT (default: the checkout this script is in) points the script at another root (the dry run's copies);
PUBLISH_0025_DRYRUN=1 skips the committed-checkpoint count (a dry-run root has no checkpoints); PUBLISH_0025_RENDER=0 skips
re-rendering outbound/evidence_page.html.
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import textwrap

import numpy as np

R = os.path.abspath(os.environ.get('PUBLISH_0025_ROOT', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DRY = os.environ.get('PUBLISH_0025_DRYRUN') == '1'
RENDER = os.environ.get('PUBLISH_0025_RENDER', '1') == '1'


def P(*p):
    return os.path.join(R, *p)


def J(p):
    with open(P(p), encoding='utf-8') as fh:
        return json.load(fh)


def T(p):
    with open(P(p), encoding='utf-8') as fh:
        return fh.read()


# ---------------------------------------------------------------- 0. refuse on VOID or NOT RUN, before anything is read further
if os.path.exists(P('artifacts', 'pivot', 'realcurve3_4096_not_run.json')):
    print('REFUSED: artifacts/pivot/realcurve3_4096_not_run.json is present; a NOT RUN is not a verdict and is published by another '
          'path. Nothing written.', file=sys.stderr)
    sys.exit(2)
V = J('artifacts/pivot/realcurve3_4096_verdict.json')
if V.get('verdict') == 'VOID' or V.get('validity_failed_clauses'):
    print(f"REFUSED: the verdict is {V.get('verdict')!r} with {len(V.get('validity_failed_clauses') or [])} failed clause(s); a VOID is "
          f"published by another path. Nothing written.", file=sys.stderr)
    sys.exit(2)

# ---------------------------------------------------------------- 1. the banked files, and every number asserted
A = J('artifacts/pivot/realcurve3_4096.json'); PR = J('prereg/0025-realcurve3-4096.json')
V24 = J('artifacts/pivot/realcurve2_4096_verdict.json'); E24 = J('artifacts/pivot/engineering_log_0024.json')
E = J('artifacts/pivot/engineering_log_0025.json'); MAN3 = J('artifacts/pivot/realfit3_corpus_manifest.json')
PINS3 = J('tools/pivot/ext_source_pins3.json')
chain = [json.loads(l) for l in open(P('prereg', 'chain.jsonl'), encoding='utf-8') if l.strip()]
ce = [x for x in chain if x['id'] == PR['id']]
assert len(ce) == 1, 'preregistration 0025 has no chain entry: it is not frozen, so there is nothing to publish'
seq = ce[0]['seq']
assert seq == int(PR['id']) and PR['frozen'] is True and ce[0]['file'] == 'prereg/0025-realcurve3-4096.json' and ce[0]['hash'] == PR['chain_hash']
assert PR['reader'] == 'tools/readers/realcurve3_4096_verdict.py'
with open(P(PR['reader']), 'rb') as fh:
    assert hashlib.sha256(fh.read()).hexdigest() == PR['reader_sha256'], 'the reader changed after the freeze'
assert V['preregistration'] == A['preregistration'] == f"{PR['id']}-{PR['slug']}" and V['source_artifact'] == 'artifacts/pivot/realcurve3_4096.json'
assert A['complete'] is True and A['missing_roles'] == [] and A['smoke'] is False and A['stage'] == 'run'
assert V['establishes_a_buyer'] is False and V['is_a_transfer_reading'] is False and V['revises_0003_0014_0015_0016_0017_0018_0019_0021_0022_0023_0024'] is False

GAINS = ['FOURTH_DOUBLING_RISES', 'FOURTH_DOUBLING_BELOW_RATE', 'FOURTH_DOUBLING_NOT_RESOLVED', 'FOURTH_DOUBLING_FALLS']   # most to least flattering
LEADS = ['MODEL_LEADS', 'LINEAR_LEADS', 'NO_SEPARATION']
ROLES = ['model', 'logistic', 'depth3_tree']
verdict = V['verdict']; gain = V['gain_reading']; lead = V['lead_reading']; F = V['flags']; B = V['bar_applied']; CV = V['curves']
FD = V['fourth_doubling']; LD = V['lead_at_top']
assert gain in GAINS and lead in LEADS and V['verdict_components'] == {'gain': gain, 'lead': lead} and verdict == f'{gain}_{lead}'
assert F['gain_reading'] == gain and F['lead_at_top'] == lead

# the rungs, the span, the sealed numbers
SR = PR['scope']['rungs']; SPp = PR['scope']['sealed_partition']; tab = SR['table']
plain = [r['n_chunks'] for r in B['rungs']]; rows = [r['n_rows'] for r in B['rungs']]
n_r, n24, n_first = SPp['n_rungs'], SPp['n_0024_rungs'], SPp['n_first_decade_rungs']
assert plain == [r['n_chunks'] for r in tab] == [r['n_chunks'] for r in SPp['rungs']] and rows == [r['n_rows'] for r in tab]
assert len(plain) == n_r == A['n_rungs'] and n24 == n_r - 1 == A['n_0024_rungs'] and n_first == A['n_first_decade_rungs']
p4, p7, p8 = plain[n_first - 1], plain[n24 - 1], plain[-1]
assert all(plain[k] == p4 * 2 ** (k - n_first + 1) for k in range(n_first - 1, n_r)), 'the rungs above rung 4 are not exact doublings'
plain24 = [r['n_chunks'] for r in V24['bar_applied']['rungs']]; assert plain24 == plain[:n24]
LOG2X = B['log2_chunks']; assert LOG2X == [r['log2_chunks'] for r in tab] and all(round(math.log2(p), 6) == x for p, x in zip(plain, LOG2X))
dbl = B['doublings_spanned']; dec = B['decades_spanned']
assert dbl == SR['doublings_spanned'] == SPp['doublings_spanned'] == F['doublings_spanned'] == round(LOG2X[-1] - LOG2X[0], 6)
assert dec == SR['decades_spanned'] == SPp['decades_spanned'] == F['decades_spanned'] == round(dbl * math.log10(2), 4)
dec24 = E24['freeze']['sealed_span']['decades_spanned']
assert dec24 == SPp['decades_spanned_0024'] == round(V24['bar_applied']['doublings_spanned'] * math.log10(2), 4)
W = {2: 'two', 3: 'three', 4: 'four', 5: 'five', 7: 'seven', 8: 'eight', 16: 'sixteen'}
x7, x8 = W[p7 // p4], W[p8 // p4]; assert p7 % p4 == 0 and p8 % p4 == 0
FAMS = sorted(V['fit3_rows_per_family']); assert FAMS == sorted(V['fit_rows_per_family']) == sorted(MAN3['families']); n_fam = W[len(FAMS)]
carve = A['corpus']['carve_bytes']; assert carve == MAN3['carve']
n_real = B['n_real_rows']; assert n_real == V['read']['n_ext_real_rows'] == A['n_ext_real_rows']
# the comparator named as the 2026-10-22 honesty pass names it: a 26-class linear model over 1108 features, never 'hand-writable'
n_cls, n_feat = A['n_classes'], A['corpus']['n_features']
assert n_cls == V['read']['n_classes'] and n_feat == J('artifacts/pivot/realcurve2_4096.json')['corpus']['n_features']
LOGI = f"the standardised logistic (a {n_cls}-class linear model over {n_feat} features)"
fit3_rows, fit3_chunks = B['fit3_rows'], B['fit3_source_chunks']
assert fit3_rows == MAN3['n_rows'] == PR['scope']['corpus_fit3']['n_new_rows'] and fit3_chunks == MAN3['n_chunks_with_rows'] == PR['scope']['corpus_fit3']['n_new_chunks_with_rows']
n_arch3 = sum(1 for k in PINS3['files'] if not k.startswith('rfc3/')); n_rfc3 = sum(1 for k in PINS3['files'] if k.startswith('rfc3/'))
assert (n_arch3, n_rfc3) == (sum(1 for k in MAN3['source_pins'] if not k.startswith('rfc3/')), sum(1 for k in MAN3['source_pins'] if k.startswith('rfc3/')))
assert os.path.exists(P('docs', 'compliance', 'EXT_SOURCES3.md'))
SRULES = ' '.join(PR['stop_rules'])

# the composition of the fourth doubling, per family
comp = F['rung_8_added_composition_per_family']
assert comp == SR['fourth_doubling_composition_per_family'] == tab[-1]['added_composition_per_family'] and sorted(comp) == FAMS
assert sum(c['n'] for c in comp.values()) == p8 - p7 and all(c['n'] == c['from_0024_pool'] + c['from_0024_archives_unused'] + c['from_new_files'] for c in comp.values())


def fam_phrase(f):
    c = comp[f]; n, new = c['n'], c['from_new_files']; noun = 'RFCs' if f == 'rfc_txt' else 'projects'
    if new == 0:
        return f"{f} other chunks of 0024's projects (all {n} plaintexts)"
    if 3 * new >= 2 * n:
        return f"{f} new {noun} for {new} of its {n} plaintexts (the rest other chunks of 0024's files)"
    return f"{f} a mixture ({new} of its {n} plaintexts from new {noun}, {n - new} other chunks of 0024's projects)"


fam_order = sorted(FAMS, key=lambda f: (-comp[f]['from_new_files'] / comp[f]['n'], f))
what_added = f"one doubling ({p8} against {p7} plaintexts) of other files of the same {n_fam} families above 0024's top rung"
FAMS_SENT = "Per family, the fourth doubling's files are " + "; ".join(fam_phrase(f) for f in fam_order)
assert 'new projects' in fam_phrase('py_src') and "other chunks of 0024's projects" in fam_phrase('c_src') + fam_phrase('pe_bin')

# the readings, the gains, the reading rule
by = {r: [p['ext_real_top1'] for p in CV[r]['rungs']] for r in ROLES}
assert by['model'] == V['model_real_top1_by_rung'] and by['model'][-1] == V['model_real_top1_top_rung'] and all(len(by[r]) == n_r for r in ROLES)
for k, row in enumerate(F['rung_table']):
    assert row['n_chunks'] == plain[k] and row['n_rows'] == rows[k] and all(row[r] == by[r][k] for r in ROLES)
bar = B['gain_per_doubling']; assert bar == FD['bar'] == PR['bar']['fourth_doubling']['threshold']


def gain_rule(point, lo, hi):
    return ('FOURTH_DOUBLING_FALLS' if hi < 0 else 'FOURTH_DOUBLING_RISES' if (point >= bar - 1e-9 and lo > 0)
            else 'FOURTH_DOUBLING_BELOW_RATE' if lo > 0 else 'FOURTH_DOUBLING_NOT_RESOLVED')


def lead_rule(lo, hi):
    return 'MODEL_LEADS' if lo > 0 else 'LINEAR_LEADS' if hi < 0 else 'NO_SEPARATION'


G = {r: FD[r] for r in ROLES}
for r in ROLES:
    g_ = G[r]
    assert g_['point'] == round(by[r][-1] - by[r][-2], 4) == CV[r]['fourth_doubling_gain'] == F['fourth_doubling_gain_by_role'][r] == V[f'{r}_fourth_doubling_gain']
    assert g_['ci95'] == F['fourth_doubling_gain_ci95_by_role'][r] and g_['reading'] == F['fourth_doubling_reading_by_role'][r] == gain_rule(g_['point'], *g_['ci95'])
gm = G['model']; gp, gci = gm['point'], gm['ci95']
assert gm['reading'] == gain and gp == V['model_fourth_doubling_gain'] == F['fourth_doubling_gain'] and gci == V['model_fourth_doubling_gain_ci95'] == F['fourth_doubling_gain_ci95_paired']
TOPK = f'r{n_r}_'; R7K = f'r{n24}_'; R4K = f'r{n_first}_'
LT = LD[f'{TOPK}model_minus_logistic']; L7 = LD[f'{R7K}model_minus_logistic']; L4 = LD[f'{R4K}model_minus_logistic']; LTT = LD[f'{TOPK}model_minus_depth3_tree']
assert LD['verdict_pair'] == f'{TOPK}model_minus_logistic' if 'verdict_pair' in LD else True
assert LT == F['lead_model_minus_logistic_at_top'] and L7 == F['lead_model_minus_logistic_at_rung7'] and L4 == F['lead_model_minus_logistic_at_rung4'] and LTT == F['lead_model_minus_depth3_tree_at_top']
assert LT['point'] == round(by['model'][-1] - by['logistic'][-1], 4) and LT['reading'] == lead == lead_rule(*LT['ci95'])
assert LTT['point'] == round(by['model'][-1] - by['depth3_tree'][-1], 4) and L4['point'] == round(by['model'][n_first - 1] - by['logistic'][n_first - 1], 4)
LT24 = V24['flags']['lead_model_minus_logistic_at_top']
assert V24['lead_reading'] == 'MODEL_LEADS' == LT24['reading'] and L7 == LT24, "rung 7's lead is not 0024's, reproduced exactly"
assert V['reproduction_bootstrap_0024']['equals_0024s_banked'] == {'slope_bootstrap': True, 'lead_at_top': True} == F['reproduction_bootstrap_0024_exact']
lp, lci = LT['point'], LT['ci95']
gap = F['model_minus_logistic_by_rung']; assert gap == [round(by['model'][i] - by['logistic'][i], 4) for i in range(n_r)]
SS = LD['s8_minus_s4_model']

# iteration caps: the gain is the model's, so only the model's cap at rung 7 or 8 touches it; the lead is touched by any role capped at 8
capped = F['roles_at_iteration_cap']; capped_top = F['roles_at_iteration_cap_at_the_top_rung']; capped_r7 = F['roles_at_iteration_cap_at_rung_7']
assert capped_top == sorted(n for n in capped if n.startswith(TOPK)) and capped_r7 == sorted(n for n in capped if n.startswith(R7K))
gain_cap_rungs = [k for k in (n24, n_r) if f'r{k}_model' in capped]
assert F['gain_is_a_recipe_reading'] == (not gain_cap_rungs) and F['lead_at_top_is_a_recipe_comparison'] == (not capped_top)
GCAP = (''.join(f' (the model at its iteration cap at rung {k})' for k in gain_cap_rungs)
        + ('; the cap is part of the sealed recipe and is never raised, and the gain is read as is, not as a recipe reading' if gain_cap_rungs else ''))
LCAP = ''.join(f' (the {n[len(TOPK):]} at its iteration cap at rung {n_r})' for n in capped_top) + ('; not a recipe comparison' if capped_top else '')


def rcap(role):
    """the cap note beside another role's (informational) fourth-doubling gain"""
    return ''.join(f' (the {role} at its iteration cap at rung {k})' for k in (n24, n_r) if f'r{k}_{role}' in capped)


# slopes: two-decade (a flag beside the fourth-doubling reading) and second-decade over rungs 4..8, recomputed
def ols(xs, ys):
    x = np.asarray(xs, np.float64); y = np.asarray(ys, np.float64); xm = x - x.mean()
    return float((xm * (y - y.mean())).sum() / (xm * xm).sum())


TD = F['two_decade_slope_per_doubling']; SD = F['second_decade_slope_per_doubling']; SDci = F['second_decade_slope_ci95']
for r in ROLES:
    assert TD[r]['slope_per_doubling'] == CV[r]['slope_per_doubling_both_decades'] == round(ols(LOG2X, by[r]), 6)
    assert TD[r]['ci95'] == V['slope_bootstrap']['both_decades'][r]['ci95']
    assert SD[r] == CV[r]['slope_per_doubling_second_decade'] == V[f'{r}_slope_per_doubling'] == round(ols(LOG2X[n_first - 1:], by[r][n_first - 1:]), 6)
    assert SDci[r] == V['slope_bootstrap'][r]['ci95']
    assert F['second_decade_slope_0024_reproduced'][r] == V24[f'{r}_slope_per_doubling'] == round(ols(LOG2X[n_first - 1:n24], by[r][n_first - 1:n24]), 6)
assert TD['model']['slope_per_doubling'] == V['model_two_decade_slope_per_doubling'] and TD['model']['ci95'] == V['model_two_decade_slope_ci95']
assert SDci['model'] == V['model_slope_ci95']
assert 'seven of its eight points were banked' in F['two_decade_slope_is'] and (W[n24], W[n_r]) == ('seven', 'eight')
dml = F['slope_model_minus_logistic_second_decade']; dml_ci = F['slope_model_minus_logistic_ci95_paired']
assert dml == round(SD['model'] - SD['logistic'], 6) and dml_ci == V['slope_bootstrap']['model_minus_logistic']['ci95']

# per-family gains, the reverse reading, the sensitivity gain
PFG = F['per_family_fourth_doubling_gain']
for r in ROLES:
    assert PFG[r] == CV[r]['per_family_fourth_doubling_gain'] == {f: round(CV[r]['rungs'][-1]['ext_per_family'][f] - CV[r]['rungs'][-2]['ext_per_family'][f], 4) for f in FAMS}
BEG = F['builder_eval_fourth_doubling_gain']
assert all(BEG[r] == round(CV[r]['rungs'][-1]['builder_eval_top1'] - CV[r]['rungs'][-2]['builder_eval_top1'], 4) for r in ROLES)
by24 = {r: [p['ext_real_top1'] for p in V24['curves'][r]['rungs']] for r in ROLES}
SENS = F['fourth_doubling_gain_with_rung7_at_0024s_reading']
assert all(SENS[r] == round(by[r][-1] - by24[r][-1], 4) == CV[r]['fourth_doubling_gain_with_rung7_at_reference'] for r in ROLES)
sens_read = F['fourth_doubling_reading_with_rung7_at_0024s_reading']; assert sens_read == gain_rule(SENS['model'], *gci)
straddle = sens_read != gain
pub = GAINS[max(GAINS.index(gain), GAINS.index(sens_read))]     # the design's rule: on a straddle the less flattering one, named as such

# floors at rung 8 (and 7), the pre-committed words read from the sealed design
FL = V['floors']; assert FL == F['floors']
for k in (n24, n_r):
    fl = FL[f'r{k}']; best = max(fl['floors'].values())
    assert fl['floors']['floor_tree3'] == by['depth3_tree'][k - 1] and fl['model'] == by['model'][k - 1] and fl['logistic'] == by['logistic'][k - 1]
    assert fl['best_floor'] == best and fl['needed_0021_clause'] == round(best + 0.05, 4) and fl['clears_0021_clause'] == (fl['model'] >= fl['needed_0021_clause'])
    assert fl['needed_with_logistic_as_floor'] == round(max(best, fl['logistic']) + 0.05, 4)
    assert fl['clears_with_logistic_as_floor'] == (fl['model'] >= fl['needed_with_logistic_as_floor'])
F8 = FL[f'r{n_r}']
mfl = re.search(r"'clears' reads '(.*?)'; 'does not clear' reads '(.*?)'\.", PR['scope']['design']['floors']); assert mfl
FLOOR_CLEARS, FLOOR_NOT = mfl.group(1), mfl.group(2)
assert f'{x8} times 0021' in FLOOR_CLEARS and f'{x8} times 0021' in FLOOR_NOT and f"within {round(F8['needed_0021_clause'] - F8['best_floor'], 4)} of" in FLOOR_NOT
floor_words = (f"clears it: {FLOOR_CLEARS}" if F8['clears_0021_clause'] else f"does not clear it: {FLOOR_NOT}")

# the shift arms
S4 = F['shift_arm_0024']; S8 = F['shift_arm_0025']
for r in ROLES:
    assert S4['readings_ext_real_top1'][r] == V['reproduction_shift_arm_0024'][r] == V['shift_arm']['readings'][r]['ext_real_top1']
    assert S8['readings_ext_real_top1'][r] == V['shift_arm_0025']['readings'][r]['ext_real_top1']
    for kk, k in (('difference_from_rung_4', n_first), ('difference_from_rung_7', n24), ('difference_from_rung_8', n_r)):
        assert S8[kk][r] == round(S8['readings_ext_real_top1'][r] - by[r][k - 1], 4)
    assert S8['difference_from_shift_arm_0024'][r] == round(S8['readings_ext_real_top1'][r] - S4['readings_ext_real_top1'][r], 4)
    assert S4['difference_from_rung_4'][r] == round(S4['readings_ext_real_top1'][r] - by[r][n_first - 1], 4)
assert SS['point'] == S8['difference_from_shift_arm_0024']['model'] and SS['ci95'] == S8['s8_minus_s4_model_ci95_paired']
assert S8['n_chunks'] == p4 == SPp['shift_arm_0025']['n_chunks'] and S8['n_rows'] == SPp['shift_arm_0025']['n_rows']
assert S8['composition_per_family'] == SPp['shift_arm_0025']['composition_per_family']

# reproduction of 0021, 0023 and 0024, the null, the seed stability, the checkpoints
tol = PR['bar']['reproduces_0021_0023_and_0024']['threshold']
mt7 = re.search(r"rung 7's three within ([0-9.]+)", PR['bar']['reproduces_0021_0023_and_0024']['passes_if']); assert mt7; tol7 = float(mt7.group(1))
D24 = F['reproduction_0024_drift']
for r in ROLES:
    assert D24[r] == [round(by[r][k] - by24[r][k], 6) for k in range(n24)] and all(abs(d) <= tol for d in D24[r]) and abs(D24[r][-1]) <= tol7
assert V['reproduction_drift'] == F['reproduction_drift_rung_4'] and all(abs(d) <= tol for d in V['reproduction_drift'].values())
assert all(abs(d) <= tol for d in F['reproduction_shift_arm_0024_drift'].values())
d7 = {r: D24[r][-1] for r in ROLES}
maxd = max((D24[r][k] for r in ROLES for k in range(n24 - 1)), key=abs)
null_real, null_ext, null_eval = V['shuffled_label_accuracy_real'], V['shuffled_label_accuracy_ext'], V['shuffled_label_accuracy_eval']
chance = V['read']['chance_accuracy']; nul_tol = PR['bar']['null_control']['threshold']
assert null_real == F['null_real_top1'] and null_ext <= chance + nul_tol and null_eval <= chance + nul_tol
ST = F['seed_stability']; VST = V['seed_stability']
assert ST['n_seeds'] == len(VST['seeds']) == len(VST['gain_readings']) == len(VST['lead_readings'])
assert ST['n_seeds_with_another_gain_reading'] == sum(1 for x in VST['gain_readings'].values() if x != gain)
assert ST['n_seeds_with_another_lead_reading'] == sum(1 for x in VST['lead_readings'].values() if x != lead)
n_fits = len(V['ext_real_top1']); mfit = re.search(r'(\d+) fits, (\d+) scorings', PR['scope']['design']['fits']); assert mfit and n_fits == int(mfit.group(1))
n_ckpt = V['checkpoints_cross_checked']
assert n_ckpt == n_fits or DRY, f'the reader cross-checked {n_ckpt} committed checkpoints, not {n_fits}'

# cost, the estimate stated in advance, the expected outcome
cost = A['cost']; wall = cost['wall_seconds_this_invocation']; fits_s = cost['banked_fit_seconds_total']; secs = cost['seconds_by_name']
launches = A['launch_number']; lw = A['launch_environment']['loadavg_waited_seconds']
assert sorted(secs) == sorted(V['ext_real_top1']) and abs(sum(secs.values()) - fits_s) < 0.05 * len(secs) + 1e-9
mest = re.search(r'In all (\d+) to (\d+) s of fits \(([\d.]+) to ([\d.]+) hours\)', PR['scope']['cost']['estimate_stated_in_advance']); assert mest
est_lo, est_hi, est_lo_h, est_hi_h = int(mest.group(1)), int(mest.group(2)), mest.group(3), mest.group(4)
EXP = PR['scope']['expected_outcome_stated_in_advance']; g24 = V24['flags']['rung_to_rung_gains']['model'][n_first - 1:n24 - 1]
assert len(g24) == 3 and f'({g24[1]}, {g24[2]})' in EXP and f'({g24[0]})' in EXP and 'NO_SEPARATION at least as likely as MODEL_LEADS' in EXP

# the sealed words the record receives: the forward pointer and the bounded sentences
mptr = re.search(r"the sentence '(both together span (\d+\.\d+) decades, short of 0003's two-decade scope rule)' \(([^)]*)\) receives, in every "
                 r"place it stands, the pointer '(.*?)'; on ", SRULES)
assert mptr and float(mptr.group(2)) == dec24, 'the stop rule does not name the sentence the record carries'
PTR = mptr.group(4)
assert PTR.startswith("with 0025's fourth doubling") and f'{dec} decades ({plain[0]} to {p8} plaintexts)' in PTR and '{' not in PTR and '}' not in PTR
assert f"keep buying the recipe the record's rate ... through {p7} plaintexts" in SRULES and "the record's scaling thesis holds on real files" in SRULES
assert "'a rise below the record's rate'" in SRULES and "'whether the fourth doubling bought anything is not resolved by the scored chunks at this size'" in SRULES
assert "'adding the fourth doubling's files of the same kinds lowered the model's reading on the original files'" in SRULES
assert "'(the model at its iteration cap at rung N)'" in SRULES
lp24, ci24 = LT24['point'], LT24['ci95']

print('numbers:', dict(verdict=verdict, published_gain_reading=pub, straddle=straddle, plain=plain, by=by, gain=(gp, gci), lead=(lp, lci),
                       two_decade=TD['model'], second_decade=(SD['model'], SDci['model']), floors_r8=F8['needed_0021_clause'], shift8=S8['readings_ext_real_top1'],
                       drift7=d7, null=null_real, stab=ST, capped=capped, ckpt=n_ckpt, cost=(wall, fits_s, launches), dec=dec, dec24=dec24))


# ---------------------------------------------------------------- 2. the sentences every document shares, by outcome
def wrap(s, width=112, prefix=''):
    return '\n'.join(textwrap.fill(p, width=width, initial_indent=prefix, subsequent_indent=prefix, break_long_words=False,
                                   break_on_hyphens=False) for p in s.split('\n'))


def L(xs):
    return ', '.join(map(str, xs))


def cap1(s):
    return s[0].upper() + s[1:]


def low1(s):
    return s[0].lower() + s[1:]


RNG = f'rung {n_r} minus rung {n24}'
GAIN_TXT = {
    'FOURTH_DOUBLING_RISES': f"{RNG} for the model is {gp} on the real-family rows (paired scored-chunk interval {gci}, entirely above 0), at or above the record's rate of {bar} per doubling",
    'FOURTH_DOUBLING_BELOW_RATE': f"{RNG} for the model is {gp} on the real-family rows (paired scored-chunk interval {gci}, entirely above 0), below the record's rate of {bar} per doubling: a rise below the record's rate",
    'FOURTH_DOUBLING_NOT_RESOLVED': f"{RNG} for the model is {gp} on the real-family rows with a paired scored-chunk interval {gci} that includes 0: whether the fourth doubling bought anything is not resolved by the scored chunks at this size, never read as 'flat' or 'equal'",
    'FOURTH_DOUBLING_FALLS': f"{RNG} for the model is {gp} on the real-family rows with a paired scored-chunk interval {gci} entirely below 0: adding the fourth doubling's files of the same kinds lowered the model's reading on the original files"}
STRADDLE = (f"; with rung {n24} held at 0024's banked {by24['model'][-1]} the gain is {SENS['model']}, which reads {sens_read}: the two straddle a reading "
            f"boundary, so the reading published here is the less flattering one, {pub}, named as such" if straddle else "")
gain_txt = GAIN_TXT[gain] + STRADDLE + GCAP
LEAD_TXT = {
    'MODEL_LEADS': f"at rung {n_r} the model leads the standardised logistic by {lp} (paired interval {lci}, entirely above 0)",
    'LINEAR_LEADS': f"at rung {n_r} the standardised logistic leads the model by {round(-lp, 4)} (paired interval of model minus logistic {lci}, entirely below 0): a rule a person can write out has overtaken the boosted recipe",
    'NO_SEPARATION': f"at rung {n_r} model minus logistic is {lp} with a paired interval {lci} that includes 0: the two are not separated at this size, never read as 'equal'"}
lead_txt = LEAD_TXT[lead] + LCAP
GAIN_HEAD = {'FOURTH_DOUBLING_RISES': f"The fourth doubling of real plaintexts rises at or above the record's bar of {bar} per doubling",
             'FOURTH_DOUBLING_BELOW_RATE': "The fourth doubling of real plaintexts buys a rise below the record's rate",
             'FOURTH_DOUBLING_NOT_RESOLVED': "Whether the fourth doubling bought anything is not resolved by the scored chunks at this size, never read as 'flat' or 'equal'",
             'FOURTH_DOUBLING_FALLS': "Adding the fourth doubling's files of the same kinds lowered the model's reading on the original files"}
LEAD_HEAD = {'MODEL_LEADS': f"at rung {n_r} the boosted model leads {LOGI} by {lp}",
             'LINEAR_LEADS': f"at rung {n_r} {LOGI} leads the boosted model by {round(-lp, 4)}",
             'NO_SEPARATION': f"at rung {n_r} the boosted model and {LOGI} are not separated, never read as 'equal'"}
headline = f"{GAIN_HEAD[pub]}{GCAP} — and {LEAD_HEAD[lead]}{LCAP}"
stab = (f"under {ST['n_seeds']} other bootstrap seeds the gain reading would have differed {ST['n_seeds_with_another_gain_reading']} times and the "
        f"lead reading {ST['n_seeds_with_another_lead_reading']} times (a flag)")
core = f"`{verdict}` — {gain_txt}; {lead_txt}; {stab}"          # the verdict sentence: the gain part never without the lead part
span_words = (f"the span meets 0003's two-decade scope rule only in the sense that the rule asked for two decades of data; its one-corpus, one-seed "
              f"terms are not met by this curve, whose first decade is the scored files' own chunks")
readings = (f"the model reads **{L(by['model'])}** over the {W[n_r]} rungs, the standardised logistic **{L(by['logistic'])}**, the depth-3 tree "
            f"**{L(by['depth3_tree'])}**")
readings_plain = readings.replace('**', '')
pf_m = ', '.join(f"{f} {PFG['model'][f]}" for f in FAMS)
flags_sentence = (
    f"Beside the fourth-doubling reading (`{verdict}`{GCAP}{LCAP}) and never as a rise of its own: the standardised logistic's "
    f"fourth-doubling gain is {G['logistic']['point']} (paired interval {G['logistic']['ci95']}){rcap('logistic')}, the depth-3 tree's "
    f"{G['depth3_tree']['point']} ({G['depth3_tree']['ci95']}); the model's per family {pf_m}; on the builder's own evaluation set the "
    f"fourth-doubling gains read model {BEG['model']}, logistic {BEG['logistic']}, tree {BEG['depth3_tree']}; the two-decade slope over all "
    f"{W[n_r]} rungs (seven of its eight points were banked before this run) is {TD['model']['slope_per_doubling']} per doubling for the model "
    f"(scored-chunk interval {TD['model']['ci95']}), {TD['logistic']['slope_per_doubling']} for the logistic ({TD['logistic']['ci95']}) and "
    f"{TD['depth3_tree']['slope_per_doubling']} for the tree ({TD['depth3_tree']['ci95']}); the second-decade slope over rungs {n_first}..{n_r} is "
    f"{SD['model']} ({SDci['model']}), {SD['logistic']} ({SDci['logistic']}) and {SD['depth3_tree']} ({SDci['depth3_tree']}), model minus "
    f"logistic {dml} (paired interval {dml_ci}); and the floors refitted at rung {n_r} (majority, stratified, one thresholded feature; the "
    f"depth-3 tree being D1 itself) put 0021's clause at {F8['needed_0021_clause']}, and the model's {F8['model']} {floor_words} (with the "
    f"logistic among the floors {F8['needed_with_logistic_as_floor']}, {'cleared' if F8['clears_with_logistic_as_floor'] else 'not cleared'})")
shift_sentence = (
    f"The two shift arms, each at rung {n_first}'s count of {p4} plaintexts: 0024's (rung {n_first + 1}'s new plaintexts alone, reproduced) "
    f"reads model {S4['readings_ext_real_top1']['model']}, logistic {S4['readings_ext_real_top1']['logistic']}, tree "
    f"{S4['readings_ext_real_top1']['depth3_tree']}; the new one (rung {n_r}'s plaintexts from 0025's corpus alone at rung {n_first}'s count, "
    f"{S8['n_rows']} rows) reads model {S8['readings_ext_real_top1']['model']}, logistic {S8['readings_ext_real_top1']['logistic']}, tree "
    f"{S8['readings_ext_real_top1']['depth3_tree']} — for the model {S8['difference_from_rung_4']['model']} against rung {n_first}, "
    f"{S8['difference_from_rung_7']['model']} against rung {n24}, {S8['difference_from_rung_8']['model']} against rung {n_r}, and "
    f"{S8['difference_from_shift_arm_0024']['model']} against 0024's arm (paired interval {SS['ci95']}): the direct reading of what the fourth "
    f"doubling's files buy alone for the original files at the same count, informational")
repro = (f"Rungs 1..{n24} and 0024's shift arm were refitted row for row under 0024's own seeds before any new plaintext was fitted and "
         f"reproduced 0024's readings (rung {n24} drift {d7['model']}, {d7['logistic']} and {d7['depth3_tree']} for the model, the logistic "
         f"and the tree; at most {abs(maxd)} in absolute value on rungs 1..{n24 - 1}) and 0024's bootstrap intervals exactly")
def mcap(k):
    """the stop rule's note beside any other lead read with the model at its cap at rung k"""
    return f' (the model at its iteration cap at rung {k})' if f'r{k}_model' in capped else ''


lead_flags = (f"at rung {n24} the same reading is 0024's {L7['point']} ({L7['ci95']}, {L7['reading']}){mcap(n24)}, reproduced exactly; at rung "
              f"{n_first} it is {L4['point']} ({L4['ci95']}, {L4['reading']}); over the depth-3 tree at rung {n_r} the model's lead is {LTT['point']} "
              f"({LTT['ci95']}, {LTT['reading']}){mcap(n_r)}; model minus logistic by rung {L(gap)}")
ckpt_words = (f"the {n_ckpt} committed checkpoints cross-checked by the reader" if n_ckpt else "no committed checkpoints present for the reader to cross-check")
controls = (f"Controls: the null control on rung {n_r}'s permuted labels reads {null_real} on the real rows, {null_ext} on the extension set "
            f"and {null_eval} on the evaluation set against chance {chance}; roles at their iteration cap: {', '.join(capped) if capped else 'none'}; "
            f"{ckpt_words}. Cost: {wall} s wall on the last of {launches} launch(es), {fits_s} s of fits banked (rung {n_r}'s model fit "
            f"{secs[f'{TOPK}model']} s), against the {est_lo} to {est_hi} s ({est_lo_h} to {est_hi_h} hours) of fits estimated in advance")
KEEP24 = f"keep raising the recipe's accuracy at or above the record's bar of {bar} per doubling"   # 0024's keep sentence, as the honesty pass worded it
MEAN_GAIN = {
    'FOURTH_DOUBLING_RISES': f"one more doubling of other files of the same kinds raises the recipe's accuracy on the files it is scored on at or above the record's bar of {bar} per doubling (the bar 0025 sealed; {gp} measured), at {p8} plaintexts ({x8} times 0021's)",
    'FOURTH_DOUBLING_BELOW_RATE': f"one more doubling of other files of the same kinds buys a rise below the record's rate on the files it is scored on, so 0024's sentence that such files {KEEP24} is bounded to {p7} plaintexts",
    'FOURTH_DOUBLING_NOT_RESOLVED': f"whether the fourth doubling bought anything is not resolved by the scored chunks at this size, never read as 'flat' or 'equal', so 0024's sentence that such files {KEEP24} is bounded to {p7} plaintexts",
    'FOURTH_DOUBLING_FALLS': f"adding the fourth doubling's files of the same kinds lowered the model's reading on the original files, so 0024's sentence that such files {KEEP24} is bounded to {p7} plaintexts, and so is 0023's sentence on the scaling thesis"}
MEAN_LEAD = {
    'MODEL_LEADS': f"at {x8} times 0021's plaintexts the boosted recipe leads {LOGI} on the record's own real content by {lp}{LCAP} — the recipe conclusion of 0021, 0022 and 0023 (that the linear rule gets most of the signal) is bounded by the size of that lead, not reversed",
    'LINEAR_LEADS': f"at {x8} times 0021's plaintexts {LOGI} leads the boosted recipe on the record's own real content by {round(-lp, 4)}{LCAP}, and 0024's lead of the model is bounded to {p7} plaintexts — the manufactured-label headline (0003, 0014) is not revised, but the claim that the recipe is what the data buys is",
    'NO_SEPARATION': f"at {x8} times 0021's plaintexts the boosted recipe and {LOGI} are not separated on the record's own real content, never read as 'equal'{LCAP}, and 0024's lead of the model is bounded to {p7} plaintexts — the recipe conclusion of 0021, 0022 and 0023 stands as measured"}
meaning = f"{MEAN_GAIN[pub]}{GCAP}; {MEAN_LEAD[lead]}"
not_transfer = (f"Not a transfer reading: every rung holds the scored files' own unscored chunks and the plaintexts added above rung {n_first} are other "
                f"files of the same kinds, so the fourth doubling confounds more plaintexts with a further shift of source, which the new shift arm "
                f"reads directly; the intervals cover the {n_real} scored real-family rows' chunks only, not the draw of rung {n_r}'s plaintexts nor the "
                f"fit side (one nesting, one seed, no replicate of rung {n_r})")
expected = (f"The sealed file expected FOURTH_DOUBLING_RISES if the gain resembled 0024's last two second-decade gains ({g24[1]}, {g24[2]}) and "
            f"FOURTH_DOUBLING_BELOW_RATE if it resembled the first ({g24[0]}), and on the lead NO_SEPARATION at least as likely as MODEL_LEADS; "
            f"the run read `{verdict}`{GCAP}{LCAP}")
closing = ("No extrapolation beyond the top rung is banked or quoted. Nothing here revises the numbers of 0003, 0014, 0015, 0016, 0017, 0018, 0019, "
           "0021, 0022, 0023 or 0024, and nothing here establishes a buyer.")
corpus_words = (f"a third fit corpus built and sealed before the freeze ({n_arch3} newly pinned PyPI archives and {n_rfc3} more RFCs, licences in "
                f"`docs/compliance/EXT_SOURCES3.md`; {fit3_chunks} new plaintexts with rows, {fit3_rows} rows), nested on 0024's pool so that rungs "
                f"1..{n24} recur chunk for chunk")

# the pointers and bounds the stop rules give earlier sentences (each carries the rung-8 reading beside it)
LEAD_BOUND_WORDS = {'MODEL_LEADS': 'MODEL_LEADS', 'LINEAR_LEADS': 'the standardised logistic ahead: LINEAR_LEADS',
                    'NO_SEPARATION': "not separated, never read as 'equal': NO_SEPARATION"}
lead_short = f"model minus logistic at rung {n_r} {lp} (paired interval {lci}), {LEAD_BOUND_WORDS[lead]}{LCAP}"
lead_short_n = f"model minus logistic at rung {n_r} ({p8} plaintexts) {lp} (paired interval {lci}), {LEAD_BOUND_WORDS[lead]}{LCAP}"
GAIN_SHORT = {'FOURTH_DOUBLING_RISES': f"at or above the record's bar of {bar} per doubling", 'FOURTH_DOUBLING_BELOW_RATE': "a rise below the record's rate",
              'FOURTH_DOUBLING_NOT_RESOLVED': "whether the fourth doubling bought anything is not resolved by the scored chunks at this size, never read as 'flat' or 'equal'",
              'FOURTH_DOUBLING_FALLS': "adding the fourth doubling's files of the same kinds lowered the model's reading on the original files"}
gain_short = f"{RNG} for the model {gp} (paired interval {gci}): {GAIN_SHORT[pub]}{STRADDLE}{GCAP}"
PTR_SPAN = f" [{PTR}]"
BOUND_KEEP = f" [bounded by 0025 to {p7} plaintexts: at rung {n_r} ({p8} plaintexts) 0025 read `{verdict}` — {gain_short}; {lead_short}]"
BOUND_THESIS = (f" [bounded by 0025: at rung {n_r} ({p8} plaintexts) adding the fourth doubling's files of the same kinds lowered the model's "
                f"reading on the original files — `{verdict}`, {RNG} for the model {gp} (paired interval {gci}){STRADDLE}{GCAP}; {lead_short}]")
BOUND_LEAD = f" [bounded by 0025 to {p7} plaintexts: {lead_short_n}]"
BOUNDED_GAINS = ('FOURTH_DOUBLING_BELOW_RATE', 'FOURTH_DOUBLING_NOT_RESOLVED', 'FOURTH_DOUBLING_FALLS')

# ---------------------------------------------------------------- 3. the anchors of the earlier sentences, whitespace-tolerant
# Anchored on the documents' wording after the 2026-10-22 honesty pass (0024's lead is stated as the reader read it, 'leads the
# standardised logistic ... by 0.0039', never 'still leads the hand-writable linear rule'), and wherever possible on 0024's banked
# numbers (the lead 0.0039, its interval [0.0001, 0.0077], rung 7's 8232 plaintexts) and the verdict token rather than on prose.
SEP = r'(?:[ ]|\n[ ]*(?:> ?)?)'                               # a space, or a line break (a list item's indent, a quote's '> ')
IN_SENT = r'(?:(?!\.(?:\*\*)?(?:\s|$))[^\n]|\n(?!\s*\n))'     # one character that neither ends the sentence nor the paragraph
SENT_END = re.compile(r'\.(?:\*\*)?(?=\s|$)|\n\s*\n')


def flex(phrase):
    return SEP.join(re.escape(w) for w in phrase.split(' '))


RX_SPAN = re.compile(flex(f'{dec24} decades, short of') + SEP + r"(?:0003's|our" + SEP + "own)" + SEP + flex('two-decade scope rule'))
# 0024's meaning sentence: other files of the same kinds keep (buying the recipe the record's rate | raising the recipe's accuracy
# at or above the record's bar) ... through rung 7's plaintexts; the bound goes after "(eight times 0021's)"
RX_KEEP = re.compile(flex('of the same kinds keep') + IN_SENT + '{0,300}?' + SEP + flex(f"through {p7} plaintexts ({x7} times 0021's)"))
# 0023's meaning sentence, anchored on "the record's scaling thesis": "holds on real files" before the honesty pass; "holds on these
# real files, in distribution, over just under a decade (0003's scope rule asks for two)" after it; since 2026-10-22 (VERDICT.md and
# DILIGENCE.md alike) "this does not establish the record's scaling thesis, which 0003's scope rule ties to two decades of data on one
# corpus with one seed (this curve spans 0.8985 of a decade)". The pointer goes after the words that follow, when they do.
RX_THESIS = re.compile(flex("the record's scaling thesis") + '(?:'
                       + flex(", which 0003's scope rule ties to two decades of data on one corpus with one seed (this curve spans") + SEP
                       + r'[0-9]+(?:\.[0-9]+)?' + SEP + flex('of a decade)')
                       + '|' + SEP + flex('holds') + '(?:' + SEP + flex('on') + '(?:' + SEP + flex('these') + ')?' + SEP
                       + flex('real files') + '(?:' + flex(', in distribution, over just under a decade') + SEP
                       + r"\(0003's" + SEP + flex('scope rule asks for two)') + ')?)?)?')
# every statement of 0024's top-rung lead: "leads the standardised logistic / the linear rule ... by 0.0039" in one sentence
# (headlines, headings, the meaning sentences, DILIGENCE's answer), "the standardised logistic 0.0039 behind the model", the one-pager's
# headline (which carries no number), and a `MODEL_LEADS` token with 0024's interval just before it
RX_LEAD_BY = re.compile(r'leads' + SEP + 'the' + SEP + r'(?:standardised' + SEP + 'logistic|linear' + SEP + 'rule)' + IN_SENT + '{0,160}?'
                        + SEP + 'by' + SEP + re.escape(str(lp24)) + r'(?![0-9])')
RX_LEAD_BEHIND = re.compile(re.escape(str(lp24)) + SEP + flex('behind the model') + '(?:' + SEP + flex("at 0024's top rung") + ')?')
RX_LEAD_EDGE = re.compile(flex('the boosted model edges ahead of the standardised linear rule'))
RX_LEAD_TOKEN = re.compile(r'`MODEL_LEADS`')
RX_LEAD_SUFFIX = re.compile(SEP + flex('by the rule sealed in advance'))
MARKS = ("with 0025's", 'bounded by 0025')


def docs_named(s):
    """the publication documents a stop rule's parenthesis names ('VERDICT.md, README.md', 'VERDICT.md, DILIGENCE.md')"""
    out = set()
    for x in re.split(r',\s*|\s+and\s+', s.strip()):
        hit = [c for c in (x, 'docs/' + x, 'outbound/' + x) if os.path.exists(P(c))]
        assert hit, f'the stop rule names {x!r}, which is not a document here'
        out.add(hit[0])
    return out


mkeep = re.search(r"the sentence 'other files of the same kinds keep buying the recipe the record's rate \.\.\. through (\d+) plaintexts' \(([^)]*)\)", SRULES)
mthes = re.search(r"on 0023's 'the record's scaling thesis holds on real files' \(([^)]*)\)", SRULES)
assert mkeep and int(mkeep.group(1)) == p7 and mthes, 'the stop rule does not name the keep or the thesis sentence where the publication expects it'
KEEP_DOCS, THESIS_DOCS = docs_named(mkeep.group(2)), docs_named(mthes.group(1))
assert KEEP_DOCS == {'VERDICT.md', 'README.md'} and THESIS_DOCS == {'VERDICT.md', 'docs/DILIGENCE.md'}, (KEEP_DOCS, THESIS_DOCS)
KEEP_WORDS = "keep buying the recipe the record's rate"; THESIS_WORDS = "the record's scaling thesis holds on real files"   # the stop rule's own


def close_bracket(s, i):
    """index of the ']' closing the '[' at s[i]"""
    depth = 0
    for j in range(i, len(s)):
        depth += {'[': 1, ']': -1}.get(s[j], 0)
        if depth == 0:
            return j
    raise AssertionError('unbalanced pointer bracket')


def insert_after(text, ends, ptr):
    """put ptr right after each anchor end; an earlier 0025 pointer already there is replaced, never doubled"""
    out, pos = [], 0
    for e in sorted(set(ends)):
        out.append(text[pos:e]); nxt = e
        if text.startswith(' [', e) and text[e + 2:].startswith(MARKS):
            nxt = close_bracket(text, e + 1) + 1
        out.append(ptr); pos = nxt
    out.append(text[pos:])
    return ''.join(out)


def lead_token_ends(text):
    """a bare `MODEL_LEADS` is 0024's published lead reading only where 0024's top-rung interval stands just before it (every 0024
    statement of the reading quotes it); a mention of the outcome's name (an expectation, a plan, a rule) is left alone"""
    ends = []
    for m in RX_LEAD_TOKEN.finditer(text):
        before = re.sub(r'\s+', ' ', text[max(0, m.start() - 240):m.start()].replace('\n>', ' '))[-200:]
        if 'likely than' in before[-24:] or 'likely as' in before[-24:] or str(ci24) not in before:
            continue
        sm = RX_LEAD_SUFFIX.match(text, m.end())
        ends.append(sm.end() if sm else m.end())
    return ends


def strip_marks(s):
    """s without the 0025 pointers and bounds already in it (so that a second run sees the sentences the first run saw)"""
    for mk in MARKS:
        while ' [' + mk in s:
            i = s.index(' [' + mk); s = s[:i] + s[close_bracket(s, i + 1) + 1:]
    return s


def lead_ends(text):
    """one bound per sentence that states 0024's top-rung lead, after the last statement of it in that sentence (a sentence that
    gives the lead and then its `MODEL_LEADS` is bounded once, after the token)"""
    ends = sorted(set([m.end() for rx in (RX_LEAD_BY, RX_LEAD_BEHIND, RX_LEAD_EDGE) for m in rx.finditer(text)] + lead_token_ends(text)))
    return [e for e, nxt in zip(ends, ends[1:] + [None]) if nxt is None or SENT_END.search(strip_marks(text[e:nxt]))]


COUNTS = {}
SITE_NOTES = []


def passes(text, name):
    """the stop rules' pointers and bounds on the sentences that stand OUTSIDE 0025's own units (which are cut out first): the span
    sentence and 0024's lead wherever they stand, the keep and the thesis sentences in the documents their stop rule names"""
    c = COUNTS.setdefault(name, {})
    ends = [m.end() for m in RX_SPAN.finditer(text)]; c['span'] = len(ends); text = insert_after(text, ends, PTR_SPAN)
    for key, rx, docs, words, applies, bound in (('keep', RX_KEEP, KEEP_DOCS, KEEP_WORDS, pub in BOUNDED_GAINS, BOUND_KEEP),
                                                 ('thesis', RX_THESIS, THESIS_DOCS, THESIS_WORDS, pub == 'FOURTH_DOUBLING_FALLS', BOUND_THESIS)):
        if name not in docs:
            continue
        ms = list(rx.finditer(text))
        for m in ms:     # the sentence no longer in the stop rule's words: still the stop rule's site, and named for the operator
            if words not in re.sub(r'\s+', ' ', text[max(0, m.start() - 60):m.end()].replace('\n>', ' ')):
                SITE_NOTES.append(f"{name} line {text.count(chr(10), 0, m.start()) + 1}: the {key} sentence the stop rule names no longer reads "
                                  f"'{words}' (it reads '{re.sub(r'[ ]+', ' ', m.group(0).replace(chr(10), ' '))[:90]}...'); "
                                  + ('bounded here all the same' if applies else 'it is still its site on the outcomes the stop rule names'))
        if applies:
            c[key] = len(ms); text = insert_after(text, [m.end() for m in ms], bound)
    if lead in ('LINEAR_LEADS', 'NO_SEPARATION'):
        ends = lead_ends(text); c['lead'] = len(ends); text = insert_after(text, ends, BOUND_LEAD)
    return text


PH = '\x00UNIT0025:{}\x00'


def line_bounds(text, i):
    s = text.rfind('\n', 0, i) + 1; e = text.find('\n', i)
    return s, (len(text) if e < 0 else e + 1)


def cut_lines(text, marker, ph):
    """replace every whole line holding marker by one placeholder (none if absent); returns (text, found)"""
    found = False
    while marker in text:
        s, e = line_bounds(text, text.index(marker))
        text = text[:s] + ('' if found else ph) + text[e:]; found = True
    return text, found


NEW = {}   # path -> new text
OLD = {}


def load(path):
    if path not in NEW:
        OLD[path] = T(path); NEW[path] = OLD[path]
    return NEW[path]


# ---------------------------------------------------------------- 4. VERDICT.md: the block, the row, the pointers
head24 = f"**Preregistration 0024 (chain seq 24) — `{V24['verdict']}`, and what it found.**"
head25 = f"**Preregistration 0025 (chain seq {seq}) — `{verdict}`, and what it found.**"
INFLIGHT_V = '**In flight — preregistration 0025 '
v = load('VERDICT.md'); assert v.count(head24) == 1
i24 = v.index(head24)
for s in (INFLIGHT_V, '**Preregistration 0025 (chain seq '):
    if s in v:
        i = v.index(s); assert i < i24 and '**Preregistration 00' not in v[i + len(s):i24], f'the 0025 text in VERDICT.md is not where it belongs ({s!r})'
        v = v[:i] + PH.format('block') + v[i24:]; break
else:
    v = v[:i24] + PH.format('block') + v[i24:]
ROW25 = '| **Fourth doubling of real plaintexts at 4096 (0025)** |'
v, _ = cut_lines(v, ROW25, '')
v = passes(v, 'VERDICT.md')
block = (
    f"{head25} {headline}. The doubling 0024 was short of — its curve spanned {dec24} decades, short of the two that 0003's scope rule "
    f"asks for — was bought with {corpus_words}: rung {n_r} is {what_added}. {FAMS_SENT}. {cap1(W[n_r])} rungs of {L(plain)} plaintexts ({L(rows)} rows; "
    f"{dbl} doublings, {dec} decades: {span_words}). 0021's three fixed recipes (M4, L3, D1) were fitted once per rung and scored once on the "
    f"same {n_real} real-family rows: {readings}. {repro}. **{cap1(core)}.**\n"
    f"\n"
    f"**{cap1(LEAD_HEAD[lead])}{LCAP}.** At {p8} plaintexts the model reads {by['model'][-1]} and the standardised logistic "
    f"{by['logistic'][-1]}: {lead_txt}, the model ahead in {LT['share_of_resamples_with_model_ahead']} of the resamples (a description of the "
    f"resamples, not a probability), read by 0024's sealed lead rule as `{lead}`; {lead_flags}.\n"
    f"\n"
    f"**The flags, beside the fourth-doubling reading.** {flags_sentence}. {shift_sentence}.\n"
    f"\n"
    f"{controls}.\n"
    f"\n"
    f"**What it means.** {cap1(meaning)}. {not_transfer}. {expected}. {closing}\n")
block = wrap(block, 112)
v = v.replace(PH.format('block'), block + '\n')
row25 = (f"{ROW25} **`{verdict}`** — {low1(headline)}: {what_added}, from {corpus_words} ({L(plain)} plaintexts; {dec} decades). {FAMS_SENT}. The model "
         f"reads {L(by['model'])}, the logistic {L(by['logistic'])}, the tree {L(by['depth3_tree'])}; {core}. {flags_sentence}. {shift_sentence}. "
         f"Rung {n24} drift {d7['model']}; null {null_real}. Chain entry {seq}. | primary-verifiable |\n")
assert '|' not in row25[len(ROW25):-len(' | primary-verifiable |\n')], 'a pipe inside the table row'
row_anchor = ('| **Second decade of real plaintexts at 4096 (0024)** |' if pub == 'FOURTH_DOUBLING_RISES' else '| **Real-content recipe search at 4096 (0022)** |')
assert v.count(row_anchor) == 1
s_, e_ = line_bounds(v, v.index(row_anchor)); v = v[:e_] + row25 + v[e_:]
NEW['VERDICT.md'] = v

# ---------------------------------------------------------------- 5. README.md
r = load('README.md'); a2 = 'The curve and the searched margin stand as measured'; assert r.count(a2) == 1
ir = r.index('Preregistration 0025 (chain entry') if 'Preregistration 0025 (chain entry' in r else r.index(a2)
assert ir <= r.index(a2) and 'Preregistration 00' not in r[ir + 10:r.index(a2)]
r = r[:ir] + PH.format('readme') + r[r.index(a2):]
r = passes(r, 'README.md')
para_r = wrap(
    f"Preregistration 0025 (chain entry {seq}) bought the doubling 0024 was short of: {what_added}, from {corpus_words} ({L(plain)} plaintexts "
    f"over {W[n_r]} rungs; {dec} decades: {span_words}). {FAMS_SENT}. **{core[:core.index(' — ')]} — {low1(headline)}**: {gain_txt}; {lead_txt}; {stab}. "
    f"{cap1(readings_plain)}. {flags_sentence}. {shift_sentence}. {repro}. {cap1(meaning)}. No extrapolation beyond the top rung is banked or "
    f"quoted.", 128) + '\n'
r = r.replace(PH.format('readme'), para_r + '\n')
NEW['README.md'] = r

# ---------------------------------------------------------------- 6. outbound/ONE_PAGER.md
o = load('outbound/ONE_PAGER.md'); M_OP24 = 'Preregistration 0024 nested three exact doublings'; M_OP25 = 'Preregistration 0025 added one doubling'
o, _ = cut_lines(o, M_OP25, '')
o = passes(o, 'outbound/ONE_PAGER.md'); assert o.count(M_OP24) == 1
para_o = (f"{headline}. {M_OP25}{what_added[len('one doubling'):]} — {fit3_chunks} new plaintexts from {n_arch3} newly pinned PyPI archives and "
          f"{n_rfc3} more RFCs, nested on 0024's pool: {L(plain)} plaintexts over {W[n_r]} rungs, {dec} decades ({span_words}) — and fitted "
          f"0021's three fixed recipes on each: {readings}; {core}. {FAMS_SENT}. {flags_sentence}. {shift_sentence}. {repro}; null {null_real}. "
          f"{cap1(meaning)}. No extrapolation beyond the top rung is banked or quoted.\n")
s_, e_ = line_bounds(o, o.index(M_OP24)); o = o[:e_] + para_o + o[e_:]
NEW['outbound/ONE_PAGER.md'] = o

# ---------------------------------------------------------------- 7. outbound/EVIDENCE_BRIEF.md: a paragraph and a findings bullet
b = load('outbound/EVIDENCE_BRIEF.md')
M_B24 = 'Preregistration 0024 built and sealed a second fit corpus'; M_B25 = 'Preregistration 0025 built and sealed a third fit corpus'
M_BB24 = '- **Second decade of real plaintexts at 4096:'; M_BB25 = '- **Fourth doubling of real plaintexts at 4096:'
b, _ = cut_lines(b, M_B25, ''); b, _ = cut_lines(b, M_BB25, '')
b = passes(b, 'outbound/EVIDENCE_BRIEF.md'); assert b.count(M_B24) == 1 and b.count(M_BB24) == 1
para_b = (f"**{headline}.** {M_B25} before its freeze — {fit3_chunks} new plaintexts, {fit3_rows} rows, from {n_arch3} newly pinned PyPI "
          f"archives and {n_rfc3} more RFCs, licences filed — and nested it on 0024's pool so that rungs 1..{n24} recur chunk for chunk: rung {n_r} is "
          f"{what_added}; {W[n_r]} rungs of {L(plain)} plaintexts ({L(rows)} rows), {dec} decades ({span_words}). {FAMS_SENT}. 0021's three fixed recipes "
          f"were fitted once per rung and scored once on the same {n_real} rows: {readings}; **{core}**. {cap1(lead_flags)}. {flags_sentence}. "
          f"{shift_sentence}. {repro}; null {null_real}; {ckpt_words}; {wall} s wall, {fits_s} s of fits against {est_lo} to {est_hi} s "
          f"estimated in advance. {cap1(meaning)}. {not_transfer}. No extrapolation beyond the top rung is banked or quoted.\n")
s_, e_ = line_bounds(b, b.index(M_B24)); b = b[:e_] + para_b + b[e_:]
bullet = (f"{M_BB25} `{verdict}` — {low1(headline)}.** {cap1(what_added)}, from {n_arch3} newly pinned PyPI archives and {n_rfc3} more RFCs "
          f"nested on 0024's pool: {L(plain)} plaintexts, {dec} decades. {FAMS_SENT}. Model {L(by['model'])}, logistic {L(by['logistic'])}, tree "
          f"{L(by['depth3_tree'])}: {gain_txt}; {lead_txt}; {stab}. {flags_sentence}. {shift_sentence}. Rung {n24} drift {d7['model']}; null "
          f"{null_real}. Expected outcome stated in advance: FOURTH_DOUBLING_RISES if the gain resembled 0024's last two second-decade gains, "
          f"FOURTH_DOUBLING_BELOW_RATE if the first; on the lead NO_SEPARATION at least as likely as MODEL_LEADS; the run read `{verdict}`{GCAP}{LCAP}. "
          f"No buyer established.\n")
s_, e_ = line_bounds(b, b.index(M_BB24)); b = b[:e_] + bullet + b[e_:]
NEW['outbound/EVIDENCE_BRIEF.md'] = b

# ---------------------------------------------------------------- 8. outbound/NARRATIVE.md: a blockquote paragraph after 0024's
n = load('outbound/NARRATIVE.md')
M_N24 = '> Then we bought the plaintexts that did not exist (0024)'; M_N25 = '> Then we bought the doubling we were short of (0025)'
END_N25 = re.compile(flex(f'We do not extrapolate past rung {n_r}.') + r'[^\n]*\n')
if M_N25 in n:
    s_ = n.index(M_N25); m_ = END_N25.search(n, s_); assert m_
    n = n[:s_] + n[m_.end():]
n = passes(n, 'outbound/NARRATIVE.md'); assert n.count(M_N24) == 1
m24 = re.compile(flex('We do not extrapolate past the top rung.') + r'[^\n]*\n').search(n, n.index(M_N24)); assert m24
para_n = wrap(
    f"{M_N25[2:]}: {n_arch3} more PyPI archives and {n_rfc3} more RFCs, pinned, licensed and hashed against every chunk and every kilobyte "
    f"run of the original files and of 0024's, nested on 0024's pool so that its {W[n24]} rungs recur chunk for chunk — rung {n_r} is "
    f"{what_added}. {FAMS_SENT}. The curve now runs from {plain[0]} to {p8} plaintexts, {dec} decades: {span_words}. {cap1(readings_plain)}, and the verdict "
    f"is read on the last doubling alone, by rules we wrote down before the run: {core}. {flags_sentence}. {shift_sentence}. {cap1(meaning)}. "
    f"We do not extrapolate past rung {n_r}.", 110, '> ') + '\n'
n = n[:m24.end()] + para_n + n[m24.end():]
NEW['outbound/NARRATIVE.md'] = n

# ---------------------------------------------------------------- 9. docs/DILIGENCE.md: the Q&A
d = load('docs/DILIGENCE.md'); a7 = '## "Who buys it?"'; Q25 = '## "Does a fourth doubling of real files help?"'; assert d.count(a7) == 1
if Q25 in d:
    assert d.index(Q25) < d.index(a7); d = d[:d.index(Q25)] + d[d.index(a7):]
d = passes(d, 'docs/DILIGENCE.md')
ANS = {'FOURTH_DOUBLING_RISES': f"Yes, at or above the record's bar of {bar} per doubling", 'FOURTH_DOUBLING_BELOW_RATE': "A rise below the record's rate",
       'FOURTH_DOUBLING_NOT_RESOLVED': "Whether the fourth doubling bought anything is not resolved by the scored chunks at this size, never read as 'flat' or 'equal'",
       'FOURTH_DOUBLING_FALLS': "No: adding the fourth doubling's files of the same kinds lowered the model's reading on the original files"}
ANS_LEAD = {k: f"and {h}" for k, h in LEAD_HEAD.items()}     # the lead head's words: never 'still', never 'hand-writable'
qa = (f"{Q25}\n\n"
      f"**{ANS[pub]}{GCAP} — {ANS_LEAD[lead]}{LCAP}** (prereg 0025, the doubling 0024 was short of: its curve spanned {dec24} decades). Rung {n_r} "
      f"is {what_added}, from {corpus_words} (`artifacts/pivot/realfit3_corpus_manifest.json`). {FAMS_SENT}. {cap1(W[n_r])} rungs of {L(plain)} plaintexts "
      f"({L(rows)} rows; {dbl} doublings, {dec} decades: {span_words}); 0021's three fixed recipes were fitted once per rung and scored once on the "
      f"same {n_real} rows (`artifacts/pivot/realcurve3_4096_verdict.json`): {readings_plain}. {repro}. The verdict is read on the fourth doubling "
      f"alone, seven of the eight points having been banked before this run: {core}. The lead flags: {lead_flags}. {flags_sentence}. "
      f"{shift_sentence}. {controls}. {expected}. What it means: {meaning}. {not_transfer}. No extrapolation beyond the top rung is banked or "
      f"quoted.\n\n")
d = d.replace(a7, qa + a7, 1)
NEW['docs/DILIGENCE.md'] = d

# ---------------------------------------------------------------- 10. the other publication documents (the stop rules name VERDICT.md, README.md, the
# outbound documents and DILIGENCE.md); any other page under docs/ (a plan, a brief, a changelog) may quote these sentences or name the
# outcomes as such, so it is never edited here: it is named in a NOTE for the operator to read
NOTES = []
for extra in sorted(os.path.relpath(os.path.join(dp, f), R) for sub in ('outbound', 'docs') for dp, _, fs in os.walk(P(sub)) for f in fs if f.endswith('.md')):
    if extra in NEW:
        continue
    t = T(extra)
    hit = bool(RX_SPAN.search(t) or (pub in BOUNDED_GAINS and RX_KEEP.search(t)) or (pub == 'FOURTH_DOUBLING_FALLS' and RX_THESIS.search(t)) or
               (lead != 'MODEL_LEADS' and lead_ends(t)))
    if hit and extra.startswith('outbound/'):
        OLD[extra] = t; NEW[extra] = passes(t, extra)
    elif hit:
        NOTES.append(f'{extra} quotes a sentence a stop rule points at or bounds; not a publication document, so it is left as it is - read it')

# the stop rules' sites, counted (the dry run checks each one is touched exactly once)
cnt = lambda k, f: COUNTS.get(f, {}).get(k, 0)  # noqa: E731
for f, k in (('README.md', 1), ('outbound/ONE_PAGER.md', 1), ('outbound/EVIDENCE_BRIEF.md', 2), ('outbound/NARRATIVE.md', 1), ('docs/DILIGENCE.md', 1)):
    assert cnt('span', f) == k, (f, COUNTS.get(f))
assert cnt('span', 'VERDICT.md') >= 1
if pub in BOUNDED_GAINS:
    assert all(cnt('keep', f) >= 1 for f in KEEP_DOCS), COUNTS
if pub == 'FOURTH_DOUBLING_FALLS':
    assert all(cnt('thesis', f) >= 1 for f in THESIS_DOCS), COUNTS
if lead != 'MODEL_LEADS':
    assert all(cnt('lead', f) >= 1 for f in ('VERDICT.md', 'README.md', 'outbound/ONE_PAGER.md', 'outbound/EVIDENCE_BRIEF.md', 'outbound/NARRATIVE.md', 'docs/DILIGENCE.md')), COUNTS
# nothing of 0025's own may stand where a stop rule's anchor would find it on the next run (0025's lead is bounded only on
# LINEAR_LEADS or NO_SEPARATION, whose units state no lead of the model)
for unit_text in (block, row25, para_r, para_o, para_b, bullet, para_n, qa):
    assert not (RX_SPAN.search(unit_text) or RX_KEEP.search(unit_text) or RX_THESIS.search(unit_text)), 'a 0025 unit carries an anchor phrase'
    assert lead == 'MODEL_LEADS' or not lead_ends(unit_text), 'a 0025 unit carries a lead anchor or a bare `MODEL_LEADS`'

# ---------------------------------------------------------------- 11. tools/render/evidence_page.py: 0024's panel, read from 0025's verdict at render time
ep = 'tools/render/evidence_page.py'; e = load(ep)
DEF_ANCHOR = 'boundary_0024 = ""\n'; assert e.count(DEF_ANCHOR) == 1
ptr_src = PTR.replace("'", "\\'")
num_old = f'{dec} decades ({plain[0]} to {p8} plaintexts)'; assert ptr_src.count(num_old) == 1
ptr_src = ptr_src.replace(num_old, '{rc3v["bar_applied"]["decades_spanned"]} decades ({rc3v["bar_applied"]["rungs"][0]["n_chunks"]} to '
                                   '{rc3v["bar_applied"]["rungs"][-1]["n_chunks"]} plaintexts)')
DEFS = (
    "# 0025's forward pointers in 0024's panel (written by the 0025 publication): the words are 0025's sealed stop rule's, every number is\n"
    "# read from 0025's verdict at render time, and both are empty unless that verdict exists, is not VOID and its run is complete.\n"
    "_rc3_live = bool(rc3a and rc3v and rc3v[\"verdict\"] != \"VOID\" and rc3a.get(\"complete\"))\n"
    "_rc3_span = (f' [" + ptr_src + "]' if _rc3_live else '')\n"
    "_rc3_lt = rc3v[\"lead_at_top\"][\"r8_model_minus_logistic\"] if _rc3_live else None\n"
    "_rc3_lcap = (\"\".join(f' (the {n[3:]} at its iteration cap at rung 8)' for n in rc3v[\"flags\"][\"roles_at_iteration_cap_at_the_top_rung\"])\n"
    "             + ('; not a recipe comparison' if rc3v[\"flags\"][\"roles_at_iteration_cap_at_the_top_rung\"] else '')) if _rc3_live else ''\n"
    "_rc3_lead_bound = (f' [bounded by 0025 to {rc3v[\"bar_applied\"][\"rungs\"][-2][\"n_chunks\"]} plaintexts: model minus logistic at rung 8 '\n"
    "                   f'({rc3v[\"bar_applied\"][\"rungs\"][-1][\"n_chunks\"]} plaintexts) {_rc3_lt[\"point\"]} '\n"
    "                   f'(paired interval {_rc3_lt[\"ci95\"]}), '\n"
    "                   + {\"LINEAR_LEADS\": \"the standardised logistic ahead: LINEAR_LEADS\",\n"
    "                      \"NO_SEPARATION\": \"not separated, never read as \\'equal\\': NO_SEPARATION\"}[rc3v[\"lead_reading\"]] + _rc3_lcap + ']'\n"
    "                   if _rc3_live and rc3v[\"lead_reading\"] in (\"LINEAR_LEADS\", \"NO_SEPARATION\") else '')\n")
if '_rc3_live = ' in e:
    s_ = e.index("# 0025's forward pointers in 0024's panel"); e = e[:s_] + e[e.index(DEF_ANCHOR):]
e = e.replace(DEF_ANCHOR, DEFS + DEF_ANCHOR, 1)
span_old = f"f'{dec24} decades, short of 0003\\'s two-decade scope rule. No extrapolation"
span_new = f"f'{dec24} decades, short of 0003\\'s two-decade scope rule' + _rc3_span + f'. No extrapolation"
if span_new not in e:
    assert e.count(span_old) == 1, 'the 0024 panel no longer carries the sealed span sentence'
    e = e.replace(span_old, span_new, 1)
COUNTS[ep] = {'span': e.count(span_new)}
CAP24 = 'for n in _cap)}'
assert e.count(CAP24) == 1
if '+ _rc3_lead_bound' not in e:
    s_, e_ = line_bounds(e, e.index(CAP24)); e = e[:e_] + '                     + _rc3_lead_bound\n' + e[e_:]
compile(e, ep, 'exec')
NEW[ep] = e

# ---------------------------------------------------------------- 12. the engineering log's run_record
E['run_record'] = {
    'invocation': PR['invocation']['run'].split(' --prereg-file')[0] + ' ...', 'launches': launches, 'load_wait_seconds': lw,
    'run_started_utc': A['run_started_utc'], 'finished_utc': A['run_finished_utc'], 'wall_seconds_last_launch': wall, 'fit_seconds_banked': fits_s,
    'seconds_by_name': secs, 'estimate_stated_in_advance_fit_seconds': {'low': est_lo, 'high': est_hi}, 'n_iter_by_name': F['n_iter_by_name'],
    'verdict': verdict, 'verdict_components': V['verdict_components'], 'validity_failed_clauses': V['validity_failed_clauses'],
    'published_gain_reading': pub, 'sensitivity_straddles_a_reading_boundary': straddle,
    'the_gain_clause': {'bar_gain_per_doubling': bar, 'model_fourth_doubling_gain': gp, 'paired_ci95': gci, 'reading': gain,
                        'share_of_resamples_with_a_gain': gm['share_of_resamples_with_a_gain'], 'gain_is_a_recipe_reading': F['gain_is_a_recipe_reading'],
                        'with_rung7_at_0024s_reading': SENS, 'reading_with_rung7_at_0024s_reading': sens_read,
                        'plaintexts_per_rung': plain, 'rows_per_rung': rows, 'doublings_spanned': dbl, 'decades_spanned': dec,
                        'model_real_top1_by_rung': by['model'], 'fourth_doubling_composition_per_family': comp},
    'the_lead_clause': {'rule': B['lead_rule'], 'rung_8': LT, 'rung_7_0024s_reproduced': L7, 'rung_4': L4, 'rung_8_over_the_tree': LTT,
                        'roles_at_iteration_cap_at_rung_8': capped_top, 'roles_at_iteration_cap_at_rung_7': capped_r7,
                        'lead_at_top_is_a_recipe_comparison': F['lead_at_top_is_a_recipe_comparison'], 'model_minus_logistic_by_rung': gap},
    'the_other_roles': {'logistic_by_rung': by['logistic'], 'depth3_tree_by_rung': by['depth3_tree'], 'fourth_doubling_gain': {r: G[r] for r in ROLES},
                        'per_family_fourth_doubling_gain': PFG, 'builder_eval_fourth_doubling_gain': BEG},
    'flags_beside_the_reading': {'two_decade_slope': TD, 'two_decade_slope_is': F['two_decade_slope_is'], 'second_decade_slope_rungs_4_to_8': SD,
                                 'second_decade_slope_ci95': SDci, 'slope_model_minus_logistic_second_decade': dml, 'paired_ci95': dml_ci,
                                 'second_decade_slope_0024_reproduced': F['second_decade_slope_0024_reproduced']},
    'floors': FL, 'shift_arm_0024': S4, 'shift_arm_0025': S8, 'seed_stability': ST,
    'controls_all_passed': {'reproduction_0024_drift': D24, 'reproduction_drift_rung_4_vs_0021': V['reproduction_drift'],
                            'reproduction_shift_arm_0024_drift': F['reproduction_shift_arm_0024_drift'],
                            'reproduction_bootstrap_0024_exact': F['reproduction_bootstrap_0024_exact'], 'null_on_real_rows': null_real,
                            'null_on_extension': null_ext, 'null_on_evaluation': null_eval, 'chance': chance, 'roles_at_iteration_cap': capped,
                            'checkpoints_cross_checked': n_ckpt},
    'what_it_found': {
        'one_line': f"{headline}: {gain_txt}; {lead_txt}.",
        'the_verdict_sentence': f"{cap1(core)}.",
        'the_fourth_doubling': f"rung {n_r} is {what_added}. {FAMS_SENT}; {readings_plain}.",
        'the_lead': f"{cap1(lead_txt)}; {lead_flags}.",
        'the_flags': f"{flags_sentence}.",
        'the_shift_arms': f"{shift_sentence}.",
        'what_it_means_for_the_record': f"{cap1(meaning)}. {not_transfer}. {closing}",
        'expected_outcome_vs_measured': f"{expected}.",
    },
    'cost': (f"{wall} s wall on the last of {launches} launch(es), {fits_s} s of fits banked (r{n_r}_model {secs[f'{TOPK}model']} s, null "
             f"{secs['null']} s); load wait {lw} s; the estimate stated in advance was {est_lo} to {est_hi} s ({est_lo_h} to {est_hi_h} hours) of fits."),
}
E['status'] = f'complete: {verdict}'
NEW['artifacts/pivot/engineering_log_0025.json'] = json.dumps(E, indent=2, sort_keys=True, ensure_ascii=True) + '\n'
OLD.setdefault('artifacts/pivot/engineering_log_0025.json', T('artifacts/pivot/engineering_log_0025.json'))

# ---------------------------------------------------------------- 13. coverage claims, primary-verifiable, each json_path checked here
cp = 'artifacts/verification/coverage.json'; OLD[cp] = T(cp); C = json.loads(OLD[cp])
assert OLD[cp] == json.dumps(C, indent=2, sort_keys=True, ensure_ascii=True) + '\n'


def jp(obj, path):
    assert path.startswith('$')
    for name, idx in re.findall(r'\.([A-Za-z0-9_]+)|\[(\d+)\]', path):
        obj = obj[name] if name else obj[int(idx)]
    return obj


art = 'artifacts/pivot/realcurve3_4096_verdict.json'; rv = 'python3 tools/readers/realcurve3_4096_verdict.py'
vtag = f"{verdict}{GCAP}{LCAP}"
claims = [
    ('realcurve34096-verdict', '$.verdict', verdict, f"Preregistration 0025: {verdict} — {low1(headline)}; rung {n_r} is {what_added}."),
    ('realcurve34096-gain-part', '$.gain_reading', gain, f"The gain part, quoted with the lead part ({lead}{LCAP}) beside it: {gain_txt}."),
    ('realcurve34096-lead-part', '$.lead_reading', lead, f"The lead part, read at rung {n_r} by 0024's sealed paired-interval rule beside the gain part ({gain}{GCAP}): {lead_txt}."),
    ('realcurve34096-model-gain', '$.model_fourth_doubling_gain', gp, f"{cap1(RNG)} for the model is {gp} on the real-family rows ({vtag})."),
    ('realcurve34096-model-gain-ci-low', '$.model_fourth_doubling_gain_ci95[0]', gci[0], f"The paired scored-chunk interval of the model's fourth-doubling gain has lower bound {gci[0]} ({vtag})."),
    ('realcurve34096-model-gain-ci-high', '$.model_fourth_doubling_gain_ci95[1]', gci[1], f"The paired scored-chunk interval of the model's fourth-doubling gain has upper bound {gci[1]} ({vtag})."),
    ('realcurve34096-logistic-gain', '$.logistic_fourth_doubling_gain', G['logistic']['point'], f"Beside the fourth-doubling reading ({vtag}), the standardised logistic's fourth-doubling gain is {G['logistic']['point']}{rcap('logistic')} (a flag)."),
    ('realcurve34096-tree-gain', '$.depth3_tree_fourth_doubling_gain', G['depth3_tree']['point'], f"Beside the fourth-doubling reading ({vtag}), the depth-3 tree's fourth-doubling gain is {G['depth3_tree']['point']} (a flag)."),
    ('realcurve34096-lead-top-point', f'$.lead_at_top.{TOPK}model_minus_logistic.point', lp, f"At rung {n_r} ({p8} plaintexts) model minus logistic is {lp}{LCAP}."),
    ('realcurve34096-lead-top-ci-low', f'$.lead_at_top.{TOPK}model_minus_logistic.ci95[0]', lci[0], f"The paired interval of model minus logistic at rung {n_r} has lower bound {lci[0]}{LCAP}."),
    ('realcurve34096-lead-top-ci-high', f'$.lead_at_top.{TOPK}model_minus_logistic.ci95[1]', lci[1], f"The paired interval of model minus logistic at rung {n_r} has upper bound {lci[1]}{LCAP}."),
    ('realcurve34096-top-rung-model', '$.model_real_top1_top_rung', by['model'][-1], f"At {p8} plaintexts the model reads {by['model'][-1]} on the real-family rows."),
    ('realcurve34096-rung7-model', f'$.model_real_top1_by_rung[{n24 - 1}]', by['model'][n24 - 1], f"At rung {n24} ({p7} plaintexts, 0024's top rung) the model reads {by['model'][n24 - 1]}: 0024's reading, drift {d7['model']}."),
    ('realcurve34096-rung7-drift', f'$.flags.reproduction_0024_drift.model[{n24 - 1}]', d7['model'], f"Rung {n24} reproduces 0024's model reading with drift {d7['model']}."),
    ('realcurve34096-two-decade-slope', '$.model_two_decade_slope_per_doubling', TD['model']['slope_per_doubling'], f"Beside the fourth-doubling reading ({vtag}) and never as a rise of its own, the model's two-decade slope over all {W[n_r]} rungs is {TD['model']['slope_per_doubling']} per doubling (interval {TD['model']['ci95']}); seven of its eight points were banked before this run."),
    ('realcurve34096-second-decade-slope', '$.model_slope_per_doubling', SD['model'], f"Beside the fourth-doubling reading ({vtag}) and never as a rise of its own, the model's second-decade slope over rungs {n_first}..{n_r} is {SD['model']} per doubling (interval {SDci['model']})."),
    ('realcurve34096-floor-r8-needed', f'$.floors.r{n_r}.needed_0021_clause', F8['needed_0021_clause'], f"Beside the fourth-doubling reading ({vtag}), the floors refitted at rung {n_r} put 0021's clause at {F8['needed_0021_clause']}, and the model's {F8['model']} {floor_words}."),
    ('realcurve34096-shift-arm-0025-model', '$.shift_arm_0025.readings.model.ext_real_top1', S8['readings_ext_real_top1']['model'], f"The new shift arm (rung {n_r}'s plaintexts from 0025's corpus alone at rung {n_first}'s count) reads {S8['readings_ext_real_top1']['model']} for the model, {S8['difference_from_rung_4']['model']} against rung {n_first} and {S8['difference_from_shift_arm_0024']['model']} against 0024's arm (informational)."),
    ('realcurve34096-null', '$.shuffled_label_accuracy_real', null_real, f"The null control on rung {n_r}'s permuted labels reads {null_real} on the real-family rows."),
]
by_id = {c['id']: c for c in C['claims']}; added = 0
for cid, path, val, text in claims:
    assert jp(V, path) == val, (cid, path)
    new_c = {'artifact': art, 'claim': text, 'class': 'primary-verifiable', 'id': cid, 'json_path': path, 'reverify': rv, 'value': val}
    if cid in by_id:
        by_id[cid].clear(); by_id[cid].update(new_c)
    else:
        C['claims'].append(new_c); added += 1
C['n_claims'] = len(C['claims'])
n_neither = sum(1 for c in C['claims'] if c['class'] == 'neither'); n_prim = sum(1 for c in C['claims'] if c['class'] == 'primary-verifiable')
n_arith = sum(1 for c in C['claims'] if c['class'] == 'arithmetic-verifiable')
NEW[cp] = json.dumps(C, indent=2, sort_keys=True, ensure_ascii=True) + '\n'
for path, rx in (('VERDICT.md', r'\*\*(\d+) of (\d+) claims are in `neither`'), ('outbound/ONE_PAGER.md', r'\*\*(\d+) of (\d+) claims are in the weakest class\*\*'),
                 ('outbound/NARRATIVE.md', r'weakest class first — (\d+) of (\d+) claims')):
    t = load(path); ms = list(re.finditer(rx, t)); assert len(ms) == 1, (path, rx, len(ms))
    m = ms[0]; NEW[path] = t[:m.start(1)] + str(n_neither) + t[m.end(1):m.start(2)] + str(C['n_claims']) + t[m.end(2):]
t = NEW['VERDICT.md']
for rx, val in ((r'\| `neither` \| \*\*(\d+)\*\* \|', n_neither), (r'\| `arithmetic-verifiable` \| (\d+) \|', n_arith), (r'\| `primary-verifiable` \| (\d+) \|', n_prim)):
    ms = list(re.finditer(rx, t)); assert len(ms) == 1, rx
    t = t[:ms[0].start(1)] + str(val) + t[ms[0].end(1):]
NEW['VERDICT.md'] = t

# ---------------------------------------------------------------- 14. leftovers of the in-flight text, then write
warn = []
for f, t in NEW.items():
    if f.endswith('.md'):
        for m in re.finditer(r'[Ii]n flight[^\n]{0,120}0025|0025 \(chain (?:seq|entry) \d+, frozen[^\n]{0,60}\)', t):
            warn.append(f'{f}: in-flight text for 0025 remains: {t[m.start():m.start() + 100]!r}')
for f in sorted(NEW):
    if NEW[f] != OLD[f]:
        with open(P(f), 'w', encoding='utf-8') as fh:
            fh.write(NEW[f])
        print(f'wrote {f}')
    else:
        print(f'unchanged {f}')
print('sites counted:', json.dumps(COUNTS, sort_keys=True))
print(f'coverage: {added} claims added, n_claims {C["n_claims"]}, neither {n_neither}, primary {n_prim}')
if RENDER:
    rp = subprocess.run([sys.executable, '-B', 'tools/render/evidence_page.py'], cwd=R, capture_output=True, text=True)
    assert rp.returncode == 0, rp.stdout[-2000:] + rp.stderr[-2000:]
    html = T('outbound/evidence_page.html')
    ptr_html = PTR.replace("'", '&#x27;') if PTR not in html else PTR
    assert html.count(PTR) + html.count(PTR.replace("'", '&#x27;')) + html.count(PTR.replace("'", '&#39;')) == 1, 'the rendered page does not carry the pointer exactly once'
    print('rendered outbound/evidence_page.html')
for w_ in warn:
    print('WARNING:', w_)
for n_ in sorted(set(SITE_NOTES)) + NOTES:
    print('NOTE:', n_)
print(f'done: preregistration 0025 published as {verdict}' + (f' (the published gain reading is the less flattering {pub}, named as such)' if straddle else ''))
