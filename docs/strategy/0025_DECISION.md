# 0025 decision: the reproduction rule after the realfit2 rebuild

- Date: 2026-10-22, branch `claude/series-a-ml-evidence-tz750o`. The review in section 4 was reconciled against `35b6493`; the commits after it, through `b988afc`, were read for what they change, and that is noted where it matters.
- For: the founders, and a diligence reader.
- Status: a recommendation. Nothing in the 0025 instrument is changed by this file.
- Numbers come from banked artifacts at the precision written there, mainly `artifacts/pivot/engineering_log_0025.json` (block `container_2026_10_21`) and 0024's banked verdict `artifacts/pivot/realcurve2_4096_verdict.json`. Array hashes are quoted by their first 16 hex characters, commits by their short id. COULD NOT VERIFY marks what no banked artifact settles.

## 1. State of 0025

1. Unfrozen and unrun: `frozen` is false in `prereg/0025-realcurve3-4096.json`, two pre-freeze amendments are recorded (`amendments_before_freeze[0..1]`), and no 0025 fit exists on a sealed corpus.
2. What it was to measure: one more exact per-family doubling of real plaintexts (rung 8: 16464 plaintexts against rung 7's 8232), nested on 0024's seven rungs; the verdict is rung 8 minus rung 7 for the model, read RISES / BELOW_RATE / NOT_RESOLVED / FALLS against 0.005, with the rung-8 lead of the model over the logistic as its suffix; the real-plaintext span would go from 1.8016 decades (130 to 8232 plaintexts) to just over two (130 to 16464).
3. Its validity rule as sealed: rungs 1..7 must reproduce 0024's readings (rung 7 within 0.0005, the rest within 0.005), and 0024's banked slope and lead intervals must recompute exactly from this run's rung 1..7 vectors before any rung-8 fit, or the run files NOT RUN.
4. What blocks it: 0024's fit corpus (realfit2), rebuilt twice on this container on two hosts, has a feature array that matches neither 0024's banked one nor the other rebuild; the rung-7 logistic refitted on the first rebuild differs from 0024's banked vector on 264 of 61409 extension rows, so the exact rule cannot pass on that rebuild (the second is untested), and on either rebuild the runner refuses to launch, because the sealed realfit2 hash is 0024's.
5. Outstanding under any option: the builder cache is not rebuilt (its banked row order cannot be reproduced), 29 of the 38 pre-freeze review findings are open (section 4), and no pre-freeze check PASS is banked (`artifacts/verification/prefreeze_0025.json` does not exist).

## 2. What was found on 2026-10-21 and 2026-10-22

- **The move.** On 2026-10-21 the work moved to a fresh container with nothing under `data/` (`CORRECTIONS.md`, 2026-10-21, the cold-clone entry). Two fetch defects were found and fixed, and every pinned source of 0003, 0018, 0024 and 0025 then verified byte-identical (`container_2026_10_21.sources`). The other 2026-10-21 entry (the CI determinism probe) records that `run_study.build()` writes rows in batch-completion order, so the banked X and g of the three caches it wrote, the builder cache `full_c4096` among them, cannot be rebuilt.
- **Corpora rebuilt** (`container_2026_10_21.corpora_rebuilt`). 0018's extension corpus and 0021's fit corpus are IDENTICAL to their banked manifests (0021's in 163.0 s). 0024's realfit2 is not: y, g and fam hash to the banked values and `chunk_meta_sha256` agrees, but X hashes to `c395da3f4c1aa3cb`, not the banked `d74bd30e71a5083f` (2734.2 s build under load, with the system python 3.11.17 and zlib 1.3; the banked build's `library_versions` name python 3.11.15 and zlib 1.3).
- **Where it differs** (`realfit2_localisation_2026_10_22`). The rows that form 0024's sealed smoke corpus (chunks with pool position k < 126 per family: 16027 rows, 629 chunks, all 26 configurations) hash to 0024's banked smoke y, g, fam and X, so the difference lies in rows of chunks with k >= 126. This container compresses deterministically (1745 chunks x 25 configurations twice, 0 differences). numpy's AVX-512 dispatch does not move 5135 sampled rows. ISA-L level 3 picks AVX2 or AVX-512 code at run time with different output; the banked build ran on an AVX-512 machine, and the banked manifests record no CPU features (manifests written from `35b6493` on record a platform block and per-block X hashes). Cause: COULD NOT VERIFY. No copy of the banked bytes survives, and the remaining explanations the log lists (a one-off fault in the banked build, a transient edit at build time, a host whose libm differed for zopfli's cost model on rare chunks) cannot be told apart.
- **Refits against 0024's banked vectors** (`refits_against_0024`), on the first rebuild. These used the sealed interpreter (python 3.11.15, 3 threads, nice 10) and the repository's own partition and fit code, with every rung's row set hashing to 0024's sealed rung hashes:
  - r4..r7 depth-3 tree: IDENTICAL.
  - r5 logistic: IDENTICAL (n_iter 479 as banked).
  - r7 logistic: DIFFERS on 264 of 61409 extension rows (171 real; 5248 against 5249 real correct; n_iter 678 against the banked 664).
  - On 0021's rebuilt-identical block, the same environment reproduces 0021's L3, D1 and B-feat1 exactly, L3 with n_iter 392 as banked (`container_2026_10_21.fitting_environment_reproduces`).
  - Not in any banked artifact: the r6 logistic and the model at rungs 5..7 refitted on the first rebuild, and any refit on the second rebuild (below). COULD NOT VERIFY how they compare.
- **Consequence.** 0025's sealed rule that 0024's slope and lead intervals recompute exactly from rungs 1..7 before any rung-8 fit cannot pass on this rebuild, because 0024's rung-7 lead interval uses the rung-7 logistic. The log states that the reading tolerances (rung 7 within 0.0005) would pass for these fits. Two earlier stops also bind as sealed:
  - `tools/pivot/run_realcurve3.py` (`_hashes()`) compares realfit2's X, y, g and fam with `scope.curve.protocol.fit2_corpus.arrays` and refuses with exit 3 on a mismatch.
  - `tools/prereg_checks/prefreeze_0025.py` requires `corpus_realfit2.py --check` to print IDENTICAL, and `corpus_realfit3.py --check` likewise.
- **Builder cache.** Not rebuilt; it was held until the realfit2 difference is understood (`corpora_rebuilt`). The reorder tool, content proof and re-seal script (`tools/prereg_gen/0025/reorder_cache.py`, `cache_content_proof.py`, `amend_cache_0025.py`) are committed and have not run; `artifacts/verification/cache_rebuild_0025.json` does not exist. This re-seal is needed under every option below.
- **realfit3** (`corpora_rebuilt`, recorded in `6c8b75b`). Run alone on 2026-10-22, after two attempts beside other work were killed by the memory cgroup at 11.4 GB, the rebuild's X, y, g and fam hash to the banked manifest's values (X `98547322dff713f0`; 802.8 s build).
  - Its `--check` prints DIFFERS only for the line that compares the realfit2 it is nested on with 0024's banked X, and that realfit2 is the rebuilt one (`c395da3f4c1aa3cb`). So 0025's own corpus needs no re-seal.
  - It was built on a different host from the realfit2 rebuild: the container restarted between them, and its CPU now reports the numpy SIMD targets AVX512_ICL and AVX512_SPR, which the earlier host did not.
  - The two results are therefore confounded (a different corpus on a different host). The realfit2 rebuild on the later host, next, separates them.
- **realfit2 on the later host** (`second_rebuild_other_host`, recorded in `b988afc`). A second realfit2 rebuild, on the later host, gives X `4ff8ec5760ccb069`, which is neither 0024's banked `d74bd30e71a5083f` nor the first rebuild's `c395da3f4c1aa3cb`.
  - Its y, g and fam are identical to the banked ones, and its smoke subset is again identical to 0024's banked smoke corpus.
  - The two rebuilds differ in exactly 6 of 193926 rows (4 chunks), every one labelled 22 or 23 (ISA-L levels 1 and 2), and the whole feature row moves in each. The log concludes that ISA-L's output at those levels depends on the CPU generation on rare inputs, which localises the realfit2 difference to ISA-L's run-time code-path dispatch.
  - The log reports a test of whether forcing a dispatch tier reproduces the banked bytes as under way, and no result is banked. COULD NOT VERIFY yet that the same mechanism explains the banked X.
  - Its manifest (scratchpad `rf2_spr/`) is the first realfit2 manifest to record the platform and per-block X hashes.
- **Ledger.** At `b988afc`, `CORRECTIONS.md` has no entry for the realfit2 difference and none dated 2026-10-22. The builder-cache row-order defect's own entry is not filed either: the 2026-10-21 probe entry says it "is filed with the cache's content proof", and that proof has not run. `docs/DILIGENCE.md` said at `35b6493` that the manifest makes "the rebuild *proven* identical, not assumed"; `938e0c7` rewrote it to say which rebuilds match and which do not, citing `CORRECTIONS.md` entries of 2026-10-21 and 2026-10-22, the second of which is not committed yet. `docs/strategy/ROADMAP.md` (R1) states the exact-interval rule as 0025's validity clause. An entry is owed under every option.

## 3. Options

Common to all three: the builder-cache rebuild, reorder, content proof and re-seal; the `CORRECTIONS.md` entry; the open review findings; and the run's own sealed cost of 11963 to 15511 s (`scope.cost`).

### (a) Recover the banked realfit2 bytes

- **What.** Find the environment or fault that produced X `d74bd30e71a5083f` for realfit2 and rebuild it, so that 0025 runs as sealed.
- **Cost.**
  - One full realfit2 build per candidate: 452.2 s as banked in 0024's manifest, 2734.2 s under load on the first host here. Each build is then compared by whole-array hash. The banked manifest has no per-block X hashes, so a near miss cannot be localised.
  - A rebuild on the later host, on which realfit3 reproduced, was tried on 2026-10-22 and gave a third X (section 2).
  - That rebuild localised the difference between the two rebuilds to ISA-L's CPU-dependent dispatch at levels 1 and 2. One bounded candidate follows from it: force each ISA-L dispatch tier and compare the result with `d74bd30e71a5083f`. The log reports that test as under way, and no result is banked.
  - Beyond it, nothing in the record: the log's other explanations are not environments one can rebuild, and two byte-identical results under this container's python 3.11.17 (0024's smoke subset and realfit3) argue against the banked builder's own python 3.11.15 as the cause. Past the dispatch test the search has no bound.
- **Can claim afterwards.** If the bytes are found: 0025 as sealed, with its instrument shown to be 0024's to the interval, and 0024's corpus reproducible again with the cause named. If they are not found: nothing, and 0025 is still blocked.
- **Changes in the sealed file.** None to the rule. `invocation.corpus` and `invocation.interpreter` would name the environment that reproduced the bytes.

### (b) Amend 0025 before its freeze: reproduction within the sealed tolerances

- **What.**
  - Rungs 1..7 and 0024's shift arm are re-measured on the rebuilt corpora and compared with 0024's banked readings within the tolerances already sealed (rung 7 within 0.0005, the others within 0.005), instead of exactly. Those tolerances were set before the rebuild difference was known and do not change; a drift beyond them is still NOT RUN.
  - 0024's slope and lead intervals are recomputed from this run's vectors and banked beside 0024's banked ones, as an informational comparison and no longer a validity clause.
  - The published sentence "seven of the eight points were banked before this run" is replaced by what is true: seven of the eight points re-measure points 0023 and 0024 banked before this run, on corpora rebuilt for it, within the sealed reading tolerances.
  - The change is filed in `CORRECTIONS.md` as a weaker reproduction check. Its size: from every interval bound exact to readings within 0.0005 at rung 7 and 0.005 elsewhere.
- **Cost.**
  - One amendment script on the mechanics of `amend_prereg_0025_b.py`: refuse if frozen, assert every edit, record under `amendments_before_freeze`.
  - The realfit2 X hash is resealed inside `scope.curve`, so `protocol_sha256` and `curve_sha256` move and the reader is regenerated from an edited template with `gen_reader_0025.py`.
  - One runner block is removed. Gate `realcurve3_4096`'s control and its two exactness cases are rebuilt. `prefreeze_0025.py`'s realfit2 checks are rewritten. The fixture is recaptured at the next smoke, and the publication path's sentences change.
  - The run's own compute is unchanged.
- **Can claim afterwards.**
  - The eighth point is read against a rung 7 fitted in the same run on the same corpora.
  - The fitting environment reproduces 0021's recipes and 0024's trees and rung-5 logistic exactly (banked above).
  - Rungs 1..7 land within the sealed tolerances of 0024's readings, or the run is NOT RUN.
  - How far the rebuild moves 0024's intervals is banked beside them for anyone to read.
- **Cannot claim.**
  - That 0025's instrument is 0024's to the interval.
  - That rungs 5..7 hold 0024's feature bytes.
  - That 0024's rung-7 MODEL_LEADS (point 0.0039, interval [0.0001, 0.0077]) survives the rebuild, unless the recomputed interval shows it. COULD NOT VERIFY now: the rebuilt rung-7 model and logistic vectors are not banked.
- **Changes in the sealed file.** Listed in 3.2.

### (c) Retire 0025 as designed; preregister a successor

- **What.** 0025 is never frozen. A successor rebuilds every rung on today's corpora under its own seals, with no clause tied to 0024's vectors.
- **Cost.**
  - A new preregistration and a way to generate it: 0025's generator `make_prereg_0025.py` was lost, and its file has since been amended by scripts.
  - A new reader and template, new gate cases, a new smoke and fixture (the last runner smoke took 2867.9 s wall), a new pre-freeze review (most of the 38 findings below carry over), and a new publication script and dry run.
  - The run's compute is the same as 0025's, and its calendar time is the longest of the three options.
- **Can claim afterwards.** One instrument on one container's corpora, with every point measured in the same run and no clause depending on 0024's lost bytes. Its own realfit2 would depend on the host in the same way as (b)'s.
- **Cannot claim.**
  - Any validity link to 0024. As specified it has no reproduction clause against 0024, so the rival explanation "the machinery is not 0024's" (`scope.rival_explanations_run_as_arms[2]`) goes unanswered inside the run, and the comparison with 0024 becomes informational.
  - A successor that kept reading-level reproduction clauses would be (b) under a new number.
- **Changes in the sealed file.** 0025 gets a retirement record (unfrozen, never run, and why), and nothing else in it changes; the work moves to a new file.

### 3.1 Recommendation: (b), unless the ISA-L dispatch test recovers 0024's bytes first

Decision rule, stated before that test's result is read: a forced dispatch tier whose realfit2 rebuild hashes to `d74bd30e71a5083f` means (a). 0025 then runs as sealed, with the tier named in `invocation.corpus`, the refits repeated on those bytes, and no rule changed. Any other result means (b), as specified here, and the search stops being a path for 0025.

Reasons:

1. **What failed is the bytes, not the fitting machinery.** On identical inputs the sealed environment reproduces 0021's per-example vectors exactly, and on the first realfit2 rebuild it reproduces 0024's trees at rungs 4..7 and its rung-5 logistic. The exact rule's stated purpose ("which proves the instrument is 0024's before any new interval is read", `scope.curve.protocol.reference_bootstrap_0024_is`) cannot be met on a corpus that is not 0024's; (b) says so instead of claiming it.
2. **(b) keeps a check against 0024 at the reading level** with tolerances sealed before the difference was known. (c), as specified, drops it.
3. **No rung-8 number exists.** The change comes before the freeze: `stop_rules[1]` bars changes after the freeze, and pre-freeze changes are recorded under `amendments_before_freeze`, as two already are. The weakening is filed at full size, not hidden behind the original commitment.
4. **The irreproducible rows become a measurement.** 0024's intervals, recomputed on a rebuilt corpus whose bytes and platform are recorded, are banked beside 0024's banked ones.
5. **Cost.** (b) changes one rule and the sentences that state it; (c) repeats the whole instrument and its review. (a) has one bounded test left, reported under way, and no candidate after it; realfit2 already has three X hashes from three hosts.

Conditions, part of the recommendation:

- Seal one rebuilt realfit2, chosen by a rule fixed before any refit on it is read. Recommended: the 2026-10-22 build (X `4ff8ec5760ccb069`), because it is the only realfit2 build whose manifest records its platform and per-block X hashes.
  - Keep its npz, because a rebuild on another host gives other bytes.
  - The refits banked in the log were made on the first rebuild. They show what to expect, not what the sealed corpus gives.
  - If 0024's intervals happen to recompute exactly on the sealed rebuild, the banked flag says so and the documents may say so; the rule does not depend on it.
- Commit the amendment before any further reproduction refit on a rebuilt corpus is run or read (the r6 logistic, the model at rungs 5..7, 0024's shift arm). Change no tolerance, bar or rule other than the exactness clause and the sentences that state it.
- Commit in the same amendment how the recomputed rung-7 lead is published. If it reads other than MODEL_LEADS, every published MODEL_LEADS of 0024 carries it in the same sentence, at the size MODEL_LEADS had, as `stop_rules[4]` already requires for a rung-8 NO_SEPARATION or LINEAR_LEADS.
- After the dispatch test, (a) continues only as a cause investigation for the `CORRECTIONS.md` entry. Once the amendment is committed, 0025 runs on the rebuilt corpora whatever that investigation later finds.
- realfit3 needs no re-seal (section 2). If a later rebuild of it differs, its hashes are resealed in the same amendment, since rung 8 has never been fitted.

### 3.2 What (b) changes

**Inside `scope.curve`.** These edits move `protocol_sha256` and `curve_sha256`, so the reader is regenerated.

| JSON path in `prereg/0025-realcurve3-4096.json` | Now | Under (b) |
|---|---|---|
| `scope.curve.protocol.fit2_corpus.arrays.X.sha256` | 0024's `d74bd30e71a5083f…` | the chosen rebuild's hash (recommended: `4ff8ec5760ccb069…`, the 2026-10-22 build; computed from the npz by the amendment script), with 0024's kept beside it the way `amend_cache_0025.py` keeps 0021's cache hashes as `*_banked_2026_08` |
| `scope.curve.protocol.fit2_corpus_described` (`manifest`, `manifest_sha256`) | 0024's banked manifest only | the rebuilt manifest (platform block, per-block X hashes) banked beside 0024's, which stays as banked |
| `scope.curve.protocol.reference_bootstrap_0024_is` | "they must equal these exactly, which proves the instrument is 0024's before any new interval is read" | recomputed from this run's vectors under 0024's seed and banked beside these; informational, not a validity clause |
| `scope.curve.protocol.rung_stream_words.bootstrap` | "so 0024's intervals reproduce exactly" | "so 0024's intervals are recomputed on 0024's own resamples" |
| `scope.curve.protocol.reproduction_tolerance_note` | "the machinery reproduced 0021, 0023 and 0024 with drift 0.0 at every rung" | adds that rungs 5..7 rest on a rebuilt realfit2 whose X differs from 0024's in rows the banked record cannot localise, and whose bytes depend on the host; the tolerances are unchanged |
| `scope.curve.protocol.reference_slopes_informational.why_no_slope_is_a_clause` | "seven of the eight points are banked" | "seven of the eight points are known in advance within the reading tolerances" |
| `scope.curve.protocol.order_is` | "every reproduction before any new plaintext is fitted" | the timing qualifier of new-9 and new-17 (the null control fits rung 8's rows first; 0024's shift arm is reproduced after rung 8) |

**Outside `scope.curve`.** These are recorded under `amendments_before_freeze`; no hash moves.

| JSON path | Now | Under (b) |
|---|---|---|
| `scope.sealed_hashes.fit2_corpus_X_sha256`, `scope.corpus_fit2.arrays.X`, `scope.corpus_fit2.library_versions` | 0024's | resealed as above; the rebuild's library versions beside 0024's |
| `title` | "Seven of the eight points are banked, so no slope is a clause"; "Rungs 1..7 must reproduce 0024's readings (rung 7 within 0.0005) and 0024's bootstrap intervals exactly." | "Seven of the eight points re-measure banked ones, so no slope is a clause"; rungs 1..7 within the sealed tolerances, 0024's intervals recomputed and banked beside its own |
| `scope.what_this_is_and_is_not` | "seven of the eight points were banked by 0023 and 0024 before this run"; "must reproduce its readings and its intervals before any new plaintext is fitted: a machinery that no longer reproduces the first seven rungs is not allowed to measure the eighth" | the replacement sentence; readings within the tolerances, intervals banked beside 0024's; a machinery whose readings of rungs 1..7 drift beyond the tolerances does not measure the eighth; the timing qualifier |
| `scope.seeds.seed2` | "(so that 0024's intervals reproduce exactly)" | "(so that 0024's intervals are recomputed on 0024's own resamples)" |
| `scope.design.lead` | "at rung 7 (0024's, which must reproduce exactly)" | "at rung 7 (re-measured, beside 0024's banked reading)" |
| `scope.design.curve_flags`, `bar.two_decade_slope_informational.passes_if`, `stop_rules[0]` | "the sentence that seven of its eight points were banked before this run" | the replacement sentence |
| `scope.rival_explanations_run_as_arms[2]`, `bar.reproduces_0021_0023_and_0024.passes_if` | "0024's banked slope and lead intervals must recompute exactly"; NOT RUN "on 0024's slope and lead intervals not recomputing exactly" | readings within tolerance; intervals recomputed and banked beside, informational; NOT RUN only on a point drift |
| `scope.flags_stated_in_advance[6]` | "whether 0024's intervals reproduced exactly" | "0024's intervals recomputed beside its banked ones, and whether they are equal" |
| `arms[3]`, `arms[6]` | "0024's slope and lead intervals must recompute exactly"; "0024's intervals not reproducing" in the VOID list | removed from both; the comparison is banked |
| `stop_rules[3]` | NOT RUN on "0024's slope and lead intervals not recomputing exactly from this run's rung 1..7 vectors" | that condition removed from the NOT RUN list |
| `invocation.corpus` | the 0024 and 0025 source fetches, then realfit3's build, check and disjoint | the prerequisite fetches and builds, without a promise that `corpus_realfit2.py --check` prints IDENTICAL (new-3's residual); it states that a realfit2 rebuild on another host gives other bytes, so a cold clone re-measures rungs 5..7 rather than reproducing them |
| `amendments_before_freeze` | two records | a third, naming every path above |

**Reader** (`tools/readers/realcurve3_4096_verdict.py`). Edit `tools/prereg_gen/0025/reader_0025_template.py` and regenerate with `gen_reader_0025.py`; the pre-freeze check requires the reader to equal the generator's output.

- Module docstring: "Seven of the eight points were banked before this run"; "and 0024's banked bootstrap intervals exactly"; "and 0024's intervals reproduce exactly".
- Constants: `FIT2`, `PROTOCOL`, `PROTOCOL_SHA256`, `CURVE_SHA256` (regenerated); the comment on `REFERENCE_BOOT_0024` ("which the reader's recomputation must equal exactly").
- `read()`, corpora clause: `fit2_corpus` is still compared with `FIT2` key for key, now against the resealed block.
- `read()`, block "(a) 0024's intervals, reproduced exactly":
  - Keep the recomputation, and keep the VOID when the banked `reproduction_bootstrap_0024` is not the reader's recomputation.
  - Remove the VOID "reproduction: 0024's banked slope and lead intervals do not reproduce exactly from this run's vectors under 0024's seed: the instrument is not 0024's".
- `read()`, flags: `reproduction_bootstrap_0024_exact` stays as a flag that may be False. `two_decade_slope_is` ("seven of its eight points were banked by 0023 and 0024 before this run") gets the replacement sentence.
- `read()`, meaning:
  - "Seven of the eight points were banked before this run, so the two-decade slope ..." gets the replacement sentence.
  - "Rungs 1..7 and 0024's shift arm reproduced 0024's readings (rung 7 within 0.0005) and 0024's bootstrap intervals exactly." becomes the readings within the tolerances, plus the recomputed rung-7 lead beside 0024's banked one.

**Outside the sealed file and the reader.**

- `tools/pivot/run_realcurve3.py`:
  - The fit-loop block that raises NOT RUN when "0024's banked slope and lead intervals do not recompute exactly ... nothing of rung 8 is fitted", and its smoke switch `RAISE_SMOKE_EXACT_CHECK`.
  - The `repro_intervals_0024()` docstring and its `unit` string.
  - The module docstring.
- `tests/mutation_test.py`, gate `realcurve3_4096`:
  - `_good_realcurve3` puts 0024's banked vectors verbatim on rungs 1..7 and 0024's shift arm.
  - The default control requires `equals_0024s_banked` to be True, and the rung-7 lead control requires 0024's exact interval.
  - The two cases "...no-longer-exact-is-VOID" become PASS controls that bank `equals_0024s_banked` False.
  - A VOID case is added for a rung-7 drift above 0.0005.
  - The straddle controls no longer need to patch the reader (new-18).
- `tools/prereg_checks/prefreeze_0025.py`: the requirement that `corpus_realfit2.py --check` and `corpus_realfit3.py --check` print IDENTICAL, and the equality of realfit3's `nested_on.realfit2_arrays` with the sealed `fit2_corpus.arrays`. Both are restated against the resealed hash, with 0024's banked one kept beside it.
- Publication path:
  - `tools/publish/publish_0025.py` ("seven of its eight points were banked"; "and 0024's bootstrap intervals exactly") and `dryrun_publish_0025.py`.
  - `tools/prereg_gen/0025/freeze_docs_0025.py`.
  - `tools/render/evidence_page.py` ("and 0024's intervals exactly"; "and 0024's bootstrap intervals exactly"; "Seven of the eight points were banked"; and, since `388d0f1`, "at rung 7 the same reading is 0024's ... reproduced exactly").
  - `docs/strategy/ROADMAP.md` R1 ("0024's intervals must recompute exactly").
- `artifacts/pivot/engineering_log_0025.json`: `design_decisions.why_0024s_intervals_must_reproduce_exactly`, and `container_2026_10_21.realfit2_localisation_2026_10_22.decision_needed`, which records the decision.

## 4. The reconciled pre-freeze review

The 38 findings of `docs/qa/PREFREEZE_REVIEW_0025_2026-10-22.json` (14 earlier, 24 new), reconciled against `35b6493`: **7 closed, 29 open, 2 refuted**. Rows marked (b) change or become required under the recommendation.

| id | severity | status | evidence | remaining change |
|---|---|---|---|---|
| old-0 | blocking (resolved) | closed | The reader accepts exactly {r7_floor_majority, r8_floor_majority} as a shared vector, and any other shared vector is VOID. The gate's control banks the pair identical, with PASS and VOID cases, and `scope.design.floors` names the pair. | Optional: the docstring sentence "pairwise distinct" in template and reader (regenerate); move the log's planned and unadjudicated entries to applied. |
| old-1 | minor (sealed values fixed; log mirror stale) | open | The prereg seals launch 11.0 GB and restates `cost.memory` (amendments [0] and [1]), and the runner refuses beside builders and the suite. The log's top-level `cost.memory` still says about 9.0 GB, and `still_open_before_the_freeze[0]` says the file still seals launch 8.0. | Set the log's `cost` equal to the prereg's `scope.cost` (`make_englog_0025.py`); mark `still_open[0]` done. |
| old-2 | minor (resolved; moot if the exact rule is amended) | closed | The runner files NOT RUN before any rung-8 fit unless 0024's slope and lead intervals recompute exactly once all 21 reproduction fits are banked, and the prose says the same. This is the rule the first realfit2 rebuild cannot pass. | (b): the runner block, `rival_explanations_run_as_arms[2]`, `bar.reproduces_0021_0023_and_0024`, `stop_rules[3]`, `arms[3]` and the log's design decision change together; `what_this_is_and_is_not` and `publish_0025.py`'s timing sentence get the shift-arm qualifier. |
| old-3 | minor | open | The reader docstring and `rival_explanations_run_as_arms[8]` say "0025's corpus alone". The runner's SHIFT8 comment and refusal, the reader's VOID text, the gate's two `expect_clause` strings and the pre-freeze label still say "new files". | Reword the runner (2 sites), the template (then regenerate), the gate's `expect_clause` (2, together with the template) and the pre-freeze label. |
| old-4 | minor (prereg fixed; log mirror stale) | open | `scope.cost.estimate_stated_in_advance` now states what its totals (11963 and 15511 s) allow for the floors (amendment [1]), so the sentence is consistent with them. The log's copy still says about 60 s. | The same log `cost` re-sync as old-1. |
| old-5 | none | refuted | The log says 0.0005 is one tenth of the point tolerance (0.005), which it is; no committed text says "one fifth". | None. Optional: mark it refuted in the log; "twenty rows" becomes "about nineteen rows". |
| old-6 | minor | open | The runner hard-codes `STABILITY_SEEDS = 20` and never reads `P['stability_seeds']`, so the smoke block's value is dead. The pre-freeze check tests only the reader's value. | The runner reads `P['stability_seeds']`, refuses a real run whose value is not 20, and uses it in the stability loop. |
| old-7 | minor (reader and gate fixed; bar text contradicts) | open | `bar.run_complete_one_scoring_per_role.passes_if` still says "no two roles bank the same per-example vector" with no exception, and the log's `design_decisions.the_floors` is the pre-amendment text. | Amend the bar sentence to name the majority-floor pair (outside `scope.curve`, no reseal); re-sync the log's `the_floors`. |
| old-8 | major (reader and gate fixed; publication path not) | open | The reader emits the lead rule's "(the <role> at its iteration cap at rung 8 (the top rung))". `publish_0025.py` (LCAP and the evidence-page DEFS string), `dryrun_publish_0025.py` and `evidence_page.py` still emit "...at rung 8)". | Change the four sites together and re-run the dry run (the same as new-22). |
| old-9 | major (resolved) | closed | The reader's flag and meaning qualify the span ("only in the sense that the rule asked for two decades of data"), the gate refuses "by construction", and the evidence page was fixed at `751f3d4`. Only the stale worktree `agent-a8b006d012b9af394` still carries "by construction". | None; do not merge from that worktree. Optional log bookkeeping. |
| old-10 | major | closed | Fixed in `4813887a1e826dd1`: the reader prints `design.floors`' pre-committed sentences byte for byte, and the gate asserts the sealed strings. | None. Optional: log `still_open[3]` cleanup; gate controls that fail if both sentences print. |
| old-11 | minor | open | The reader and `publish_0025.py` use `stop_rules[0]`'s words; the evidence page's 0025 panel still drifts for BELOW_RATE, NOT_RESOLVED and FALLS, and the gate asserts only fragments. | Replace the three panel strings with `stop_rules[0]`'s words (with new-15); optional gate tightening. |
| old-12 | minor | open | One case cannot fail (a forged drift with r7_model perturbed and no `expect_clause`), the reader's exception path is never reached, a dummy-floor branch in the template is dead, and many VOID clauses have no case naming them. This is not moot under (b). | Give the case an `expect_clause`; make the shape case reach the exception path; delete the dead template branch and regenerate; add one forgery case per uncovered clause (COULD NOT VERIFY that each fires only its own clause without running the gate). |
| old-13 | minor | open | No control pins a rung-8 lead whose lower bound is exactly 0, though the runner smoke's fixture banks one read NO_SEPARATION. | Add a pass control with `ci95[0] == 0.0` reading NO_SEPARATION, and confirm it fails on a reader with `lo >= 0`. The proposed accuracy is a skeptic's computation (COULD NOT VERIFY until run). |
| new-0 | blocking | closed | `prefreeze_0025.py` now executes the module it loads (`e441f69`). Its step 1 runs the committed reader generator `gen_reader_0025.py`, wired in `freeze_0025.sh`, so the lost `make_prereg_0025.py` is never needed. | None. (b): the check's realfit2 and realfit3 `--check` IDENTICAL requirements change (3.2). |
| new-1 | major | open | `corpus_realfit3.py` scans only new-file chunks for runs shared with 0024's blob, and chunks cut from 0024's frame get pool-position and source-hash checks only. `--disjoint` still prints "shares nothing with anything scored or fitted before", and `rival_explanations_run_as_arms[3]` states the scan for every candidate. | Reword the `--disjoint` success line, keeping "shares nothing"; amend `rival[3]`; run an informational scan of frame chunks against the 0024 chunks fitted at rungs 5..7 and bank it before the freeze. |
| new-2 | major (moderate: informational arm) | open | `rival[8]` and the reader are fixed. The runner, the reader's VOID text, the gate's `expect_clause`, `freeze_docs_0025.py` ("reads directly"), the pre-freeze label and `what_this_is_and_is_not` ("reads the shift directly") still present s8 as new files alone, though all of c_src's and pe_bin's s8 plaintexts are 0024's archives' unused chunks. | The old-3 edits, plus `freeze_docs_0025.py` and an amended `what_this_is_and_is_not` stating the composition. |
| new-3 | major | closed | Builders no longer overwrite a banked manifest on `--build` (`27a61aa`), and `--check` compares with the banked manifest. Residual: `invocation.corpus` lists only realfit3's steps. | (b): `invocation.corpus` lists the prerequisite fetches and builds, without promising `corpus_realfit2.py --check` IDENTICAL. |
| new-4 | major | refuted | `/root/venv311` is python 3.11.15 with numpy 2.4.6 and scikit-learn 1.9.0, as sealed, and `freeze_0025.sh` uses it. The log records it reproducing 0021's and 0024's fits exactly. | None; do not reseal `environment.python`. |
| new-5 | minor | open | `corpus_realfit3.py` computes the rebuilt 0024 blob's sha256 and bytes and never compares them with the banked `per_family.blob_0024_sha256` and `blob_0024_bytes`. | In `plan()`, refuse before featurising when they differ from the banked manifest; optionally the same check in `disjoint()`. |
| new-6 | minor | open | Both `headroom_per_family` blocks give `pool_positions_needed` as pool size less 0024's chunks with rows, which is neither what the builder took nor what rung 8 needs. | Set or rename the field from the banked manifest and reword `headroom_is` (inside `scope.curve`: reseal, regenerate, recapture the fixture). Fold this into the (b) amendment. |
| new-7 | minor | open | `ext_source_pins3.json` and the log say rst_doc needs no new project; the sealed composition takes part of rst_doc's rung-8 plaintexts from new files. The pins file's sha256 is sealed in `scope.artifact_identity_at_writing`. | A byte-exact edit of the pins sentence and the log copy; reseal `ext_source_pins3_sha256` once, together with new-13 and new-21. |
| new-8 | minor | open | The run rule drops a chunk on 16 consecutive non-constant 64-byte windows on the chunk's own grid. The prose in the prereg (`what_this_does_not_cover`, `rival[3]`, `why_this_preregistration_exists`), `EXT_SOURCES3.md`, the reader template, `freeze_docs_0025.py` and `publish_0025.py` states a 1024-byte run at any offset. No ledger entry exists. | State the actual guarantee in each place (no reseal for fields outside `scope.curve`); add a `CORRECTIONS.md` entry for 0024's sealed sentences. The count of affected chunks is COULD NOT VERIFY. |
| new-9 | minor | open | The sealed order starts with the null control on rung 8's rows, yet six fields say "before any new plaintext is fitted", as do the runner, `freeze_docs_0025.py`, `publish_0025.py` and the log. | (b): carry the qualifier ("under its own labels"; the null control first) in the amendment's new text; `order_is` is in the protocol, so reseal once. |
| new-10 | blocking as sealed text; major in practice | open | `stop_rules[4]`'s site lists omit published sites of the span, keep-buying and thesis sentences. `publish_0025.py` already applies its patterns to every document it edits, but its asserts require only some files. | Amend `stop_rules[4]` (outside `scope.curve`) to list every site "in every place it stands"; extend `publish_0025.py`'s asserts; recount after the in-flight outbound edits land. |
| new-11 | blocking | closed | The reader's flag and meaning carry the qualified scope sentence (`4813887a1e826dd1`), the evidence page was fixed (`751f3d4`), and the gate requires the qualification. | None. Optional: a gate check on the flag text; log bookkeeping. |
| new-12 | major | open | `scope.expected_outcome_stated_in_advance` maps gains to readings but ranks none of the four gain readings, whereas 0023 and 0024 each committed a forecast. | The author writes the forecast they hold before the freeze (a reviewer cannot supply it), with a pre-freeze check for it and the freeze and publication scripts quoting it. |
| new-13 | major | open | A reviewer's reconstruction, from an RFC index copy that is not banked, says the 2026-09-23 ledger entry understates 0024's RFC frame defect: five-digit entries and four-digit entries whose format annotation wraps were also dropped. `rfc_frame_correction` (in the protocol), `EXT_SOURCES3.md`, the pins' `frame_note` and the log repeat the 2026-09-23 account. | Bank the index under `docs/compliance/sources/` with a MANIFEST entry, or write COULD NOT VERIFY; file a ledger entry; fix the four restatements; reseal together with new-7. |
| new-14 | major | open | `evidence_page.py`'s `_rc3_ok` marks FOURTH_DOUBLING_RISES with a check and every other non-VOID reading with a cross, though the bar says no reading is a pass. The chip note says "the fourth doubling buys" for every reading and "0024's intervals exactly". | A neutral chip for every non-VOID reading; "rung 8 minus rung 7 is"; the cap note; (b): the "intervals exactly" words change. |
| new-15 | major | open | The 0025 panel says "(one corpus, one seed, no replicate of rung 8)", omits the per-family composition and the one-doubling sentence, never prints 0024's shift arm, drifts from `stop_rules[0]` and uses the short lead-cap note. Nothing checks the panel. | The six panel edits and a dry-run check on the rendered panel; (b): its two "intervals exactly" sentences change too. |
| new-16 | minor | open | The expected outcome says the one-doubling half-width was "0.0035 to 0.0036", but the sealed half-widths are 0.0035, 0.0034 and 0.0036. The log and `ROADMAP.md` copy the wrong range. | "0.0034 to 0.0036" in the prereg (next amendment, no reseal), the log and `ROADMAP.md`; optionally a pre-freeze guard. |
| new-17 | minor | open | Besides the null control, 0024's shift arm is reproduced after rung 8, so "every reproduction before any new plaintext is fitted" is false twice. (b) rewrites the same sentences. | (b): carry the timing correction in the amendment's new text and in `freeze_docs_0025.py` and `publish_0025.py`. |
| new-18 | minor | open | The reader publishes the less flattering of the measured and sensitivity readings (`06f81a2`). The evidence page never states the sensitivity reading, and `publish_0025.py` asserts that the measured reading equals the published one, so a straddle would make publication refuse. Latent under the exact rule; reachable under (b). | (b), required before any run: a straddle sentence on the evidence page; `publish_0025.py` separates measured and published readings; dry-run cases in both directions. |
| new-19 | minor | open | The reader's docstring and meaning say nothing fitted shares "a byte, a kilobyte run" with anything scored. The runner measures chunk ids, source-chunk hashes and byte-identical rows, the run rule is narrower (new-8), and the scored files' own unscored chunks were never run-scanned. | Template wording to what is measured, then regenerate; the same in `EXT_SOURCES3.md`. |
| new-20 | minor | open | The prereg closed the floor gap (amendment [1]). Its 24.6 s per iteration is not derivable from the banked per-iteration ratios (COULD NOT VERIFY where its factor came from), and the log's cost and `ROADMAP.md`'s cost lines are stale. | State the factor in the prereg's cost sentence (no reseal); the log's cost re-sync; `ROADMAP.md`'s cost lines. |
| new-21 | minor | open | The pins, the log and `why_this_preregistration_exists` credit the doubling to new archives and RFCs, but all of c_src's and pe_bin's added plaintexts come from 0024's own archives, which were not run-checked against 0024's blob. | Reword the pins sentence (reseal its hash once, with new-7 and new-13), the prereg's why paragraph and the log; optionally `publish_0025.py`'s corpus words. |
| new-22 | minor | open | The same publication-path lead-cap defect as old-8, at four sites. The dry run's short string is not a substring of the sealed note. | Change the four sites together (old-8). |
| new-23 | minor | open | The key `scope.what_a_flat_or_falling_doubling_would_mean_for_the_record` files BELOW_RATE and NOT_RESOLVED under "flat". `stop_rules[5]`'s seed-stability threshold ("within 0.0005 of 0") differs from `design.seed_stability`'s ("one unit of the fourth decimal"). | Rename the key; restate `stop_rules[5]`'s tail; update the log and `make_englog_0025.py`. |

Commits after `35b6493`, through `b988afc`, move no status in the table, but they change these rows:

- `f44b63b` replaced "new files alone" in the runner's module docstring and in `prefreeze_0025.py`'s shift-arm label. These are two of the old-3 and new-2 sites; the runner's SHIFT8 comment and refusal, the reader's VOID text and the gate's `expect_clause` are unchanged.
- `388d0f1` reworked the evidence page's 0025 chip and panel:
  - The lead cap note is now taken from `bar.lead_rule`'s words. That fixes the evidence-page site of old-8 and new-22; `publish_0025.py` and `dryrun_publish_0025.py` still use the short form, and `publish_0025.py`'s edits to the page must be re-checked against the reworked panel.
  - Both readings are now stated on a straddle (new-18, part A), and the chip quotes the published point as "rung 8 minus rung 7" (part of new-14).
  - Still as found: `_rc3_ok`, "(one corpus, one seed", the drifted BELOW_RATE, NOT_RESOLVED and FALLS sentences, 0024's shift arm not printed and the per-family composition (old-11, new-14, new-15).
- `6c8b75b` and `b988afc` record in the engineering log the realfit3 rebuild and the second realfit2 rebuild (section 2). The remaining commits in the range edit `README.md`, `VERDICT.md`, `docs/DILIGENCE.md`, `docs/strategy/MILESTONES.md`, the outbound documents and tooling outside the 0025 instrument (`f44b63b` also edited `amend_cache_0025.py`'s docstring).
- No commit in that range touched the preregistration, the reader, its template or generator, or the gate.

## 5. Before any freeze under (b), in order

If the dispatch test recovers the banked bytes, steps 3 to 5 shrink to the findings' own edits and the realfit2 parts of step 8 fall away; the rest stands.

1. Record in `engineering_log_0025.json` (`container_2026_10_21`) the ISA-L dispatch test's result and the decision taken under the rule in 3.1; the second realfit2 rebuild and the realfit3 rebuild are already recorded (`b988afc`, `6c8b75b`). Under (b), put the chosen realfit2 build at `data/pivot/realfit2_c4096.npz`, with its manifest, and keep a copy, since another host will not rebuild it.
2. File the `CORRECTIONS.md` entries:
   - realfit2 rebuilt on two hosts with two different X arrays, neither of them 0024's. Claimed: DILIGENCE's "proven identical" rebuild (as it stood at `35b6493`), and 0025's and ROADMAP's exact-interval rule. Cause: COULD NOT VERIFY. Size: the weakening in 3(b).
   - The builder-cache row order, if it is not yet filed.
3. Write and commit the amendment script (next to `amend_prereg_0025_b.py`) before any further reproduction refit is run or read.
   - It makes every change in 3.2 and the conditions in 3.1 that belong in the file: which realfit2 is sealed, and how the recomputed rung-7 lead is published.
   - It also folds in the prereg text the open findings need, so the file is amended and resealed once: old-7, new-1, new-2, new-6, new-8, new-9, new-10, new-13, new-16, new-17, new-20, new-21, new-23, and new-12 once the author has written the forecast.
   - It reseals `ext_source_pins3_sha256` once, for new-7, new-13 and new-21.
4. Edit the reader template (the exactness VOID, docstring, flags, meaning; old-3, old-12, new-19) and regenerate the reader with `gen_reader_0025.py`.
5. Runner: remove the exact-interval NOT RUN block, and apply old-3/new-2, old-6 and new-9.
6. Corpus builder: new-1 (the `--disjoint` line and the informational frame scan) and new-5 (the 0024 blob check).
7. Builder cache: build, `reorder_cache.py`, `cache_content_proof.py`, `amend_cache_0025.py`, with the machine alone.
8. `prefreeze_0025.py`: replace the realfit2 and realfit3 `--check` IDENTICAL requirements and the `nested_on` equality with checks against the resealed hash, 0024's kept beside it.
9. Gate `realcurve3_4096`: the control and exactness cases for (b), and old-12, old-13 and new-18's cases.
10. Publication path:
    - Fix `publish_0025.py`, `dryrun_publish_0025.py`, `freeze_docs_0025.py` and `evidence_page.py` for old-8/new-22, old-11, new-14, new-15, new-18 and the (b) sentences, then get the dry run to ALL PASS.
    - Update `ROADMAP.md` R1's validity line and its half-width and cost lines (new-16, new-20).
    - `stop_rules[0]` and `[4]` quote 0024's published sentences word for word, and the honesty pass applied on 2026-10-22
      reworded three of the sites they name (`VERDICT.md` "keep raising the recipe's accuracy" and "holds on these real files,
      in distribution", `docs/DILIGENCE.md` "the record's scaling thesis holds"). `publish_0025.py` now anchors on the current
      wording and prints a NOTE at each such site; the amendment should name the sites, not their words.
11. Engineering log: regenerate or re-sync `cost`, `the_floors`, the design decisions and the review lists (old-1, old-4, old-7, new-20, and the bookkeeping rows).
12. Runner smoke on the amended runner, then the fixture recapture, the full mutation suite and the counts. Bank `prefreeze_0025.py` PASS to `artifacts/verification/prefreeze_0025.json`, and only then run `freeze_0025.sh`.
