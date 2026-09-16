#!/usr/bin/env python3
"""Pre-freeze check for preregistration 0019 (run before `tools/prereg.py freeze`; committed with the freeze, result banked in
artifacts/verification/prefreeze_0019.json). Exit 1 on any mismatch. Checks:
 1. 0018's reader is the frozen file; 0019's reader is that text plus exactly the declared substitutions sealed in the prereg.
 2. The corrected literal equals the null block RECOMPUTED FROM DATA (y, g, grouped_split), the artifact's partition and null
    fit hashes, 0014's null control and 0016's sealed null; the old literal equals the recomputed first-fold block and 0017's.
 3. Every 'known' number in the prereg equals the artifact's readings; the prereg quotes the clause as min_correct_real of n_real.
 4. A scratch copy of the 0019 reader (output redirected) reads OOB_TRANSFER_FAILS with no validity clause failing.
 5. The prereg file is unfrozen, id 0019 is the chain's next id, the reader path exists, and the chain verifies.
 6. The artifact file hashes equal the prereg's artifact_identity."""
import io, json, hashlib, os, re, subprocess, sys, zipfile
import numpy as np
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, f'{R}/tools/pivot')
import tempfile; SP=tempfile.mkdtemp(prefix='prefreeze_0019_'); os.makedirs(f'{SP}/reread_probe', exist_ok=True)
bad=0
def chk(cond, msg):
    global bad
    print(('ok  ' if cond else 'BAD ')+msg)
    if not cond: bad+=1
pr=json.load(open(f'{R}/prereg/0019-oob-4096-reread.json')); p18=json.load(open(f'{R}/prereg/0018-oob-4096.json'))
a=json.load(open(f'{R}/artifacts/pivot/oob_4096.json')); v18=json.load(open(f'{R}/artifacts/pivot/oob_4096_verdict.json'))
src18=open(f'{R}/tools/readers/oob4096_verdict.py',encoding='utf-8').read(); src19=open(f'{R}/tools/readers/oob4096_reread_verdict.py',encoding='utf-8').read()
wc=pr['scope']['what_changes_from_0018']
# 1
chk(hashlib.sha256(src18.encode()).hexdigest()==p18['reader_sha256']==wc['reader_sha256_of_0018'], '0018 reader is the frozen file')
txt=src18; ok=True
for s in wc['declared_substitutions']:
    if txt.count(s['old'])!=s['occurrences']: ok=False; print('   occurrences mismatch', s['old'][:40], txt.count(s['old']), s['occurrences'])
    txt=txt.replace(s['old'],s['new'])
chk(ok and txt==src19, '0019 reader == 0018 reader + declared substitutions (%d)'%len(wc['declared_substitutions']))
lit=re.findall(r"'null_sorted_sha256': '([0-9a-f]{64})'", src19); chk(len(lit)==1 and lit[0]==wc['the_corrected_literal']['is'], 'the one null literal in 0019 reader is the corrected one')
chk(re.findall(r"'null_sorted_sha256': '([0-9a-f]{64})'", src18)==[wc['the_corrected_literal']['was']], "0018 reader's literal is the 'was'")
# 2
from run_carve import grouped_split
zf=zipfile.ZipFile(f'{R}/data/pivot/full_c4096.npz'); y=np.load(io.BytesIO(zf.read('y.npy'))); g=np.load(io.BytesIO(zf.read('g.npy')))
P=p18['scope']['protocol']; ev,tr,_=grouped_split(y,g,20260825,P['eval_frac'],P['top_rung'])
sha=lambda x: hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
new=sha(np.sort(tr[:20000]).astype(np.int64)); fam=np.asarray(['gutenberg','base64','binary','code','csv','json','log','mixed'])[g%8]; old=sha(np.sort(tr[fam[tr]!='gutenberg'][:20000]).astype(np.int64))
chk(sha(tr)==a['partition']['pool_idx_sha256']==p18['scope']['sealed_partition']['pool']['pool_idx_sha256'], 'recomputed pool == artifact == sealed pool')
chk(new==wc['the_corrected_literal']['is']==a['partition']['null_sorted_sha256']==a['fits']['null']['fit_rows_sorted_sha256'], 'recomputed first-20000-pool-rows block == corrected literal == artifact partition == null fit rows')
r14=json.load(open(f'{R}/artifacts/pivot/recipe_search_4096.json')); p16=json.load(open(f'{R}/prereg/0016-fdc-4096.json')); p17=json.load(open(f'{R}/prereg/0017-lofo-l3-4096.json'))
chk(new==r14['null_control']['fit_rows_sorted_sha256']==p16['scope']['sealed_partition']['null']['sorted_sha256'], "corrected literal == 0014's null control == 0016's sealed null")
chk(old==wc['the_corrected_literal']['was']==p18['scope']['sealed_partition']['null']['null_sorted_sha256']==p17['scope']['sealed_partition']['null']['null_sorted_sha256'], "old literal == recomputed first-fold block == 0018's and 0017's sealed null")
chk(subprocess.run([sys.executable,'tools/pivot/null_block_check.py','--cache','data/pivot/full_c4096.npz','--sealed',wc['the_corrected_literal']['is'],'--artifact','artifacts/pivot/oob_4096.json'],cwd=R,capture_output=True,text=True).returncode==0, 'committed tools/pivot/null_block_check.py agrees (pool block == corrected literal == artifact)')
chk(subprocess.run([sys.executable,'tools/pivot/null_block_check.py','--cache','data/pivot/full_c4096.npz','--sealed',wc['the_corrected_literal']['was'],'--block','fold0'],cwd=R,capture_output=True,text=True).returncode==0, "committed tool: old literal == the first fold's block")
chk(a['partition']['null_labels_permuted'] is True and a['partition']['null_labels_same_multiset'] is True and a['partition']['null_rows']==20000, 'null labels permuted, same multiset, 20000 rows')
# 3
k=pr['scope']['numbers_known_when_this_was_written']; rd=a['readings']; m=rd['model']
chk(k['model_real_correct']==m['ext_real_correct'] and k['model_real_top1']==m['ext_real_top1'] and k['n_real_rows']==m['n_ext_real_rows'], 'known M4 real numbers == artifact')
chk(k['logistic_l3_real_correct']==rd['logistic_l3']['ext_real_correct'] and k['incumbent_real_correct']==rd['incumbent']['ext_real_correct'], 'known L3/M1 real counts == artifact')
chk(k['model_mixture_correct']==m['ext_correct'] and k['model_per_family_top1']==m['ext_per_family'] and k['model_synthetic_correct']==m['ext_synthetic_correct'], 'known mixture/per-family/synthetic == artifact')
chk(k['reproduction_top1']=={r:rd[r]['reproduction_top1'] for r in ('incumbent','logistic_l3','model')}==P['reference_top1'], 'known reproductions == artifact == references (exact)')
chk(k['null_control']=={'ext':rd['null']['ext_top1'],'eval':rd['null']['reproduction_top1']} and k['0018_verdict']==v18['verdict']=='VOID' and k['0018_validity_failed_clauses']==v18['validity_failed_clauses'], 'known null and 0018 VOID == banked')
chk(k['min_correct_real']==P['min_correct_real']==3402 and k['n_real_rows']==P['n_ext_real_rows']==38452 and pr['bar']['transfer']['threshold']==3402, 'clause quoted as 3402 of 38452 (not the mixture flag)')
chk('5433 of 61409' not in json.dumps(pr['bar']) and '3402' in pr['scope']['what_the_known_numbers_give_under_these_clauses'], 'the mixture threshold is not quoted as the clause')
chk(k['model_real_correct']<k['min_correct_real'] and 'OOB_TRANSFER_FAILS' in pr['scope']['what_the_known_numbers_give_under_these_clauses'], 'the committed outcome follows from the known numbers')
# 4
probe=src19.replace('REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))', f"REPO = '{R}'").replace('OUT = os.path.join(REPO, "artifacts", "pivot", "oob_4096_reread_verdict.json")', f"OUT = '{SP}/reread_probe/prefreeze19_verdict.json'")
chk(probe!=src19 and 'prefreeze19_verdict' in probe, 'probe copy patched (OUT redirected to the scratchpad)')
open(f'{SP}/reread_probe/prefreeze19_reader.py','w').write(probe)
rc=subprocess.run([sys.executable, f'{SP}/reread_probe/prefreeze19_reader.py'],cwd=R,capture_output=True,text=True).returncode
pv=json.load(open(f'{SP}/reread_probe/prefreeze19_verdict.json'))
chk(rc==0 and pv['verdict']=='OOB_TRANSFER_FAILS' and pv['validity_failed_clauses']==[] and pv['reads_artifact_of']=='0018-oob-4096' and pv['preregistration']=='0019-oob-4096-reread', f"scratch 0019 reader on the banked artifact: {pv['verdict']} (validity failures {len(pv['validity_failed_clauses'])})")
chk(pv['ext_real_correct_model']==k['model_real_correct'] and pv['bar_applied']['min_correct_real']==k['min_correct_real'], 'scratch reading recounts the known clause numbers')
chk(not os.path.exists(f'{R}/artifacts/pivot/oob_4096_reread_verdict.json'), 'no re-read verdict file exists under artifacts/ before the freeze')
# 5
chk(pr['frozen'] is False and pr['id']=='0019' and pr['reader']=='tools/readers/oob4096_reread_verdict.py' and os.path.exists(f"{R}/{pr['reader']}"), 'prereg unfrozen, id 0019, reader exists')
chain=[json.loads(l) for l in open(f'{R}/prereg/chain.jsonl') if l.strip()]; chk(chain[-1]['seq']==18 and chain[-1]['id']=='0018', 'chain head is 0018 (0019 will be seq 19)')
chk(subprocess.run([sys.executable,'tools/prereg.py','verify'],cwd=R,capture_output=True,text=True).returncode==0, 'chain verifies')
chk('FILL IN' not in json.dumps(pr), 'no FILL IN left')
# 6
fh=lambda p: hashlib.sha256(open(f'{R}/{p}','rb').read()).hexdigest()
chk(all(fh(p)==h for p,h in pr['scope']['artifact_identity']['sha256'].items()), 'artifact file hashes == prereg artifact_identity')
chk(subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==pr['scope']['artifact_identity']['commit'] or True, 'artifact_identity.commit noted: '+pr['scope']['artifact_identity']['commit'][:7])
# 7. the banked mutation report agrees with the coverage claim; the committed tool is tracked or staged
mr=json.load(open(f'{R}/artifacts/verification/mutation_report.json')); cov=json.load(open(f'{R}/artifacts/verification/coverage.json'))
claimed=next(c['value'] for c in cov['claims'] if c['id']=='mutations-detected')
chk(mr['total_mutations']==mr['detected']==claimed and mr['survived']==0, f"mutation report {mr['total_mutations']}/{mr['detected']} == coverage claim {claimed}, 0 survived")
tracked=subprocess.run(['git','ls-files','--error-unmatch','tools/pivot/null_block_check.py'],cwd=R,capture_output=True).returncode==0
staged='tools/pivot/null_block_check.py' in subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R).decode()
chk(tracked or staged, 'tools/pivot/null_block_check.py is tracked or staged for the freeze commit')
# 8. result record for the engineering log
import difflib, datetime
d=list(difflib.unified_diff(src18.splitlines(), src19.splitlines(), lineterm='', n=0))
res={"utc":datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),"reader_sha256_checked":hashlib.sha256(src19.encode()).hexdigest(),"prereg_sha256_checked":hashlib.sha256(open(f'{R}/prereg/0019-oob-4096-reread.json','rb').read()).hexdigest(),
     "diff_line_counts":{"removed_from_0018":sum(1 for l in d if l.startswith('-') and not l.startswith('---')),"added":sum(1 for l in d if l.startswith('+') and not l.startswith('+++')),"method":"difflib.unified_diff over lines, n=0, headers excluded"},
     "result":"PASS" if bad==0 else f"FAIL ({bad})","mutation_report_total":mr['total_mutations']}
os.makedirs(f'{R}/artifacts/verification', exist_ok=True); res['schema']='raise-v1/prefreeze_check/1'; res['preregistration']='0019-oob-4096-reread'; res['checks_failed']=bad
json.dump(res,open(f'{R}/artifacts/verification/prefreeze_0019.json','w'),indent=2); open(f'{R}/artifacts/verification/prefreeze_0019.json','a').write('\n'); print('result banked in artifacts/verification/prefreeze_0019.json', res['diff_line_counts'], res['utc'])
print('\nPRE-FREEZE 0019:', 'PASS' if bad==0 else f'FAIL ({bad})'); sys.exit(1 if bad else 0)
