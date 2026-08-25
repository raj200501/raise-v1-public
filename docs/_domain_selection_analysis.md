## The finding that changed the gates

VPT worked for a reason that is easy to state and easy to miss. The inverse dynamics model
saw **future frames**. The student, at inference time, sees only the past. So the IDM held
information the student's input could not contain, and distilling it pulled the student
toward a target above its own reach.

Round 1 produced a candidate in which that relationship is exactly inverted, and it took an
adversarial reviewer measuring the real data to see it. The serial-crystallography proposal
was to run CrystFEL across the public archive and treat every pattern it successfully indexes
as a free labelled example. But **CrystFEL sees precisely the same peak list the student
sees.** There is no extra information anywhere in the loop. Training on those labels is
distillation, and distillation ceilings at the teacher. Worse, the commercial claim was to
index the 33–50% of patterns classical indexers *discard* — which is exactly the population
for which no label can be manufactured. The manufacturer is definitionally blind to the
population the thesis is about.

That failure is invisible to G1–G5 as originally written. A mechanism can be abundant, free,
legal, uncrowded and commercially attractive, and still be worthless because it cannot teach
anything its student could not already have learned. So it becomes a gate, and it is applied
from here on:

> **G2a — INFORMATION ASYMMETRY.** The label manufacturer must have access to information the
> student's input does not contain. If the manufacturer sees exactly what the student sees,
> the study is distillation, its ceiling is the teacher, and the curve flattens there.

Applying G2a retroactively to the round-1 survivors is clarifying rather than decorative:

| Survivor | What the manufacturer knows that the student cannot | G2a |
|---|---|:--:|
| Inverse Linking | DWARF debug info, deleted from the stripped input | pass |
| Compressed-stream provenance | the exact `argv` the encoder was invoked with | pass |
| JVM build-provenance | the `MANIFEST.MF` declaration, deleted from the input | pass |
| Headerless load-layout | the ELF/PE header, deleted from the input | pass |
| CopybookLM | the generator's copybook | pass |
| ProcedureNet | the coded ARINC 424 procedure, absent from the trajectory | pass |
| Serial crystallography | **nothing** — CrystFEL sees the identical peak list | **fail** |

### Three more failure modes round 1 surfaced

Each of these killed a candidate, each was found by measurement rather than argument, and
each is cheap enough to test that it should be tested *first* from now on.

**1. Zero channel capacity — the label is not a function of the input.** The JVM reviewer
downloaded four JDKs, compiled a real 345-class library under each, and byte-compared the
output. `javac 17.0.8` and `javac 17.0.13` at `--release 8` produced 345 of 345 byte-identical
class files. Not "hard to distinguish" — *identical*. The proposed headline label carries zero
bits, and no quantity of data raises a curve over a channel of zero capacity.
→ *Before anything else, verify the label actually varies with the input.*

**2. Heuristic-shaped labels.** The CopybookLM reviewer wrote a ~50-line rule with no learning
in it and reached exact-boundary F1 0.768 from 20 records; 20,000 records bought 1.4 points.
Most of the label mass was a regex over EBCDIC nibble ranges. A manufactured label that a
regex mostly solves leaves a curve drawn over a residual.
→ *Write the dumbest possible non-learned baseline first, and measure it before building anything.*

**3. Corpus terms that forbid this specific use.** Maven Central's `robots.txt` reads
`Content-Signal: search=yes,ai-train=no,use=reference` followed by `Disallow: /`. G1 is not
"can the bytes be fetched". It is "may we use them this way, and may we redistribute what we
build" — because Phase 3 requires shipping an open artifact.
→ *Read the actual terms of the actual corpus before scoring G1, not after.*

## Where round 1 leaves us

**No candidate cleared all the gates.** Of four finalists reviewed adversarially: zero SELECT,
two BACKUP, two REJECT. The two rejections were decisive and were established by measurement.
The two BACKUPs each survive only in a narrowed regime:

- **Compressed-stream encoder provenance** survives only for *carved fragments with no
  plaintext and no stream start*, because every incumbent tool — `preflate`, `precomp`,
  `grittibanzli`, `list-compresslevel.py` — needs one or the other, and brute-force
  recompression needs the plaintext. That narrowing is real and the reviewer measured signal
  in it (trivial baselines at 0.235 against 0.111 chance; unscaled logistic regression at
  chance across every feature set). But the reviewer also found that the white-space claim as
  originally written is falsified by `microsoft/preflate-rs`, which fingerprints encoder
  implementation and parameters in production. G4 is weaker than the round-1 score suggests.
- **Serial-crystallography indexing** fails the new G2a outright, as set out above.

### This is not "no viable domain found" — yet

That verdict is a permitted and legitimate terminal outcome, and it will be issued if the
evidence supports it. It does not yet, in both directions:

1. **Two screened survivors were never adversarially tested.** *Headerless load-layout
   recovery* and *ProcedureNet* were cut by a mechanical top-4 slice, not by a judgement.
   Neither has been attacked.
2. **Two of the four adversarial reviews ran with their web-search quota exhausted** and fell
   back to direct arXiv/Europe PMC fetches. Their on-box measurements are first-hand and
   strong; their external-evidence coverage is weaker than it looks, and is recorded as such.
3. **The candidate pool was generated before G2a existed.** A pool generated *with* the
   asymmetry requirement, and with these three failure modes named as explicit anti-patterns,
   is a materially different search.

Declaring "no viable domain" on evidence this incomplete would be exactly the kind of
confident-but-unearned claim this project exists to avoid. Round 2 closes these three gaps
specifically. If round 2 also returns no SELECT, that is the answer and it will be written
down as the answer.

---

## Rounds 2 and 3: what closed the search

Round 2 ran the two survivors round 1 had never attacked, and generated a fresh pool organised by
*asymmetry structure* rather than by sector. Round 3 was declared the final round in advance, under
a preregistration frozen before it ran. Both returned zero.

### The three laws

Each was derived by measurement, not argument, and each retires a whole family of candidates.

> **L1 — Smooth reprocessing corrections are fitted, not learned.**
> Measured on three real Sentinel-1 RESORB/POEORB orbit arcs: a cubic polynomial plus a
> once-per-revolution sinusoid — about ten lines, no learning — explains 0.946 to 0.994 of the
> residual variance in eight of nine component-arcs; `poly5+2cpr` leaves 0.03–0.15 cm RMS.
> *Retires the entire "an agency later revises its own product" family: orbit corrections, tide-gauge
> revisions, streamflow revisions, precipitation reanalysis, altimetry reprocessing, definitive
> magnetometer data, air-quality certification. They are curve fits wearing a label.*

> **L2 — If the generator is analytically invertible, a closed-form inverse takes the whole label.**
> Killed four round-2 candidates outright: NMR apodization read off the reconstructed FID, cryo-EM
> sharpening off a Guinier plot, halftone screen parameters off a 2-D FFT, read aligner off the MAPQ
> value set. *Only lossy, non-invertible generators are candidates at all.*

> **L3 — For a label to be free at scale, the labelling must already be someone's job or someone's
> by-product. There are exactly three ways that happens, and each destroys a different gate.**
>
> Three scouts working independently in round 3 each derived a law and each numbered it L3. They are
> the same law seen from three sides:
>
> **(i) A machine does the labelling** — so the machine is re-runnable, and *re-run-and-compare* is a
> zero-training decoder. **Reproduced independently in this repository** with six real CDCL solvers
> (`tools/repro/sat_solver_identity.py`): re-solving returns the byte-identical model in 1530 of 1530
> checks; all six solvers agree on **0 of 3,000** instances, so this is not a zero-capacity channel;
> the free decoder reaches **0.9857** with no training at all; and a learned model on joint
> formula-assignment features reaches **0.18** at 13,500 rows against a chance level of **0.1667**.
>
> *The originating subagent reported a faster-improving learned arm (0.2384 at the same rung, +2.8
> accuracy points per decade). That did not reproduce — see `CORRECTIONS.md`. The disagreement runs in
> the direction that flatters this law, so neither slope figure is quoted as established; what the
> evidence supports is the qualitative claim, that a free decoder near 0.986 faces a learned model
> near chance across a gap no realistic quantity of data closes.*
>
> **(ii) An institution reveals it on a schedule** — so the revelation channel is a published,
> well-known data product. That is exactly why the field already built the tool, and why the buyer's
> incumbent is "wait" or "buy the better feed". Measured as four direct efforts on hidden-liquidity
> prediction and four on offer-curve inverse optimisation.
>
> **(iii) A human records it in a register** — and *a register publishes the decision, not the state*.
> Registers exist for accountability, not prediction: twenty to forty audited fields whose channel
> capacity is fixed and small. Measured on the UK MOT archive (OGL v3, ~38M vehicles, ~500M recorded
> decisions — no licence problem, no crowding problem, no effective-N problem): an untrained two-term
> rule `age/10 + mileage/100000` scores **AUC 0.6553** and beats the learned model at every *n* below
> ~3×10⁴; 1.58 orders of magnitude from 10⁵ to 3.8×10⁶ buys **+0.0203 AUC**; the entire prior-defect
> code history buys **+0.0004**; and the same vehicle's own previous outcome predicts the next at
> **AUC 0.5077**.

### Why VPT escapes and nothing in 99 candidates does

There is a fourth case, and the pool contains zero instances of it. In VPT the label is a by-product
of a human acting on a **rich sensor stream**, where the stream itself is the published artifact.

Case (iii) fails for a reason worth stating precisely: **a register row is a *description* of a
decision; a video frame is a physical *effect* of one**, at 20 Hz across two million pixels. The MOT
tester put the car on a ramp; the fire officer stood in the burned room; the delay-attribution clerk
read the signaller's log. In each the private information is the whole of the evidence, and the
public artifact is an identifier and a date. Consecutive video frames retain statistical evidence of
the action taken. A registration document retains almost none of what a mechanic decided about a set
of brake pads.

So the class that would work, named explicitly, is:

> **A high-bandwidth physical recording that is the causal consequence of the hidden variable,
> published in bulk for a reason unrelated to the label.**

Ninety-nine candidates across three rounds, and not one has it. That is not a failure of the gates.
It is the gates correctly reporting that the search space as framed — machine generators, scheduled
revelations, and decision registers — is exhausted, and that the one class that would work was never
in it.

### Two candidates that could not be cleared, recorded so they are not lost

- **UK rail delay attribution.** The only candidate whose artifact is genuinely high-dimensional (a
  graph of hundreds of trains' timings over an area and period), whose asymmetry is real without being
  total, whose label is a 250-way code no published rule derives from timings, and whose buyer pays
  nine figures a year for exactly this. Untestable here: the attribution labels moved to the
  registration-gated Rail Data Marketplace and the TRUST movement-data inputs have no open bulk
  historical release. **UNVERIFIED is not PASS**, and G1 as written demands a named licence with a URL.
- **PresetPrint.** The round-3 screener recorded a kill it could *not* sustain: this candidate's G4 is
  **not** crowded. It dies on G1 and G6, and a future round must kill it there rather than on a G4 it
  does not have.

### Two branches closed for reasons that are not gates

Scout A declined to develop two candidate shapes and said so: recovering precise locations from
statutorily generalised sensitive-species records, and redaction-span prediction on staged
declassification releases. Both are tools whose purpose is defeating a protection — one that exists to
stop people locating endangered species and sensitive sites. They are recorded here so the omission is
visible rather than silent.

## Terminal verdict

Preregistration `0001-phase0-terminal-verdict` was frozen — hash-chained, reader hashed, externally
time-anchored to NIST Beacon pulse 1916929 and drand round 6406735 — **before round 3 ran**. Its
frozen reader, unmodified since freezing and verified so by `prereg.py verify`, read the round-3
artifact and emitted:

> ## NO VIABLE DOMAIN FOUND

**A note on letter versus substance,** because the two could have disagreed. The frozen clause reads
"Zero adversarial reviews (e.g. every survivor failed G4) is `NO_VIABLE_DOMAIN_FOUND`." The realised
path was different from the parenthetical's example: nothing survived the *screen*, so no G4 and no
adversarial review ever ran. The letter covers it — the parenthetical is an example, not a condition —
and the substance agrees, since zero survivors is a *stronger* negative than survivors who failed G4.
Both readings point the same way, and this is recorded because they could have pointed differently.
