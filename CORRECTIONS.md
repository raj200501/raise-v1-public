# Corrections ledger

Every claim withdrawn or revised, dated, at the same size as the claim it replaces.

The rule (`docs/OPERATING_RULES.md` §5): an over-claim against our own interest is still an
over-claim and gets filed here at full size. Entries are append-only. Nothing is deleted; a
correction that is itself wrong gets a further entry.

Format:

```
## YYYY-MM-DD - <one-line description>
**Claimed:**   what was said, quoted, with where it was said.
**Actual:**    what is true, with the artifact that establishes it.
**Size:**      how much the claim moved, in the units of the claim.
**Cause:**     why the wrong version was written.
**Fix:**       what changed in the instrument so this class of error is caught next time.
```

---

## 2026-08-25 — Called the round-3 finding "a usable specification"; it is not white space

**Claimed.** In `VERDICT.md`: *"The class that would work: a high-bandwidth physical recording that
is the causal consequence of the hidden variable, published in bulk for a reason unrelated to the
label. … That is a usable specification for a fourth round, and it is the most valuable thing the
search produced."* Amplified in `outbound/ONE_PAGER.md` as *"That is a usable specification, not a
consolation."*

**Actual.** Round 4 checked that class first-hand and found it **occupied wherever it was probed**.
Five instances, five crowded:

| Instance in the class | What is already there |
|---|---|
| chess clock traces → rating | *Chess Rating Estimation from Moves and Clock Times Using a CNN-LSTM* (arXiv 2409.11506, Springer 2025) — the proposal itself, and it reports that clock usage carries skill information board-only models cannot recover. Plus RatingNet, *Predicting Chess Player Rating Based on a Single Game* (2023), ChessMimic (2026). |
| GNSS SNR → antenna / signal condition | An established multipath and NLOS classification literature, 2021–2025. |
| hydrophone recordings + AIS → ship | *Automated data curation for self-supervised learning in underwater acoustic analysis* (arXiv 2505.20066) pairs AIS with bulk passive-acoustic recordings to pseudo-label a large unlabelled corpus for SSL — **the FDM-1 structure itself, already built**. Plus Oceanship (arXiv 2401.02099). |
| LIGO strain → detector data quality | `iDQ`, a supervised learner on thousands of auxiliary channels, **in production across four observing runs**, with a 2024 performance paper. Plus Gravity Spy. |
| open radio archives → signal state | Adjacent to RF modulation classification, already on the pre-existing kill list. |

A general search confirms the shape: pseudo-labelling a large unlabelled sensor archive from weak or
independent supervision is a **named, surveyed methodology** across sensing disciplines —
pseudo-labeling, self-training, weak supervision — with its own review literature.

**Size.** This retracts the single most positive-sounding output of the entire project. It was the
one forward-looking sentence in a document that is otherwise a negative result, it was the line the
outbound one-pager led its closing section with, and it is now withdrawn as written.

**Precisely what survives and what does not.** What survives: the round-3 observation that the
99-candidate pool contained **zero instances of the class**. That is still true and still
interesting. What does not survive: the inference that the class is therefore **open**. Membership
in the class is not evidence of white space — the class is where every sensing discipline already
works. Five probes is not proof that every instance is occupied, and the corrected claim is the
narrower one: *the class is not white space by default, and every instance must be crowding-checked
individually.*

**Cause.** A finding about the *absence of something in our pool* was written up as a finding about
*the presence of an opportunity in the world*. Those are different claims and the evidence only
supported the first. It read well, it was the only encouraging thing in the document, and it was
not checked before being published — including into outbound copy. That combination is exactly how
an over-claim survives review.

**Fix.** Both documents now state the narrower claim and carry the five probes. Added to
`docs/OPERATING_RULES.md` §6: **a finding that something is absent from our sample is never written
as a finding that it is available in the world without a separate check** — and where the two get
conflated, the conflation is the error, not the wording.

## 2026-08-25 — Published a scaling-rate figure that our own reproduction does not reproduce

**Claimed.** In `docs/_domain_selection_analysis.md`, under law L3(i): *"a learned model on 27 joint
features scores **0.2384** at 13,500 rows, rising **+2.8 accuracy points per decade**. Closing that
gap needs roughly 27 more decades of data."* Repeated in `VERDICT.md` as *"climbs only a couple of
accuracy points per decade"*. Both were taken from a subagent's measurement and stated as fact.

**Actual.** Re-derived here from scratch with six real CDCL solvers via PySAT
(`tools/repro/sat_solver_identity.py`, banked in `artifacts/verification/repro_sat_comparison.json`),
at the same top rung of 13,500 training rows: the learned model reaches **0.1800**, not 0.2384; the
slope is **+1.21** accuracy points per decade, not +2.8; and the gap closes in **66.6** decades, not
27. Three other figures from the same subagent *did* reproduce — determinism exactly (1530 of 1530
re-solves returning the byte-identical model), the free decoder closely (0.9857 against 0.9863), and
the divergence result more strongly (all six solvers agreed on 0 of 3,000 instances against 0 of 339).

**Size.** One of three headline numbers in one of the three laws that close Phase 0, wrong by more
than a factor of two on the slope and by a factor of 2.5 on the decades. The qualitative claim — a
free zero-training decoder near 0.986 against a learned model near the 0.1667 chance level, with a
gap no realistic quantity of data closes — survives intact and is if anything strengthened.

**Cause, and the part that matters.** The error runs in the direction that *flatters our own
conclusion*: a weaker learned arm makes law L3(i) look stronger. That is precisely why it cannot be
quietly corrected by adopting the better-looking number. The most likely explanation is **not** that
the subagent was wrong but that **the feature set implemented here is worse than the one it used** —
both of our runs sit barely above chance, which is what an underpowered feature set looks like. The
subagent's code lived in an ephemeral scratch directory and is gone, so the two implementations
cannot be diffed and the cause cannot be established. Underlying all of it: a number measured by a
subagent, in a directory that no longer exists, was written into a published document as though it
were established.

**Fix.** Three changes, all made. (1) Neither figure is quoted as established anywhere. The documents
now state the qualitative claim, cite the reproduced numbers as reproduced, and record the subagent's
as not reproduced. (2) The reproduction ships as runnable code and both runs are banked, including
the first run that could **not** reach the top rung — kept so the run that did cannot be mistaken for
the only one. (3) `artifacts/verification/coverage.json` now carries an explicit `neither` row for
the subagent's SAT figures whose stated reason is that this repository tried to reproduce them and
could not.

## 2026-08-25 — Miscounted the ACS PUMS allocation-flag columns, and blamed a subagent for it

**Claimed.** In `artifacts/phase0/reproduction_alloctrace.json`, first version, under
`discrepancies`: the round-2 reviewing agent reported "77 contiguous allocation flags" in the
2023 ACS PUMS person file; this repository recorded "76 columns match the filter
`startswith('F') and endswith('P')`" and assessed the gap as "a naming-filter difference, not a
substantive disagreement", listing it as a discrepancy in an artifact whose stated purpose was
checking the agent's work.

**Actual.** There are exactly **77** allocation flags, and the agent's count was right. The
person file has 80 columns beginning with `F`; three of them — `FER` (gave birth in the past 12
months), `FOD1P` and `FOD2P` (recoded field of degree) — are substantive data variables that
merely start with `F`. Three genuine flags end in `C` rather than `P` (`FHINS3C`, `FHINS4C`,
`FHINS5C`), which is why the filter used here does not return 77. The full column list is in the
banked artifact and can be recounted by anyone.

**Size.** One column in an absolute count (76 vs 77, 1.3% of the count). Substantively larger
than that: the entry appeared in a verification artifact, under a heading that reads as "what
the agent got wrong", and it recorded a defect in this repository's own check as though it were
a defect in the thing being checked. The direction of the error is the part that matters. An
independent-verification artifact that manufactures a discrepancy is worse than one that finds
none, because its whole value is that its findings can be trusted in both directions.

**Cause.** A regex-shaped assumption — that PUMS allocation flags are exactly the columns
matching `F*P` — was written into a one-off check and never tested against the data dictionary,
then reported as a measurement. It is the same failure this repository has spent two rounds
killing in other people's candidates: a heuristic mistaken for ground truth. It was caught only
because the raw column list was printed alongside the count, which is luck, not process.

**Fix.** Two changes, both made. (1) The artifact now records 77 with its derivation stated
explicitly, so the count can be checked without rerunning anything. (2) The standing rule, now
in `docs/OPERATING_RULES.md` §8: a count derived from a *pattern over names* is not a
measurement until the pattern has been checked against the authoritative definition, and any
artifact reporting such a count must print the derivation beside it. Where a check disagrees
with the thing it is checking, the check is assumed wrong until it is shown otherwise.
