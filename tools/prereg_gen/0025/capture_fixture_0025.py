#!/usr/bin/env python3
"""Capture tests/fixtures/realcurve3_runner_shape.json from the 0025 smoke run's artifact and scores file."""
import json, os
SP = os.environ.get('RAISE_SCRATCH', os.path.dirname(os.path.abspath(__file__))); R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
art = json.load(open(f'{SP}/smoke_realcurve3/out.json')); sc = json.load(open(f'{SP}/smoke_realcurve3/scores.json'))
assert art['smoke'] is True and art['complete'] is True and sc['smoke'] is True and len(art['fits']) == 37
dropped = ['per_example', 'eval_chunk_ids', 'ext_chunk_ids', 'ext_fam']
scores = {k: v for k, v in sc.items() if k not in dropped}
fx = {"schema": "raise-v1/realcurve3_runner_shape/1",
      "why": "the shape of tools/pivot/run_realcurve3.py's artifact and scores file, captured from a smoke run of the runner itself so the "
             "realcurve3_4096 mutation gate builds its control with the runner's key set at every level (docs/OPERATING_RULES.md section 4); "
             "the values are a smoke's and are used for nothing",
      "captured_from": "python3 tools/pivot/run_realcurve3.py --stage run --smoke against prereg/0025-realcurve3-4096.json's smoke block (0023's "
                       "smoke_realfit/ext_small.npz and fit_small16.npz, a 126-pool-chunk-per-family second-decade smoke corpus built by "
                       "corpus_realfit2.py --cap-per-family 126 --base-per-family 16, and a 128-new-chunk-per-family fourth-doubling smoke corpus built "
                       "by corpus_realfit3.py --cap-per-family 128 --base-per-family 16 nested on it, all in the scratchpad), 2026-09-23, after the "
                       "three-lens pre-freeze review, before the freeze",
      "scores_keys_dropped_for_size": dropped, "artifact": art, "scores": scores}
out = f'{R}/tests/fixtures/realcurve3_runner_shape.json'
json.dump(fx, open(out, 'w'), indent=1, sort_keys=True); open(out, 'a').write('\n')
print('wrote', out, os.path.getsize(out), 'bytes; fits', len(art['fits']), 'ledger', len(art['ledger']),
      'model rungs', [p['ext_real_top1'] for p in art['curves']['model']['rungs']], 'gain', art['fourth_doubling']['model'], 'lead', art['lead_at_top']['r8_model_minus_logistic']['reading'])
