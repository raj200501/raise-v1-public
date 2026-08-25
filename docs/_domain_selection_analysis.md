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
