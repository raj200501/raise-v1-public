# Diligence map

The questions a hostile technical reviewer should ask, with where each answer lives. None of these
are hypothetical — most were literally asked by the 54-agent adversarial audit whose full record,
rejected findings included, is banked at `artifacts/verification/adversarial_audit.json`.

## "Is the slope real, or a seed artifact?"

The interval is a cluster bootstrap over the 10,000 held-out source chunks — the dependence unit
the split declares — after an audit found the original fragment-level interval anti-conservative
(`artifacts/pivot/audit_rederivations.json`, CORRECTIONS.md 2026-08-31). Seed variance is measured
by two full-pipeline replications at independent seeds: `artifacts/pivot/deflate_curve_seed*.json`,
summarised in `artifacts/pivot/seed_robustness.json` and tabled in `outbound/EVIDENCE_BRIEF.md`.

## "Is it memorising content rather than identifying encoders?"

Three answers, one of them against us. The split is grouped by source chunk, and the archived trial
measured the random-split failure this prevents (0.4873 → 0.1531). The null control retrains on
shuffled labels and falls to chance. And the audit found the grouping guarantee **false for the
gutenberg family** (shared byte pool) — with the measured impact running *against* the headline:
excluding the leaked family widens both margins (`$.gutenberg_excluded_margins` in
`audit_rederivations.json`).

## "Won't a frontier model just do this?"

The input is mid-stream entropy-coded bitstream — no header, no text, nothing `javap`-like renders
legible (the attack that killed the JVM candidate in `trial/pivot/DOMAIN_SELECTION.md` was checked
here and does not transfer). No stand-in for "clever prior, no task-specific data" was measured:
no large pretrained model was tested. The headline margins are over the trivial-baseline ladder up
to depth-16 trees and logistic regression (since 0014, a searched standardised logistic), all
trained on the same data as the top rung, which bounds cheap learned rules, not a frontier model.

## "Where does the signal actually live?"

`artifacts/pivot/per_family_curves.json`: ~+0.09/decade on the builder's synthetic structured
generators (csv, log, json) at about ten times chance (on real files, scored on held-out chunks of
the files fitted, the model reaches at most 0.1404, prereg 0024), near-flat on incompressible
families sitting at the measured collision ceiling (`channel_capacity.json`: 14.667 and 14.75
distinct streams of 26 for base64 and binary). The headline is a mixture and the decomposition is
published — at 2048 too (`per_family_curves_2048.json`): csv and log clear the 0.05 bar on both
readings (+0.0554 and +0.0501 against the depth-16 tree), the structured four clear it as a set
(+0.0549), and the mixture misses on every reading — even without the three incompressible families
(+0.0478).

## "Does it survive realistic carve sizes?"

**No, and that is preregistered and published**: `CARVE_FAILS` at 1024 bytes (prereg 0007), with
transfer collapsing to chance, an information-ceiling measurement showing that byte collisions
barely change across sizes and so do not explain it, and two learned-representation attempts
(0009, 0010) that did not rescue it. At 2048 bytes (prereg 0011, expected outcome stated before the corpus
existed) it fails again — +0.0475 against the 0.05 bar on the frozen set, +0.0294 against all
baselines, transfer from 4096 at 0.0455 — so the boundary of the working window is bracketed to
(2048, 4096], each size under its own protocol (top rung 800000 at 4096, 500000 at 2048 and 1024). A
symmetric recipe search at 2048 (prereg 0012, read under 0013 after 0012's own frozen reader voided
the run on a defect of its own, filed in `CORRECTIONS.md`) moved the model to 0.212 and the
standardised logistic baseline to 0.1886, so the margin fell to +0.0234: `RECIPE_FAILS`. The same
search at 4096 (prereg 0014, its expected outcome stated in advance as uncertain) clears: 0.2884
against a searched logistic at 0.2317, +0.0567 on the frozen and the expanded reading and +0.0576
with the leaked gutenberg family excluded, `RECIPE_CLEARS`, so the headline margin is quoted at its
searched size rather than the +0.1003 fixed recipes gave. Every number in this repository is a
4096-byte-window number and the documents say so.

## "Does it work on content it has never seen?"

**No, at the preregistered level, and that is published at full size** (prereg 0015, expected
outcome stated in advance as uncertain): with each of the eight content families withheld from
training in turn, 0003's recipe identifies the encoder on the withheld family at a stitched 0.0859
against chance 0.0385, 0.0026 short of the chance + 0.05 bar, and a raw logistic on the same
features transfers better (0.0928). Per family the model keeps 0.25 to 0.65 of its in-distribution
accuracy (`artifacts/pivot/lofo_4096_verdict.json`, `retention_per_family`). The curve and the
searched margin stand as measured; they are statements about these eight content families.

## "Would more content types fix that?"

**Modestly, and depth would not** (prereg 0016, bar calibrated to the transfer regime before the
freeze, expected outcome stated as close to even): at a fixed plaintext budget of 4900 source
chunks spread over 1, 2, 4 or 7 of the other families, 0003's recipe identifies the encoder on the
unseen family at 0.0666, 0.0653, 0.0736 and 0.0829, a slope of 0.00596 per doubling of families
against a 0.005 bar, `DIVERSITY_HELPS` (`artifacts/pivot/fdc_4096_verdict.json`). A single family
at 700 to 4900 chunks moves the same reading by -0.002, and the seven-family point at 700 chunks per
family sits -0.003 from 0015's seven-family mixture at about 5000 chunks per family: under transfer
the row axis is nearly flat. The per-family curves are composition curves under one sealed
ordering and are banked; nothing extrapolates past seven families or beyond these eight.

## "Is the boosted recipe even the right one for unseen content?"

**Not shown, at the preregistered margin** (prereg 0017, expected outcome stated in advance as uncertain): 0014's
searched, standardised logistic, fitted on 0015's eight sealed folds, identifies the encoder on unseen
families at a stitched 0.0951 against 0003's recipe at 0.0859, 2393 more correct rows of 260000 against
a bar of 5200 (0.02), `L3_LEAD_BELOW_BAR` (`artifacts/pivot/lofo_l3_4096_verdict.json`); the lead does not reach the
record's 0.05 margin. In distribution the boosted recipe leads the same linear rule by 0.0078; under transfer the
point ordering reverses (the linear rule ahead by 0.0092), but the preregistered margin does not certify it. 0014's searched model was not fitted under transfer;
that is a separate preregistration.

## "Does it work on content outside your own corpus builder?"

**No, at the preregistered bar, for these five real families** (prereg 0018, expected outcome stated in advance as
close to even after a discounted within-builder bracket of 0.097 to 0.118): an evaluation-only extension corpus of 61409 rows
from eight families the builder never produced (five real, pinned by sha256: CPython source and documentation, the SQLite
amalgamation, RFC texts, one Windows package's PE files; three from fresh synthetic generators), scored by 0014's searched model fitted on
the builder's eight families: 0.0637 on the 38452 real-family rows against chance + 0.05 = 0.088462, 2450 rows against
3402 needed, `OOB_TRANSFER_FAILS` (`artifacts/pivot/oob_4096_reread_verdict.json`); the eight-family mixture with the three synthetic families
is 0.0766, a flag. The incumbent reads 0.0634 and the standardised logistic 0.0716 on the same rows; no real
family sits at the bar and two synthetic ones do; per-family ceilings are banked. 0018's own frozen reader emitted `VOID` on one
wrong sealed literal (the null block hash restated from 0017's fold-based block; `CORRECTIONS.md` 2026-09-10) and stands `VOID`;
preregistration 0019 re-read the same banked artifact with the literal corrected and every number disclosed in advance. It is a
statement about these families at 4096 bytes, as pinned, chosen before any fit touched them.

## "Does real content carry the signal at all, if you fit on it?"

**Yes — and a hand-writable rule gets most of it** (prereg 0021; 0020 sealed the identical design and refused at launch). The same three recipes fitted on 26346 rows from 1029 plaintexts of the same five pinned files (the chunks 0018's sealed corpus does not use, disjoint by index, chunk id, source-chunk hash and feature-row bytes) and read in distribution on the same 38452 rows: the searched model reads 0.1193 (4587 rows), 3.1× chance and nearly double 0018's builder-fitted 0.0637 (`artifacts/pivot/realfit_4096_rerun_verdict.json`). Four trivial baselines fitted on the same rows set the floor per `OPERATING_RULES` §4a; the depth-3 tree reaches 0.0929, so 5495 rows were needed and 4587 arrived: `REAL_FIT_FAILS`, a margin of 0.0264 over a rule a person could write by hand. Under the chance-based bar 0020 first drafted (3402 rows) it would have passed; the bar was moved before the freeze on a reviewer's argument that is now the measurement. 0 of 5 families clear their own floor (all five are above it; py_src short by 0.0033). Builder-matched arms at the same row and plaintext budgets read 0.0671 and 0.0638: content, not budget. Reproduction 0.1965 against 0003's banked 0.1965, drift 0.0; null 0.0394. An in-distribution reading on real content, not a transfer reading. 0020's refusal measured a property of the record's foundation no preregistration had: the corpus builder emitted 9 pairs of duplicate source chunks, one straddling 0003's split (`artifacts/pivot/builder_duplicate_chunks.json`); 0021 seals their collisions by row identity.

## "Would a recipe searched on real content clear it?"

**No — and the search moved nothing** (prereg 0022, the question 0021 deferred). 0014's roster verbatim (35 candidates over seven heads, eight enumerated recipes each for the model, the logistic, the depth-3 tree and the deep tree) was searched inside 0021's 26346-row real fit block: selection on a chunk-rule holdout (5291 rows, 206 chunks), one stage on the other 21055 rows, keep 1, one confirmatory fit per head on all 26346 rows, scored once on the same 38452 rows; the selection stage gathered 0 scored rows. The bar is the best searched trivial baseline floored at 0021's reading plus 0.05 (`OPERATING_RULES` §4a), so the search could only raise it: from 6457 rows before the run to 6468 after it. The searched model (M3) reads 0.1189 (4573 rows), the searched logistic (L5) 0.1182: searched margin 0.0007, `REAL_RECIPE_FAILS` (`artifacts/pivot/realsearch_4096_verdict.json`). Gains from the search over 0021's unsearched readings: model -0.0004, logistic 0.0003, depth-3 tree 0.0044; on the builder's corpus the identical search had moved the model by 0.0489 and the logistic by 0.0965. The searched model sits 14 rows below 0021's unsearched M4 on the scored rows while winning the holdout by 0.0012; under a macro-averaged selection rule it would have selected M4, which the reproduction clause pins to 0021's reading. 0 of 5 families clear; the logistic leads the model outright on py_src and rst_doc. Four reproduction arms (M1, M4, L3, D1) land on 0021's banked values with drift 0.0; null 0.0392 against chance 0.038462; no arm at its cap. Expected outcome stated in the sealed file: fails, more likely than not — for a reason (the baseline would gain more) that turned out wrong; neither gained. The recipe excuse is closed on this roster at this budget. The budget excuse, a scaling curve on real plaintexts, is named in the sealed file as not covered and was preregistered and read as 0023 (next question).

## "Does more real data help?"

**Yes — and it helps the linear rule more** (prereg 0023, the budget question 0021 and 0022 left open). 0021's 26346-row real fit block was cut into four nested, family-stratified rungs of plaintexts (130, 258, 515, 1029; 3344, 6635, 13207, 26346 rows; 2.984659 doublings, just under a decade: the only real content the record has outside its sealed scoring set), and 0021's three fixed recipes (M4, L3, D1; 0022 measured that searching them moves nothing) were fitted once per rung and scored once on the same 38452 rows (`artifacts/pivot/realcurve_4096_verdict.json`). The model reads 0.0974, 0.1065, 0.1139, 0.1193: 0.007344 per doubling of plaintexts, scored-chunk interval [0.006199, 0.00846], against 0.005 required with the lower bound above 0.0 — `REAL_CURVE_RISES`. The top rung is 0021's reading (0.1193 against 0.1429 needed over the depth-3 tree), so the curve rises to a failing number and the sealed file said in advance that a pass is never 'more real data fixes the model'. The standardised logistic reads 0.0911, 0.0939, 0.1085, 0.1179 (0.009551 per doubling); model minus logistic -0.002207, paired interval [-0.003707, -0.000752], the model ahead in 0.002 of the resamples, read by the rule sealed in advance as 'the linear rule buys more per doubling than the model' — the model leads at every rung and the lead shrinks from 0.0063 to 0.0014. The depth-3 tree rises 0.003002; the smallest rung cut again under a second nesting moved it by 0.0084 (the model by 0.001, the logistic by -0.0013), so its rise is within a redraw; the scored-chunk interval does not resample the fit side and the sealed file says so. The model's slope is 0.7276 of the builder's in-distribution per-plaintext rate (0.010093). On content the model was not fitted on, more real plaintexts have moved readings little, not uniformly, and none of these readings is a verdict: on the builder's own evaluation set the model's reading moved 0.000222 per doubling over these rungs and the depth-3 tree's rose 0.009842 (informational); over 0024's second decade the model's moved 0.00231 per doubling, below the rate, and its reading on the extension corpus's three synthetic families (hexdump, sql, xml), which no real-fit corpus contains, went from 0.0693 at 1029 plaintexts to 0.0987 at 8232 (`realcurve2_4096_verdict.json`, `ext_subsets`). The top rung reproduced 0021's three readings with drift 0.0; null 0.0409 against chance 0.038462; no role at its cap; sixteen committed checkpoints cross-checked by the reader; 1208.2 s wall on one launch. Expected outcome stated in the sealed file: rises, more likely than not, with the difference the number of interest; the difference came out entirely below 0. What it means: on these five files, in distribution, over just under a decade (0003's scope rule asks for two), the record's scaling thesis holds — rising to a reading that fails the record's margin — and what grows fastest with real data is the standardised linear rule. No extrapolation beyond the top rung is banked or quoted: the plaintexts it would count do not exist.

## "Does a second decade of real files help?"

**Yes — and at the top rung the boosted model leads the linear rule, by 0.0039** (prereg 0024, the question 0023's numbers raised). A second fit corpus was built and sealed before the freeze from other files of the same five families — 23 newly pinned archives and 600 more RFC texts: other Python projects' .py and .rst, other C projects' .c and .h, other Windows programs' .exe and .dll, other RFCs; 193926 rows, 7574 plaintexts with rows, every chunk hashed against every whole chunk and every kilobyte run of the 0018 pinned files (`artifacts/pivot/realfit2_corpus_manifest.json`, `docs/compliance/EXT_SOURCES2.md`), and nested on 0021's block in three exact per-family doublings: seven rungs of 130, 258, 515, 1029, 2058, 4116, 8232 plaintexts (3344, 6635, 13207, 26346, 52766, 105214, 210751 rows; 5.984659 doublings in all), rungs 1..4 being 0023's cuts row for row, and the 'second decade' is 3.0 doublings (0.9031 of a decade) of other files above 0021's block; both together span 1.8016 decades, short of 0003's two-decade scope rule. 0021's three fixed recipes were fitted once per rung and scored once on the same 38452 rows (`artifacts/pivot/realcurve2_4096_verdict.json`). The model reads 0.0974, 0.1065, 0.1139, 0.1193, 0.1236, 0.13, 0.1404: a second-decade slope of 0.00697 per doubling of plaintexts, scored-chunk interval [0.00571, 0.00824], against 0.005 required with the lower bound above 0.0 — both clauses pass: the model's second-decade slope is at or above 0.005 and the interval's lower bound above 0.0 — `SECOND_DECADE_RISES`. The logistic's second-decade slope (0.00638) clears the same bar and the tree's (-0.0003) does not: a rise the linear rule shares is a rise of the cheap signal, not of the recipe. The standardised logistic reads 0.0911, 0.0939, 0.1085, 0.1179, 0.1241, 0.1321, 0.1365 (0.00638 per doubling over the second decade), the depth-3 tree 0.0834, 0.0901, 0.0915, 0.0929, 0.0921, 0.0921, 0.0919 (-0.0003); model minus logistic 0.00059, paired interval [-0.00102, 0.00231], the model ahead in 0.756 of the resamples: the paired interval includes 0: not resolved at this size; never read as 'equal'. At the top rung, the model leads the standardised logistic by 0.0039 (paired interval [0.0001, 0.0077], entirely above 0) — `MODEL_LEADS` by the rule sealed in advance; at rung 4 the same reading is 0.0014 ([-0.002303, 0.0047], NO_SEPARATION), and model minus logistic by rung is 0.0063, 0.0126, 0.0054, 0.0014, -0.0005, -0.0021, 0.0039. The shift arm — rung 5's new plaintexts alone (1029 plaintexts, 26420 rows: rung 4's count, none of 0021's block) — reads model 0.1184, logistic 0.118, tree 0.0923: against rung 4 by -0.0009, 0.0001 and -0.0006, against rung 5 by -0.0052, -0.0061 and 0.0002 — the direct reading of what other files of the same families buy for the original files at the same count, informational. 0021's clause re-applied at the top rung (informational): 0.1404 does not clear 0.1419 over the tree and does not clear 0.1865 over the higher of the tree and the logistic. Rung 4 reproduced 0021's three readings with drift 0.0, 0.0, 0.0, rungs 1..4 reproduced 0023's; null 0.0372 against chance 0.038462; roles at their iteration cap: none; 25 committed checkpoints cross-checked by the reader; 6456.7 s wall on the last of 1 launch(es), 5950.5 s of fits against 8097 to 24604 s estimated in advance. Expected outcome stated in the sealed file: rises, more likely than not but less likely than 0023's pass; the linear rule ahead or not separated, more likely than the model ahead; the run read `SECOND_DECADE_RISES_MODEL_LEADS`. What it means: other files of the same kinds keep raising the recipe's accuracy on the files it is scored on at or above the record's bar of 0.005 per doubling, through 8232 plaintexts (eight times 0021's), so the budget excuse is answered a second time on real content, this time with other files; at eight times 0021's plaintexts the boosted recipe leads the standardised logistic (26 classes over 1108 features) on the record's own real content by 0.0039, with a paired interval over the scored chunks that does not resample the fit side — the recipe conclusion of 0021, 0022 and 0023 (that the linear rule gets most of the signal) is bounded by the size of that lead, not reversed. Not a transfer reading, and not 0023's in-distribution reading either: every rung holds the scored files' own unscored chunks, and the plaintexts added above rung 4 are other files of the same kinds, so the second decade confounds more plaintexts with plaintexts from other files, which the shift arm reads directly. No extrapolation beyond the top rung is banked or quoted.

## "Who buys it?"

Uncleared, and filed in the coverage map's **weakest class** rather than dressed as a finding. The
structural argument for why this family of tasks resists buyers is stated as three labelled
conjectures (C1, C2 and a refinement) with falsifiers, plus a preregistered search for C1's
falsifier that returned `NO_FALSIFIER_FOUND` across 14 candidates (prereg 0008).

## "How do I know the bars weren't set after the results?"

`python3 tools/prereg.py verify` — a hash chain where entry *N* carries entry *N−1*'s hash, NIST
Beacon and drand anchors per entry, and readers frozen by sha256. Two honest limits, stated in the
record itself: the beacon proves **not-before only** (both interpretation artifacts carry that
correction), and precedence over measurements otherwise rests on commit history — which is why the
PR was merged with a merge commit, preserving it.

## "What did you get wrong?"

`CORRECTIONS.md`: 23 entries at full size, including a published figure our own reproduction
contradicted, an instrument warning grepped out of view before a commit, a wrong reading of our own
null control (an error *against* us, filed anyway), and the audit's thirteen findings. The pattern
of what the gates missed is stated there: they check mechanical honesty, not reasoning between
numbers.

## "Can my engineer verify any of this without trusting you?"

```
bash tools/gates.sh                                  # every gate, one command, exit non-zero on failure
pip install -r requirements-pivot.txt                # the compressors the corpus builder calls (zopfli, isal, libdeflate)
bash tools/pivot/fetch_sources.sh                    # fetch sources; pin_sources.py fails unless they hash to the banked edition
python3 tools/pivot/run_study.py --cache data/pivot/full_c4096.npz --chunks 50000 --carve 4096 \
    --model hgb --rungs 1000 10000 100000 800000 --tag full \
    --out /tmp/deflate_curve.json --scores-out /tmp/deflate_rung_scores.json
                                                     # build the cache, then re-measure the curve into scratch files
                                                     # (a re-measurement on a different draw of the pool, not the banked number)
python3 tools/pivot/corpus_manifest.py --check       # compare the rebuild's array hashes with the banked ones; X and g
                                                     # of the build() caches print DIFF by design (see below)
```

The corpora are not committed: they are rebuilt from upstream sources pinned by sha256 and the
shipped generators. The fetch has broken before: Gutenberg re-edited banked books twice and one
fetch script never worked on an empty machine until it was repaired; two books now come from a
commit-pinned third-party copy (`CORRECTIONS.md`, 2026-09-02 and 2026-10-21). The manifests bank
content hashes of every array, so a rebuild is checked rather than assumed, and the check does not
pass for every array (`CORRECTIONS.md`, 2026-10-21 and 2026-10-22). A rebuild reproduces the pinned
sources, checked byte for byte; the labels (y) of the builder caches and of 0024's corpus;
`raw_c1024` whole; the 4096 builder cache's evaluation set as a set of chunks, whose banked order
can be restored from banked layouts; and 0018's and 0021's corpora (`ext_c4096`, `realfit_c4096`),
rebuilt identical on a second machine on 2026-10-21. It does not reproduce X and g of the three
caches `run_study.build()` wrote (`full_c4096`, `carve_c1024`, `carve_c2048`), whose rows are in
worker-completion order by design, so every builder-pool result can be re-measured on a different
draw but not re-derived on the same rows; nor the X of 0024's `realfit2_c4096`, which rebuilt on a
second machine differs in rare rows of the larger chunks (its smoke subset rebuilds identical;
0024's rung-7 logistic does not reproduce on it bit for bit; the cause is not identified). Where the
rebuild of 0025's `realfit3_c4096` stands is recorded in
`artifacts/pivot/engineering_log_0025.json`.

801 mutations across 25 gates certify every gate can fail
(as banked on 2026-09-17, before the unfrozen 0025 gate was registered; that count is checked
against the mutation report by `tools/freshness.py`, because an earlier version of this sentence
said 132 while the artifact said 134); the reproduction that matters most — the audit — is
banked with its kill-list included.
