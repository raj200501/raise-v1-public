# Roadmap (checked): from the record as it stands to the evidence an FDM-1 programme would need

Checked version of the draft of 2026-10-21, for the founders. It is not outbound copy. Every number in it was traced to the artifact it cites, and the file passes `tools/claimcheck.py` (run on this copy, outside `outbound/`). The changes from the draft and their reasons are listed in `docs/strategy/ROADMAP_changes.md`.

Conventions:

- Every number is a banked number at the precision it is banked, with its artifact beside it. Where a figure's only home is a preregistration file, which is not under `artifacts/`, the text says so.
- **EXTRAPOLATION** marks a projection and states its basis on the same line.
- **COULD NOT VERIFY** marks anything no artifact holds.
- Preregistration ids are assigned by the chain at freeze. The items below are called R1 to R6 only in this plan.
- FDM-1 is used here only as the company's name for a model. The record holds no FDM-1 model, and nothing here says what one could do. The record itself uses the term for the structure of an outside result and for "the FDM-1 question", quality against the volume of manufactured labels (`VERDICT.md`; `prereg/0023-realcurve-4096.json`).
- Every reading cited is at a 4096-byte carve, over 26 DEFLATE configurations, with chance at 0.038462. The exceptions are 0009 and 0010, which were byte models at 1024 bytes, and the window-size verdicts named in section 3.
- "The boosted model" or M4 means 0021's fixed model recipe, the searched model of 0014. 0015 and 0016 read 0003's recipe, which is named as such.

---

## 1. Where the record stands

1. **What holds.** On real content, the boosted model's accuracy on the 38452 scored real-family rows rises from 0.0974 at 130 plaintexts to 0.1404 at 8232. Its second-decade slope is 0.00697 per doubling (scored-chunk interval [0.00571, 0.00824]) against the record's 0.005 rate (`artifacts/pivot/realcurve2_4096_verdict.json`, `SECOND_DECADE_RISES_MODEL_LEADS`). It is not a transfer reading: every rung holds the scored files' own unscored chunks, and the plaintexts above 1029 are other files of the same five families.
2. **What holds, narrowly.** At 8232 plaintexts the model leads the standardised linear rule by 0.0039, paired interval [0.0001, 0.0077], one unit of the fourth decimal above 0 (same artifact; `artifacts/pivot/engineering_log_0025.json`). The linear rule itself rises 0.00638 per doubling over the same decade. The model's slope minus the linear rule's is 0.00059, with a paired interval of [-0.00102, 0.00231]: not resolved, and never read as equal (same artifact). Over the first decade the linear rule rose faster than the model, 0.009551 against 0.007344 per doubling, with a paired difference interval of [-0.003707, -0.000752] (`artifacts/pivot/realcurve_4096_verdict.json`, `REAL_CURVE_RISES`).
3. **What does not hold.** Every preregistered transfer verdict but one fails its bar. The exception is item 5.
   - With one builder family held out, 0003's recipe reads 0.0859 against 0.088462 (`artifacts/pivot/lofo_4096_verdict.json`, `TRANSFER_FAILS`).
   - On the same folds, 0014's searched linear rule reads 0.0951. It leads 0003's recipe by 0.0092, under the 0.02 its bar asked (`artifacts/pivot/lofo_l3_4096_verdict.json`, `L3_LEAD_BELOW_BAR`).
   - Fitted on the builder and scored on five real families, M4 reads 0.0637 against 0.088462 (`artifacts/pivot/oob_4096_reread_verdict.json`, `OOB_TRANSFER_FAILS`). 0018's own reading of that run was VOID.
4. **More data of one kind has moved readings of unseen content little, and none of those readings is a verdict.**
   - Seeing seven times more of one builder family (700 to 4900 chunks) moved 0003's recipe's held-out mixture by -0.002 (`artifacts/pivot/fdc_4096_verdict.json`, 0016's depth arm, informational).
   - More real plaintexts moved the real-fitted model's reading on the builder's evaluation set by 0.000222 per doubling over 0023's rungs (130 to 1029 plaintexts; `realcurve_4096_verdict.json`). Over 0024's second decade they moved it by 0.00231 per doubling, below the rate (`realcurve2_4096_verdict.json`).
   - These reverse readings are informational, and not all of them are flat. The depth-3 tree's reading on the builder's evaluation set rose 0.009842 per doubling over 0023's rungs (`realcurve_4096_verdict.json`). The model's reading on the extension corpus's three synthetic families (hexdump, sql, xml), which no real-fit corpus contains, went from 0.0693 at 1029 plaintexts to 0.0987 at 8232 (`realcurve2_4096_verdict.json`, `ext_subsets`). None of these is a verdict, and none is quotable as a pass.
5. **The one passing transfer verdict is narrow.** At a fixed budget of 4900 source chunks, the number of builder families seen moves 0003's recipe on an unseen family by 0.00596 per doubling of families, against 0.005. Its seven-family point, 0.0829, is still under 0015's bar, and the linear rules' curves were steeper, at 0.007267 and 0.008019 per doubling (informational) (`artifacts/pivot/fdc_4096_verdict.json`, `DIVERSITY_HELPS`).
6. **In flight.** 0025 adds one doubling: rung 8, at twice 8232 plaintexts and 421015 rows. The row count is restated in `engineering_log_0025.json`. The preregistration's plaintext count for rung 8 is in no artifact (COULD NOT VERIFY as banked), and neither is its figure for the span in decades (COULD NOT VERIFY).
   - 0025 is not frozen (`prereg/0025-realcurve3-4096.json`, `frozen: false`).
   - Its pre-freeze review found one blocking defect, which the log records as fixed.
   - The log's list of steps still open before the freeze has five entries. The log's own record of the 2026-10-21 container says the preregistration was amended by script and the reader regenerated, and the latest commit applied the review's reader-wording findings. The list has not been updated since, so how many steps remain is COULD NOT VERIFY from the artifacts (`artifacts/pivot/engineering_log_0025.json`).

---

## 2. Next preregistrations, in order

**The machine.** The record's banked runs used one machine at a time.
- At 0024's launch it had 4 cores, no GPU, 15.66 GB available and 3.82 GB of free disk, with its memory cgroup banked as unlimited (`artifacts/pivot/realcurve2_4096.json`, `launch_environment`). 0025's pre-freeze review says the launch check does not resolve the process's own cgroup, and puts that real limit at about 14.35 GB (`engineering_log_0025.json`).
- On 2026-10-21 the work moved to a fresh container with nothing under `data/` (`engineering_log_0025.json`, `container_2026_10_21`). Its launch environment is not banked (COULD NOT VERIFY).
- 0018's runner refuses to launch beside any other `tools/pivot` runner (prereg 0018 `scope.cost`). 0025's runner also refuses beside a corpus builder or the mutation suite (`engineering_log_0025.json`). The runners for R2 and R4 to R6 do not exist yet.

So the items that use this machine run one after another.

**Why this order.** R1 is in flight. R2 is small, and it sets the cost fields the later runs need. R3 runs on someone else's machine, beside R4. R4 is the question the thesis turns on, and it needs no new sources. R5 needs new sources, which can be gathered while R4 runs. R6 is the largest build, and it needs R2 and R4.

| Item | Uses this machine | Needs first |
|---|---|---|
| R1. Finish 0025 | yes | the open pre-freeze steps; 0024's and 0025's fit corpora and the builder cache rebuilt on this container and checked |
| R2. Cost beside quality | yes | R1 |
| R3. External verification | no | R1 published; the 2026-10-21 fetch fixes (committed on `main`) carried to the mirror |
| R4. Transfer-scaling curve | yes | R1, R2 |
| R5. Replicate: second seed, separate draw | yes | R1 read, R2; new pinned sources |
| R6. Byte-level model at equal compute | yes | R2, R4; a raw-byte corpus |

### R1. Finish 0025: the fourth doubling

- **Question.** Does one more exact doubling of other files of the same five families, from 8232 plaintexts to twice that (rung 8), still buy the model the record's rate on the files it is scored on? Is the boosted model still ahead of the linear rule at that rung? (`prereg/0025-realcurve3-4096.json`, `scope.why_this_preregistration_exists`)
- **Why it is next.**
  - The third fit corpus has been built: 218955 new rows from 8569 new plaintexts. It is pinned by array hash in the preregistration and in its banked manifest (`artifacts/pivot/realfit3_corpus_manifest.json`; `engineering_log_0025.json`, `corpus`).
  - Each new chunk was hashed against every chunk of the 0018 files and of 0024's corpus, and scanned for shared 1024-byte runs (prereg `scope.corpus_fit3`, `rival_explanations_run_as_arms`).
  - It was built on the previous container. On this one, the log records only 0018's extension corpus and 0021's fit corpus as rebuilt identical. 0024's and 0025's fit corpora and the builder cache, all named in the preregistration's run invocation, are not recorded as rebuilt (`engineering_log_0025.json`, `container_2026_10_21`; prereg `invocation.run`).
  - It would take the real-content span from 1.8016 decades (`artifacts/pivot/engineering_log_0024.json`) to the two decades 0003's rule asked for.
- **What remains before the freeze.** The log lists these (`engineering_log_0025.json`, `still_open_before_the_freeze`):
  - regenerate the preregistration and the reader from the patched generator. The log's own container entry says the generator was lost, and that the preregistration was amended by a script of asserted replacements and the reader regenerated instead (prereg `amendments_before_freeze`);
  - re-run the runner smoke;
  - run the two review lenses that did not complete, and a skeptic pass;
  - adjudicate the remaining findings. The latest commit applied the cap, scope-rule and floors wording. The cost-sum finding is still open: the preregistration still states 11963 to 15511 s;
  - run the full mutation suite and `tools/prereg_checks/prefreeze_0025.py`. The log puts the suite at 963 cases, written before the latest commit added cases to 0025's gate. The last banked full run, `artifacts/verification/mutation_report.json`, has 801.

  Not on the log's list: rebuild 0024's and 0025's fit corpora and the builder cache on this container, and check each against its banked manifest. The 2026-10-21 correction says every corpus rebuilt on this container is checked against its banked manifest before any preregistration uses it (`CORRECTIONS.md`).

  Then freeze, run, read and publish.
- **Clause that can fail.** The verdict is read on rung 8 minus rung 7 for the model, with a paired cluster-bootstrap interval over the 1488 scored real chunks. That interval does not cover the draw of rung 8's plaintexts or the fit side.
  - `FOURTH_DOUBLING_RISES` needs a gain of at least 0.005 and an interval whose 2.5th percentile is above 0. Over one doubling, 0.005 is 192 rows of 38452.
  - Otherwise the reading is `BELOW_RATE`, `NOT_RESOLVED` or `FALLS`.
  - The lead suffix is read at rung 8 by 0024's rule: `MODEL_LEADS`, `LINEAR_LEADS` or `NO_SEPARATION`.
  - Validity: rungs 1 to 7 must reproduce 0024's readings (rung 7 within 0.0005), and 0024's intervals must recompute exactly. Otherwise the run is NOT RUN or VOID.
  - Expectation stated in advance (prereg `scope.expected_outcome_stated_in_advance`; `engineering_log_0025.json`, `expected_outcome`):
    - the paired half-width of a one-doubling gain on 0024's vectors was 0.0035 to 0.0036, so a gain below about 0.0035 would read `NOT_RESOLVED`;
    - `NO_SEPARATION` is at least as likely as `MODEL_LEADS`.
- **What each outcome would mean for the FDM-1 thesis.**
  - `RISES` with `MODEL_LEADS`: the fourth doubling of other files of the same five families bought at least the record's rate on the original files, and the boosted recipe was still ahead of the linear rule at rung 8. It is one doubling, not a slope. It is not a transfer reading, and it says nothing about content of a kind the model has never seen.
  - `RISES` with `NO_SEPARATION`: more files still bought the rate, but the scored chunks do not resolve whether the boosted recipe is ahead of a hand-writable rule, which is never read as equal.
  - `RISES` with `LINEAR_LEADS`: the hand-writable rule is ahead.
  - Either of those two bounds 0024's `MODEL_LEADS` to 8232 plaintexts and weakens the case for a larger learned model.
  - `BELOW_RATE` ("a rise below the record's rate") or `NOT_RESOLVED` ("whether the fourth doubling bought anything is not resolved by the scored chunks at this size"): 0024's sentence that other files of the same kinds keep buying the recipe the record's rate is bounded to 8232 plaintexts.
  - `FALLS`: adding the fourth doubling's files of the same kinds lowered the model's reading on the original files. As a plan, that closes the more-files-of-the-same-kinds route at this scale.
  - A gain or lead read with the model at its iteration cap at rung 7 or 8 is published with that cap named in the same sentence.
  - VOID: nothing is counted. The run may be resumed from its checkpoints under the identical invocation, and it is never re-parameterised.
  - NOT RUN: filed as `artifacts/pivot/realcurve3_4096_not_run.json`. Nothing is re-scoped to fewer rungs, a smaller doubling or a lower bar.
- **Rough cost.**
  - Fits were estimated in advance at 11963 to 15511 s (3.3 to 4.3 hours). Rung 8's model fit is one uncheckpointable stretch of up to 7675 s (`engineering_log_0025.json`, `cost`; prereg `scope.cost`).
  - An unadjudicated review finding says the components sum to 11903 to 15451 s (`engineering_log_0025.json`).
  - Not in that estimate: rebuilding the corpora on this container. Their original builds banked 3415.5 s for the builder corpus (`artifacts/pivot/deflate_curve.json`), and 452.2 s and 625.7 s for 0024's and 0025's fit corpora (their manifests).
  - Memory: the log's `cost.memory` estimate is about 9.0 GB. The pre-freeze review put the peak at about 10.2 GB, at rung 8's tree fits. The amended preregistration (unfrozen) now states that peak, keeps the 13.0 GB kill threshold and requires 11.0 GB available at launch (prereg `amendments_before_freeze`, `scope.cost.memory`; the figures are banked in `engineering_log_0025.json`).
  - The last runner smoke took 2867.9 s wall, on scratchpad corpora.
  - The model's iteration count is projected at 177 to 248, against a cap of 250. A capped fit is named beside every reading.
  - COULD NOT VERIFY until run.
- **Depends on.** No earlier item. The corpora must be rebuilt on this container first.

### R2. Cost beside quality

- **Question.** What does each recipe cost to train, and to run per prediction, on this machine? Does the boosted model's lead over the linear rule survive when both are held to the same cost per prediction?
- **Why it is next.**
  - `docs/OPERATING_RULES.md` §7 asks for cost beside every score.
  - The record banks seconds per fit. It banks no time per prediction for any recipe of the 0003-to-0025 line, and no dollar figure. A search of the artifacts found none, and `docs/strategy/MILESTONES.md` says the same about dollars.
  - The only per-item timing found is phase 0's brute-force recompression with the plaintext in hand: 24 ms per stream over 36 candidates, on 2 streams (`artifacts/phase0/round1_domain_search.json`). That is a different method in a different setting.
  - What is banked already shows the question. At 8232 plaintexts the model's fit took 2352.6 s and read 0.1404. The linear rule's fit took 371.6 s and read 0.1365. The depth-3 tree's fit took 35.2 s and read 0.0919 (`artifacts/pivot/realcurve2_4096.json`, `cost.seconds_by_name`; `realcurve2_4096_verdict.json`).
  - It is small, and R4 to R6 need its timing fields and its definition of equal compute.
- **Clause that can fail.**
  - (a) Validity: every role banks its fit seconds, scoring seconds per row, featurisation seconds per fragment and peak memory. A missing field is VOID.
  - (b) The model is cut to the largest number of boosting iterations whose measured cost per prediction, carving and featurisation included, does not exceed the linear rule's. Its top-rung lead is then read by 0024's paired rule. `MODEL_LEADS` at equal cost needs the interval entirely above 0. If no cut of the model fits inside the linear rule's cost, that is named as the reading.
- **What each outcome would mean for the FDM-1 thesis.**
  - `MODEL_LEADS` at equal cost: at this scale, the boosted edge is not bought only with prediction-time compute. It says nothing about what a larger model would do.
  - `NO_SEPARATION` (not resolved, never read as equal), `LINEAR_LEADS`, or no cut that fits: the record would hold no evidence that the boosted model leads per unit of prediction cost on this machine. The hand-writable rule is then the reference, and any FDM-1 plan must beat that rule on cost as well as on accuracy.
- **Rough cost.**
  - It refits at the top rung: 2352.6 s, 371.6 s and 35.2 s banked at 0024's rung 7, or R1's measured seconds at rung 8.
  - It also times scoring on the 321409-row scoring set, which has no banked time (COULD NOT VERIFY).
  - Memory: EXTRAPOLATION, at most R1's peak at the same rung. Basis: the same fits on the same rows.
- **Depends on.** R1 finished (one runner at a time). If R1 completes, the top rung is 0025's rung 8. Otherwise it is 0024's rung 7.

### R3. External verification

- **Question.** Does a third party, on a cold clone of the public mirror (https://github.com/raj200501/raise-v1-public), get every gate passing and every banked verdict re-emitted?
- **Why it is next.**
  - It uses no time on this machine, so it can run beside R4.
  - The coverage map files 233 of its 283 claims as primary-verifiable: a stranger can re-derive them with the shipped code. Sources: `VERDICT.md`, Verification coverage; `artifacts/verification/coverage.json`, where 283 is `n_claims` and 233 is the count of entries classed primary-verifiable, a count no field stores.
  - The record names no stranger who has done so. Its own closing list says most of its findings rest on subagent measurements that have not been independently reproduced.
  - On 2026-10-21 a cold container could not rebuild the corpora that 0018 to 0025 rest on. One fetch script had never worked on a cold machine, and two Gutenberg books had been re-edited upstream (`CORRECTIONS.md`, entry of 2026-10-21).
  - The fix was tested only on the record's own fresh container, where 0018's extension corpus and 0021's fit corpus rebuilt identical (`engineering_log_0025.json`). No one else has tested the new rebuild path.
- **Clause that can fail.** The mirror commit and the verdict string each frozen reader must print are frozen before the verifier runs.
  - Tier 1: `bash tools/gates.sh` exits 0, `python3 tools/prereg.py verify` passes, and every reader prints its listed verdict.
  - Tier 2: the documented fetches pass their pin checks, and every rebuilt corpus reads IDENTICAL against its banked manifest.
  - Any mismatch is a fail. The verifier signs a statement that names the commit, the commands and the outputs.
- **What each outcome would mean for the FDM-1 thesis.**
  - Pass: someone other than the founders has checked the chain order, the reader hashes, the number tracing, the readers' arithmetic on the banked artifacts and the corpus rebuilds. R3 does not re-run the fits, so the banked measurements still rest on the record's own runs. Nothing about FDM-1's capability follows.
  - Fail: outbound use of the record stops until the cause is found and filed in `CORRECTIONS.md` at full size.
- **Rough cost.** It runs on the verifier's machine. The gates' run time is not banked (COULD NOT VERIFY). Tier 2 rebuild times are banked from the original builds:
  - 3415.5 s for the builder corpus (`artifacts/pivot/deflate_curve.json`);
  - 216.1 s for the extension corpus (`ext_corpus_manifest.json`);
  - 83.9 s, 452.2 s and 625.7 s for the three real-content fit corpora (their manifests). 0021's took 163.0 s on the 2026-10-21 container (`engineering_log_0025.json`).

  Fetch time is not banked.
- **Depends on.**
  - R1 published, so that the signed run covers chain entry 25.
  - The fetch-script fixes described in the 2026-10-21 correction are committed on `main`. They were committed before the draft of this plan was saved. Whether the mirror carries them, and whether it is current with `main`: COULD NOT VERIFY.
  - The Gutenberg fallback depends on a third-party repository that can be deleted. The same correction says so.

### R4. Transfer-scaling curve on unseen real families

- **Question.** Does more real data of seen families buy identification on a real family the model has never seen?
- **Why it is next.**
  - This is the question the FDM-1 thesis turns on, and the record has never asked it as a preregistered question with real data on both sides.
  - 0015 to 0017 stay inside the builder. 0018 fits on builder content and scores real files. 0021 to 0025 fit and score the same five real families.
  - The record's readings of real-fitted models on content they did not contain are informational, not verdicts. They are on the builder's evaluation set and on the extension corpus's three synthetic families.
    - The model's reverse slope on the builder's evaluation set is 0.000222 per doubling over 0023's rungs and 0.00231 over 0024's second decade, below the rate (`realcurve_4096_verdict.json`, `realcurve2_4096_verdict.json`).
    - The depth-3 tree's reverse slope over 0023's rungs is 0.009842.
    - The model's synthetic-family reading went from 0.0693 to 0.0987 over 0024's second decade.
    - None is on a real family, and none is quotable as a pass.
  - It needs no new sources, because the three real-content fit corpora hold the data. On this container two of them must first be rebuilt (see R1).
- **Design.**
  - Hold out each of the five real families (c_src, pe_bin, py_src, rfc_txt, rst_doc) in turn.
  - Fit 0021's three fixed recipes on nested doublings of the other four families' plaintexts. Exclude every file of the held-out family.
  - Score once on the held-out family's rows of the 38452, and stitch the five readings at each rung into one mixture.
  - One hazard is already banked. py_src is 17197 of 0021's 26346 fit rows and 126104 of 0024's 193926 (`realfit_4096_rerun_verdict.json`; `realcurve2_4096_verdict.json`, `fit2_rows_per_family`), so the py_src fold trains on far less. Per-fold readings are banked beside the mixture.
- **Clause that can fail.** The stitched mixture's slope must be at least 0.005 per doubling of plaintexts, with the scored-chunk interval's lower bound above 0. This is the bar 0023 and 0024 used.
  - Flags: the top-rung mixture against chance + 0.05 (0.088462, the bar of 0015 and 0018), and against floor + 0.05 (`OPERATING_RULES` §4a).
  - The record's own prior is a flat reading. 0016's depth arm moved -0.002. 0025's preregistration (unfrozen) states the expectation that "every reading the record has of content the model did not see is flat (0015, 0018/0019)" (`engineering_log_0025.json`, `expected_outcome`).
- **What each outcome would mean for the FDM-1 thesis.**
  - Rises at the rate: the first preregistered measurement in the record that real data volume buys identification on a real content kind the model never saw.
  - Below the rate, or not resolved: the record would hold no preregistered evidence that real data volume buys identification on an unseen real family at this scale. An FDM-1 programme would then have to plan on covering each content kind it is meant to identify, not on volume alone.
- **Rough cost.**
  - EXTRAPOLATION: there are five folds per rung, and each fold is smaller than the full rung. A curve to 8232 plaintexts is therefore about five times 0024's 5950.5 s of fits, or less.
  - Basis: fit time grew with rows in 0024, whose model fits took 478.1 s, 1141.1 s and 2352.6 s at rungs 5 to 7. Iteration counts can differ by fold, so this is not a bound.
  - A top rung at rung 8's count adds R1's measured seconds per fold.
  - Memory: EXTRAPOLATION, at most R1's peak. Basis: no fold is larger than the full rung.
- **Depends on.** R1 (the machine, its corpus and its reading) and R2's timing fields.

### R5. Replicate with a second seed and a separately drawn corpus

- **Question.** Do the second-decade rise and the top-rung lead come back when the added plaintexts are a second, separately drawn set of other files of the same five families, under a second seed?
- **Why it is next.**
  - The fit-side variance of the second decade is unmeasured (`prereg/0024-realcurve2-4096.json`, `what_this_does_not_cover`). 0025 declined a second seed for its top rung because it "doubles the fourth doubling's fits on a 15 GB machine" (`engineering_log_0025.json`).
  - The only fit-side replicate in the real-content thread is 0023's smallest rung. It moved the model by 0.001 and the tree by 0.0084 (`realcurve_4096_verdict.json`).
  - The lead's lower bound at 8232 plaintexts is 0.0001.
  - The builder curve has seed replicates: three full-pipeline runs, with a slope spread of 0.0014 (`artifacts/pivot/seed_robustness.json`). The real curve has none.
  - It follows R4 because it needs new sources, which can be fetched and pinned while R4 runs.
- **Design.**
  - Pin new archives and RFCs that 0018, 0024 and 0025 did not pin, and file their licences. Hash every chunk against every chunk and every kilobyte run of all earlier sources.
  - Use a second seed for the pool permutation and the row order.
  - Rungs 1 to 4 stay 0021's block, which is the scored files' own unscored chunks. Re-nest them under the second seed, as 0023 did for rung 1.
  - Rungs 5 to 7 come from the new draw. Use 0021's three recipes, scored on the same 38452 rows.
- **Clause that can fail.** Two parts, both named in the verdict.
  - The replicate's second-decade slope is at least 0.005, with the interval's lower bound above 0 (0024's clause).
  - Its top-rung lead, read by 0024's paired rule, gives the same reading as 0024 (`MODEL_LEADS`), or as 0025 if R1 changes it.
  - The replicate-minus-original difference per rung is banked as a flag.
- **What each outcome would mean for the FDM-1 thesis.**
  - Both reproduce: the real-content rise and the boosted edge are not properties of one draw of files.
  - The slope reproduces and the lead does not: more files still help, but the boosted model's edge over the linear rule is not shown to survive a second draw, and `MODEL_LEADS` is bounded to 0024's draw.
  - The slope does not reproduce: the record's only rising real-content curve is not shown to hold beyond the files 0024 drew, and scaling the same design further is not justified.
- **Rough cost.**
  - Fetching, pinning and licence work have no banked time.
  - Corpus builds were banked at 452.2 s (0024) and 625.7 s (0025).
  - Fits: EXTRAPOLATION, about 0024's 5950.5 s of fits (6456.7 s wall). Basis: the same rungs and recipes.
  - Disk: 0024 launched with 3.82 GB free. 0025's third corpus is 218955 × 1108 float32, about 0.97 GB (`engineering_log_0025.json`). Free disk now: COULD NOT VERIFY.
  - Source headroom: 0025's preregistration states its unused candidates per family (`scope.corpus_fit3.headroom_per_family`). Whether a full separate draw fits inside them: COULD NOT VERIFY until the builder runs.
- **Depends on.** R1's reading, which sets the lead the replicate must match and whether rung 8 is in scope. R2's timing fields. It does not depend on R4's result.

### R6. A learned byte-level model against the boosted recipe at equal compute

- **Question.** Given the same fit seconds on this machine, does a model that learns from the raw carved bytes beat 0021's boosted recipe on the real-content rows? Does it beat it on R4's unseen-family folds?
- **Why it is next.**
  - The record says a model that works at 1024 bytes would need a different kind of representation, one that learns from the raw bit sequence rather than from summary statistics over it, and that this is not started (`VERDICT.md`, the byte-model sections under L4).
  - The two byte models it did try were both at 1024 bytes on the builder corpus, and neither beat the hand-engineered feature model:
    - 0009's CNN (182842 parameters) read 0.0849, against the hand-engineered model's 0.1165 and a byte-histogram logistic's 0.0943 (`artifacts/pivot/byte_model_verdict.json`, `BYTE_MODEL_FAILS`).
    - 0010's flatten head (392506 parameters) read 0.0385, which is chance. Its null control never became failable (0.0393 against a 0.30 bar), so the reader named it inconclusive (`artifacts/pivot/byte_model_flat_verdict.json`, `BYTE_FLAT_FAILS`).
  - `VERDICT.md` draws the lesson that a fair test needs a recipe search per head, not a shared recipe.
  - The comparator's recipe has been searched once on real content. 0022's budgeted search on 26346 rows moved the boosted model by -0.0004, an informational reading under a verdict of `REAL_RECIPE_FAILS` (`realsearch_4096_verdict.json`).
  - It comes last because it needs R2's definition of equal compute and R4's folds, and because it is the largest build. The record holds raw bytes only for the builder corpus at 1024 bytes (`raw_c1024.npz`, 650000 × 1024, `artifacts/pivot/corpus_manifest.json`). It has none for real content at 4096.
- **Clause that can fail.**
  - Run a symmetric recipe search per head, using the protocol of 0014 and 0022: a roster per head, a chunk-rule holdout, and one confirmatory fit. Every candidate is held to M4's fit seconds at the chosen rung.
  - 0010's failable-null clause carries over: the null must reach 0.30 train accuracy on shuffled labels before a clean control counts.
  - Read byte model minus M4 on the 38452 rows by the paired-interval rule. `BYTE_LEADS` only if the interval is entirely above 0.
  - Read the same comparison on R4's folds. Floor + 0.05 (§4a) is a flag.
- **What each outcome would mean for the FDM-1 thesis.**
  - `BYTE_LEADS`: the first case in the record of a learned representation beating the hand-engineered recipe at equal compute. That is a precondition the record would need before spending on a larger learned model. It does not say what a larger model would do.
  - `NO_SEPARATION`: whether learning from raw bytes buys anything over the 1108 hand-engineered features is not resolved at this compute. It is never read as equal.
  - The boosted model ahead: at this compute, learning from raw bytes does not beat the 1108 hand-engineered features. Any claim that a bigger model would do better stays unmeasured.
  - VOID on the null clause: inconclusive, as 0010 was.
- **Rough cost.**
  - Per candidate, the cost is fixed by design at M4's banked fit seconds at the rung (2352.6 s at 8232 plaintexts), times the roster size.
  - For scale: 0022's 35-candidate search on 26346 rows banked 1634.3 s of selection fits. 0009's whole round, at 1024 bytes on 100000 training rows, banked 3665.7 s.
  - The raw-byte real-content corpus must be built, and no build time for it is banked.
  - No GPU appears in any banked cost, so a GPU cost is COULD NOT VERIFY.
- **Depends on.** R2 (equal compute), R4 (the folds) and R1 (the machine).

---

## 3. What will never be claimed

- **No customer, user, partner or buyer until one exists.** The record claims none. `docs/OPERATING_RULES.md` §10 says "There are none at the time of writing", and `VERDICT.md` says "It has no customers, no users and no partners."
  - The verdict files of 0006 to 0024 each carry `establishes_a_buyer: false`. 0003's verdict file and the earlier ones carry no such field.
  - `VERDICT.md` notes that a self-reported `establishes_a_buyer: false` is evidence of intent rather than of fact.
  - G5, a named buyer type, is uncleared, and no item above can clear it (`README.md`; `VERDICT.md`).
- **No extrapolation beyond a measured rung.** This covers more plaintexts, more compute and a larger model alike. 0023, 0024 and 0025 each say that "no extrapolation beyond the top rung is quoted as anything".
- **No transfer claim from same-family numbers.** Every rung of the real-content curve holds the scored files' own unscored chunks.
  - 0021, 0022, 0023 and 0024 each bank `is_a_transfer_reading: false`, and 0025's stop rules forbid quoting any of its numbers as one.
  - 0024 calls itself "neither a transfer reading nor 0023's in-distribution reading".
  - A transfer claim can only come from a transfer reading, such as R4.
- **No claim that the real-content model clears the record's margin rule.** At 8232 plaintexts, 0.1404 does not clear the 0.1419 that 0021's rule asks over a depth-3 tree (informational, `realcurve2_4096_verdict.json`).
- **No claim that the real curve meets 0003's two-decade scope rule.** Even with 0025's doubling, that rule's one-corpus, one-seed terms are not met (0025 stop rules).
- **No claim at any other window size.** The task fails its own bar at 1024 and 2048 bytes (`CARVE_FAILS` under 0007 and 0011; `VERDICT.md`).
- **No claim about encoders outside the 26 configurations.** 7-Zip's deflate, Java's `Deflater`, Go's `flate`, and the Cloudflare and Windows zlib forks are not covered (`VERDICT.md`).
- **No FDM-1 capability claim.** The name is used, and nothing is said about what such a model does.
- **No softened reading.** `NOT_RESOLVED` is never written as "flat" or "equal". The gain part of a verdict is never quoted without the lead part (0025 stop rules). An informational reading is never quoted as a pass.

---

## 4. Decision points

| After | Outcome | Action |
|---|---|---|
| R1 | `FOURTH_DOUBLING_FALLS` | **Stop** buying more files of the same kinds as a plan. Add the forward pointer 0025's stop rules commit to, on 0023's "the record's scaling thesis holds on real files". **Redirect** to R4 and R6. |
| R1 | `BELOW_RATE` or `NOT_RESOLVED` | Bound 0024's sentence "other files of the same kinds keep buying the recipe the record's rate ... through 8232 plaintexts" to 8232 plaintexts. Do not plan a fifth doubling (see the machine ceiling below). |
| R1 | `LINEAR_LEADS` or `NO_SEPARATION` | Bound 0024's `MODEL_LEADS` to 8232 plaintexts. The case for a larger learned model then rests on R6 alone. |
| R1 | VOID | Resume from the checkpoints under the identical invocation, never re-parameterised. |
| R1 | NOT RUN | File it. Do not re-scope to fewer rungs, a smaller doubling or a lower bar. A defect found after the freeze becomes a new preregistration (the precedent of 0013, 0019 and 0021) and is never an edit. |
| Machine ceiling | any | A fifth doubling would need about 350 MB of Python source alone and a float64 block of about 7.5 GB on a 15 GB machine (`engineering_log_0025.json`; prereg 0025 `why_one_doubling_nested_on_0024s_pool`). Rungs above rung 8 are a hardware decision with no banked cost. |
| R2 | The model's lead does not survive equal cost | Treat the linear rule as the reference. R6 must beat it on cost, not only on accuracy. |
| R3 | Fail | **Stop** outbound use of the record until the cause is found, fixed and filed in `CORRECTIONS.md`. |
| R4 | Below the rate, or not resolved | **Stop** presenting data volume as a route to unseen content. **Redirect** to diversity of content kinds, the one axis whose preregistered transfer verdict passed (0016, on the builder's families and 0003's recipe), and to R6's transfer arm. |
| R4 and R6 | Neither shows a preregistered gain under transfer | **Stop** presenting any route from this record to a model that generalises across content kinds. What remains is a same-family result on real content, which is not a transfer reading, at one window size. |
| R5 | Slope does not reproduce | **Stop** scaling the same design. The second-decade rise is filed as not shown beyond 0024's draw. |
| R5 | Lead does not reproduce | Withdraw `MODEL_LEADS` from headline wording and bound it to 0024's draw. |
| R6 | Byte model does not lead at equal compute | **Stop** the learned-representation line at this compute. A larger compute budget is a separate decision with no banked evidence behind it. |
| R6 | `BYTE_LEADS` | **Redirect** the programme to learned representations, and re-run R4 and R5 with the byte model. |

Standing rules, from the record:

- No measurement here clears G5.
- "If a later round produces more argument and no measurement, that is a signal to stop, not to continue" (`VERDICT.md`).
- No sealed parameter, bar or rule changes after a freeze (0025 stop rules).

---

## Sources read

`VERDICT.md`, `README.md`, `outbound/EVIDENCE_BRIEF.md`, `docs/DILIGENCE.md`, `docs/OPERATING_RULES.md`, `CORRECTIONS.md`, `docs/strategy/MILESTONES.md`; `prereg/0015-lofo-4096.json`, `0016-fdc-4096.json`, `0018-oob-4096.json`, `0019-oob-4096-reread.json`, `0021-realfit-4096-rerun.json`, `0023-realcurve-4096.json`, `0024-realcurve2-4096.json`, `0025-realcurve3-4096.json`, `prereg/chain.jsonl` (24 entries); `artifacts/pivot/lofo_4096_verdict.json`, `fdc_4096_verdict.json`, `oob_4096_verdict.json` (VOID), `oob_4096_reread_verdict.json`, `realfit_4096_rerun_verdict.json`, `realcurve_4096_verdict.json`, `realcurve2_4096_verdict.json`, `realcurve2_4096.json`, `engineering_log_0025.json`, `byte_model_verdict.json`, `byte_model_flat_verdict.json`, `byte_model.json`, `seed_robustness.json`, `deflate_curve.json`, the corpus manifests; `artifacts/verification/mutation_report.json`, `coverage.json`; `tools/gates.sh`.

Added by the check: `prereg/0017-lofo-l3-4096.json` and `artifacts/pivot/lofo_l3_4096_verdict.json`; `artifacts/pivot/realsearch_4096_verdict.json`, `realsearch_4096.json`, `realsearch_4096_selection.json`; `artifacts/pivot/engineering_log_0024.json`; `artifacts/pivot/realfit3_corpus_manifest.json`; `artifacts/phase0/round1_domain_search.json`; every verdict file under `artifacts/` (for `establishes_a_buyer`); the preregistration's `amendments_before_freeze` and `invocation`; `tools/claimcheck.py`; the git history of 2026-10-21.
