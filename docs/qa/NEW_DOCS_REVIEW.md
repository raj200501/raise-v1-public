# Research QA — red-team review of the post-audit documents

Scope: `outbound/EVIDENCE_BRIEF.md`, `outbound/evidence_page.html` (and its renderer
`tools/render/evidence_page.py`, read to locate root causes only), `docs/DILIGENCE.md`, and the
audit-correction sections of `VERDICT.md`. These four are the documents the 54-agent audit never
saw. Method mirrors `artifacts/verification/adversarial_audit.json`: every candidate defect was
verified against the primary artifact before filing; restatements of already-disclosed weaknesses
were discarded as false positives. All four reviewed files pass
`.venv/bin/python tools/claimcheck.py` (verified 2026-08-31; banked from 66 artifact files, 16728
values, allowlist empty) — every finding below is therefore a defect claimcheck cannot see:
a real number attached to the wrong claim, a stale number, or a claim stronger than its artifact.

Reviewer: Research QA department (<contact: see the repository owner> session, 2026-08-31). Findings only;
no reviewed document was edited.

---

## Finding 1 — MAJOR. The evidence page attributes the all-family collision ceiling to incompressible content — the exact error class the audit already corrected once

- **File:** `outbound/evidence_page.html` (the "Where the curve lives" subhead); root cause at
  `tools/render/evidence_page.py` line 246.
- **Quoted text:** "incompressible content sits at the measured collision ceiling (20.9125
  distinct streams of 26 at this carve)"
- **Why wrong:** 20.9125 is `artifacts/pivot/carve_channel_capacity.json`
  `$.by_carve.4096.mean_distinct_streams_of_26` — the mean over source chunks spanning **all
  eight content families** at the 4096-byte carve. The measured ceiling for the incompressible
  families is roughly 14 distinct streams of 26: `artifacts/pivot/channel_capacity.json`
  `$.per_family.base64.mean_distinct = 14.667`, `$.per_family.binary.mean_distinct = 14.75`.
  `outbound/EVIDENCE_BRIEF.md` states this correctly ("14.667 and 14.75 distinct streams of 26
  for base64 and binary"), so the two outbound documents contradict each other. Worse, this is a
  repeat of a defect the audit confirmed and the repository already corrected: CORRECTIONS.md
  2026-08-31 findings 6–8 ("22.27 — the all-family mean distinct-stream rate — was attributed to
  base64/binary content, which actually collapses to ~14.7 ... an error in the flattering
  direction") and the corrected bullet in VERDICT.md ("22.27 is the mean across all eight content
  families, which an earlier version of this bullet wrongly attributed to the worst families").
  The renderer reintroduces the same misattribution with the carve-level number: it implies the
  incompressible families' ceiling is ~20.9/26 when their measured ceiling is ~14.7/26 —
  flattering direction, in the section the page itself calls "the sharpest statistic in the
  package", and in direct contradiction of VERDICT.md.
- **Severity:** MAJOR. Fix belongs in `tools/render/evidence_page.py` (attach the per-family
  ceilings from `channel_capacity.json`, or drop the parenthetical), then re-render.

## Finding 2 — MODERATE. DILIGENCE.md states a mutation count that matches no artifact

- **File:** `docs/DILIGENCE.md`, final section ("Can my engineer verify any of this without
  trusting you?").
- **Quoted text:** "132 mutations across 13 gates certify every gate can fail"
- **Why wrong:** `artifacts/verification/mutation_report.json` says `total_mutations = 134`,
  `detected = 134`, `survived = 0`, and `by_gate` sums to 134 over 13 gates. VERDICT.md ("134
  mutations, 134 detected, 0 survived"), `outbound/EVIDENCE_BRIEF.md` ("**134** deliberate
  mutations across **13** gates, **134** detected"), and `outbound/evidence_page.html`
  ("134/134") all say 134. So DILIGENCE.md contradicts the artifact and every sibling document.
  claimcheck passes only because 132 collides with unrelated banked values. This is precisely the
  stale-mutation-count failure the repository has filed three corrections about (CORRECTIONS.md
  2026-08-25, "Broke CI with a stale mutation count for the THIRD time") — recurring in a brand-new
  document.
- **Severity:** MODERATE (single stale integer, but it sits in the "verify without trusting us"
  section, and the number is checkable by any diligence engineer in one command).

## Finding 3 — MODERATE. "All fixed by measurement" is stronger than the audit record

- **Files:** `outbound/EVIDENCE_BRIEF.md` ("The instrument these numbers passed through") and
  `outbound/evidence_page.html` (instrument tile).
- **Quoted text:** brief: "a **54-agent adversarial audit** whose 13 confirmed findings (three
  critical) were each fixed by measurement"; page: "13/24 adversarial-audit findings confirmed by
  double refutation (11 rejected, record banked) — all fixed by measurement".
- **Why wrong:** the banked record does not support the universal quantifier.
  `artifacts/verification/adversarial_audit.json` records findings only (no fix field), and the
  fixes documented in CORRECTIONS.md 2026-08-31 are a mix: the bootstrap, gutenberg-leak, and
  G4-provenance findings were indeed answered by new measurements
  (`audit_rederivations.json`, `baseline_family_rescore.json`, `g4_github_firsthand.json`), but
  at least five confirmed findings were prose contradictions or labelling defects fixed by
  editing text — e.g. "'Two' vs 'three of the four' thirteen lines later", the closing section
  that denied the headline, the not-before-anchor wording (both interpretation artifacts "now say
  so in their own text"), and the diagnostic quoted without its "not quotable as a result" label.
  Editing a sentence is not a measurement. The claim as written overstates the rigor of the
  response to the audit — the one section of these documents whose whole point is not overstating.
- **Severity:** MODERATE. Accurate alternatives exist in the record itself, e.g. "every finding
  fixed, the load-bearing ones by new measurement".

## Finding 4 — MODERATE. The PENDING seed-robustness rows are stale: a completed replication is banked

- **Files:** `outbound/EVIDENCE_BRIEF.md` ("Seed robustness" table and the preamble "Rows marked
  `PENDING` are genuinely unmeasured") and `outbound/evidence_page.html` ("PENDING — two
  full-pipeline replications are running; rows fill from artifacts or stay pending").
- **Quoted text:** "| Full-pipeline replications at independent seeds | PENDING |"
- **Why wrong:** `artifacts/pivot/deflate_curve_seed7.json` (with per-example scores in
  `deflate_rung_scores_seed7.json`) is a **completed** full-pipeline replication at seed 7 —
  slope 0.048578, top rung 0.2425, frozen-set margin 0.1116 — written at 19:00 on 2026-08-31,
  four minutes after both outbound files (18:56). As the repository stands, "genuinely
  unmeasured" is false for the first row, and the page's own renderer would fill it: its seed
  loop looks for `deflate_curve_seed7.json` and builds the table. The page provenance line also
  shows the staleness ("rendered from artifacts at 302aa93" — HEAD has advanced two commits
  since, per `.git/logs/HEAD`). The stale direction runs **against** the raise (the banked
  replication supports the headline: seed-7 slope 0.0486 vs 0.0491), but the brief's preamble
  promise — rows "are filled mechanically from artifacts" — is currently broken, and this is
  again the stale-claim bug class CORRECTIONS.md documents. Note: only one seed artifact exists,
  so "Slope range across seeds" legitimately stays PENDING until the second (the renderer also
  expects seed 1234567).
- **Severity:** MODERATE. Fix: re-run `tools/render/evidence_page.py` and fill the brief's first
  row from `deflate_curve_seed7.json`; leave the range row PENDING.

## Finding 5 — MINOR. "About 45% wider" does not match the two intervals the sentence itself quotes

- **File:** `VERDICT.md`, audit-correction bullet in "What is weak about it" (and the same figure
  echoed in `outbound/EVIDENCE_BRIEF.md`: "anti-conservative by ~45%").
- **Quoted text:** "The corrected interval ... is **[0.0482, 0.0500]** — about 45% wider than the
  superseded [0.0485, 0.0497]"
- **Why wrong:** the banked final rederivation
  (`artifacts/pivot/audit_rederivations.json`: cluster [0.048216, 0.050014], width 0.001798;
  superseded fragment-level [0.048538, 0.04973], width 0.001192) gives a ratio of 1.508 — the
  corrected interval is ~51% wider, and even at the sentence's own displayed precision the
  arithmetic is 0.0018 / 0.0012 = exactly 50% wider. The "~45%" traces to the audit's
  *preliminary* rederivation recorded in `adversarial_audit.json` ("[0.0483, 0.0500] vs the
  banked [0.04854, 0.04973] — about 45% wider"), which the final banked artifact superseded. The
  brief's phrasing ("An adversarial audit found ... anti-conservative by ~45%") is literally
  faithful to the audit record, so it is filed here as minor and only against the figure's
  currency: measured against the final banked intervals, ~45% mildly understates the defect
  (flattering direction).
- **Severity:** MINOR. "About half again as wide" or "~50%" would match the banked numbers.

## Finding 6 — MINOR. DILIGENCE.md cites the wrong artifact for the per-family ceiling claim

- **File:** `docs/DILIGENCE.md`, "Where does the signal actually live?"
- **Quoted text:** "near-flat on incompressible families sitting at the measured collision
  ceiling (`carve_channel_capacity.json`)"
- **Why wrong:** `artifacts/pivot/carve_channel_capacity.json` contains only all-family mean
  distinct-stream counts per carve size (20.79–20.9125); it has no per-family breakdown. The
  measured per-family ceilings for the incompressible families (14.667 base64, 14.75 binary)
  live in `artifacts/pivot/channel_capacity.json` `$.per_family`. A diligence engineer following
  this pointer to check the family-level claim will not find it. No number is misquoted — the
  pointer is wrong for the claim it is attached to (and the wrong pointer is the same conflation
  that produced Finding 1).
- **Severity:** MINOR. Cite `channel_capacity.json` (or both).

---

## Checks run that found nothing (all verified against primary artifacts at written precision)

1. **claimcheck** passes on all four reviewed files (run 2026-08-31, allowlist empty).
2. **Headline curve:** rung accuracies 0.0988 / 0.1415 / 0.1965 / 0.2395, slope +0.0491, r²
   0.9978, 2.9031 decades, chance 0.038462, null 0.0389 — all match
   `artifacts/pivot/deflate_curve.json`; cluster CI [0.0482, 0.0500] and full-precision
   [0.048216, 0.050014] match `audit_rederivations.json`; "6.2× chance" = 0.2395/0.038462 ✓.
3. **All four margin rows** in the brief (logistic 0.1392 / +0.1003; depth-16 tree 0.1812 /
   +0.0583; excluded: 0.1438 / +0.1073 and 0.1891 / +0.0620) match `deflate_curve.json`,
   `audit_rederivations.json` `$.gutenberg_excluded_margins`, and the leak-direction claim
   (both margins widen) matches the artifact's own reading.
4. **Per-family table and chart:** all eight slopes, CIs, and top-rung accuracies match
   `per_family_curves.json` at written precision; every `ci_excludes_zero` is true, as claimed;
   "roughly +0.09/decade" and "about ten times chance" (0.3888/0.038462 = 10.1) check out.
5. **Both SVG charts render their data faithfully:** every plotted y/x coordinate in the headline
   curve (points, baseline reference lines at 0.1812/0.1392, chance line) and every dot/CI-bar
   x-coordinate in the per-family chart was recomputed from the axis gridlines and matches the
   artifact values to sub-pixel; tooltip labels match the data.
6. **Operational reading:** top-5 0.5694 (margin +0.1084 over depth-16 tree 0.4610), decile
   0.7922 vs 0.6937 (+0.0985), top-5 slope 0.0985 with cluster CI [0.097121, 0.099902], declined
   looser reading +0.2510, decile n = 26,000 — all match `deflate_topk.json`,
   `deflate_topk_margins.json`, `topk_prereg_interpretation.json`; "~2× faster" = 0.0985/0.0491 ✓.
7. **Boundaries:** CARVE_FAILS numbers (0.1355 vs 0.1256, margin +0.0099, transfer 0.0403,
   ceiling 20.9125 → 20.79 across 4096 → 512 as an all-family statement) match
   `carve_generalisation.json`, `carve_margins.json`, `carve_channel_capacity.json`;
   BYTE_MODEL_FAILS (0.0849 vs 0.1165 vs 0.0943) matches `byte_model.json`; the 0010 chip's
   "inconclusive" reading matches `byte_model_flat_verdict.json` (whose verdict string is
   literally `BYTE_FLAT_FAILS` with meaning "Inconclusive", so the chip is faithful).
8. **Instrument tiles:** 10 preregistrations, chain verified, head 83707ff010a299d4…, drand +
   NIST Beacon 2.0 anchors on all 10 entries (`prereg_status.json`); 24 raw / 13 confirmed /
   11 rejected / 3 critical / 54 agents (`adversarial_audit.json`); 14 of 80 coverage claims in
   class `neither`, G5 among them (`coverage.json`); 8 dated correction entries in
   CORRECTIONS.md; 134/134 mutations in the brief and page match `mutation_report.json`.
9. **DILIGENCE.md spot-checks:** 0.4873 → 0.1531 random-vs-grouped matches
   `repro_assembly_splits.json` (full METHOD STRING task); NO_FALSIFIER_FOUND across 14
   candidates matches `c1_falsifier_verdict.json`; the 99-candidate total matches
   `phase0_totals.json` (36+37+26); cited tools (`tools/gates.sh`, `tools/prereg.py`,
   `tools/pivot/corpus_manifest.py`, `trial/pivot/DOMAIN_SELECTION.md`) all exist; "two
   dependencies, CPU-only" matches `requirements.txt` (numpy, scikit-learn).
10. **VERDICT audit-correction sections:** gutenberg-excluded slope +0.0524 [0.0514, 0.0535],
    0.1596 vs 0.2511, corrected top-5 CI [0.0971, 0.0999] vs superseded [0.0977, 0.0993],
    corrected 1024-carve CI [0.0197, 0.0212] — all match `audit_rederivations.json`; "four
    measured laws, three conjectures, eight corrections, 99-candidate search" in the page footer
    all trace.
11. **No-overclaim scan:** the "not claimed" sections (no customer/user/partner/buyer, G5
    uncleared and in the weakest class, every number a 4096-byte-window number, 1024 failure
    stated at equal force) are consistent with `coverage.json`, the carve artifacts, and
    VERDICT.md. "Transfer 0.0403 — chance" mirrors VERDICT's own "collapsed to chance" framing
    (0.0403 vs chance 0.038462) and was not filed.

## COULD NOT VERIFY

- That "two full-pipeline replications are running" (page seed panel) was true at render time —
  only the seed-7 artifact has landed; no artifact records a second run in progress.
- The merge-commit / commit-history precedence claims in DILIGENCE.md and VERDICT.md (git
  commands are off-limits to this review; `.git/logs/HEAD` was read as a file only to confirm the
  page's render commit 302aa93 is two commits behind, for Finding 4).
- The live NIST/drand beacon values behind the anchors (network verification out of scope; the
  banked anchor fields were checked for presence and shape only).
