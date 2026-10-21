"""artifacts/pivot/engineering_log_0025.json, pre-freeze state: numbers read from the preregistration, the corpus manifest and the
smoke; later steps add the gate result, the freeze and the run record. Idempotent for the fields it owns."""
import json, os
R = '/home/user/raise-v1'; SP = os.environ.get('RAISE_SCRATCH', os.path.dirname(os.path.abspath(__file__)))
pr = json.load(open(f'{R}/prereg/0025-realcurve3-4096.json')); S = pr['scope']; P = S['curve']['protocol']; sp = S['sealed_partition']
sm = json.load(open(f'{SP}/smoke_realcurve3/out.json')); man = json.load(open(f'{R}/artifacts/pivot/realfit3_corpus_manifest.json'))
pins = json.load(open(f'{R}/tools/pivot/ext_source_pins3.json'))
path = f'{R}/artifacts/pivot/engineering_log_0025.json'
E = json.load(open(path)) if os.path.exists(path) else {}
fam = man['families']; pf = man['per_family']
E.update({
 "schema": "raise-v1/engineering_log/1", "preregistration": "0025-realcurve3-4096",
 "why_this_exists": S['why_this_preregistration_exists'],
 "corpus": {
  "what": "a third real-content fit corpus - the NEW pool positions of a pool nested on 0024's (0024's pool in 0024's order as its prefix) - "
          "built pre-freeze by tools/pivot/corpus_realfit3.py from twelve new pinned PyPI archives, 600 new RFC texts and the candidates of "
          "0024's own archives that 0024's pool did not use, sealed by array hash; nothing under data/pivot is committed",
  "sources": {"archives": len([k for k in pins['files'] if 'url' in pins['files'][k]]), "rfc_files": len([k for k in pins['files'] if k.startswith('rfc3/')]),
              "per_family_composition_of_the_fourth_doubling": S['rungs']['fourth_doubling_composition_per_family'],
              "share_of_the_fourth_doubling_from_new_files": S['rungs']['share_of_the_fourth_doubling_from_new_files'],
              "why_these": pins.get('selection_of_projects'), "licences": "docs/compliance/EXT_SOURCES3.md"},
  "why_no_new_c_or_windows_sources": "the C and Windows families' fourth doubling is served entirely by 0024's own archives' unused candidates "
                                     "(c_src 2313 candidate chunks against 386 needed, pe_bin 5429 against 3206); fetching more of either would have "
                                     "added sources without changing what the doubling can be, and codeload.github.com still answers 403 through the proxy",
  "rfc_sampler": {
   "frame": "every RFC the index lists, minus 0018's and 0024's pinned RFCs and every RFC related to one of them by an Obsoletes, Obsoleted by, "
            "Updates or Updated by annotation in either direction; seed 20260923; the index as served is hashed in docs/compliance/sources/MANIFEST.json",
   "validation": "the 0024 sampler's four-digit patterns skipped RFCs 1 to 999 and five wrapped annotations; the 0025 sampler parses any RFC number "
                 "and joins wrapped lines, and was validated by re-deriving 0024's banked 600 from 0024's frame under 0024's seed: the residual "
                 "differences are explained by the parser defect and filed as CORRECTIONS.md 2026-09-23 (the drawn sample and 0024's sealed corpus "
                 "are unchanged; 0024's frame is now described as it was)",
  },
  "exclusion": man['exclusion'], "candidates_per_family": {f: pf[f]['n_candidate_chunks'] for f in fam},
  "new_candidates_per_family": {f: pf[f]['n_new_candidate_chunks'] for f in fam},
  "dropped_new_chunk_duplicate_of_a_0024_chunk": {f: len(man['chunks_dropped'][f]['new_chunk_duplicate_of_a_0024_chunk']) for f in fam},
  "dropped_for_a_run_shared_with_0024s_blob": {f: len(man['chunks_dropped'][f]['shares_a_run_with_0024s_blob_of_the_same_family']) for f in fam},
  "pool_sizes": man['pool_sizes'], "pool_sizes_0024": {f: pf[f]['pool_size_0024'] for f in fam},
  "new_chunks_with_rows_per_family": {f: pf[f]['n_new_chunks_with_rows'] for f in fam}, "n_new_chunks_with_rows": man['n_chunks_with_rows'],
  "n_new_rows": man['n_rows'], "build_seconds": man['build_seconds'], "npz_bytes": os.path.getsize(f'{R}/data/pivot/realfit3_c4096.npz'),
  "nesting": "the builder reproduces 0024's candidate scan on the 0024 part of every family blob and refuses on any difference in count or dropped "
             "lists; 0024's pool positions are read back from the realfit2 npz metas and checked against 0024's manifest; the new pool positions "
             "are default_rng([20260923, family_index + 1])'s permutation of the remaining candidates; chunk ids continue 0024's per family",
  "run_overlap_rules": "every new candidate is dropped on a 1024-byte run shared with any 0018 pinned blob at any offset (0024's rule) and, new files "
                       "only, on a run shared with 0024's same-family blob (so a new archive vendoring a 0024 project adds no 0024 bytes); a chunk cut "
                       "from 0024's frame IS a region of 0024's blob and is subject to the first rule and to not being a 0024 pool position",
  "determinism": "corpus_realfit3.py --probe built a capped slice twice in two task orders and got identical arrays; --check and --disjoint pass on "
                 "the built corpus",
  "pre_freeze_catches_in_the_builder": [
   "the disjoint proof applied the new-files run rule to every built chunk and flagged the 43 smoke chunks cut from 0024's frame (each a region of "
   "0024's blob, 512 windows shared); the proof now applies the build's own rule - new files against 0024's blob, frame chunks against 0024's pool "
   "positions - and prints the two counts",
  ],
 },
 "design_decisions": {
  "one_doubling_nested_on_0024s_pool": S['why_one_doubling_nested_on_0024s_pool'],
  "no_slope_is_a_clause": P['reference_slopes_informational']['why_no_slope_is_a_clause'],
  "the_clause_is_the_fourth_doubling": pr['bar']['fourth_doubling']['passes_if'],
  "the_lead_rule_is_in_the_verdict_string": pr['bar']['lead_rule']['passes_if'],
  "why_the_lead_stays_a_verdict_part": "0024's reason stands (a flag can be left unquoted, a verdict suffix cannot); the review's proposal to demote "
                                       "the lead to a flag was declined for that reason and the twelve-string verdict keeps it",
  "reproduction_before_any_new_plaintext": P['order_is'],
  "why_0024s_intervals_must_reproduce_exactly": "0024's bootstrap seed is sealed for every verdict interval here and 0024's banked slope and lead "
                                                "intervals must recompute exactly from this run's rung 1..7 vectors: the instrument that reads the "
                                                "fourth doubling is proven to be 0024's before it reads anything new (a drift of four rows in rung 7's "
                                                "vector, within the point tolerance, is caught by this clause; the gate has that control)",
  "why_rung_7_has_the_tighter_tolerance": "rung 7 is the anchor the gain and the lead read against; 0.0005 is one tenth of the point tolerance and "
                                          "twenty rows of the 38452, against a banked determinism of 0.0 over fifteen reproductions",
  "the_floors": S['design']['floors'],
  "b_tree3_is_d1": "0021's fourth floor, B-tree3, is D1 (DecisionTreeClassifier(max_depth=3, random_state=0)) under another name; fitted twice on "
                   "the same rung it banks the identical per-example vector twice and the reader's pairwise-distinct clause VOIDs the run. Found while "
                   "writing the gate's control (the recipe comparison), before the freeze: three floors are refitted, the tree floor is the rung's D1 "
                   "reading, the order has 37 fits, and the gate keeps a case that banks the tree's vector under a floor's name and expects VOID",
  "the_new_shift_arm": S['design']['shift_arms'],
  "seeds": S['seeds'],
  "caps_never_raised": "the iteration caps are part of the sealed recipe; a capped role at rung 8 or 7 is named in the same sentence as the gain and "
                       "the lead, the gain is read as is (never re-parameterised) and the flags gain_is_a_recipe_reading and "
                       "lead_at_top_is_a_recipe_comparison say what the reading is",
  "seed_stability": "twenty other bootstrap seeds re-read the two verdict intervals; the counts are flags, quoted beside any reading whose interval "
                    "bound is within 0.0005 of 0 (0024's rung-7 lead had a 2.5th percentile of 0.0001)",
  "expected_outcome": S['expected_outcome_stated_in_advance'],
  "no_replicate": "a second nesting of rung 8 would double the fourth doubling's pool and its fits; the fit-side variance of one doubling is named "
                  "as what this does not cover and the new shift arm against 0024's is the one between-draw comparison banked",
 },
 "pre_freeze_review": {
  "method": "an adversarial workflow on the design brief before any instrument was frozen: a statistician's lens (nine findings) and a diligence "
            "lens (fourteen), an engineer's lens on the corpus mechanics, each finding refuted twice by independent agents that recomputed the "
            "numbers from the banked artifacts; every confirmed finding adopted or declined with a reason, then the instrument built and the gate "
            "written; two further defects found by the author's own pre-freeze gate work (the B-tree3/D1 duplicate vector, the disjoint proof's rule)",
  "adopted": {
   "statistician": ["the eight-rung slope clause dropped: seven of eight points are banked, so it could not fail short of a collapse (recomputed: "
                    "with rung 8 flat at rung 7 the slope stays 0.0062, the bar fails only below about 0.12x); the verdict's curve part is the fourth "
                    "doubling alone, read four ways",
                    "the gain's reading rule written from 0024's banked paired half-widths (0.0034 to 0.0036 over the scored chunks), with NOT_RESOLVED "
                    "distinct from BELOW_RATE and FALLS",
                    "the sensitivity gain with rung 7 at 0024's banked reading banked as a flag, and rung 7's tolerance tightened to 0.0005",
                    "0024's seed sealed for every verdict interval so 0024's intervals reproduce exactly (a reproduction of the instrument, checked "
                    "as a validity clause)", "a seed-stability count banked for the two verdict intervals",
                    "the lead read at rung 8 by 0024's rule, not re-read at rung 7 under a new seed (rung 7's is reproduced exactly)"],
   "diligence": ["the two-decade span stated with the scope-rule caveat in every place ('one-corpus, one-seed terms are not met by this curve')",
                 "forward pointers pre-committed for the eight places that say 'short of 0003's two-decade scope rule' and for 'keep buying ... "
                 "through 8232 plaintexts'", "the floors refitted at rungs 7 and 8 so 0021's clause is banked without the 'optimistic' caveat, "
                 "both variants", "the fourth doubling's composition per family sealed and stated in every document (new projects for py_src "
                 "and rfc_txt, other chunks of 0024's projects for c_src and pe_bin, a mixture for rst_doc)", "the caps named in the sentence, "
                 "never raised", "a per-family gain flagged as the noisiest number (c_src adds 192 plaintexts)"],
   "engineer": ["the candidate scan runs two passes over one seen-set so a byte-identical collision is charged to the new chunk; the 0024 part "
                "must reproduce 0024's candidates and dropped lists or the build refuses", "vendored directories excluded from the new archives",
                "the pool size per family carries headroom and the shortfall refuses"],
  },
  "declined": {
   "demoting_the_lead_to_a_flag": "0024's reason stands: a flag can be left unquoted, a verdict suffix cannot",
   "a_verdict_slope_over_the_second_decade_4_to_8": "four of its five points are banked; the same objection as the eight-rung slope, in smaller form; "
                                                    "banked as a flag with its interval",
   "a_second_seed_for_rung_8": "doubles the fourth doubling's fits on a 15 GB machine; named as what this does not cover, with the between-draw "
                               "shift-arm comparison as the one banked reading of draw-to-draw variation",
  },
 },
 "instrument": {
  "corpus_builder": "tools/pivot/corpus_realfit3.py (pins in tools/pivot/ext_source_pins3.json, fetch by tools/pivot/fetch_ext_sources3.sh); imports "
                    "corpus_realfit2.py's candidate rule, window hashing and featurisation and never copies them; --verify-pins, --build, --check, "
                    "--disjoint, --probe",
  "runner": "tools/pivot/run_realcurve3.py (single stage; rung_partition3, sealed_order, gain_reading are module-level so the generator, the check and "
            "the gate call them; imports run_realcurve2.py's rung_partition2 and paired_lead_bootstrap and run_realcurve.py's ols_slope and "
            "slope_bootstrap); refusal and NOT RUN paths as 0024's",
  "reader": "tools/readers/realcurve3_4096_verdict.py, generated from a template by a generator; every literal from the sealed file or a banked "
            "artifact; slope_bootstrap, ols_slope and paired_lead_bootstrap copied from the runners statement for statement (the pre-freeze check "
            "compares the ASTs)",
  "preregistration_generator": "make_prereg_0025.py (scratchpad): every sealed value read from 0021's, 0023's and 0024's banked artifacts, the corpus "
                               "manifests and the pins, or computed by calling the runner's own functions on the data",
  "fixture": "tests/fixtures/realcurve3_runner_shape.json, captured from the runner's smoke run",
  "gate": "tests/mutation_test.py realcurve3_4096: the control is built from the fixture's key set with the reader's sealed values; rungs 1..7 and "
          "0024's shift arm carry 0024's BANKED per-example vectors verbatim (the exact-reproduction clause admits nothing else), rung 8, the new "
          "arm, the floors and the null are derived by flipping rows at a deterministic spread; curves, floors, bootstraps, gains, leads and the "
          "stability counts computed with the runners' own functions; controls for all twelve verdict strings and for the exactness clause",
  "pre_freeze_check": "tools/prereg_checks/prefreeze_0025.py",
  "smoke": {"wall_seconds": sm['cost']['wall_seconds_this_invocation'], "fits": len(sm['fits']),
            "model_fourth_doubling_gain": sm['model_fourth_doubling_gain'],
            "gain_reading": sm['fourth_doubling']['model']['reading'], "lead_at_top": sm['lead_at_top']['r8_model_minus_logistic']['reading'],
            "reproduction_bootstrap_0024_exact_on_the_smoke": sm['reproduction_bootstrap_0024']['equals_0024s_banked'],
            "note": "scratchpad corpora only (0023's 16-per-family smoke fit corpus, 0024's 126-per-family smoke of the second-decade corpus rebuilt "
                    "hash for hash, and a 128-per-family smoke of the new corpus nested on it); the smoke's reproductions are of nothing, so its "
                    "reproduction and exactness readings are false by construction and the reader VOIDs it by design"},
 },
 "cost": S['cost'],
 "status": ("unfrozen; the review's blocking defect (the majority-class floor banks "
            "the same vector at rungs 7 and 8, which the reader's pairwise-distinct clause would VOID); see pre_freeze_instrument_review"),
})
json.dump(E, open(path, 'w'), indent=2, sort_keys=True, ensure_ascii=True); open(path, 'a').write('\n')
print('engineering log written', path)
