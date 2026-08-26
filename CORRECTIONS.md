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

## 2026-08-26 — Published a reading of our own null control that does not follow, and it understated our own result

**What was published.** The 0009 write-up, in `VERDICT.md` and as a coverage claim, read the null
control this way:

> The shuffled-label loss never moves from chance at all — **0.0006** across ten epochs. That is a
> clean null control, and it simultaneously says this architecture cannot memorise 100000 random
> labels. A model with no capacity to overfit may simply be too small, so part of "it failed" is
> "it was small".

**Why it does not follow.** A probe holding everything fixed except the final pooling layer:

| head | train accuracy on 5000 **shuffled** labels, 30 epochs |
|---|---:|
| global average pool — what 0009 used | 0.0486, against 0.0385 chance |
| flatten — position preserved | **0.364**, and still climbing steeply from 0.056 at epoch 20 |

Convolutional capacity is identical in both arms. The network could not memorise because a global
average pool **averages away per-example identity** — two fragments with the same local statistics
become the same vector, at any parameter count. It was not a shortage of capacity, and "it was
small" is not a supported reading of that number.

**Size.** One inferential step, in a caveat rather than a headline. But it is the caveat attached to
a *negative result*, and it is the sentence a reader would use to decide how much the negative is
worth — so it is load-bearing in the way caveats often are.

**Direction, and why it is worth naming.** This error ran **against us**: it manufactured a
weakness in our own finding that the evidence did not support, making the 0009 negative sound
flimsier than it was. Nearly every other entry in this ledger corrects an error that flattered us.
An unforced hedge is a smaller sin than an unforced boast, but it is the same failure — a statement
that the measurement did not license — and filing only the flattering ones would make this ledger a
performance rather than a record.

**What replaces it.** A narrower and better-supported caveat: 0009 tested one architecture whose
final pooling is a strong inductive bias, and whether that bias hurts the *task* is untested. Local
byte order may be exactly the right signal and position may be irrelevant, in which case the pool is
sensible and the negative stands cleanly.

**The generalisable lesson, which this repository should have reached on its own.** A null control
that the model **cannot fail** carries no information. `tests/mutation_test.py` exists because a gate
that cannot fail is decoration — and a control that cannot fail is decoration for exactly the same
reason. That argument was already written down here, applied to gates, and nobody applied it to
controls. Preregistration 0010 therefore adds a clause requiring a model to *demonstrate* it can
memorise shuffled labels before its null control is credited.

## 2026-08-25 — Broke CI with a stale mutation count for the THIRD time, after building the gate that catches it

**What happened.** I added 15 mutation tests for preregistration 0007's gate, took the suite from
81 to 96, and committed without updating the three places that carry that count: the
`mutations-detected` claim in `coverage.json`, the row in `VERDICT.md`, and the line in
`outbound/ONE_PAGER.md`. CI went red on `raj200501/raise-v1#1`.

**Why this one is worse than the first two.** The instrument caught it. `tests/mutation_test.py`
has carried a guard for exactly this since the first occurrence, and it printed exactly what it was
designed to print:

```
!! artifacts/verification/coverage.json claims 81 mutations, this run has 96.
!! Update the 'mutations-detected' claim or tools/coverage.py will fail and CI will go red.
```

**I did not see it, because I piped that command through
`grep -E "carve |MUTATION REPORT"` to keep the output short.** The filter I chose to read the
result with dropped the warning the result came with. Then I committed without running the gate
suite, because I had run *the tests* and treated that as the same thing.

So this is not a third instance of forgetting a number. It is the first instance of **defeating my
own instrument for convenience** — the warning existed, fired correctly, and was discarded by the
reader rather than missed by the writer.

**Size.** One CI cycle on an open pull request, and no published number was wrong for longer than
it took to notice — the gates that failed are the ones that stopped it reaching anyone. Against
that: the third occurrence of one bug class, with the second occurrence's fix in place and working.
A guard that a hurried reader can filter out of view is not a guard, and I am the hurried reader it
has to survive.

**Fix, in two parts.**

1. **The warning is now an exit code.** `tests/mutation_test.py` returns 1 when the banked claim
   disagrees with the run. An exit code cannot be grepped away. Verified by temporarily setting the
   claim to a wrong value and confirming the suite fails, rather than by assuming it would.

2. **`tools/gates.sh` runs every gate in one command**, in the order CI runs them, and CI now
   invokes that same script instead of listing the steps separately — so local and CI cannot drift
   apart, and "I ran the tests" stops being a different act from "I ran the gates".

   The script distinguishes a **pending** reader from a broken one: a frozen reader whose artifact
   does not exist yet exits 2, which is the normal state between freezing a preregistration and
   measuring it, and it is reported by name rather than treated as a failure. That leniency is safe
   only because a deleted result artifact is still caught elsewhere — every banked result is cited
   by a claim in the coverage map, and `coverage.py` fails on a claim whose artifact is missing.

**What it does not fix.** `gates.sh` has to actually be run. Nothing in this repository forces it
before a commit, and a pre-commit hook would live outside the committed tree where CI cannot see
it. The honest statement is that the guard now fails loudly in two places instead of one, and that
the remaining failure mode is a person skipping the command — which is what happened here.

## 2026-08-25 — Published three stale numbers in `VERDICT.md`, and the outbound gate passed all three

**What was published.** Three numbers in `VERDICT.md` describing the current state of the
instrument had stopped being true and kept being published:

| Row | Published | Actual at the time it was read |
|---|---|---|
| Preregistration chain | `1 entry, head cfcc915c…` | 5 entries, head `8ebe55a5…` |
| Weakest coverage row | `9 of 32 claims are in neither` | 9 of 36 |
| Coverage table | `primary-verifiable  17` | 21 |

All three were true when written. None was true when found. The chain row is the worst of them:
it is the row a reader would check *first* to decide whether anything else in the document can be
trusted, and it understated the instrument's own record by four preregistrations.

**Why the gate passed them.** `tools/claimcheck.py` asks: does this number appear in a banked
artifact at the precision written? For a fabricated number that is the right question. For a stale
one it is the wrong question, and the gate cannot be tuned into asking the right one — the old
value stays banked forever, so it keeps passing on its own merits. `cfcc915c` really is the hash
of chain entry 1. `17` really was the count. The gate was working exactly as specified and the
specification had a hole in it.

**Size.** Three numbers, in the document that exists to be the honest summary, one of them the
integrity claim about the preregistration chain itself. Against that: the direction is
*self-deprecating* in all three cases — fewer preregistrations, fewer primary-verifiable claims,
a smaller denominator on the weakest row. Nothing here flattered the work. That is luck rather
than process, and it is not a mitigation: a mechanism that lets stale numbers through lets
flattering ones through equally.

**This is the second instance of the same bug.** The first is the entry above, dated the same day:
the mutation count in `coverage.json` said 49 while the suite ran 58, CI went red for about an
hour, and the principal caught it before this repository did. That was patched with a one-off
guard inside `tests/mutation_test.py` comparing the two numbers. A one-off guard for one number
is not a fix for a class of bug, and writing a second one-off would have been the wrong response
to being shown the same failure twice.

**Fix.** `tools/freshness.py`, a gate that re-derives each live number from its artifact and fails
on divergence, driven by a data registry (`docs/live_claims.json`) so adding a claim needs no code
change. It is wired into CI and `tools/pivot/verify.sh`. On its first run against the unmodified
repository it failed, naming all three stale numbers — the failure above is the gate's own control
case, not a hypothetical.

Two design choices worth stating, because both could have been made the comfortable way:

- A registry pattern that **no longer matches** its document is a FAILURE, not a skip. Otherwise
  any claim escapes the gate by being reworded. This is the case that caught the chain row: the
  document said "1 entry" where the pattern wanted "entries".
- A **missing artifact** is a failure, not a skip. Absence is never a pass, the same rule the
  frozen readers already apply.

Nine mutation tests cover it, including the one that states the point: a stale count that
`claimcheck` still passes must make `freshness` fail. The suite is now 67 mutations across 8
gates, 67 detected, 0 survived.

**What it does not fix.** Only numbers entered in the registry are checked; a live number nobody
registers is still unguarded. The registry is a judgement call about which numbers describe the
present rather than a past measurement, and that judgement is not itself mechanised. A 2026-08-25
accuracy is *supposed* to stay what it was, so it must stay out of the registry — and the boundary
between those two kinds of number is drawn by hand.

## 2026-08-25 — Published a mutation count that did not match the repository, and broke CI for an hour

**Claimed.** `VERDICT.md`, `README.md` and `outbound/ONE_PAGER.md` all stated "38 mutations, 38
detected, 0 survived".

**Actual.** 49. Eleven mutation cases for the pivot reader were added and committed without
updating the claim, so for roughly an hour the published figure understated the instrument by
eleven cases and **GitHub Actions was red on every push in that window**.

**Size.** Small in the number, and it errs *against* our own interest — understating how many ways
the gates were shown to fail makes the instrument look weaker, not stronger. What is not small is
the process failure behind it.

**Cause.** The mutation tests were added, run, and committed — but `tools/coverage.py` was not run
before committing. Locally the gates are only green if you actually run all of them, and I ran the
one I had just changed. The stale claim then surfaced one gate later, in CI, where I was not
looking. **The user noticed the red CI before I did**, which is the part worth recording: an
unwatched gate is not a gate.

**Fix.** Two changes. (1) `tests/mutation_test.py` now compares its own case count against the
`mutations-detected` claim in the coverage map and prints a loud warning at the moment they
diverge, so the mismatch surfaces where it is created rather than one gate downstream.
`tools/coverage.py` remains the enforcing gate. (2) All four documents now read 49, from the
banked artifact.

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
