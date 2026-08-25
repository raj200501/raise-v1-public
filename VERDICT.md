# Verdict

Every result, passes and failures at the same size, each reconciling to a machine-readable
artifact under `artifacts/`.

---

## Phase 0 — TERMINATED: NO VIABLE DOMAIN FOUND

The search for a domain in which to reproduce the FDM-1 structure was run to three rounds and
stopped by a rule frozen before the last round ran. It did not find one.

| | |
|---|---|
| **Verdict** | `NO_VIABLE_DOMAIN_FOUND` |
| **Emitted by** | `tools/readers/phase0_verdict.py`, frozen and hashed before the data existed |
| **Governed by** | `prereg/0001-phase0-terminal-verdict.json`, chain seq 1 |
| **Anchored to** | NIST Beacon 2.0 pulse 1916929 · drand round 6406735 |
| **Reader unchanged since freeze** | yes — `python3 tools/prereg.py verify` |
| **Artifact** | `artifacts/phase0/phase0_verdict.json` |

Candidate domains generated: **99**, across three rounds, before any was selected.
Candidates put through adversarial review with default posture REJECT: **8**.
Candidates that received an adversarial SELECT: **0**.

This is the outcome the task explicitly permitted, and it is filed as a finding rather than as
a failure. A search that must return a domain will invent one.

### A note on letter versus substance

The frozen clause reads: *"Zero adversarial reviews (e.g. every survivor failed G4) is
`NO_VIABLE_DOMAIN_FOUND`."* The realised path differed from the parenthetical's example — in
round 3 nothing survived the *screen*, so no white-space check and no adversarial review ever
ran. The letter covers it, since the parenthetical is an example and not a condition. The
substance agrees, since zero survivors is a *stronger* negative than survivors who failed G4.
Both point the same way. It is recorded because they could have pointed differently, and the
rule in that case is to take the reading that does not flatter us.

---

## What the search actually produced

The useful output is not the absence of a domain. It is three laws, each derived by measurement,
and a precise statement of the class of problem that would work — which no candidate had.

### L1 — Smooth reprocessing corrections are fitted, not learned

A cubic polynomial plus a once-per-revolution sinusoid — about ten lines, no learning — explains
between 0.946 and 0.994 of the residual variance in eight of nine Sentinel-1 orbit-correction
component-arcs. This retires the entire *"an agency later revises its own product"* family:
orbit corrections, tide-gauge and streamflow revisions, precipitation reanalysis, altimetry
reprocessing, definitive magnetometer data, air-quality certification. They are curve fits.

### L2 — An analytically invertible generator yields a closed-form inverse that takes the whole label

Four candidates died to this in one round: NMR apodization read off the reconstructed FID,
cryo-EM sharpening off a Guinier plot, halftone screen parameters off a 2-D FFT, read aligner off
the MAPQ value set. Only lossy, non-invertible generators are candidates at all.

### L3 — For labels to be free at scale, the labelling must already be someone's job or by-product — and there are exactly three ways that happens, each destroying a different gate

**(i) A machine does it.** Then the machine is re-runnable, and *re-run-and-compare* is a
zero-training decoder. Six CDCL SAT solvers, same instance, models kept and trajectories discarded —
**reproduced independently here, and the only law whose evidence is primary-verifiable.** Re-solving
returns the byte-identical model in 1530 of 1530 checks; all six solvers agree on 0 of 3,000
instances; the free decoder reaches 0.9857 with zero training rows; a learned model on joint features
reaches 0.18 at 13,500 rows against 0.1667 chance. The originating subagent reported a
faster-improving learned arm and **that part did not reproduce** — filed in `CORRECTIONS.md`, and
neither slope figure is quoted as established.

**(ii) An institution reveals it on a schedule.** Then the revelation channel is a published,
well-known data product — which is precisely why the field already built the tool, and why the
buyer's incumbent is "wait" or "buy the better feed". Four direct efforts found on hidden-liquidity
prediction; four more on offer-curve inverse optimisation.

**(iii) A human records it in a register.** And *a register publishes the decision, not the state.*
Registers exist for accountability, not prediction: twenty to forty audited fields whose channel
capacity is fixed and small. On the UK MOT archive — no licence problem, no crowding problem, no
effective-N problem, roughly 38 million vehicles — an untrained two-term rule scores AUC 0.6553 and
beats the learned model at every *n* below about 30 thousand; 1.58 orders of magnitude of extra data
buys 0.0203 AUC; and the same vehicle's own previous outcome predicts its next at AUC 0.5077.

### Why VPT escapes and nothing in 99 candidates does

There is a fourth case, and the pool contained zero instances of it. In VPT the label is a
by-product of a human acting on a **rich sensor stream**, where the stream itself is the published
artifact. Case (iii) fails for a reason worth stating exactly: **a register row is a *description*
of a decision; a video frame is a physical *effect* of one**, at 20 Hz across two million pixels.
The MOT tester put the car on a ramp. The fire officer stood in the burned room. In each case the
private information is the whole of the evidence and the public artifact is an identifier and a
date.

> **The class that would work: a high-bandwidth physical recording that is the causal consequence
> of the hidden variable, published in bulk for a reason unrelated to the label.**

That is a usable specification for a fourth round, and it is the most valuable thing the search
produced. It is not a claim that no such domain exists — only that this search, framed around
machine generators, scheduled revelations and decision registers, did not contain one.

---

## Results at the same size, passes and failures alike

### Passed

| Result | Value | Class |
|---|---|---|
| Every gate can be shown to fail | 38 mutations, 38 detected, 0 survived | primary-verifiable |
| Preregistration chain verifies, reader unchanged since freeze | 1 entry, head `cfcc915c…` | primary-verifiable |
| Census leak reproduced first-hand | mean AUC 0.8026 from a one-line rule, 0 training rows | primary-verifiable |
| ACS PUMS record count reproduced | 392,318 records | primary-verifiable |
| Instrument reproduces on a cold clone | preflight names cause and fix | primary-verifiable |
| SAT free decoder re-derived | 0.9857 with zero training rows, against 0.1667 chance | primary-verifiable |
| Assembly-provenance split leak re-derived | temporal split 0.4765 **loses** to a 0.4805 constant | primary-verifiable |
| Assembly-provenance confound re-derived | a fake BioProject partition is predictable at 0.7772 | primary-verifiable |

### Failed, or did not reach a conclusion

| Result | What happened | Class |
|---|---|---|
| **Phase 0 domain selection** | **Terminated with no domain. 99 candidates, 8 adversarial reviews, 0 SELECT.** | arithmetic-verifiable |
| Phase 1 (falsify the data thesis) | **Not started.** There is no domain to falsify a thesis about. | n/a |
| Phase 2 (the scaling curve) | **Not started, and this is the headline absence.** The machinery to fit and interval a slope is built and mutation-tested; no slope has been fitted, because no domain was selected. | n/a |
| Phase 3 (credibility artifact) | Partially delivered. The *instrument* ships and reproduces; the intended open dataset or weights do not exist. | n/a |
| Round 3 screener's own arithmetic | Reported 11 adversarial reviews. Recounted from the banked artifacts: **8**. The screener's candidate total of 99 is correct. | arithmetic-verifiable |
| Our own allocation-flag count | Recorded 76 against a subagent's 77 and filed it as *the subagent's* discrepancy. The subagent was right. Filed in `CORRECTIONS.md` at full size. | primary-verifiable |
| **A scaling-rate figure we published** | Stated the learned SAT arm at 0.2384 and +2.8 points per decade. Our own reproduction gives 0.18 and +1.21, in the direction that flatters our conclusion. **Not reproduced.** Filed in `CORRECTIONS.md`. | neither |

---

## Verification coverage

Machine-checked by `python3 tools/coverage.py`, which refuses to let a claim be filed as
primary-verifiable unless the command that re-derives it exists in this repository.

**The weakest row, stated loudest:**

> **9 of 27 claims are in `neither`.** They can be neither re-derived nor re-run by anyone,
> including us. Eight are subagent measurements made inside ephemeral scratch directories that no
> longer exist, with no script banked and no inputs retained. **The ninth is worse than unverified:
> it is a figure this repository actively tried to reproduce and could not.**
>
> **This includes the measurements that close the search.** The Sentinel-1 fit that retires an
> entire candidate family under L1. The MOT numbers that are the strongest single piece of evidence
> for L3(iii). The javac byte-identity result. The ELF base-address entropy. A reader who declines
> to take a subagent's word for those is left with the laws unproven, and would be right to.
>
> Two of the load-bearing measurements have since been pulled out of that class by re-deriving them
> here from public data with shipped code — the census leak and the SAT-solver decoder. Reproducing
> the second one **contradicted a figure this repository had already published**, in the direction
> that flattered its own conclusion. That is filed in `CORRECTIONS.md` at full size rather than
> resolved by adopting the better-looking number. The rest have not been re-derived, and are marked
> accordingly rather than quietly upgraded.

| Class | Count | Meaning |
|---|---:|---|
| `neither` | **9** | Cannot be re-derived or re-run. Eight asserted from sources we cannot reproduce; one actively failed to reproduce. |
| `arithmetic-verifiable` | 5 | Follows by arithmetic from a banked artifact, but the artifact rests on our run. |
| `primary-verifiable` | 13 | A stranger can re-derive it from raw inputs with the shipped code. |

Three of the four load-bearing subagent measurements have now been pulled out of the weakest class
by re-deriving them here — the census leak, the SAT decoder, and the assembly-provenance split leak.
The last of those was only possible because that reviewer happened to write its inputs into the
repository instead of a scratch directory, which is luck rather than process, and is recorded as
such in `data/asmprov/README.md`.

---

---

## Why a fourth round is not being run here

The finding names the missing class precisely enough to search for it directly. A fourth round
aimed at *high-bandwidth physical recordings that are the causal consequence of a hidden variable*
is the obvious next move, and it would be a genuinely different search rather than a rerun.

It is not being run, for one reason: **preregistration 0001 says it may not be.** Its frozen scope
reads *"It does not license a fourth round: under this preregistration, a round-3 result with no
qualifying candidate terminates Phase 0."*

Running one anyway would require a new preregistration superseding that clause — written, on this
timeline, *after* seeing a result we did not like. That is exactly the move the whole discipline
exists to prevent: the bar was frozen, it was not cleared, and the bar moved. The fact that the new
round would be well-motivated is not a defence; a well-motivated bar change made after seeing the
number is still a bar change made after seeing the number.

So it is flagged rather than taken. **A fourth round is a decision for the principal, not for the
process that just failed to clear its own bar.** If it is authorised, it needs its own
preregistration, frozen before it runs, that states in its own scope that it was opened in response
to this negative result and what would make it stop.

## An instruction that could not be followed

The task specified: *"Stop only for the three things listed under STOP CONDITIONS."* **No STOP
CONDITIONS section was present in the instructions given.** Rather than guess at three conditions
and act as though they had been specified, this is recorded as `COULD NOT VERIFY`.

In their absence, the explicit stop instruction in the Phase 0 section was applied — *"If nothing
clears all five gates, write that, commit it, and STOP."* That is what happened. If the three
missing conditions would have produced a different stopping point, that is a gap in the record and
not a judgement that was made.

## What this repository does not establish

- **It does not establish that a viable domain does not exist.** It establishes that a search of
  99 candidates across three framings did not find one, and it names the framing that was missing.
- **It contains no scaling curve.** The slope fitter, its paired bootstrap, its permutation test and
  its scope refusals are all built and mutation-tested against synthetic data. No real slope has
  been fitted.
- **It has no customers, no users and no partners.** None are claimed anywhere.
- **Most of its findings rest on subagent measurements** that have not been independently
  reproduced, as the coverage map states in detail.
