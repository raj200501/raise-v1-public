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

> **The class the pool lacked: a high-bandwidth physical recording that is the causal consequence
> of the hidden variable, published in bulk for a reason unrelated to the label.**

**That class was checked in round 4 and it is not white space.** Every instance probed was already
occupied — chess clock traces, GNSS SNR, hydrophone recordings paired with AIS, LIGO strain paired
with auxiliary channels, open radio archives. In one case the occupant is the FDM-1 structure
itself: AIS used to pseudo-label bulk passive-acoustic recordings for self-supervised learning. And
the shape has a name and a survey literature — pseudo-labelling a large unlabelled sensor archive
from weak or independent supervision is the standard playbook of every sensing discipline.

What survives is the narrower claim: the pool contained zero instances of the class, and membership
in the class is **not** evidence of white space. Each instance still needs its own crowding check.
The wider claim — that this was "a usable specification" — is withdrawn in `CORRECTIONS.md`.

---

## Results at the same size, passes and failures alike

### Passed

| Result | Value | Class |
|---|---|---|
| Every gate can be shown to fail | 67 mutations, 67 detected, 0 survived | primary-verifiable |
| A number that is real but STALE is caught, not just a fabricated one | `tools/freshness.py`, 9 mutations | primary-verifiable |
| Preregistration chain verifies, reader unchanged since freeze | 5 entries, head `8ebe55a5…` | primary-verifiable |
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
| **Three numbers in this document went stale** | The chain length, the coverage denominator and the primary-verifiable count kept being published after they stopped being true. The outbound gate passed all three, because a stale number is still a real one. Second instance of this bug; filed in `CORRECTIONS.md` with the general fix. | primary-verifiable |
| **A scaling-rate figure we published** | Stated the learned SAT arm at 0.2384 and +2.8 points per decade. Our own reproduction gives 0.18 and +1.21, in the direction that flatters our conclusion. **Not reproduced.** Filed in `CORRECTIONS.md`. | neither |

---

## Verification coverage

Machine-checked by `python3 tools/coverage.py`, which refuses to let a claim be filed as
primary-verifiable unless the command that re-derives it exists in this repository.

**The weakest row, stated loudest:**

> **9 of 37 claims are in `neither`.** They can be neither re-derived nor re-run by anyone,
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
| `arithmetic-verifiable` | 6 | Follows by arithmetic from a banked artifact, but the artifact rests on our run. |
| `primary-verifiable` | 22 | A stranger can re-derive it from raw inputs with the shipped code. |

Three of the four load-bearing subagent measurements have now been pulled out of the weakest class
by re-deriving them here — the census leak, the SAT decoder, and the assembly-provenance split leak.
The last of those was only possible because that reviewer happened to write its inputs into the
repository instead of a scratch directory, which is luck rather than process, and is recorded as
such in `data/asmprov/README.md`.

---

---

---

## EphemErr — `A2_FAILED`, by less than one part in ten of the bar

The one candidate the archived search resurrected under an "effort" lens: predict, from a GPS
broadcast ephemeris record alone, whether that record's signal-in-space range error will exceed
its 0.90 quantile at a future epoch. Free labels — the truth is the precise orbit and clock
product IGS publishes days later, so the environment supplies the answer key at zero marginal
cost, forever.

| | |
|---|---|
| **Verdict** | `A2_FAILED` |
| **Emitted by** | `tools/readers/ephemerr_a2_verdict.py`, frozen and hashed before the data existed |
| **Governed by** | `prereg/0005-ephemerr-a2`, chain seq 5 |
| **Artifact** | `artifacts/ephemerr/a2_result.json` |

| Reading | Value |
|---|---:|
| Learned model, held-out AUC | 0.9821 |
| Best trivial baseline (`per_satellite_mean`) | 0.9363 |
| **Margin** | **0.0458** against a frozen bar of **0.05** |
| Null control (labels shuffled) | 0.4804 |
| Split | temporal — train on days 1–15, test on 16–21 |
| Test epochs / satellites | 51839 / 30 |

### The pipeline was validated before the bar was applied

An instrument that has never been checked against a known answer cannot fail honestly. Two bugs
were found and fixed *before* any bar was applied, both by validating magnitudes against published
values rather than by inspecting code:

- The GPS epoch constant was **2444244** instead of **2444245**. Symptom: **729** km position
  errors and 799 of **9248** epochs matching. Published broadcast orbit error is one to two metres,
  so this was not a subtle discrepancy. After the fix, orbit RMS **1.386** m radial, **0.863** m
  along-track, **0.520** m cross-track — the textbook range.
- The clock column of an orbit-only SP3 product was used where a separate clock product was
  needed. Fixing it left the residual unchanged, which **ruled the hypothesis out rather than
  fixing anything**. Recorded, because a ruled-out hypothesis is still evidence.

### The gate caught what the pre-run analysis did not

Before the run, the anticipated killer was the operator's own broadcast accuracy index (URA/SISA),
shipped free inside the student's input. It measured **0.5037** — a coin. The actual killer was
**satellite identity**: a per-satellite historical mean scores **0.9363** on its own. Six earlier
candidates died to the same shape, which is why the A2 clause exists and why it is applied before
any learned number is believed.

### A calibration observation, recorded and deliberately NOT applied

An absolute margin of 0.05 against a baseline already at 0.9363 demands more than **three
quarters** of all the headroom that remains above it — a far harder bar than the same 0.05
against a baseline at 0.5, where it demands a fraction of the room available. That is a real
argument, it was noticed *after* the result missed, and acting on it would be moving the bar to
admit a result it excluded. **The verdict stands as `A2_FAILED`.** The observation is filed as
guidance for future preregistrations — margins against high baselines should be specified in
headroom, and specified before the data exists.

---

## Round 4 — authorised by the principal, and it also found nothing

A fourth round was authorised after the verdict above, under a **new preregistration frozen before
any candidate was chosen** (`prereg/0002`, chain seq 2, anchored to a beacon pulse eleven hours
after 0001's, so the ordering of the two is externally provable). Its bar moved **up**, not down:
rounds 1–3 admitted argued evidence, and four of this round's seven clauses require a **measured**
value and reject an estimate however confident the prose around it. It cannot overturn 0001.

**Verdict: `NO_VIABLE_DOMAIN_FOUND_ROUND4`.** Five candidates considered, all five G4-dead; one
measured, and it failed two clauses.

### Its finding is a retraction of ours

Round 3 named a class the pool lacked and this repository published that as *"a usable
specification."* Round 4 checked the class first-hand and **found it occupied at every instance
probed** — chess clock traces, GNSS SNR, hydrophone recordings paired with AIS, LIGO strain paired
with auxiliary channels, open radio archives. In one case the occupant is the FDM-1 structure
itself. Pseudo-labelling a bulk unlabelled sensor archive from weak supervision has a name and a
survey literature; it is the default of every sensing discipline. Filed in `CORRECTIONS.md`.

### The instrument was finally run on real data

Until this round, every part of the Phase 2 apparatus had only ever been exercised on synthetic
fixtures. An instrument that has only measured its own test data has not been shown to work. So it
was run end to end on 400,000 real units from a CC0 corpus — deliberately on a **G4-dead** domain,
because a domain that cannot be selected gives no incentive to flatter the result. It fired
correctly three times:

1. `tools/scaling.py` **refused** the three-rung dataset with exit code 3, citing the preregistered
   four-rung scope. The scope gate fires on real data, not just on fixtures.
2. With four rungs spanning 2.4771 decades it produced a real fit: **+0.0338 accuracy points per
   decade**, paired-bootstrap 95% interval **[0.0306, 0.0369]** excluding zero, r² 0.9794.
3. The **A2 clause rejected the candidate anyway**: its measured margin over the best trivial
   baseline is **0.0313**, below the **0.05** frozen before this data existed.

So this repository does now contain a real, fitted, interval-bounded scaling curve — on a domain
that cannot be selected, that fails its own preregistered margin, and whose last half-decade of
data bought 0.0032. It is a validation of the instrument. It is not a result about the world, and
it must not be quoted as one.

## Why a fifth round is not being run here

Round 4 was not taken unilaterally. Preregistration 0001's frozen scope forbade it, and opening a
round after a result you did not like is exactly the move the discipline exists to prevent. So it
was flagged as a decision for the principal, authorised by them, and then run under its own
preregistration whose scope records — in a field named `opened_in_response_to` — that it was opened
because of a negative result, and whose bar moved up rather than down.

Preregistration 0002 forbids a fifth round on the same terms. If one is wanted, it needs its own
preregistration, frozen before it runs, saying the same things about itself.

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
- **It contains no scaling curve that means anything.** One real curve has now been fitted, with a
  real interval, on real data — but on a domain that is G4-dead, that fails its own preregistered
  A2 margin, and that was chosen *because* it could not be selected. It validates the instrument
  and says nothing about the world.
- **It has no customers, no users and no partners.** None are claimed anywhere.
- **Most of its findings rest on subagent measurements** that have not been independently
  reproduced, as the coverage map states in detail.
