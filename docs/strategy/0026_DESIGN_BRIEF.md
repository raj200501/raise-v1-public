# 0026 design brief: does more real data of the families the model sees buy identification on a real family it has not seen?

**Status: a design brief for 0026, not a preregistration. Nothing in it is frozen. 0026 is written and frozen only after 0025's run.**

**State of 0025.** 0025 is still unfrozen: `prereg/0025-realcurve3-4096.json` has `frozen: false`, and `artifacts/pivot/engineering_log_0025.json` `status` reads "unfrozen…".

**Tags.**
- **[B]** banked, cited as file and key. Files cited by bare name are in `artifacts/pivot/`. A cite to a preregistration file is to its sealed text (unfrozen, for 0025), which is not under `artifacts/`.
- Every number the draft of this brief computed from banked vectors is now banked in `artifacts/pivot/design_0026_numbers.json`, written by `tools/prereg_gen/0026/bank_design_numbers.py`. That script uses 0024's own `slope_bootstrap` and `ols_slope` (`tools/pivot/run_realcurve.py`) and `paired_lead_bootstrap` (`tools/pivot/run_realcurve2.py`), with 0024's seed, resample count and resample construction. Those numbers are tagged [B] with their key under `numbers`. The file's own status reads "design numbers for an unfrozen, unwritten preregistration; informational". Under OPERATING_RULES §2 and rule 4, the pre-freeze check must still recompute each one with the 0026 runner's code and bank it in the preregistration's design block.
- **[E]** an estimate: an EXTRAPOLATION from banked inputs by a stated formula, with its basis on the same line. Each is banked as an estimate under `estimates` in `design_0026_numbers.json`. None is a measurement.
- **COULD NOT VERIFY** is said where it applies.

All paths are relative to the repository root.

**Reader positive control, already passed [B].** The 0026 construction recomputes 0024's banked model slope 0.00697 [0.00571, 0.00824] (`realcurve2_4096.json` `model_slope_per_doubling`, `slope_bootstrap.model.ci95`) exactly. It also recomputes the lead interval [0.0001, 0.0077] (`lead_at_top.r7_model_minus_logistic.ci95`) exactly, from `realcurve2_4096_scores.json` (`design_0026_numbers.json` `numbers.positive_control_model_slope_second_decade`, `numbers.positive_control_lead_r7_model_minus_logistic`; `checks.positive_control_*_equals_banked`).

---

## 0. What changed from the design the review preferred (the statistician's), and why

| Fatal flaw named by the reviewers | Fix in this brief |
|---|---|
| Over budget. (That design's fit-second figure is in no artifact and is not restated here.) | The clause uses 3 rungs (k = 0, 1, 3) of a cleaner construction. The core costs **15582 s (4.33 h)** central [E: `estimates.cost_fit_seconds` `core`, `core_hours`; basis §12]. The informational arms run under a fit-seconds time box, and the clause never waits for them. |
| The rung-4 anchor is 0021's block, which shares projects with the held-out family: CPython across py_src/rst_doc, and the embed zip's SQLite DLLs in pe_bin against c_src. It was never screened for runs across families. | **Every fold fits only the other-project pools, realfit2 then realfit3.** Both were screened at 1 KiB against the pinned blobs of all five families (`realfit2_corpus_manifest.json` and `realfit3_corpus_manifest.json` `exclusion.run_overlap`, window 64 × 16 runs). `realfit_corpus_manifest.json` has no `exclusion` key [B]. 0021's block survives only as contrast arm A1. The anchor choice is decisive: on the never-fitted synthetic families, the r4-anchored second decade reads 0.00977 and an s4-anchored proxy reads 0.00490 [B: `numbers.synthetic_second_decade_r4_anchored_slope`, `numbers.proxy_synthetic_s4_anchored_slope`] (§9). |
| A6 depended on 0025's unfrozen shift-arm rule | Dropped. 0026 pins realfit3 by its manifest's X sha only and reads no 0025 rule or result. The fit-side replicate is deferred to a successor and stated in every sentence. |
| Outcome table had no precedence (hi < 0 met two outcomes) | An exhaustive ordered rule (§1). |
| Computed numbers were unbanked | All are banked in `design_0026_numbers.json`. Pre-freeze item 2 recomputes them with the runner's code. |
| Reproduction gate too loose (another review brief's "within 0.005") | Exact equality of the extension-row correctness vectors and drift 0.0, as in the record's practice. |
| The clause mixed decades (another review brief) | Not applicable. Every rung adds the same kind of data. |
| Mis-cites in other briefs | Not carried over. 0018's null on real rows was 0.0382 (`oob_4096.json` `readings.null.ext_real_top1`), not the figure another brief gave. All ten Gutenberg sources are on disk, but two had been re-edited upstream (CORRECTIONS 2026-10-21). 0026 never touches the builder cache. |

---

## 1. The question and the one clause that can fail

**Question.** M4 is fitted on real plaintexts of four of 0018's five real families. None of those plaintexts comes from a scored file's project, and the per-family count doubles exactly at each rung. Does its accuracy on the fifth family's sealed 0018 rows rise at the record's rate?

**Estimand T.**
- Fit five leave-one-family-out folds at rungs k ∈ {0, 1, 3}.
- At each rung, stitch the 38452 real rows: each family's rows are predicted by the fold that never saw it. That gives A_k.
- T is the OLS slope of A_k against k (doublings of seen plaintexts, exact in every fold).
- T equals the row-weighted mean of the five per-fold slopes, with weights 7800, 7407, 7709, 7761 and 7775 of 38452 (`ext_corpus_manifest.json` `per_family.*.n_rows` [B]).

**Bar.** 0.005 per doubling, the record's rate:
- `realcurve2_4096_verdict.json` `bar_applied.slope_per_doubling`;
- `fdc_4096_verdict.json` `bar_applied.slope_per_doubling_must_reach` [B];
- 0016 set it as "calibrated to the transfer regime" (`prereg/0016-fdc-4096.json` `scope.expected_outcome_stated_in_advance`; VERDICT.md, 0016 section).

**Verdict rule.** Exhaustive, read in this order. lo and hi are the 2.5th and 97.5th percentiles of T's paired cluster bootstrap.

| Order | Condition | Verdict |
|---|---|---|
| 1 | hi < 0 | `TRANSFER_FALLS` |
| 2 | T ≥ 0.005 and lo > 0 | `TRANSFER_RISES` (the only pass) |
| 3 | lo > 0 and T < 0.005 | `TRANSFER_BELOW_RATE` |
| 4 | lo ≤ 0 and hi < 0.005 | `TRANSFER_FLAT`: zero is inside the interval and the rate is excluded |
| 5 | otherwise (lo ≤ 0, hi ≥ 0.005) | `TRANSFER_NOT_RESOLVED` |

- **Downgrade only.** A RISES that fails any screen S1, S3 or S4 (§8) becomes `TRANSFER_RISES_NOT_ROBUST`, and the failing screens are named. A screen can never turn a fail into a pass.
- **The departure is stated openly.** 0025 says "never 'flat'". 0026 uses FLAT only when the interval excludes 0.005, because the question requires that a flat result can be published as flat at full size.
- **Every non-RISES reading publishes hi** as "bought at most {hi} per doubling".
- **Flag `BOUNDED_BELOW_HALF_RATE`.** It is set when (lo, hi) ⊂ (−0.0025, 0.0025). Only with it may a document say "flat to within half the bar".
- **Readings every document must carry in the same sentence as the verdict** (not part of the verdict string):
  - **LEAD:** M4 minus L3 at k = 3 on the stitched rows, read by 0024's `bar_applied.lead_rule` as MODEL_LEADS, LINEAR_LEADS or NO_SEPARATION.
  - **GAP** (§5).
  - Any M4 at its 250-iteration cap at k = 0 or k = 3.
  - The fit-side caveat (§6).

---

## 2. Hold-out: rotate over all five families

A single sealed family is also a single file set:
- SQLite for c_src;
- CPython for py_src and rst_doc, which share `Python-3.11.9.tgz` (`ext_corpus_manifest.json` `source_pins`, families [py_src, rst_doc] [B]);
- 79 RFCs for rfc_txt;
- the CPython embed zip for pe_bin.

One family alone gives a slope half-width of 0.0026 to 0.0031 [B: `numbers.proxy_one_fold_half_width`; §6]. Rotation applies 0015's stitched mixture to real content. It fits exactly 4.00 times the rows of one all-five curve, because fold rows at each rung sum to 4.00 times the all-five rows [B: `numbers.rotation_rows_ratio`]. Per-fold slopes are flags only.

---

## 3. Corpora and rungs (nothing fetched)

**Pools.**
- `realfit2`: X sha `d74bd30e…`, 7574 chunks with rows (185/1492/4927/668/302).
- `realfit3`: X sha `98547322dff713f0…`, new positions 198/1684/5595/756/336, in that manifest's pool order.
- Both are concatenated per family in pool order, chunk id ascending (`*_corpus_manifest.json` `chunk_order_note` [B]). realfit3's ids continue realfit2's within each family, and the concatenated pools equal realfit3's `n_pool_chunks_with_rows_total` [B: `design_0026_numbers.json` `checks`].
- realfit3 is pinned by its manifest hash at 0026's freeze. Nothing reads 0025's prereg rules or results.

**Rung rule.** Rung k takes, per family g, the first n_g·2^k chunks with rows of g's concatenated pool, where n_g is 0021's chunk count (24/203/672/90/40, `realfit2_corpus_manifest.json` `base_chunks_with_rows_0021` [B]). Fold F at rung k is the all-five rung k with every row of F deleted.

All-five rungs [B: `numbers.rungs_all_five`]:

| k | All-five plaintexts | All-five rows | realfit3 positions used |
|---|---:|---:|---|
| 0 | 1029 | 26420 | 0 |
| 1 | 2058 | 52632 | 0 |
| 3 | 8232 | 210720 | 658 (7/132/449/52/18) |

- **k = 0 is 0024's shift arm s4** (`realcurve2_4096.json` `shift_arm.arm.n_rows` 26420, `rows_per_family` 599/5201/17241/2339/1040 [B]; `same_chunks_as_rung_5s_new_chunks: true`). The rows derived from the manifests equal s4's rows per family, and their sorted chunk ids reproduce s4's `chunks_sha256` e96399af… [B: `numbers.rungs_all_five`; `checks.k0_equals_0024_s4_rows_and_chunks`].
- **k = 4 is impossible:** c_src needs 384 and the pools hold 185 + 198 = 383. Every family is short at k = 4: pe_bin 3248 against 3176, py_src 10752 against 10522, rfc_txt 1440 against 1424, rst_doc 640 against 638 [B: `numbers.k4_impossible`].
- **k = 2 is skipped for cost.** It would add 5270 s [E: `estimates.cost_fit_seconds` `skipped_k2`; basis: the §12 interpolation].
- **About 8% of k = 3's plaintexts (658 of 8232) come from realfit3** [B: `numbers.realfit3_share_of_k3_plaintexts`]. That includes projects absent from k = 0 and 1 (botocore, dask, homeassistant, ipython, nova…, `realfit3_corpus_manifest.json` `source_pins` [B]). This is flag R7.

**Fold sizes** [B: `numbers.fold_sizes`; scored sizes from `ext_corpus_manifest.json` `per_family`]:

| Held out | Seen plaintexts k0 / k1 / k3 | Fit rows k0 / k1 / k3 | Scored rows (chunks with rows) |
|---|---|---|---|
| c_src | 1005 / 2010 / 8040 | 25821 / 51491 / 206010 | 7800 (300) |
| pe_bin | 826 / 1652 / 6608 | 21219 / 42197 / 169011 | 7407 (288) |
| py_src | 357 / 714 / 2856 | 9179 / 18278 / 73205 | 7709 (300) |
| rfc_txt | 939 / 1878 / 7512 | 24081 / 48010 / 192254 | 7761 (300) |
| rst_doc | 989 / 1978 / 7912 | 25380 / 50552 / 202400 | 7775 (300) |

**Row order.**
- k = 0 uses s4's sealed order `np.random.default_rng([20260917, 150])` (`prereg/0024` `rung_stream_words.shift_arm_rows` [B]) with F's rows removed.
- k = 1 and 3 permute the all-five rung by `default_rng([seed4, 300 + k])`, then remove F. seed4 is new and sealed, and the second words are distinct per 0024's `why_distinct`.
- M4's last-10% validation split is therefore a random tenth of the seen families' rows, and early stopping never sees F.

**Mix.** Exact per-family doubling keeps each fold's family mix fixed across rungs.

---

## 4. Recipes and environment

- **Recipes.** 0021's fixed M4 (HGB, learning rate 0.05, 127 leaves, l2 1.0, max_iter 250, n_iter_no_change 20), L3 (standardised logistic, C 1.0, max_iter 1000) and D1 (depth-3 tree), verbatim (`prereg/0024-realcurve2-4096.json` `scope.curve.recipes` [B]).
- **Floors.** B-majority, B-stratified and B-feat1 (`prereg/0021` `scope.recipes` [B]); B-tree3 is D1. There is no search, and caps are never raised.
- **Environment.** `/root/venv311`: python 3.11.15, numpy 2.4.6, sklearn 1.9.0, checked when the draft was written. That matches `realcurve2_4096.json` `environment` [B]. Runs at 3 threads, nice 10.
- **New runner.** It imports `slope_bootstrap` (`tools/pivot/run_realcurve.py`) and `paired_lead_bootstrap` (`tools/pivot/run_realcurve2.py`) and never opens `full_c4096.npz`.

---

## 5. Scoring rows and the readings beside the clause

**Scoring rows.**
- Each fit is scored once on the 61409-row extension corpus (`data/pivot/ext_c4096.npz`, X sha `c578eaf1…` [B]) and on nothing else.
- **0003's sealed evaluation set is not scored.** 0025 is its twelfth preregistration (`prereg/0025` `scope.sealed_set_disclosure` [B]), and its builder cache is absent from `data/pivot`.
- The synthetic families (hexdump, sql, xml) are read as flags.

**Readings beside T, all paired on the same resamples:**

1. **Matched seen-family slope S, at zero fit cost.** On F's rows, take the mean correctness of the four folds G ≠ F, each of which saw F at n_F·2^k plaintexts, with the same construction and fit sizes. Stitch, then take the slope over k ∈ {0, 1, 3}.
   - **GAP = T − S**, paired: `GAP_CLOSES` if lo > 0, `GAP_WIDENS` if hi < 0, otherwise `GAP_NOT_RESOLVED`.
   - Retention at k = 3: (T₃ − 0.038462) / (S₃ − 0.038462).
   - This replaces the all-five refits another review brief proposed. 0024's r4..r7 cannot serve here, because they contain the scored files' own chunks.
2. **References.**
   - 0024's banked second-decade slope 0.00697 [0.00571, 0.00824] [B] (r4-anchored, own files).
   - The s4-anchored in-distribution proxy {s4, r5, r7} at x = {0, 1, 3}: 0.00749 [0.00624, 0.00876] [B: `numbers.proxy_real_s4_anchored_slope`].
   - 0024's banked s4 as the all-five k = 0 reading: 0.1184 / 0.118 / 0.0923 (`shift_arm.readings.*.ext_real_top1` [B]).
3. **Real against manufactured data.** Stitched T₃ minus 0018's builder-fitted M4 on the same rows: 0.0637 (`oob_4096.json` `ext_real_top1.model` [B]; `oob_4096_scores.json` `per_example.model`, whose chunk ids and families equal 0024's row for row [B: `numbers.oob_vectors_aligned`]).
4. **Exchange-rate flag.** The smallest 0024 rung whose in-distribution reading on F's rows reaches fold F's T₃. Its sentence: "{n} plaintexts of the other four kinds bought less on {F} than {m} that included {j} of {F}'s own". For example, 0024's r1 read c_src 0.1035 with 3 c_src plaintexts (`realcurve2_4096.json` `ext_per_family.r1_model.c_src` [B]).
5. **Transfer-level flag.** T₃ against chance + 0.05 = 0.088462 (`lofo_4096_verdict.json` `bar_applied.mixture_must_reach` [B]).

---

## 6. Interval, precision and operating characteristics

**Interval.**
- 0024's construction: 2000 cluster resamples of the 1488 scored real chunks, `default_rng(20260917)`, same draw order, rung accuracies rounded to 4 decimals (`realcurve2_4096.json` `slope_bootstrap.model.n_boot/seed` [B]).
- One resample serves every rung, role and fold, 0024's banked vectors and 0018's vector.
- A 20-seed stability count is banked: the number of seeds that would read a different word.

**Precision proxies** [B: `design_0026_numbers.json` `numbers.proxy_*` and `numbers.real_s4_minus_r4`]. 0024 vectors at s4, r5 and r7, standing in for k = 0, 1 and 3. r5 and r7 still contain 0021's block, so these are proxies only.

| Quantity | 95% half-width |
|---|---:|
| Stitched slope over {0,1,3}, synthetic families (a transfer proxy, 899 chunks) | 0.00124 |
| Stitched slope over {0,1,3}, real families in-distribution (1488 chunks) | 0.00126 |
| Stitched slope over {0,3} only (real, synthetic) | 0.00123–0.00128 |
| One fold (per family: c_src, pe_bin, py_src, rfc_txt, rst_doc) | 0.00296, 0.00266, 0.00308, 0.00287, 0.00257 |
| A paired equal-count difference (real s4 − r4: −0.0009, interval [−0.0048, 0.0027]) | ≈0.0038 |

**Operating characteristics** [B: `numbers.oc_standard_error`, `numbers.operating_characteristics`; a normal approximation with standard error 0.00064, the real proxy's half-width over 1.96]. NOT_RESOLVED needs a half-width of at least 0.0025, so it has probability ≈ 0.000 at every true slope.

| True slope | 0 | 0.0015 | 0.0025 | 0.0035 | 0.005 | 0.0065 |
|---|---|---|---|---|---|---|
| Reading (probability) | FLAT 0.95 (FALLS 0.02, BELOW 0.02) | BELOW 0.65 / FLAT 0.35 | BELOW 0.97 / FLAT 0.03 | BELOW 0.99 / RISES 0.01 | RISES 0.50 / BELOW 0.50 | RISES 0.99 / BELOW 0.01 |

- With the expected width, FLAT implies `BOUNDED_BELOW_HALF_RATE`.
- At exactly 0.005 a point bar is a coin flip at any sample size; the brief states this.

**Not covered: the fit side.** 0023's one replicate moved the model by 0.001 (`realcurve_4096_verdict.json` `flags.replicate_rung_1.difference_from_rung_1.model` [B]). Suppose that is the standard deviation per rung, independent across rungs:
- the slope's dispersion becomes about 0.00079 [E: `estimates.fit_side`; basis: the square root of 0.00064 squared plus 0.001 squared over the spread of x = {0, 1, 3}];
- the interval does not widen;
- a true zero then reads FLAT with probability about 0.89 instead of 0.95 [E: `estimates.fit_side`; same basis].

Every sentence states that the interval does not cover the fit side.

---

## 7. Controls (each one VOIDs the run or files it NOT RUN)

- **Reader positive control** (no fit). Recompute 0024's 0.00697 [0.00571, 0.00824] and lead [0.0001, 0.0077] exactly. This passed from the banked vectors [B: `numbers.positive_control_*`]. A mismatch is VOID.
- **Reproduction** (353.2 s = 286.8 + 63.5 + 2.9, `realcurve2_4096.json` `cost.seconds_by_name.s4_*` [B]).
  - Refit s4 on all five families with M4, L3 and D1, before any fold fit.
  - The readings must equal 0.1184 / 0.118 / 0.0923, with per-family M4 0.1264 / 0.0998 / 0.1302 / 0.1193 / 0.1155 [B].
  - The extension-row slice of `realcurve2_4096_scores.json` `per_example.s4_*` must equal the refit's correctness vectors element for element. The banked `per_example_sha256` cannot be compared directly, because it also covers the 260000 builder rows.
  - s4's `idx_sha256` cfa130ee…, `sorted_sha256` 016b97f6… and `chunks_sha256` e96399af… are recomputed from data with the runner's code (rule 4).
  - Any drift files the run NOT RUN.
- **Null.**
  - M4 with permuted labels (`default_rng([seed4, 400])`) on the largest block, the c_src fold at k = 3.
  - It must read at most 0.038462 + 0.01 on all real rows and on each family.
  - Cost about 218 s [E: `estimates.cost_fit_seconds` `null`; basis: 223.1 s × 206010/210751, linear in rows; 0024's null stopped at 20 iterations, `fit_info_by_name.null.n_iter` [B]].
  - It runs first, so it is also the memory probe.
- **Validity (no leakage).**
  - Zero rows and zero chunk ids of F in fold F.
  - No chunk id or source hash shared between fit and scored sets.
  - No byte-identical feature row shared between them.
  - The count of aligned 1024-byte runs between each fold's fit plaintexts and F's scored chunks must be 0. This is re-measured; it is expected to be 0 by construction.
- **Floors.** B-majority, B-stratified and B-feat1 are fitted per fold at every rung, about 48 s in all [E: `estimates.cost_fit_seconds` `floors`; basis: B-feat1 took 1.1 s at 26346 rows and B-majority and B-stratified 0.0 s (`realfit_4096_rerun.json` `cost.seconds_by_name.floor_*` [B]), linear in rows over the 15 fold-rung blocks]. D1 is fitted at every rung.
- **Label-prior bound** [B: `numbers.label_prior_bound`, read from `ext_c4096.npz` after its y, g and fam hashes were checked against `ext_corpus_manifest.json`]. The largest per-family label frequency is 0.038916 (py_src), against chance 0.038462, so a prior-only rule moves the level by at most 0.000454. Over k ∈ {0, 1, 3} that bounds its OLS slope at 0.000162 per doubling (5/14 of the level bound). 1473 of 1488 chunks carry all 26 rows (38298 rows).

---

## 8. Rival explanations, run as arms or screens

| Rival | What is run | Effect |
|---|---|---|
| R1 Project links between the fit and the scored files | Construction: no 0018-project plaintext in any fold. **A1 contrast arm** (time-boxed): fold F at 0024's r4 (0021's block minus F, per-family counts identical to k = 0) paired against fold k = 0 on F's rows. The rfc_txt fold, which has no pinned-project link, is A1's internal control. A pre-freeze cross-family 1024-byte run scan of 0021's block against each F's scored chunks is banked, and A1 is also read with any flagged chunks dropped. | Flag |
| R2 Shared runs under 1 KiB, or boilerplate (licence blocks and the like) | **S3:** for each scored chunk, the share of its aligned, non-constant 64-byte windows found at any offset of its fold's k = 3 plaintexts. Median split per family, sealed before freeze. T re-read on the low-similarity half. The paired high-minus-low slope is a dose-response flag. | Screen on RISES |
| R3 Falling floors inflating the gap (D1 on never-fitted sql fell 0.0742 → 0.0477 from r4 to r7, `realcurve2_4096_verdict.json` `ext_per_family.r{4,7}_depth3_tree.sql` [B]) | **S1:** slope of A_k(M4) − max(F*_k, F*_0), where F*_k is the best stitched floor (B-majority, B-stratified, B-feat1, D1) at rung k | Screen on RISES |
| R4 The cheap linear signal | L3 and D1 transfer slopes; M4 − L3 slope difference, paired; the LEAD reading. Prior: L3 transferred better before (0015: 0.0928 against 0.0859, `lofo_4096_verdict.json` `lofo.logistic.mixture_top1`, `lofo_mixture_top1`; 0019: 0.0716 against 0.0637, `oob_4096_reread_verdict.json` `ext_real_top1` [B]) | Reading |
| R5 One family carries it | **S4:** at least 4 of 5 per-fold slopes > 0, and every drop-one-fold stitched slope ≥ 0.0025. Per-fold slopes and intervals are published; five folds cannot reach significance on a sign test. | Screen on RISES; drop-one words are flags otherwise |
| R6 A near-twin family (py_src and rst_doc pools are .py and .rst members of the same 14 PyPI archives, `realfit2_corpus_manifest.json` `per_family.*.composition.rule` [B]) | **Pair fold** {py_src, rst_doc} at k = 0 and 3 (time-boxed). The strict mixture takes the py_src and rst_doc rows from the pair fold, uses rungs {0,3} for every fold, and applies the same rule. If it is less favourable, it leads the sentence. The confound of one fewer seen family is named (0016: 0.00596 per doubling of families, `fdc_4096_verdict.json` `fdc_slope_per_doubling` [B]). | Strict reading |
| R7 New projects at k = 3 (realfit3, about 8%) | Distinct-archive counts and shares banked per rung; the k = 0→1 slope (realfit2 only) as a flag | Flag |
| R8 A weaker model because one family is missing | The cross-fold seen reading S₀ against 0024's all-five s4 on the same rows | Flag |
| R9 Machinery drift | Reader positive control; exact s4 reproduction | VOID |
| R10 Bootstrap seed; iteration cap | 20-seed count; every n_iter banked, and a capped fit is named in the same sentence | Flag |
| R11 Fit-side variance | Not run. Stated in every sentence; successor (§10) | — |

Each of S1, S3 and S4 passes only if its point estimate is at least 0.0025 and its 2.5th percentile is above 0 (S4 uses its own point rules). All are applied only to a RISES reading.

---

## 9. Expected outcome, stated in advance (pilot from never-fitted families)

0024's real-content fits never saw hexdump, sql or xml. Their readings at r1..r7 were 0.0688, 0.0712, 0.0683, 0.0693, 0.0865, 0.096, 0.0987, and 0.0846 at s4 (`realcurve2_4096_verdict.json` `ext_subsets.r*_model.ext_synthetic_top1` [B]). From these vectors [B: `design_0026_numbers.json`, keys as named]:

- First decade (r1..r4): −0.00014 [−0.00121, 0.00108] (`numbers.synthetic_first_decade_slope`).
- Second decade anchored at r4 (0024's construction): **0.00977 [0.0086, 0.011]** (`numbers.synthetic_second_decade_r4_anchored_slope`).
- s4 − r4 (other projects against the pinned files at equal count): +0.0153 [0.0115, 0.0192] (`numbers.synthetic_s4_minus_r4`).
- **Anchored at s4** (proxy {s4, r5, r7} at k = {0, 1, 3}): **0.00490 [0.00371, 0.00619]** (`numbers.proxy_synthetic_s4_anchored_slope`).
- r7 − 0018's builder M4 on these rows: +0.0006 [−0.0034, 0.0044] (`numbers.synthetic_r7_minus_0018_builder_model`).

So half of the r4-anchored "rise" on never-fitted families is a one-time switch of source. Anchoring on s4 removes it, and the pilot then sits on the bar. This is a synthetic proxy; whether it carries over to real families is COULD NOT VERIFY.

**Prior:**
- BELOW_RATE is most likely, then RISES and FLAT; FALLS is unlikely.
- GAP_WIDENS is more likely than GAP_CLOSES.
- For LEAD, NO_SEPARATION or LINEAR_LEADS is more likely than MODEL_LEADS.
- Evidence for flat: 0016's depth arm −0.002 (`fdc_4096_verdict.json` `row_effect_within_family_model`), 0023's reverse slope 0.000222 (`realcurve_4096_verdict.json` `curves.model.builder_eval_slope_per_doubling`), 0015 TRANSFER_FAILS and 0019 OOB_TRANSFER_FAILS [B].
- Evidence for a rise: 0024's reverse slope over the second decade, 0.00231 (`flags.builder_eval_slope_per_doubling_second_decade.model` [B]).

If 0026 freezes after 0025 has been read, this paragraph must say so.

---

## 10. What each outcome means for the thesis that more data buys generalisation

FDM-1 is used here only as the company's name for a model. The record holds no FDM-1 model, and nothing here says what one could do. Nothing here is a claim about any customer, user, partner or buyer.

| Outcome | Meaning for "more data buys generalisation" | Follow-up |
|---|---|---|
| RISES | On five real families over three doublings, more real data of the seen kinds bought identification on an unseen kind at the record's rate or better. This supports the leg at this scale and does not extrapolate past 8232 plaintexts. | A fit-side replicate (a second nesting); then a fourth transfer doubling, which needs new fetched pools because k = 4 is impossible |
| RISES_NOT_ROBUST | There is a rise, but it rests on a named confound (floors, near-copies or one family). The thesis is not supported until that is removed. | A successor that targets the failing screen |
| BELOW_RATE | Data buys some transfer, below the rate. Volume is an expensive route to unseen kinds. | A real-content breadth curve (number of seen families at a fixed budget, 0016's axis), which needs new real families pinned |
| FLAT | More data of the seen kinds did not buy identification on an unseen kind, and the rate is excluded. The scaling on real content that 0023 and 0024 measured is within-family scaling, and the thesis is contradicted at this scale with this representation. | A learned representation at equal compute on the same folds; and the breadth curve |
| NOT_RESOLVED | No inference either way (expected to be improbable). | A second sealed scoring set; precision is bought on the scoring side |
| FALLS | The recipe specialises as it grows, the opposite of the thesis. | The fit-side replicate first |

- GAP_WIDENS means the data budget must buy coverage of kinds, not volume.
- GAP_CLOSES puts more transfer doublings ahead of the breadth curve.

---

## 11. Sentences to publish (the reader fills the braces)

**FLAT:**
> "Fitted on other projects' real files of four families, at 1029 to 8232 plaintexts (the fifth family and every scored file's project removed), the boosted recipe's accuracy on the fifth real family, the one it never saw, moved {T} per doubling (95% interval over 1488 scored chunks [{lo}, {hi}]). Zero is inside the interval and the record's rate of 0.005 is excluded, so it bought at most {hi} per doubling. The same doublings with the family seen moved {S} per doubling (GAP {word}). One nesting and one seed, so the interval does not cover the fit side; five families; 4096-byte carves. More real data of the kinds the model sees did not buy identification on a real kind it has not seen."

"Flat to within half the bar" is added only with `BOUNDED_BELOW_HALF_RATE`. Every outbound statement of 0023's or 0024's rise then carries "on the families it is fitted on".

**RISES:** the same frame, carrying in the same sentence:
- the number of folds resolved above zero;
- S and the retention;
- the LEAD, and L3's slope;
- the A1 and strict readings if they ran;
- "not beyond 8232 plaintexts or these five families".

It is never written as "generalises".

---

## 12. Cost (fit seconds, log-log interpolated from `realcurve2_4096.json` `fits[*].seconds` [B])

Every figure in this section is an estimate [E: `design_0026_numbers.json` `estimates.cost_fit_seconds` unless named otherwise]. Basis: per role, log(seconds) is interpolated linearly in log(fit rows) between 0024's adjacent rungs r1..r7, at each fold's fit rows.

| Layer | Fits | Seconds [E] | Cumulative |
|---|---:|---:|---:|
| Reader positive control | 0 | 0 | 0 |
| Null (c_src fold, k = 3) | 1 | 218 | 218 |
| s4 reproduction gate | 3 | 353.2 | 571 |
| Clause k = 0, 5 folds × M4/L3/D1 | 15 | 1556 | 2127 |
| Clause k = 1 | 15 | 2504 | 4631 |
| Clause k = 3 (M4 9283 of it) | 15 | 10903 | 15534 |
| Floors, every rung | 45 | about 48 | **15582 (4.33 h): the core** |
| *Time-boxed:* A1 contrast arm (0021's r4 minus F) | 15 | 1551 | 17134 (4.76 h) |
| *Time-boxed:* pair fold {py_src, rst_doc}, k = 0 and 3 | 6 | 850 | 17983 (5.00 h) |

**Per fold** (core clause, k = 0 + 1 + 3): c_src 3662, pe_bin 3023, py_src 1254, rfc_txt 3424, rst_doc 3600 s.

**Range for the core**, driven by k = 3 M4 [E: `estimates.cost_range_by_iterations`]. The per-iteration rule is about 3.90 + 0.0000546 × rows seconds, the least-squares line through 0024's 5.40, 6.64, 9.75 and 15.38 s per iteration at r4..r7 (seconds / `fit_info.n_iter`, with n_iter 62, 72, 117, 153 [B]). The central estimate corresponds to about 141.7 iterations per k = 3 M4 fit.

| Case | Core fit seconds |
|---|---:|
| 117 iterations (r6's count) | 13964 (3.88 h) |
| 184 iterations (1.2 × r7's 153, rounded up) | 18353 (5.10 h) |
| At the 250 cap | 22676 (6.30 h) |

The same fit took 280.1 s in 0021 and 334.8 s in 0024 (`realfit_4096_rerun.json` and `realcurve2_4096.json` `cost.seconds_by_name` [B]), so allow about ±20%.

**Time box.** An informational arm starts only if the fit seconds banked so far plus its central estimate stay within 5.0 h of fit seconds (a proposal; §16). Otherwise it is filed "NOT RUN (time box)". The clause fits are never time-boxed.

**Wall time.** At most 1.085 × fit seconds (0024: 6456.7 / 5950.5, `cost.wall_seconds_this_invocation`, `cost.banked_fit_seconds_total` [B], which included scoring 321409 rows per fit; 0026 scores 61409). That gives a core of at most about 16900 s (4.7 h) [E: `estimates.wall_time`].

**Memory** [E: `estimates.memory_peak`; COULD NOT VERIFY until run]. About 6.1 GB anonymous peak (the unrounded components sum to 6.15 GB):
- start from 0024's 3.59 GB before the rung-7 block (`realcurve2_4096.json` `ledger`, the `rung_bound` event of `run_r7_depth3_tree` [B]; restated in `prereg/0025` `scope.cost.memory`);
- subtract the 1.15 GB builder scoring set and add realfit3 (0.97 GB);
- add the c_src k = 3 block in float64 (1.83 GB) and the trees' float32 copy (0.91 GB).

Against that: `memory_kill_gb` 13.0 (`prereg/0024` `scope.curve.protocol.caps` [B]). The launch floor is 8.0 GB.

**Order.**
1. Null.
2. Reproduction.
3. k = 0 for all folds.
4. k = 1 for all folds.
5. k = 3 cheapest first: py_src (867 s), pe_bin (2190), rfc_txt (2506), rst_doc (2645), c_src (2694) [E: `estimates.cost_fit_seconds` `per_fold_k3`].
6. Within each fold: floors, D1, L3, then M4.
7. A1, then the pair fold.

**Checkpoints.** One checkpoint per fit, with commits pushed at least every 30 minutes. The longest stretch without a checkpoint is the c_src k = 3 M4 fit: about 2298 s central, about 3786 s at the cap [E: `estimates.cost_fit_seconds` `c_src_k3_model`; `estimates.cost_range_by_iterations` `c_src_k3_model_at_cap`].

**Scheduling.** 0026 runs after 0025 (estimated 3.3 to 4.3 h, `prereg/0025` `scope.cost.estimate_stated_in_advance`; restated in `engineering_log_0025.json` `cost` [B]). The two cannot run in parallel: 4 cores, 3 threads sealed, and the runner refuses to start beside another runner.

**Before the run (not fit seconds).** Rebuild and `--check` realfit2 (452.2 s) and realfit3 (625.7 s) (`build_seconds` [B]). This is shared with 0025.

**Cuts if needed**, sealed before the freeze, in this order: the pair fold, then A1, then k = 1 (the clause then runs on {0,3}, half-width 0.00123–0.00128 [B: `numbers.proxy_two_rung_half_width`]).

---

## 13. Pre-freeze checks

1. realfit2 and realfit3 pass `--check` against their manifests. At the time of writing, only `ext_c4096.npz` and `realfit_c4096.npz` are in `data/pivot`.
2. Recompute every number in `design_0026_numbers.json` with the runner's code and bank it in the design block (rule 2). `python3 -B tools/prereg_gen/0026/bank_design_numbers.py --check` reproduces that file byte for byte from the banked inputs.
3. Seal every fold, A1 and pair block's idx, sorted and chunks hashes. Prove that fold ∪ F's rows equals the all-five rung. Recompute s4's banked hashes from data (rule 4).
4. Bank the following:
   - the 1 KiB run counts of fit against scored chunks per fold (expected 0);
   - the cross-family run scan of 0021's block (for A1);
   - the S3 per-chunk similarity and its median split;
   - archive counts and shares per rung.
5. A smoke run on scratchpad corpora. The reader's gate control is built from the runner's output (rule 4), and the mutation test must pass.
6. Confirm the runner never opens `full_c4096.npz`.

---

## 14. What it does not cover

- Carve sizes other than 4096.
- Recipes other than M4, L3, D1 and the floors.
- Learned representations.
- Rung 8 or k = 4.
- The first decade, or depth within 0021's block (0016's depth arm is the record's reading on that).
- Fit-side variance.
- The family-count axis on real content.
- Families beyond these five. Each held-out "family" is also one project or release, and families are defined by file extension.
- Overlap below 64-byte windows, and kinship between source code and compiled code. For example, the c_src pool includes `zlib-1.3.1.tar.gz` (`realfit2_corpus_manifest.json` `per_family.c_src.composition` [B]); whether zlib is compiled into the scored `python311.dll` is COULD NOT VERIFY, because no zlib version banner was found.
- The rows-versus-plaintexts decomposition.
- Any customer, user, partner or buyer.

---

## 15. COULD NOT VERIFY

- Any transfer reading on a held-out real family.
- Whether the synthetic pilot carries over to real families.
- Fold iteration counts and seconds; the memory peak.
- That realfit2 and realfit3 rebuild identically on this container.
- The S3 distribution, the cross-family scan of 0021's block, and the cost of the pre-freeze scans.
- Whether L3 is invariant to the BLAS thread count (the exact reproduction will show it).
- The zlib link described in §14.

---

## 16. Decisions left for the preregistration author

1. The value of seed4.
2. The time-box threshold (5.0 h of fit seconds proposed).
3. Confirm the FLAT naming and its stated departure from 0025.
4. Keep k = 1, or cut it before the freeze.
5. Whether 0026 is frozen before or after 0025 is read; the expected-outcome paragraph must say which.

**Key files.**
- `artifacts/pivot/design_0026_numbers.json` (this brief's computed numbers and estimates)
- `tools/prereg_gen/0026/bank_design_numbers.py` (writes and `--check`s it)
- `artifacts/pivot/realcurve2_4096.json`
- `artifacts/pivot/realcurve2_4096_scores.json`
- `artifacts/pivot/realcurve2_4096_verdict.json`
- `artifacts/pivot/realfit_corpus_manifest.json`
- `artifacts/pivot/realfit2_corpus_manifest.json`
- `artifacts/pivot/realfit3_corpus_manifest.json`
- `artifacts/pivot/ext_corpus_manifest.json`
- `artifacts/pivot/oob_4096.json`
- `artifacts/pivot/oob_4096_scores.json`
- `artifacts/pivot/lofo_4096_verdict.json`
- `artifacts/pivot/fdc_4096_verdict.json`
- `artifacts/pivot/realcurve_4096_verdict.json`
- `prereg/0024-realcurve2-4096.json`
- `prereg/0025-realcurve3-4096.json`
- `tools/pivot/run_realcurve.py`
- `tools/pivot/run_realcurve2.py`
- `tools/pivot/corpus_realfit2.py`
