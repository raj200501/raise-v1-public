#!/usr/bin/env python3
"""In-flight paragraphs for 0025, generated from the sealed file after the freeze (0021's to 0024's precedent: never a typed
threshold). Idempotent: replaces an earlier insertion."""
import json
R = '/home/user/raise-v1'
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json')); S = pr['scope']; P = S['curve']['protocol']; sp = S['sealed_partition']
assert pr.get('frozen') is True, 'run this after the freeze'
chain = [json.loads(l) for l in open(f'{R}/prereg/chain.jsonl') if l.strip()]
e = [x for x in chain if x['id'] == '0025'][0]; seq = e['seq']; frozen = pr['frozen_utc']
rg = sp['rungs']; bar = P['bar']['gain_per_doubling']; nb = P['bootstrap']['n_boot']; f3 = S['corpus_fit3']; rgs = S['rungs']
tol = P['reproduction_tolerance']; tol7 = P['reproduction_tolerance_rung7']; n_real = P['n_ext_real_rows']
ref7 = {r: P['reference_0024'][r][-1] for r in ('model', 'logistic', 'depth3_tree')}
rung_line = ", ".join(f"{r['n_chunks']}" for r in rg); rows_line = ", ".join(f"{r['n_rows']}" for r in rg)
top = rg[-1]; r7 = rg[-2]; s8 = sp['shift_arm_0025']; comp = rgs['fourth_doubling_composition_per_family']
assert pr['bar']['fourth_doubling']['threshold'] == bar and P['bootstrap']['seed'] == P['seed2']
n_new_archives = P['fit3_corpus_described']['n_new_archives']; n_rfc = P['fit3_corpus_described']['n_new_rfc_files']
EXPECTED = ("RISES if the fourth doubling's gain resembles 0024's last two second-decade gains, BELOW_RATE if it resembles the first; on the lead, "
            "NO_SEPARATION at least as likely as MODEL_LEADS")
para = (
 f"**In flight — preregistration 0025 (chain seq {seq}, frozen {frozen}).** Two decades of real plaintexts. 0024 stopped at "
 f"{sp['doublings_spanned_0024']} doublings ({sp['decades_spanned_0024']} decades), short of 0003's two-decade scope rule; this run adds ONE more exact per-family "
 f"doubling of other files of the same five families, nested on 0024's seven rungs, so the real-content curve spans {rgs['doublings_spanned']} "
 f"doublings ({rgs['decades_spanned']} decades, {rung_line} plaintexts; {rows_line} rows). A third fit corpus was built before the freeze from "
 f"{n_new_archives} new pinned PyPI archives and {n_rfc} new RFC texts plus the unused candidates of 0024's own archives (licences in "
 f"`docs/compliance/EXT_SOURCES3.md`): {f3['n_new_rows']} new rows, {f3['n_new_chunks_with_rows']} new plaintexts with rows, every chunk hashed "
 f"against every whole chunk and every kilobyte run of the 0018 files and, for the new files, against every kilobyte run of 0024's own files. "
 f"Per family the fourth doubling is what it can be: new projects and RFCs for py_src and rfc_txt, other chunks of 0024's projects for c_src and "
 f"pe_bin, a mixture for rst_doc (the composition is sealed and banked). 0021's three fixed recipes (M4, L3, D1) are fitted once per rung and scored "
 f"once on the same {n_real} real-family rows; three of 0021's four trivial-baseline floors are refitted at rungs 7 and 8 (B-tree3 being D1 itself); "
 f"0024's shift arm is reproduced and a second one — rung 8's plaintexts from the new corpus alone at rung 4's count, {s8['n_chunks']} plaintexts — "
 f"is fitted last, informational. The null control runs first on the top rung (labels permuted by a sealed stream, hash sealed). Rung 7 is refitted "
 f"first and its three roles must land within {tol7} of 0024's banked {ref7['model']}, {ref7['logistic']} and {ref7['depth3_tree']}; rungs 1..6 and "
 f"0024's shift arm within {tol}; and 0024's slope and lead intervals must recompute EXACTLY from this run's vectors under 0024's bootstrap seed — all "
 f"before any new plaintext is fitted.\n"
 f"\n"
 f"No slope is a clause: seven of the eight points were banked by 0023 and 0024 before this run, so an eight-rung slope could not fail on any "
 f"rung-8 reading short of a collapse. The verdict's curve part is read on the FOURTH DOUBLING alone by `tools/readers/realcurve3_4096_verdict.py` "
 f"on the recounted score vectors: rung 8 minus rung 7 for the model on the real-family rows, with a paired cluster-bootstrap interval over the "
 f"scored real chunks ({nb} resamples, 0024's seed, the same resample serving both rungs). Entirely below 0 is `FOURTH_DOUBLING_FALLS`; a gain of "
 f"at least **{bar}** (0023's and 0024's rate restated as a one-doubling gain) with the interval entirely above 0 is `FOURTH_DOUBLING_RISES`; "
 f"entirely above 0 but short of {bar} is `FOURTH_DOUBLING_BELOW_RATE`; an interval that includes 0 is `FOURTH_DOUBLING_NOT_RESOLVED`, never "
 f"'flat'. The verdict string carries a second part from 0024's sealed lead rule at rung 8 — model minus logistic, paired interval entirely above 0 "
 f"`MODEL_LEADS`, entirely below 0 `LINEAR_LEADS`, otherwise `NO_SEPARATION` — and no document quotes one part without the other; a role at its "
 f"iteration cap at rung 8 or rung 7 is named beside the reading it touches. Twelve verdict strings, each published at the same size. The two-decade "
 f"slope, the second-decade slope over rungs 4..8, the per-family gains, the floors, both shift arms and a seed-stability count for the two verdict "
 f"intervals are flags, quoted only beside the fourth-doubling reading. The expected outcome, stated in the sealed file: "
 f"{EXPECTED}.\n"
 f"\n"
 f"Not a transfer reading: every rung holds the scored files' own unscored chunks and the added plaintexts are other files of the same kinds, so "
 f"the fourth doubling confounds more plaintexts with a further shift of source, which the new shift arm reads directly. One corpus, one seed, no "
 f"replicate of rung 8: the scored-chunk interval does not cover the fit-side variance of one doubling. The span meets 0003's two-decade rule only in "
 f"the sense that the rule asked for two decades of data; its one-corpus, one-seed terms are not met by this curve, whose first decade is the "
 f"scored files' own chunks. Nothing below this line changes until its frozen reader has read the completed run.\n")
v = open(f'{R}/VERDICT.md').read()
anchor = "**Preregistration 0024 (chain seq 24) — `SECOND_DECADE_RISES_MODEL_LEADS`, and what it found.**"
assert v.count(anchor) == 1
start = "**In flight — preregistration 0025 "
if start in v:
    v = v[:v.index(start)] + v[v.index(anchor):]
open(f'{R}/VERDICT.md', 'w').write(v.replace(anchor, para + "\n" + anchor, 1))
sent = (
 f"Preregistration 0025 (chain entry {seq}, frozen {frozen[:10]}) asks two decades: one more exact doubling of other files of the same five\n"
 f"families ({f3['n_new_chunks_with_rows']} new plaintexts with rows from {n_new_archives} new PyPI archives, {n_rfc} new RFC texts and the unused candidates\n"
 f"of 0024's archives, licences filed), nested on 0024's seven rungs ({rung_line} plaintexts over eight rungs, {rgs['decades_spanned']} decades).\n"
 f"No slope is a clause: seven of the eight points are already banked. The verdict is read on the fourth doubling alone - rung 8 minus rung 7\n"
 f"for the model with a paired scored-chunk interval into RISES (at least {bar}), BELOW_RATE, NOT_RESOLVED or FALLS - with the model's lead\n"
 f"over the linear rule at rung 8 read by 0024's sealed rule into the verdict string itself; rungs 1..7 must reproduce 0024's readings and its\n"
 f"intervals exactly first. Expected outcome stated in advance: {EXPECTED}. It is frozen and running.\n")
r = open(f'{R}/README.md').read()
i24 = r.index("Preregistration 0024 (chain entry 24)")
a2 = "No extrapolation beyond the top rung is banked or quoted.\n"
i = r.index(a2, i24) + len(a2)
rest = r[i:]
if rest.startswith("\nPreregistration 0025 (chain entry"):
    j = rest.index("It is frozen and running.\n") + len("It is frozen and running.\n"); rest = rest[j:]
open(f'{R}/README.md', 'w').write(r[:i] + "\n" + sent + rest)
print("in-flight paragraphs written: seq", seq, "frozen", frozen)
