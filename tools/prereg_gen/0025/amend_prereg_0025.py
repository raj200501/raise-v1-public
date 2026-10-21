#!/usr/bin/env python3
"""Amend the UNFROZEN preregistration 0025 with the changes its pre-freeze instrument review required, without the generator
(make_prereg_0025.py was lost with the old container on 2026-10-21; the committed file is its last output). Every edit is an
exact replacement asserted to occur exactly once, or an explicit value change; the sealed hashes are recomputed with the reader
generator's canonical serialisation; every other byte of meaning is asserted unchanged; the changes are recorded in the file
itself under amendments_before_freeze. Refuses on a frozen file. Idempotent: a second run changes nothing."""
import copy, hashlib, json, sys

R = '/home/user/raise-v1'
PATH = f'{R}/prereg/0025-realcurve3-4096.json'
canon = lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)  # noqa: E731
sha = lambda o: hashlib.sha256(canon(o).encode()).hexdigest()  # noqa: E731

pr = json.load(open(PATH, encoding='utf-8'))
assert pr.get('frozen') is False, 'refusing: the preregistration is frozen'
before = copy.deepcopy(pr)
S = pr['scope']; P = S['curve']['protocol']
a24 = json.load(open(f'{R}/artifacts/pivot/realcurve2_4096.json', encoding='utf-8'))

# ---- the memory peak, derived from banked numbers only
RB7 = [e['rss_gb'] for e in a24['ledger'] if e.get('name') == 'run_r7_depth3_tree' and e.get('event') == 'rung_bound'][0]
ROWS8 = S['sealed_partition']['rungs'][-1]['n_rows']; N_FIT3 = P['fit3_corpus']['n_rows']
BLOCK8 = round(ROWS8 * 1108 * 8 / 1e9, 2); F3 = round(N_FIT3 * 1108 * 4 / 1e9, 2)
PEAK8 = round(RB7 + F3 + BLOCK8 + BLOCK8 / 2, 1)
TREE7_HB = a24['fits']['r7_depth3_tree']['heartbeat_max_rss_gb']; MODEL7_HB = a24['fits']['r7_model']['heartbeat_max_rss_gb']
assert (RB7, BLOCK8, F3) == (3.59, 3.73, 0.97), (RB7, BLOCK8, F3)

changes = []


def replace_once(obj_get, obj_set, old, new, where, why):
    s = obj_get()
    if new in s and old not in s:
        return
    assert s.count(old) == 1, (where, s.count(old), old[:80])
    obj_set(s.replace(old, new))
    changes.append({"where": where, "why": why})


# 1. the launch floor
if P['launch']['min_mem_available_gb'] != 11.0:
    assert P['launch']['min_mem_available_gb'] == 8.0
    P['launch']['min_mem_available_gb'] = 11.0
    changes.append({"where": "scope.curve.protocol.launch.min_mem_available_gb", "was": 8.0, "is": 11.0,
                    "why": "the run's own peak at rung 8 is above 8.0 GB (pre-freeze instrument review, runner lens, major)"})

# 2. the memory estimate: the peak, from banked numbers
old_mem = S['cost']['memory']
new_mem = (f"from 0024's banked ledger and heartbeats: anonymous RSS at rung 7's rung_bound (before its block) was {RB7} GB; 0024's "
           f"r7_depth3_tree heartbeat peaked at {TREE7_HB} GB and r7_model's at {MODEL7_HB} GB, the tree's rise over its start being the "
           f"float32 copy sklearn's trees make of the float64 block. For rung 8: {RB7} GB + the third fit corpus in float32 ({F3} GB) + "
           f"rung 8's float64 block ({BLOCK8} GB) + the trees' float32 copy of it ({round(BLOCK8 / 2, 2)} GB) gives about {PEAK8} GB anonymous "
           f"at r8_floor_feat1 and r8_depth3_tree, the run's peak, against the sealed memory_kill_gb of {P['caps']['memory_kill_gb']} on a "
           f"15 GB machine whose shell memory cgroup is limited to about 14.3 GB; the launch therefore requires 11.0 GB available and "
           f"nothing else heavy in the same cgroup (the runner refuses to start beside another runner, a corpus builder or the mutation "
           f"suite). An earlier version of this sentence projected about 9.0 GB from a line through post-fit readings, which understates "
           f"the trees' peak (pre-freeze instrument review). COULD NOT VERIFY until run.")
if old_mem != new_mem:
    S['cost']['memory'] = new_mem
    changes.append({"where": "scope.cost.memory", "why": "the peak restated from heartbeat maxima with the trees' float32 copy counted (review, runner lens, major)"})

# 3. the new NOT RUN rule: 0024's intervals checked exactly before rung 8
NR_OLD = "the runner files NOT RUN on the first drift it sees, which by the sealed order is rung 7, before any new plaintext is fitted."
NR_NEW = ("the runner files NOT RUN on the first point drift it sees (by the sealed order, rung 7 first) and, once all twenty-one "
          "reproduction fits are banked, on 0024's slope and lead intervals not recomputing exactly - both before any new plaintext is fitted.")
for i, txt in enumerate(S['rival_explanations_run_as_arms']):
    if NR_OLD in txt or NR_NEW in txt:
        replace_once(lambda i=i: S['rival_explanations_run_as_arms'][i], lambda v, i=i: S['rival_explanations_run_as_arms'].__setitem__(i, v),
                     NR_OLD, NR_NEW, f"scope.rival_explanations_run_as_arms[{i}]", "the runner now checks 0024's intervals exactly before rung 8 (review, runner lens)")
b = pr['bar']['reproduces_0021_0023_and_0024']
replace_once(lambda: b['passes_if'], lambda v: b.__setitem__('passes_if', v), NR_OLD, NR_NEW,
             "bar.reproduces_0021_0023_and_0024.passes_if", "the same rule, in the bar")
STOP_OLD = "outside its tolerance; the null control's permuted labels"
STOP_NEW = ("outside its tolerance; 0024's slope and lead intervals not recomputing exactly from this run's rung 1..7 vectors once the last "
            "of them is banked, before any rung-8 fit; the null control's permuted labels")
for i, txt in enumerate(pr['stop_rules']):
    if txt.startswith('NOT RUN is reachable only by mechanical rules'):
        replace_once(lambda i=i: pr['stop_rules'][i], lambda v, i=i: pr['stop_rules'].__setitem__(i, v), STOP_OLD, STOP_NEW,
                     f"stop_rules[{i}]", "the new mechanical NOT RUN condition is listed with the others")

# 4. the majority-floor pair
FL_OLD = "the reader's pairwise-distinct clause would VOID the run; found at the pre-freeze gate). 0021's clause"
FL_NEW = ("the reader's pairwise-distinct clause would VOID the run; found at the pre-freeze gate). B-majority predicts one constant class, the "
          "majority label of its rung, which is the same label at rungs 7 and 8, so its two fits bank the same vector honestly: the reader "
          "accepts exactly that pair and no other shared vector (found by the pre-freeze instrument review on the runner's smoke). 0021's clause")
replace_once(lambda: S['design']['floors'], lambda v: S['design'].__setitem__('floors', v), FL_OLD, FL_NEW, "scope.design.floors",
             "the majority-floor pair (review, runner and reader lenses, blocking)")

# 5. the new shift arm is 0025's corpus, not the new files alone
S8_OLD = "the new shift arm reads the new files alone at 0021's count"
S8_NEW = ("the new shift arm reads rung 8's plaintexts from 0025's corpus alone at 0021's count (the new files and 0024's archives' unused "
          "chunks; the composition per family is banked)")
for i, txt in enumerate(S['rival_explanations_run_as_arms']):
    if S8_OLD in txt or S8_NEW in txt:
        replace_once(lambda i=i: S['rival_explanations_run_as_arms'][i], lambda v, i=i: S['rival_explanations_run_as_arms'].__setitem__(i, v),
                     S8_OLD, S8_NEW, f"scope.rival_explanations_run_as_arms[{i}]", "s8 is not the new files alone (review, runner lens, minor)")

# 6. the interpreter the sealed environment names
INTERP = ("a Python 3.11.15 interpreter with numpy 2.4.6 and scikit-learn 1.9.0 - scope.curve.protocol.environment, which the runner banks "
          "and the reader VOIDs on any other; the corpora are built with the interpreter whose zlib is 1.3, as the corpus manifests record")
if pr['invocation'].get('interpreter') != INTERP:
    pr['invocation']['interpreter'] = INTERP
    changes.append({"where": "invocation.interpreter", "why": "the container that runs this is not the one that wrote it (2026-10-21); the sealed environment names the interpreter"})

# ---- the sealed hashes, recomputed over the amended objects
S['sealed_hashes']['protocol_sha256'] = sha(P)
S['sealed_hashes']['curve_sha256'] = sha(S['curve'])

# ---- nothing else moved: compare everything outside the edited fields
def strip(d):
    d = copy.deepcopy(d); s = d['scope']
    s['curve']['protocol']['launch'].pop('min_mem_available_gb'); s['cost'].pop('memory')
    s['rival_explanations_run_as_arms'] = [t.replace(NR_NEW, NR_OLD).replace(S8_NEW, S8_OLD) for t in s['rival_explanations_run_as_arms']]
    d['bar']['reproduces_0021_0023_and_0024']['passes_if'] = d['bar']['reproduces_0021_0023_and_0024']['passes_if'].replace(NR_NEW, NR_OLD)
    d['stop_rules'] = [t.replace(STOP_NEW, STOP_OLD) for t in d['stop_rules']]
    s['design']['floors'] = s['design']['floors'].replace(FL_NEW, FL_OLD)
    s.pop('sealed_hashes'); d['invocation'].pop('interpreter', None); d.pop('amendments_before_freeze', None)
    return d
assert strip(pr) == strip(before), 'an edit touched something outside its field'

if changes:
    pr.setdefault('amendments_before_freeze', []).append({
        "date": "2026-10-21", "by": "tools: scratchpad amend_prereg_0025.py (the generator was lost with the old container; the committed file was its last output)",
        "source": "artifacts/pivot/engineering_log_0025.json pre_freeze_instrument_review", "changes": changes})
    with open(PATH, 'w', encoding='utf-8') as fh:
        json.dump(pr, fh, indent=2, ensure_ascii=False); fh.write('\n')
print(f"{len(changes)} change(s); peak {PEAK8} GB; protocol {S['sealed_hashes']['protocol_sha256'][:12]} curve {S['sealed_hashes']['curve_sha256'][:12]}")
for c in changes:
    print(' -', c['where'])
