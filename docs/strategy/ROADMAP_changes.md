# Changes from ROADMAP_draft.md to ROADMAP_checked.md

Method:
- Every number in the draft was extracted with `tools/claimcheck.py`'s own regex and mapped to the artifact fields that hold it. Each sentence that states a result was then checked against the artifact it cites, for the number, the direction and the reading (preregistration and verdict string).
- `claimcheck` on the draft: FAIL, 3 unbacked (2.1026, three times). On the checked copy: PASS.
- The claimcheck rule is necessary, not sufficient. It also accepts ×100 and ÷100 matches and coincidences, so two draft numbers that passed it (16464 and 233) are backed only by unrelated values. See items 11 and 32.

Each entry gives where the change is, what changed, and why, with the evidence.

## Header and conventions

1. **Status line.** "Has not been through claimcheck" is now "passes claimcheck on this copy". The file was checked: exit 0.
2. **New convention:** figures whose only home is a preregistration file are flagged. Many draft figures cite `prereg/0025-realcurve3-4096.json`, which is not under `artifacts/`. Where the same figure is banked (mostly in `artifacts/pivot/engineering_log_0025.json`), that artifact is now cited too.
3. **FDM-1 convention.** Dropped "a foundation-scale model of this signal". FDM-1 is now used only as the company's name for a model, with a note on how the record itself uses the term.
   - Why: "foundation-scale" and "of this signal" describe a model no artifact holds.
   - The record uses "FDM-1" for the structure of an outside result and for "the FDM-1 question", quality against manufactured-label volume (`VERDICT.md` lines 10 and 152; `prereg/0023`; `prereg/0004`: "FDM-1 was timing plus capability").
4. **"Everything is at a 4096-byte carve"** now names its exceptions. 0009 and 0010 were byte models at 1024 bytes (`byte_model_verdict.json` and `byte_model_flat_verdict.json`, `read.carve_bytes` 1024). Section 3 also cites the 1024 and 2048 verdicts.
5. **Added a recipe-naming convention.** The draft calls two different recipes "the model".
   - 0015's 0.0859 and 0016's curve are 0003's recipe (M1): `lofo_4096_verdict.json` `meaning`; `fdc_4096_verdict.json` `bar_applied.verdict_is_about` = "0003's M1 recipe".
   - 0019's 0.0637 and 0021 to 0025 are M4, 0014's searched model (`prereg/0021`: "0014's searched model M4, 0003's incumbent M1").

## Section 1

6. **Item 1.** "38452 held-out real-family rows" is now "scored", and a not-a-transfer-reading sentence is added.
   - `realcurve2_4096_verdict.json` banks `is_a_transfer_reading: false`.
   - Every rung holds the scored files' own unscored chunks. "Held-out" invites a transfer reading.
7. **Item 2.** Added three things:
   - the paired slope difference, model minus linear rule, 0.00059 [-0.00102, 0.00231], which is not resolved and never read as equal (`realcurve2_4096_verdict.json` `flags`);
   - the first-decade reading, in which the linear rule rose faster: 0.009551 against 0.007344, paired [-0.003707, -0.000752] (`realcurve_4096_verdict.json`, "the linear rule buys more per doubling");
   - "one unit of the fourth decimal above 0" (`engineering_log_0025.json`).

   Why: without these, the section reads more favourably for the boosted recipe than its readings.
8. **Item 3.** "Every reading of content the model was not fitted on fails its bar" is now "Every preregistered transfer verdict but one fails its bar".
   - It was false as written. The draft's own item 5 is a passing verdict (`DIVERSITY_HELPS`), and the informational reverse readings carry no bar and are not all flat (item 9).
   - 0015's reading is now attributed to 0003's recipe, and 0019's to M4.
   - Added 0017, which the draft never stated: `L3_LEAD_BELOW_BAR`, the searched linear rule at 0.0951 with a lead of 0.0092 against a bar of 0.02 (`lofo_l3_4096_verdict.json`).
   - Noted that 0018's own run was VOID.
9. **Item 4.** "More data does not move those readings" is rewritten.
   - The draft cited only 0023's 0.000222. 0024's second-decade reverse slope was 0.00231 (`realcurve2_4096_verdict.json` `curves.model.builder_eval_slope_per_doubling_second_decade`).
   - 0023's depth-3 tree reverse slope was 0.009842 (`realcurve_4096_verdict.json`).
   - The model's reading on the extension corpus's synthetic families, which no real-fit corpus contains, went from 0.0693 at rung 4 to 0.0987 at rung 7 (`realcurve2_4096_verdict.json` `ext_subsets.r4_model` and `.r7_model`).
   - All of these are informational and are labelled so.
   - The -0.002 is now stated as 0003's recipe over 700 to 4900 chunks of one family. That is the definition of `row_effect_within_family` in `prereg/0016`, and the reading is informational.
10. **Item 5.** The heading "the number of builder families seen does move transfer" is now scoped to 0003's recipe at a fixed budget of 4900 chunks. The linear rules' steeper curves (0.007267, 0.008019, informational) are added (`fdc_4096_verdict.json`; `VERDICT.md`: "the linear rules' curves are steeper").
11. **Item 6.**
    - **2.1026 removed.** No artifact holds it; it is only in `prereg/0025`. This was claimcheck's only failure.
    - **16464 replaced** with "twice 8232" or "rung 8", and marked COULD NOT VERIFY as banked. No artifact holds it as a plaintext count; claimcheck passes it only because unrelated `eval_chunk_ids` in the `*_scores.json` files equal 16464.
    - 421015 is kept: it is banked in `engineering_log_0025.json` (review finding text).
12. **Item 6, "five steps remain before the freeze".** Rewritten as COULD NOT VERIFY how many remain. The log's list has five entries but is stale:
    - Its own `container_2026_10_21` entry says the generator was lost, the preregistration was amended by script and the reader was regenerated. The first listed step's route, "from the patched generator", is impossible.
    - The latest commit, at 20:47 on 2026-10-21 (after the log's last change at 20:39), applied the cap, scope-rule and floors wording findings. The log was not updated.

## Section 2: the machine, the order and the table

13. **"The record's one machine. It has 4 cores and no GPU"** is now stated as banked at 0024's launch, with two additions:
    - the work moved to a fresh container on 2026-10-21, whose launch environment is not banked (`engineering_log_0025.json` `container_2026_10_21`);
    - the review says the launch check does not resolve the process's own cgroup, and puts the real limit at about 14.35 GB, while 0024's launch banked the limit as "unlimited".
14. **"Each runner refuses to launch beside another runner, a corpus builder or the mutation suite"** was an overgeneralisation.
    - 0018's runner refuses only beside other `tools/pivot` runners (`prereg/0018` `scope.cost`).
    - Only 0025's runner adds corpus builders and the mutation suite (`engineering_log_0025.json` `applied_before_the_freeze.launch_memory`).
    - The runners for R2 and R4 to R6 do not exist.
15. **"Why this order".** R4 "needs no new data" is now "no new sources", because two of its corpora must be rebuilt on this container.
16. **Table.**
    - R1's "Needs first" adds the corpora rebuild (item 18).
    - R3's "fetch fixes committed and mirrored" is now "committed on `main`, carried to the mirror" (item 36).

## R1

17. **Question.** 16464 is now "twice that (rung 8)" (item 11).
18. **"It is built. The third fit corpus is sealed by hash ..."**
    - It was built on the previous container.
    - On this container, the log records only 0018's extension corpus and 0021's fit corpus as rebuilt identical (`container_2026_10_21.corpora_rebuilt`).
    - 0024's and 0025's fit corpora and the builder cache are named in the run invocation (`--cache data/pivot/full_c4096.npz`, `--realfit2`, `--realfit3`), and none is recorded as rebuilt. On disk now, `data/pivot` holds only `ext_c4096.npz` and `realfit_c4096.npz`; this was observed, not banked.
    - "Sealed" is now "pinned by array hash in the (unfrozen) preregistration and its banked manifest" (`realfit3_corpus_manifest.json`).
    - The span: 1.8016 is now cited to `engineering_log_0024.json` `freeze.sealed_span`, and 2.1026 is removed.
19. **"What remains" list.** Each step is annotated:
    - step 1: the generator was lost, and the preregistration was amended by script (`amendments_before_freeze`);
    - step 4: the wording findings were applied, and the cost-sum finding is still open, since the preregistration still states 11963 to 15511 s;
    - step 5: "963 cases" is the log's count, written before the latest commit added cases to 0025's gate. The last banked full run, `mutation_report.json`, has 801.

    A step the log omits is added: rebuild and check the missing corpora. `CORRECTIONS.md` (2026-10-21) says every corpus rebuilt on this container is checked against its manifest before any preregistration uses it.
20. **Clause.**
    - Added that the interval does not cover the draw of rung 8's plaintexts or the fit side (`engineering_log_0025.json` `the_clause_is_the_fourth_doubling`).
    - "Sealed expectation" is now "Expectation stated in advance". 0025 is not frozen, so nothing in it is sealed.
    - Added the basis, a half-width of 0.0035 to 0.0036, with citations to prereg `scope.expected_outcome_stated_in_advance` and the log's `expected_outcome`.
21. **Outcome `RISES` with `MODEL_LEADS`.** "In-distribution scaling on real content holds through 16464 plaintexts" is now "one doubling, not a slope; not a transfer reading".
    - `prereg/0025` `what_this_is_and_is_not`: "It is not a slope".
    - 0024 calls itself "Neither a transfer reading nor 0023's in-distribution reading".
22. **Outcome `RISES` with `NO_SEPARATION` or `LINEAR_LEADS`.** "A hand-writable rule gets the same signal" read `NO_SEPARATION` as equal, which the lead rule forbids ("NO_SEPARATION (never 'equal')", `realcurve2_4096_verdict.json` `bar_applied.lead_rule`). The two outcomes are now split, and each bounds 0024's `MODEL_LEADS` to 8232 plaintexts, as the stop rules say.
23. **Outcome `BELOW_RATE` / `NOT_RESOLVED`.** Added the stop rules' pre-committed phrasings and the exact sentence that is bounded.
24. **Outcome `FALLS`.** Now uses the stop rules' sentence. "Closes the route" is kept, labelled as a plan inference.
25. **Added the cap rule:** a capped model at rung 7 or 8 is named in the same sentence (stop rules).
26. **"VOID or NOT RUN: ... the run resumes under the identical invocation"** was wrong for NOT RUN. NOT RUN is filed as `realcurve3_4096_not_run.json`, and nothing is re-scoped; only a VOID run may be resumed (stop rules [2] and [3]).
27. **Rough cost, memory.** "The sealed estimate is about 9.0 GB ... the launch floor is being raised to 11.0 GB" was stale when written.
    - The amended preregistration, committed at 20:39, before the draft was saved at 20:41, already states a peak of about 10.2 GB and requires 11.0 GB at launch (`amendments_before_freeze`; `scope.cost.memory`; `launch.min_mem_available_gb` 11.0).
    - 9.0 GB survives only in the log's stale `cost.memory`.
    - Also added: corpus-rebuild seconds that are not in the fit estimate (3415.5, 452.2, 625.7); the cost figures cited to the log; and that the smoke ran on scratchpad corpora.
28. **Depends on.** Added the corpora rebuild.

## R2

29. **"It banks no time per prediction ... a search of every artifact found none"** is now scoped to this record's recipes. One artifact does bank a per-item timing: phase 0's brute-force recompression with the plaintext in hand, 24 ms per stream over 36 candidates on 2 streams (`artifacts/phase0/round1_domain_search.json`). It is a different method, but "every artifact" was false.
30. **Outcomes.**
    - "MODEL_LEADS at equal cost ... the first cost-side support for spending on a larger model" is now "not bought only with prediction-time compute; says nothing about a larger model". A cheaper cut of the boosted model leading is no evidence about a larger model; this guards the no-capability rule.
    - The `NO_SEPARATION` wording no longer reads as equal.
    - "Serving cost" is now "prediction cost on this machine", which is what R2 measures.
31. **Memory "stays under R1's"** is now marked EXTRAPOLATION, with its basis.

## R3

32. **Coverage.** Now cites `artifacts/verification/coverage.json` (`n_claims` 283). 233 is the count of entries classed primary-verifiable, a count I recounted; no field stores 233. Claimcheck passes it only via unrelated values, such as an `n_iter` of 233 in `fdc_4096.json`.
33. **Rebuild path.** Added that the fix was tested on the record's own fresh container, where 0018's and 0021's corpora rebuilt identical (`engineering_log_0025.json`). It is still untested by anyone else.
34. **Pass outcome.** "The chain order, the reader hashes, the number tracing and the verdicts stop resting on the founders' word" overclaimed.
    - Tier 1 re-runs readers on banked artifacts, and Tier 2 rebuilds corpora. Neither re-runs a fit.
    - The text now says the banked measurements still rest on the record's own runs.
35. **Rough cost.** Added 0021's rebuild time on the 2026-10-21 container, 163.0 s (`engineering_log_0025.json`).
36. **"They were uncommitted in the working tree when this draft was written"** is false.
    - The commit at 20:35:34 UTC on 2026-10-21, which is on `main` and `origin/main`, changed `tools/pivot/fetch_ext_sources.sh` and `fetch_sources.sh`.
    - The draft file was saved at 20:41:38, and the working tree is clean.
    - Whether the mirror carries the fix: COULD NOT VERIFY (unchanged).

## R4

37. "Has never asked it with real data on both sides" now reads "as a preregistered question", because informational readings exist.
38. **"The only readings of real-fitted models on content they did not contain are on the builder's evaluation set. They are flat ... or below the rate"** was false.
    - The extension corpus's three synthetic families (hexdump, sql, xml) are also content no real-fit corpus contains, and the model's reading there rose from 0.0693 to 0.0987 over 0024's second decade.
    - 0023's tree reverse slope was 0.009842.
    - All of these are now stated as informational, and as not on a real family.
39. "Needs no new sources" now adds that two of the corpora must first be rebuilt on this container.
40. The py_src citation now names the banked artifact (`realcurve2_4096_verdict.json` `fit2_rows_per_family`) instead of only `prereg/0024`.
41. **"0025's sealed file says every reading of content the model did not see is flat."** The preregistration is unfrozen, and the sentence is an expectation that cites only 0015 and 0018/0019. It is now quoted verbatim and cited to the log's `expected_outcome`.
42. **Outcomes.**
    - "The first measurement in the record that real data volume buys identification on a content kind the model never saw" is now "first preregistered measurement ... on a real content kind". An informational synthetic-family reading has already moved with volume.
    - "Flat or below the rate: data volume buys only the kinds it contains ... each content kind it serves" is now "Below the rate, or not resolved: no preregistered evidence ...". The old wording over-generalised from one design, "flat" is not a reading of this clause, and "serves" implied deployment.
43. **Rough cost.** "At most five times" is now "about five times or less, not a bound". Iteration counts vary by fold; 0024's model took 62, 72, 117 and 153 iterations over rungs 4 to 7 (`engineering_log_0025.json`). Memory is marked EXTRAPOLATION.

## R5

44. "A seed replicate" is now "seed replicates: three full-pipeline runs" (`seed_robustness.json` `runs`).
45. **Outcomes.**
    - "The boosted model's edge ... is a draw effect" is now "not shown to survive a second draw".
    - "Depends on which files were drawn" is now "not shown to hold beyond the files 0024 drew".

    A failure to reproduce, which could be a `NO_SEPARATION`, does not establish a draw effect.
46. **Disk and headroom.**
    - Disk: added the third corpus's size, about 0.97 GB (`engineering_log_0025.json` `cost.memory`).
    - Headroom: "0025 banked its unused candidates" is now "0025's preregistration states", because a preregistration is not an artifact.

## R6

47. **"The record names learning from the raw bit sequence as the kind of representation it has not built (VERDICT.md, L4)."** 0009 and 0010 were raw-byte models, so "has not built" misdescribes them. `VERDICT.md` says a model that works at 1024 would need such a representation, and that it is not started. That statement is in the byte-model sections under L4; the text now says so.
48. **"The two byte models it did try did not beat the boosted recipe."** They were compared at 1024 bytes on the builder corpus with the hand-engineered feature model (0.1165 at the 100000 rung), not with 0021's boosted recipe at 4096 (`byte_model_verdict.json` `read`).
49. "So it was inconclusive" is now "the reader named it inconclusive" (`byte_model_flat_verdict.json` `meaning`).
50. **"The comparator is not under-searched: ... -0.0004."** One search on 26346 rows does not establish that. The -0.0004 is an informational reading under `REAL_RECIPE_FAILS` (`realsearch_4096_verdict.json`). The sentence is now "searched once on real content", with that context.
51. **Outcomes.**
    - `BYTE_LEADS`: "the measured precondition for spending on a larger learned model" is now "a precondition the record would need; it does not say what a larger model would do".
    - `NO_SEPARATION`: "buys nothing" read not-resolved as equal. It is now split from "boosted model ahead".
52. **Rough cost.** 0009's round is now stated as at 1024 bytes on 100000 training rows (`byte_model.json`).

## Section 3

53. **Buyer bullet.**
    - "None exists" is now "The record claims none", with quotations from `OPERATING_RULES` §10 and `VERDICT.md`.
    - "Every reader emits `establishes_a_buyer: false`" is false. Five readers never emit it: `pivot_deflate_curve.py` (0003), `phase0_verdict.py`, `phase0_round4_verdict.py`, `market_timing_verdict.py` and `ephemerr_a2_verdict.py`. 0003's `deflate_verdict.json` has no such field.
    - The verdict files of 0006 to 0024 do carry `false`; 0020 banked no verdict.
    - Added `VERDICT.md`'s own caveat that the self-reported flag is evidence of intent rather than of fact.
54. **Quotation "No extrapolation beyond the top rung is banked or quoted."** This is verbatim only in 0023, inside a parenthetical. The wording all three files share is "no extrapolation beyond the top rung is quoted as anything", and that is now quoted.
55. **"No transfer claim from in-distribution numbers"** is now "same-family numbers".
    - 0024 calls itself "neither a transfer reading nor 0023's in-distribution reading".
    - "Each marked 'not a transfer reading'" is now the banked field `is_a_transfer_reading: false`, which 0021, 0022, 0023 and 0024 all carry.
56. "Even at 2.1026 decades" is now "Even with 0025's doubling" (item 11).
57. The window-size bullet now cites 0007 and 0011, which both read `CARVE_FAILS`.
58. Added "An informational reading is never quoted as a pass". Every verdict file's `informational_only` field says so, and this plan now quotes informational readings.

## Section 4

59. **FALLS row.** "The forward pointer 0025 sealed" is now "0025's stop rules commit to", because 0025 is unfrozen.
60. **BELOW_RATE row.** The paraphrase 'keeps buying the record's rate' was in quotation marks. It is replaced by the exact sentence (README line 109; `prereg/0025` stop rules).
61. **VOID / NOT RUN row** is split into two rows (item 26).
62. **Machine ceiling row.** Now cites the engineering log, where the figures are banked. "Above 16464 plaintexts" is now "above rung 8".
63. **R4 row.**
    - "Flat or below the rate" is now "Below the rate, or not resolved".
    - "The one axis that moved under transfer (0016)" is now "the one axis whose preregistered transfer verdict passed (0016, on the builder's families and 0003's recipe)". Informational readings also moved with volume (item 9).
64. **R4 and R6 row.**
    - "Both flat under transfer" is now "Neither shows a preregistered gain".
    - "An in-distribution result" is now "a same-family result on real content, which is not a transfer reading" (item 55).
65. **R5 row.** "Filed as draw-dependent" is now "filed as not shown beyond 0024's draw" (item 45).

## Sources

66. Added a line naming the further files the check read.

## Checked and left unchanged

All of the following match their cited artifacts at the precision written:
- **0024:** 0.0974, 0.1404, 0.00697 [0.00571, 0.00824], 0.0039 [0.0001, 0.0077], 0.00638, 0.1365, 0.0919, 0.1419, `SECOND_DECADE_RISES_MODEL_LEADS`; fit seconds 2352.6, 371.6, 35.2, 478.1, 1141.1; total 5950.5, wall 6456.7 in a single launch; at launch 15.66 GB, 3.82 GB, 4 cores, no GPU.
- **0015 to 0023:** 0015 0.0859 against 0.088462, `TRANSFER_FAILS`. 0016 0.00596, 0.0829, -0.002, `DIVERSITY_HELPS`. 0019 0.0637, `OOB_TRANSFER_FAILS`. 0023 0.000222, 0.001, 0.0084. 0024 reverse slope 0.00231.
- **0025:** 218955, 8569, 1488, 192, 0.0005, 0.0035, 11963 to 15511, 3.3 to 4.3 hours, 7675, 11903 to 15451, 2867.9, 177 to 248 against 250, 350 MB, 7.5 GB, 15 GB.
- **Byte models:** 182842, 0.0849, 0.1165, 0.0943 (a byte-histogram logistic per `VERDICT.md`), 392506, 0.0385, 0.0393 against 0.30, `BYTE_MODEL_FAILS`, `BYTE_FLAT_FAILS`, 3665.7, `raw_c1024` 650000 × 1024.
- **0022:** 35 candidates (8+8+8+8+1+1+1), 1634.3 s, -0.0004.
- **Builds and other figures:** 3415.5, 216.1, 83.9, 452.2, 625.7; 321409; seed spread 0.0014 (0.001366); 283.
- **Text checks:** the `VERDICT.md` quotations; the encoder list; G5 uncleared; no dollar figure in any artifact; no time per prediction for any recipe of this record.
- **No customer, user, partner or buyer** is claimed anywhere in the draft. "FDM-1" is never used as a capability claim; only the convention's descriptor (item 3) and outcome wording (items 21, 30, 42 and 51) needed tightening.

## Found outside the draft (read-only; nothing changed)

- **`docs/DILIGENCE.md` line 113.** It says "more real plaintexts do not move a reading on content the model was not fitted on". It was written from 0023's first decade, and 0024's informational readings (0.00231 per doubling on the builder's set; 0.0693 to 0.0987 on the synthetic families) contradict it as a general statement.
- **`artifacts/pivot/engineering_log_0025.json` is stale** against the amended preregistration and the latest commit: `cost.memory` (9.0 GB), `status`, and `still_open_before_the_freeze`.
- **The corpora 0025's run needs are not on disk** on this container: `full_c4096.npz`, `realfit2_c4096.npz` and `realfit3_c4096.npz` are missing.
- **Claimcheck's limits.** Its rule passes 16464 and 233 through coincidental values, and it accepts ×100 and ÷100 matches. Passing it does not by itself show that a number is the one cited.
