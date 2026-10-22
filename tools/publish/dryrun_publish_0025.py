#!/usr/bin/env python3
"""Dry run of publish_0025.py: every one of the twelve 0025 verdict strings (plus two iteration-cap variants and a VOID), each
published into its own temporary copy of the repository's text files, then checked.

Nothing is written under the real repository. The copies live in $RAISE_SCRATCH/dryrun0025/. Every artifact set is built by
the realcurve3 gate's own control machinery (tests/mutation_test.py's _good_realcurve3, imported FROM THE COPY so its REPO is
the copy), and every verdict file is the real frozen reader's output, run inside the copy. If the real preregistration is not
frozen yet, the freeze is simulated in the copy with tools/prereg.py's own cmd_freeze (network anchors and git stubbed). If the
real VERDICT.md / README.md carry no 0025 in-flight paragraph yet, stand-ins are put in every other copy, laced with every
anchor phrase, so the publication must cut them before it points. The run artifact's cost block, which the control leaves empty,
is filled with synthetic seconds in the copy only.

Checks per case: the reader reads the expected string; publish exits 0 and only the expected files change; every forward-pointer
site (and every bound the outcome calls for) is touched exactly once and nothing else is; a second run changes no byte; no
NOT_RESOLVED (or anything) is read as flat or equal outside the sealed 'never read as' words; the gain part is never in a
sentence without the lead part; the two-decade slope only beside the fourth-doubling reading with the seven-of-eight sentence;
the cap notes in the same sentence when a cap is set; every document unit carries the eight readings per role, the per-role
gains with intervals, the two-decade slope, the floors, both shift arms, the lead and the per-family composition; the coverage
claims resolve; coverage.py, claimcheck.py and freshness.py pass after as they did before. The VOID case must be refused with
nothing written. Usage: python3 dryrun_publish_0025.py [CASE_SUBSTRING ...]
"""
import hashlib
import json
import os
import re
import resource
import shutil
import subprocess
import sys
import time

SP = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(os.environ['RAISE_SCRATCH'], 'dryrun0025')   # copies live outside the repository (RAISE_SCRATCH required)
PUB = os.path.join(SP, 'publish_0025.py')
PY = sys.executable
GATE_SCORES = 'artifacts/pivot/realcurve2_4096_scores.json'      # 0024's banked vectors: the gate's controls need them (base copy only)
GAINS = ['RISES', 'BELOW_RATE', 'NOT_RESOLVED', 'FALLS']
LEADS = ['MODEL_LEADS', 'LINEAR_LEADS', 'NO_SEPARATION']
MAIN = [f'FOURTH_DOUBLING_{g}_{l}' for g in GAINS for l in LEADS]
EXTRA = ['CAP8:FOURTH_DOUBLING_NOT_RESOLVED_LINEAR_LEADS', 'CAP7:FOURTH_DOUBLING_BELOW_RATE_NO_SEPARATION']
VOID = 'VOID'
EXPECTED_CHANGED = {'VERDICT.md', 'README.md', 'outbound/ONE_PAGER.md', 'outbound/EVIDENCE_BRIEF.md', 'outbound/NARRATIVE.md',
                    'docs/DILIGENCE.md', 'tools/render/evidence_page.py', 'outbound/evidence_page.html',
                    'artifacts/verification/coverage.json', 'artifacts/pivot/engineering_log_0025.json'}


def run(cmd, cwd, env=None, timeout=1200):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', **(env or {})))
    return p.returncode, p.stdout + p.stderr


# ---------------------------------------------------------------- the generator (a child process per case keeps memory bounded)
def spec_for(case, mt):
    R7m, R7l = mt._RC3_R7['model'], mt._RC3_R7['logistic']; ACC = mt._RC3_ACC
    table = {   # the gate's own controls for each string (tests/mutation_test.py, realcurve3_4096 gate)
        'FOURTH_DOUBLING_RISES_MODEL_LEADS': {},
        'FOURTH_DOUBLING_RISES_LINEAR_LEADS': {'acc': {'r8_logistic': 0.1565}},
        'FOURTH_DOUBLING_RISES_NO_SEPARATION': {'acc': {'r8_logistic': ACC['r8_model']}},
        'FOURTH_DOUBLING_BELOW_RATE_MODEL_LEADS': {'acc': {'r8_model': R7m + 0.003, 'r8_logistic': 0.134}},
        'FOURTH_DOUBLING_BELOW_RATE_LINEAR_LEADS': {'acc': {'r8_model': R7m + 0.003, 'r8_logistic': 0.1565}},
        'FOURTH_DOUBLING_BELOW_RATE_NO_SEPARATION': {'acc': {'r8_model': R7m + 0.003, 'r8_logistic': R7m + 0.003}},
        'FOURTH_DOUBLING_NOT_RESOLVED_MODEL_LEADS': {'acc': {'r8_model': R7m + 0.002, 'r8_logistic': 0.133}, 'gain_mode': 'mixed'},
        'FOURTH_DOUBLING_NOT_RESOLVED_LINEAR_LEADS': {'acc': {'r8_model': R7m + 0.002, 'r8_logistic': 0.1565}, 'gain_mode': 'mixed'},
        'FOURTH_DOUBLING_NOT_RESOLVED_NO_SEPARATION': {'acc': {'r8_model': R7m + 0.002, 'r8_logistic': R7m + 0.002}, 'gain_mode': 'mixed'},
        'FOURTH_DOUBLING_FALLS_MODEL_LEADS': {'acc': {'r8_model': R7m - 0.01, 'r8_logistic': R7l - 0.014}},
        'FOURTH_DOUBLING_FALLS_LINEAR_LEADS': {'acc': {'r8_model': R7m - 0.01, 'r8_logistic': 0.1405}},
        'FOURTH_DOUBLING_FALLS_NO_SEPARATION': {'acc': {'r8_model': R7m - 0.01, 'r8_logistic': R7m - 0.01}},
        VOID: {'perturb': {'r7_model': 31}},
    }
    caps = {'CAP8': ['r8_model', 'r8_logistic'], 'CAP7': ['r7_model']}.get(case.split(':')[0], []) if ':' in case else []
    return table[case.split(':')[-1]], caps


def gen(case, base, out):
    sys.dont_write_bytecode = True
    import importlib.util
    spec = importlib.util.spec_from_file_location('mutation_test', os.path.join(base, 'tests', 'mutation_test.py'))
    mt = importlib.util.module_from_spec(spec); sys.modules['mutation_test'] = mt; spec.loader.exec_module(mt)
    assert os.path.realpath(mt.REPO) == os.path.realpath(base), 'the gate module must read the copy, not the repository'
    kw, caps = spec_for(case, mt)
    art, scores = mt._good_realcurve3(**kw)
    r25 = mt._rc3_reader()
    for name in caps:     # the gate's own cap controls: an iteration count at the role's sealed cap
        art['fits'][name]['fit_info'] = dict(art['fits'][name]['fit_info'], n_iter=r25.MAX_ITER[name.split('_', 1)[1]])
        art['fit_info_by_name'][name] = art['fits'][name]['fit_info']
    names = list(art['fits']); secs = {n: round(10.0 + 3 * i, 1) for i, n in enumerate(names)}
    art['cost'] = {'wall_seconds_this_invocation': round(sum(secs.values()) + 321.0, 1), 'seconds_by_name': secs,
                   'interruptions_by_name': {n: 0 for n in names}, 'banked_fit_seconds_total': round(sum(secs.values()), 1),
                   'checkpoints': 'artifacts/pivot/realcurve3_4096_ckpt'}       # synthetic: the control banks none (dry run only)
    piv = os.path.join(out, 'artifacts', 'pivot'); os.makedirs(piv, exist_ok=True)
    with open(os.path.join(piv, 'realcurve3_4096_scores.json'), 'w') as fh:
        json.dump(scores, fh)
    with open(os.path.join(piv, 'realcurve3_4096.json'), 'w') as fh:
        json.dump(art, fh)
    print(f'generated {case} into {out}')


# ---------------------------------------------------------------- the copies
def snapshot_repo(dest):
    files = subprocess.run(['git', 'ls-files'], cwd=REPO, capture_output=True, text=True).stdout.split('\n')
    files += subprocess.run(['git', 'ls-files', '-o', '--exclude-standard'], cwd=REPO, capture_output=True, text=True).stdout.split('\n')
    n = 0
    for f in sorted(set(files)):
        if not f or f.startswith('.claude/') or '_ckpt/' in f or f.startswith('data/') or '__pycache__' in f or f.endswith('.pyc'):
            continue
        src = os.path.join(REPO, f)
        if not os.path.isfile(src) or (os.path.getsize(src) > 3_000_000 and f != GATE_SCORES):
            continue
        d = os.path.join(dest, f); os.makedirs(os.path.dirname(d), exist_ok=True); shutil.copy2(src, d); n += 1
    return n


def files_of(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f); rel = os.path.relpath(p, root)
            if rel.endswith('realcurve3_4096_scores.json') or '__pycache__' in rel:
                continue
            with open(p, 'rb') as fh:
                out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def T(root, rel):
    with open(os.path.join(root, rel), encoding='utf-8') as fh:
        return fh.read()


def W(root, rel, text):
    assert os.path.realpath(root).startswith(os.path.realpath(WORK) + os.sep), 'refusing to write outside the dry-run directory'
    with open(os.path.join(root, rel), 'w', encoding='utf-8') as fh:
        fh.write(text)


def simulate_freeze(base):
    pr = json.load(open(os.path.join(base, 'prereg', '0025-realcurve3-4096.json')))
    if pr.get('frozen'):
        return 'the real preregistration is already frozen'
    code = ("import sys; sys.path.insert(0, 'tools'); import prereg\n"
            "prereg.fetch_anchors = lambda: {'dry_run': 'no network: anchors stubbed by the dry run'}\n"
            "prereg.git_head = lambda root: 'dryrun'; prereg.git_dirty = lambda root: False\n"
            "class Args: path = 'prereg/0025-realcurve3-4096.json'\n"
            "sys.exit(prereg.cmd_freeze(Args))\n")
    rc, out = run([PY, '-B', '-c', code], base)
    assert rc == 0, out
    return 'simulated in the copy: ' + out.strip()


def add_inflight(root):
    """stand-ins for the freeze's in-flight paragraphs, laced with every anchor phrase the publication points at"""
    v = T(root, 'VERDICT.md'); r = T(root, 'README.md')
    head24 = '**Preregistration 0024 (chain seq 24) —'
    lace = ("both together span 1.8016 decades, short of 0003's two-decade scope rule; other files of the same kinds keep buying the "
            "recipe the record's rate on the files it is scored on, through 8232 plaintexts (eight times 0021's); other files of the same "
            "kinds keep raising the recipe's accuracy on the files it is scored on at or above the record's bar of 0.005 per doubling (the "
            "bar 0024 sealed; 0.00697 measured; second decade minus first: -0.000374), through 8232 plaintexts (eight times 0021's); this "
            "does not establish the record's scaling thesis, which 0003's scope rule ties to two decades of data on one corpus with one seed "
            "(this curve spans 0.8985 of a decade); the record's scaling thesis holds on these real files, in distribution, over just under "
            "a decade (0003's scope rule asks for two); at the top rung the boosted model "
            "leads the standardised logistic, by 0.0039; the boosted model edges ahead of the standardised linear rule; the standardised "
            "logistic 0.0039 behind the model at 0024's top rung; the model leads the standardised logistic by 0.0039 (paired interval "
            "[0.0001, 0.0077], entirely above 0) — `MODEL_LEADS` by the rule sealed in advance")
    st_v = (f"**In flight — preregistration 0025 (chain seq 25, frozen 2026-10-21T00:00:00Z).** Dry-run stand-in for the freeze's paragraph: "
            f"{lace}.\n\nIts second paragraph: it is frozen and running.\n\n")
    if '**In flight — preregistration 0025 ' not in v:
        i = v.index(head24); W(root, 'VERDICT.md', v[:i] + st_v + v[i:])
    a2 = 'The curve and the searched margin stand as measured'
    st_r = f"Preregistration 0025 (chain entry 25, frozen 2026-10-21) asks the fourth doubling; dry-run stand-in: {lace}. It is frozen and running.\n\n"
    if 'Preregistration 0025 (chain entry' not in r:
        i = r.index(a2); W(root, 'README.md', r[:i] + st_r + r[i:])


# ---------------------------------------------------------------- the checks
def norm(t):
    return re.sub(r'\n[ ]*(?:> ?)?', ' ', t)


def brackets(t, starts=("[with 0025's", '[bounded by 0025')):
    out, i = [], 0
    while True:
        js = [t.find(s, i) for s in starts]; js = [j for j in js if j >= 0]
        if not js:
            return out
        j = min(js); depth = 0
        for k in range(j, len(t)):
            depth += {'[': 1, ']': -1}.get(t[k], 0)
            if depth == 0:
                break
        out.append(t[j:k + 1]); i = k + 1


def sentences(t):
    return [s for s in re.split(r'(?<=\.)\s+(?=[A-Z`*\[(|])', norm(t)) if s.strip()]


GAIN_MARKERS = ['FOURTH_DOUBLING_', 'minus rung 7 for the model', 'fourth doubling bought', 'fourth doubling of real plaintexts', "a rise below the record's rate",
                "lowered the model's reading", 'fourth-doubling gain', 'fourth-doubling reading', "raises the recipe's accuracy"]
LEAD_MARKERS = ['MODEL_LEADS', 'LINEAR_LEADS', 'NO_SEPARATION', 'model minus logistic', 'linear rule', 'standardised logistic leads', 'leads the standardised logistic',
                'a rule a person can write out', 'the standardised logistic (a ']


def check_case(case, root, orig, before, after1, after2, out1, V, PR, problems):
    verdict = V['verdict']; gain = V['gain_reading']; lead = V['lead_reading']; F = V['flags']
    P = lambda m: problems.append(f'{case}: {m}')  # noqa: E731
    # the files that changed, and idempotency
    changed = {f for f in set(before) | set(after1) if before.get(f) != after1.get(f)}
    if changed != EXPECTED_CHANGED:
        P(f'changed files {sorted(changed ^ EXPECTED_CHANGED)} differ from the expected set')
    if after1 != after2:
        P(f'not idempotent: a second run changed {sorted(f for f in after1 if after1[f] != after2.get(f))}')
    if 'WARNING' in out1:
        P('the publication printed a warning: ' + out1[out1.index('WARNING'):][:300])
    E24 = json.load(open(os.path.join(root, 'artifacts/pivot/engineering_log_0024.json')))
    dec24 = E24['freeze']['sealed_span']['decades_spanned']
    m = re.search(r"receives, in every place it stands, the pointer '(.*?)'; on ", ' '.join(PR['stop_rules'])); PTR = m.group(1)
    p7 = V['bar_applied']['rungs'][-2]['n_chunks']; p8 = V['bar_applied']['rungs'][-1]['n_chunks']
    # the stop rules' publication documents; every other page (docs/strategy/*, a plan or a changelog) must be left as it is,
    # which the changed-file set checks
    md = sorted(f for f in after1 if f in ('VERDICT.md', 'README.md', 'docs/DILIGENCE.md') or (f.startswith('outbound/') and f.endswith('.md')))
    span_phr = [f"{dec24} decades, short of 0003's two-decade scope rule", f"{dec24} decades, short of our own two-decade scope rule"]
    # the stop rules' sites in the documents' wording after the 2026-10-22 honesty pass, each phrase ending where its bound goes. The
    # keep and thesis sentences are bounded only in the documents their stop rule names; a reworded copy elsewhere is left alone.
    keep_phr = {'README.md': [f"keep buying the recipe the record's rate on the files it is scored on, through {p7} plaintexts (eight times 0021's)"],
                'VERDICT.md': [f"keep raising the recipe's accuracy on the files it is scored on at or above the record's bar of 0.005 per doubling "
                               f"(the bar 0024 sealed; 0.00697 measured; second decade minus first: -0.000374), through {p7} plaintexts (eight times 0021's)"]}
    th_new = ("this does not establish the record's scaling thesis, which 0003's scope rule ties to two decades of data on one corpus with one "
              "seed (this curve spans 0.8985 of a decade)")
    thesis_phr = {'VERDICT.md': [th_new], 'docs/DILIGENCE.md': [th_new]}
    lead_phr = ["at the top rung the boosted model leads the standardised logistic by 0.0039", "at the top rung the boosted model leads the standardised logistic, by 0.0039",
                "At the top rung the boosted model leads the standardised logistic, by 0.0039", "at the top rung the boosted model leads the linear rule, by 0.0039",
                "at the top rung the boosted model edges ahead of the standardised linear rule",
                "the boosted recipe leads the standardised logistic (26 classes over 1108 features) on the record's own real content by 0.0039",
                "the boosted recipe leads the standardised logistic on the record's own real content by 0.0039",
                "the boosted recipe leads the standardised logistic — a 26-class linear model over 1108 features, not a rule anyone writes out by hand — by 0.0039",
                "the standardised logistic 0.0039 behind the model at 0024's top rung"]
    SITES = {'keep': {'VERDICT.md': 1, 'README.md': 1}, 'thesis': {'VERDICT.md': 1, 'docs/DILIGENCE.md': 1},   # counted by hand on 2026-10-22
             'lead': {'VERDICT.md': 7, 'README.md': 3, 'outbound/ONE_PAGER.md': 3, 'outbound/EVIDENCE_BRIEF.md': 5, 'outbound/NARRATIVE.md': 2, 'docs/DILIGENCE.md': 3}}
    KEEP_P = f" [bounded by 0025 to {p7} plaintexts: at rung 8 ({p8} plaintexts) 0025 read `{verdict}`"
    THESIS_P = ' [bounded by 0025: at rung 8'
    LEAD_P = f' [bounded by 0025 to {p7} plaintexts: model minus logistic at rung 8 ({p8} plaintexts)'
    bounded = gain.split('FOURTH_DOUBLING_')[1] in ('BELOW_RATE', 'NOT_RESOLVED', 'FALLS')
    totals = {'span': 0, 'keep': 0, 'thesis': 0, 'lead': 0}
    for f in md:
        o = norm(orig.get(f, '')); t = norm(T(root, f))
        for ph in span_phr:
            k = o.count(ph); totals['span'] += k
            if t.count(ph) != k or t.count(ph + f' [{PTR}]') != k:
                P(f'{f}: {k} sites of {ph!r}, {t.count(ph + f" [{PTR}]")} carry the pointer, {t.count(ph)} stand')
        if t.count(f'[{PTR}]') != sum(o.count(ph) for ph in span_phr):
            P(f'{f}: the pointer stands {t.count(f"[{PTR}]")} times')
        k = sum(o.count(ph) for ph in keep_phr.get(f, [])); totals['keep'] += k
        if k != SITES['keep'].get(f, 0):
            P(f'{f}: {k} keep sites in the wording counted on 2026-10-22, not {SITES["keep"].get(f, 0)}')
        got = sum(t.count(ph + KEEP_P) for ph in keep_phr.get(f, []))
        if got != (k if bounded else 0) or t.count(KEEP_P) != (k if bounded else 0):
            P(f'{f}: keep sites {k}, bounded {got} of {t.count(KEEP_P)} keep bounds ({"bound expected" if bounded else "no bound expected"})')
        k = sum(o.count(ph) for ph in thesis_phr.get(f, [])); totals['thesis'] += k; falls = gain.endswith('FALLS')
        if k != SITES['thesis'].get(f, 0):
            P(f'{f}: {k} thesis sites in the wording counted on 2026-10-22, not {SITES["thesis"].get(f, 0)}')
        got = sum(t.count(ph + THESIS_P) for ph in thesis_phr.get(f, []))
        if got != (k if falls else 0) or t.count(THESIS_P) != (k if falls else 0):
            P(f'{f}: thesis sites {k}, pointed {got} of {t.count(THESIS_P)} thesis pointers')
        lk = sum(o.count(ph) for ph in lead_phr)
        lk_tok = 0
        for mm in re.finditer(r'`MODEL_LEADS`', o):     # 0024's reading: its top-rung interval stands just before the token
            if 'likely' in o[max(0, mm.start() - 24):mm.start()] or '[0.0001, 0.0077]' not in o[max(0, mm.start() - 200):mm.start()]:
                continue
            lk_tok += 1
        lk += lk_tok; totals['lead'] += lk
        if lk != SITES['lead'].get(f, 0):
            P(f'{f}: {lk} statements of 0024\'s MODEL_LEADS in the wording counted on 2026-10-22, not {SITES["lead"].get(f, 0)}')
        want = lk if lead != 'MODEL_LEADS' else 0
        got_after_anchor = sum(t.count(ph + LEAD_P) for ph in lead_phr) + t.count('`MODEL_LEADS`' + LEAD_P) + t.count('`MODEL_LEADS` by the rule sealed in advance' + LEAD_P)
        if t.count(LEAD_P) != want or got_after_anchor != want:
            P(f'{f}: MODEL_LEADS sites {lk}, bounded {t.count(LEAD_P)} (directly after an anchor {got_after_anchor}), want {want}')
        if re.search(r"\] \[(?:with 0025's|bounded by 0025)", t):
            P(f'{f}: two 0025 pointers stand side by side')
    if totals['span'] != 8:
        P(f"the sealed span sentence stands {totals['span']} times in the Markdown copy, not the 8 counted when this was written (the page is the 9th)")
    for key in ('keep', 'thesis', 'lead'):
        if totals[key] != sum(SITES[key].values()):
            P(f"{totals[key]} {key} sites in the Markdown copy, not the {sum(SITES[key].values())} counted on 2026-10-22")
    # the evidence page, source and rendered
    e = T(root, 'tools/render/evidence_page.py'); h = T(root, 'outbound/evidence_page.html')
    if e.count("+ _rc3_span +") != 1 or e.count('+ _rc3_lead_bound') != 1:
        P('evidence_page.py: the pointer or the lead bound is not wired exactly once')
    hp = sum(h.count(PTR.replace("'", q)) for q in ("'", '&#x27;', '&#39;'))
    if hp != 1:
        P(f'evidence_page.html: the pointer stands {hp} times')
    if h.count('[bounded by 0025 to') != (1 if lead != 'MODEL_LEADS' else 0):
        P(f"evidence_page.html: the lead bound stands {h.count('[bounded by 0025 to')} times")
    # the 0025 units
    v = T(root, 'VERDICT.md'); r = T(root, 'README.md'); o = T(root, 'outbound/ONE_PAGER.md'); b = T(root, 'outbound/EVIDENCE_BRIEF.md')
    n = T(root, 'outbound/NARRATIVE.md'); d = T(root, 'docs/DILIGENCE.md')
    line = lambda t, mk: [l for l in t.split('\n') if mk in l]  # noqa: E731
    units = {}
    try:
        units['VERDICT block'] = v[v.index('**Preregistration 0025 (chain seq'):v.index('**Preregistration 0024 (chain seq 24)')]
        units['VERDICT row'] = line(v, '| **Fourth doubling of real plaintexts at 4096 (0025)** |')[0]
        units['README'] = r[r.index('Preregistration 0025 (chain entry'):r.index('The curve and the searched margin stand as measured')]
        units['ONE_PAGER'] = line(o, 'Preregistration 0025 added one doubling')[0]
        units['BRIEF paragraph'] = line(b, 'Preregistration 0025 built and sealed a third fit corpus')[0]
        units['BRIEF bullet'] = line(b, '- **Fourth doubling of real plaintexts at 4096:')[0]
        nn = norm(n); s_ = nn.index('Then we bought the doubling we were short of (0025)')
        units['NARRATIVE'] = nn[s_:nn.index('We do not extrapolate past rung 8.', s_) + 34]
        units['DILIGENCE'] = d[d.index('## "Does a fourth doubling of real files help?"'):d.index('## "Who buys it?"')]
    except (ValueError, IndexError) as ex:
        P(f'a 0025 unit is missing ({ex})'); return {}
    for k_, cnt in ((v, v.count('**Preregistration 0025 (chain seq')), (v, len(line(v, '(0025)** |'))), (o, len(line(o, 'Preregistration 0025 added'))),
                    (b, len(line(b, 'Preregistration 0025 built'))), (b, len(line(b, '- **Fourth doubling'))), (n, n.count('(0025):')), (d, d.count('fourth doubling of real files help')),
                    (r, r.count('Preregistration 0025 (chain entry'))):
        if cnt != 1:
            P(f'a 0025 unit stands {cnt} times')
    rowsec = v[:v.index('### Failed, or did not reach a conclusion')]
    if (units['VERDICT row'] in rowsec) != gain.endswith('RISES'):
        P('the VERDICT row is in the wrong table')
    by = {role: [p['ext_real_top1'] for p in V['curves'][role]['rungs']] for role in ('model', 'logistic', 'depth3_tree')}
    G = V['fourth_doubling']; LT = V['lead_at_top']['r8_model_minus_logistic']; TD = F['two_decade_slope_per_doubling']['model']
    must = [f'`{verdict}`', f'one doubling ({p8} against {p7} plaintexts)', 'new projects', "other chunks of 0024's projects", 'a mixture',
            'seven of its eight points were banked before this run', str(TD['slope_per_doubling']), str(TD['ci95']),
            str(V['floors']['r8']['needed_0021_clause']), str(F['shift_arm_0024']['readings_ext_real_top1']['model']),
            str(F['shift_arm_0025']['readings_ext_real_top1']['model']), str(abs(LT['point'])), str(LT['ci95'])]   # LINEAR_LEADS states the lead as a positive lead of the logistic
    must += [', '.join(map(str, by[role])) for role in by] + [f"{G[role]['point']}" for role in by] + [str(G[role]['ci95']) for role in by]
    words = {'BELOW_RATE': "a rise below the record's rate", 'NOT_RESOLVED': 'whether the fourth doubling bought anything is not resolved by the scored chunks at this size',
             'FALLS': "adding the fourth doubling's files of the same kinds lowered the model's reading on the original files", 'RISES': "the record's rate"}
    must.append(words[gain.split('FOURTH_DOUBLING_')[1]])
    for name, u in units.items():
        un = norm(u)
        miss = [x for x in must if x.lower() not in un.lower()]
        if miss:
            P(f'{name}: lacks {miss[:4]}')
    # every new sentence: units, pointers, coverage claims, the engineering log's run_record
    C = json.load(open(os.path.join(root, 'artifacts/verification/coverage.json')))
    E = json.load(open(os.path.join(root, 'artifacts/pivot/engineering_log_0025.json')))
    texts = list(units.values()) + [x for f in md for x in brackets(T(root, f))] + [c['claim'] for c in C['claims'] if c['id'].startswith('realcurve34096-')]
    texts += [x for x in E['run_record']['what_it_found'].values()]
    caps = F['roles_at_iteration_cap']
    gcaps = [f'(the model at its iteration cap at rung {k})' for k in (7, 8) if f'r{k}_model' in caps]
    lcaps = [f'(the {x[3:]} at its iteration cap at rung 8)' for x in F['roles_at_iteration_cap_at_the_top_rung']]
    for t in texts:
        tn = norm(t)
        for mm in re.finditer(r'flat', tn, re.I):
            if "never read as 'flat' or 'equal'" not in tn[max(0, mm.start() - 15):mm.end() + 15]:
                P(f"'flat' outside the sealed words: ...{tn[max(0, mm.start() - 80):mm.end() + 30]}...")
        for mm in re.finditer(r'equal', tn, re.I):
            ctx = tn[max(0, mm.start() - 26):mm.end() + 2]
            if "never read as 'equal'" not in ctx and "'flat' or 'equal'" not in ctx:
                P(f"'equal' outside the sealed words: ...{tn[max(0, mm.start() - 80):mm.end() + 30]}...")
        for s in sentences(t):
            g_ = any(x in s for x in GAIN_MARKERS); l_ = any(x in s for x in LEAD_MARKERS)
            if g_ and not l_:
                P(f'the gain part without the lead part: {s[:200]}')
            if 'two-decade slope' in s and not ('seven of its eight points were banked before this run' in s and g_):
                P(f'the two-decade slope outside the fourth-doubling sentence: {s[:200]}')
            if 'second-decade slope' in s and not g_:
                P(f'the second-decade slope outside the fourth-doubling sentence: {s[:200]}')
            if (verdict in s or 'minus rung 7 for the model' in s) and not all(c_ in s for c_ in gcaps):
                P(f'a gain read at the cap without its note: {s[:200]}')
            if (verdict in s or 'model minus logistic at rung 8' in s or 'at rung 8 the model leads' in s or 'at rung 8 the standardised logistic leads' in s
                    or 'at rung 8 model minus logistic' in s) and not all(c_ in s for c_ in lcaps):
                P(f'a lead read at the cap without its note: {s[:200]}')
    if gcaps or lcaps:
        if not any(all(c_ in norm(u) for c_ in gcaps + lcaps) for u in units.values()):
            P('the cap notes are missing from the units')
    # the claims and the counts
    ids = [c for c in C['claims'] if c['id'].startswith('realcurve34096-')]
    if len(ids) != 19 or C['n_claims'] != len(C['claims']):
        P(f'coverage: {len(ids)} 0025 claims, n_claims {C["n_claims"]} for {len(C["claims"])}')
    nn_ = sum(1 for c in C['claims'] if c['class'] == 'neither')
    if f"**{nn_} of {C['n_claims']} claims are in `neither`" not in v or f"**{nn_} of {C['n_claims']} claims are in the weakest class**" not in o \
            or f"{nn_} of {C['n_claims']} claims" not in norm(n):
        P('a claim-count sentence is stale')
    if E.get('status') != f'complete: {verdict}' or 'run_record' not in E:
        P('the engineering log carries no run_record or a stale status')
    for f in md:
        if re.search(r'In flight — preregistration 0025|0025 \(chain (?:seq|entry) \d+, frozen', T(root, f)):
            P(f'{f}: in-flight text for 0025 remains')
    return {k: len(norm(u)) for k, u in units.items()}


GATES = [('coverage', ['tools/coverage.py']), ('claimcheck', ['tools/claimcheck.py', 'outbound', 'VERDICT.md']), ('freshness', ['tools/freshness.py'])]


def gates(root):
    return {name: run([PY, '-B'] + cmd, root, timeout=600) for name, cmd in GATES}


def main(argv):
    if len(argv) >= 4 and argv[0] == '--gen':
        gen(argv[1], argv[2], argv[3]); return 0
    sel = argv
    t0 = time.time()
    if os.path.exists(WORK):
        shutil.rmtree(WORK)
    base = os.path.join(WORK, 'base'); n_files = snapshot_repo(base)
    frz = simulate_freeze(base)
    PR = json.load(open(os.path.join(base, 'prereg', '0025-realcurve3-4096.json')))
    print(f'base copy: {n_files} files; freeze: {frz}', flush=True)
    cases = [c for c in MAIN + EXTRA + [VOID] if not sel or any(s in c for s in sel)]
    problems, sizes, summary = [], {}, []
    for i, case in enumerate(cases):
        root = os.path.join(WORK, f'c{i:02d}')
        shutil.copytree(base, root, ignore=lambda dpath, names: [x for x in names if os.path.join(os.path.relpath(dpath, base), x).lstrip('./') == GATE_SCORES])
        orig = {f: T(root, f) for f in files_of(root) if f.endswith('.md')}
        if i % 2 == 0:
            add_inflight(root)
        rc, out = run([PY, '-B', os.path.abspath(__file__), '--gen', case, base, root], SP)
        if rc != 0:
            problems.append(f'{case}: generation failed: {out[-1500:]}'); continue
        rc, out = run([PY, '-B', 'tools/readers/realcurve3_4096_verdict.py'], root)
        os.remove(os.path.join(root, 'artifacts', 'pivot', 'realcurve3_4096_scores.json'))
        V = json.load(open(os.path.join(root, 'artifacts', 'pivot', 'realcurve3_4096_verdict.json')))
        want = case.split(':')[-1]
        if case == VOID:
            if V['verdict'] != 'VOID':
                problems.append(f'VOID case read {V["verdict"]}'); continue
            before = files_of(root)
            rc, out = run([PY, '-B', PUB], root, env={'PUBLISH_0025_ROOT': root, 'PUBLISH_0025_DRYRUN': '1'})
            ok = rc == 2 and 'REFUSED' in out and files_of(root) == before
            summary.append((case, V['verdict'], 'refused, nothing written' if ok else f'NOT REFUSED rc={rc}'))
            if not ok:
                problems.append(f'VOID: the publication did not refuse cleanly (rc={rc}): {out[-600:]}')
            continue
        if V['verdict'] != want:
            problems.append(f'{case}: the reader read {V["verdict"]} ({V["validity_failed_clauses"][:3]})'); continue
        g0 = gates(root); before = files_of(root)
        env = {'PUBLISH_0025_ROOT': root, 'PUBLISH_0025_DRYRUN': '1'}
        rc1, out1 = run([PY, '-B', PUB], root, env=env); after1 = files_of(root)
        if rc1 != 0:
            problems.append(f'{case}: publish failed rc={rc1}: {out1[-2500:]}'); summary.append((case, V['verdict'], 'PUBLISH FAILED')); continue
        rc2, out2 = run([PY, '-B', PUB], root, env=env); after2 = files_of(root)
        if rc2 != 0:
            problems.append(f'{case}: the second publish failed rc={rc2}: {out2[-1500:]}')
        n0 = len(problems)
        sz = check_case(case, root, orig, before, after1, after2, out1, V, PR, problems)
        if case in MAIN:          # the same size is asked of the twelve strings; a cap variant adds its notes on purpose
            sizes[case] = sz
        g1 = gates(root)
        for name in g0:
            if g1[name][0] != 0 and g0[name][0] == 0:
                problems.append(f'{case}: {name} passed before the publication and fails after: {g1[name][1][-800:]}')
        summary.append((case, V['verdict'], 'PASS' if len(problems) == n0 else f'{len(problems) - n0} problem(s)'))
        print(f'[{time.time() - t0:6.0f}s] {case}: {summary[-1][2]}', flush=True)
    # the same size: each unit's length across the twelve strings
    if len(sizes) > 1:
        print('\nunit lengths (characters, normalised) across the cases: min / max / ratio')
        for unit in next(iter(sizes.values())):
            ls = [s[unit] for s in sizes.values() if unit in s]
            ratio = max(ls) / min(ls)
            print(f'  {unit:<16} {min(ls):>6} / {max(ls):>6} / {ratio:.3f}')
            if ratio > 1.15:
                problems.append(f'{unit}: not published at the same size across outcomes (ratio {ratio:.3f})')
    print('\nSUMMARY')
    for c, vv, s in summary:
        print(f'  {c:<52} {vv:<44} {s}')
    peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6
    print(f'\npeak child RSS {peak:.2f} GB; {time.time() - t0:.0f} s')
    if problems:
        print(f'\n{len(problems)} PROBLEM(S):')
        for p in problems:
            print('  -', p[:1200])
        return 1
    print('\nDRY RUN: ALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
