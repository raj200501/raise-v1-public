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

The useful output is not the absence of a domain. It is four laws, each derived by measurement —
three from the search, and a fourth from our own pivot — one conjecture that is explicitly *not*
measured, and a precise statement of the class of problem that would work, which no candidate had.

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

### L4 — A representation made of summary statistics over a fragment binds the result to the fragment's length, and the failure to transfer is total rather than graded

The first three laws came out of the search. This one came out of our own work, which is the only
reason it is stated with a narrower scope than the others.

Where the student's input is a fragment of variable length and the features are statistics computed
over that fragment, quality is bound to the length the model was trained at. Measured on the
carved-DEFLATE task at a matched training rung, shortening the window from 4096 to 1024 bytes:

- **Transfer is total, and the ceiling does not explain it** — the two preregistered halves of the
  evidence, banked under 0007: a 4096-trained model reaches 0.0403 on 1024-byte fragments against
  0.038462 chance, while the byte-identity ceiling barely moves (20.9125 → 20.79 distinct of 26).
- **Uniform degradation across feature subsets** — supporting evidence from a **diagnostic that is
  not preregistered and whose artifact says "not quotable as a result"**, quoted here with that
  label because L4's claim leans on it: six *overlapping subsets* (one is the full set; two are
  near-complements) degrade by ratios 0.5895–0.6275, a spread of 0.038. They are subsets, **not**
  the seven disjoint families the artifact defines — four of those (pair-hash, bit-runs, scalars,
  stored-block) were never measured alone, so "no family survives and none dies" is established
  only up to that resolution, and part of the ratio uniformity is mechanical column-sharing. An
  earlier version of this bullet called the subsets "families" and carried no diagnostic label;
  caught by adversarial audit, filed in `CORRECTIONS.md`.
- **Transfer is not graded, it is total.** A 4096-trained model on 1024-byte fragments reaches
  0.0403 against a chance level of 0.038462. Every feature is a window-length-dependent statistic,
  so the joint distribution at another length is systematically different rather than noisier.
- **The information loss does not explain it.** The byte-identity ceiling barely moves across the
  range — 20.9125 distinct streams of 26 at 4096 against 20.79 at 512 — so this is a property of the
  representation, not of the fragment.
- **Measured a second time, at 2048 bytes (0011).** Transfer lands at 0.0455 against 0.038462
  chance from a model that reproduced its own 4096 accuracy of 0.1965 first, and the within-size
  margin fails on every reading — by 0.0025 on the frozen set, by more on the stricter ones. L4
  rests on two shorter sizes, not one.

**What it retires.** Any candidate whose student receives a variable-size fragment and whose planned
representation is hand-engineered statistics over it. The result will hold at one size and the
buyer, who does not choose the size, will get another.

**Scope, stated because this law is ours and we have the most reason to overstate it.** It is
measured on one task and one family of hand-engineered statistics. When first written it noted that
no *learned* representation had been tested; two have since been tried under their own
preregistrations — 0009's byte CNN failed against its bars, and 0010's corrected-head variant came
back inconclusive — so the honest current statement is: one small learned architecture did not
rescue the task, and nothing tested rules out that a larger or differently-shaped one would. It
also does not follow that mixing training lengths would rescue such a task here: it could not,
because the within-size result at 1024 fails its own margin independently of any transfer question.

### C1 — a CONJECTURE, not a law: withholding the transform's input is what creates the white space, and it is the same thing that makes the market small

Everything above this line is measured. **This is not**, and it is labelled `C1` rather than `L5`
for that reason. It is an argued reading of this repository's own search record, which is the
weakest kind of evidence there is — our search, our framing, our blind spots.

The pattern it names is this. The identity-shortcut law says to hunt **transform** label factories
rather than **record** ones, because a transform's label varies within an entity while a record's
does not. The carved-DEFLATE task is the one candidate that survived that screen, and it survived
because the manufacturer's input — the plaintext — is withheld from the student. That withholding is
precisely why no incumbent tool applies: `preflate` needs the stream start, `precomp` needs the
plaintext, and a carved fragment has neither. **The withholding is the white space.**

But an artifact examined without the input that produced it, by someone who wants to know what
produced it, *is* a forensics problem. That is what forensics means. So the same withholding that
creates the white space also fixes the buyer: someone reconstructing provenance after the fact,
working on artifacts they did not generate. Those markets are real and they are small, and the
tooling in them is mature enough that G4 white space usually means the question is narrow rather
than that it is unclaimed.

If C1 is right, the FDM-1 shape does not fail here for want of a cleverer domain. It fails because
the property that makes a transform factory *findable* — a withheld input, hence no incumbent — is
the property that lands it in a low-value market, and the two cannot be separated by searching
harder.

**What would falsify it.** A transform label factory where the input is withheld for a reason other
than after-the-fact loss — withheld by privacy, by regulation, by physics, or by commercial
boundary, with the artifact still published in bulk. Those exist in principle. This repository's 99
candidates plus round 4 plus the market-timing search contained none that also cleared G4, which is
evidence about the search and not proof about the world.

**Why it is filed at all.** Because the alternative is to keep running rounds against a structural
constraint without naming it, and a conjecture that can be attacked is worth more than an unstated
assumption that cannot.

### C1's falsifier was hunted under its own preregistration, and not found — which sharpens C1 rather than proving it

`NO_FALSIFIER_FOUND`, from preregistration 0008 (chain seq 8), frozen before a single candidate was
enumerated. **14** candidates across all four non-loss withholding modes — privacy, regulation,
physics, commercial — default posture REJECT. None cleared.

**This does not promote C1 to a law**, and the reader emits that sentence into its own artifact so
it cannot be dropped in summary. A search that fails to find a counterexample is evidence about the
search. C1 stays labelled C1 and stays in the weakest class.

**Read the substantive blockers, not the mechanical one.** The reader prints the first clause each
candidate trips, and for most that is the abundance clause — because 0008 held round 4's raised
standard that an unverified count does not pass, and for most candidates the count was never
verified first-hand. That makes the mechanical reading of this search weaker than it looks, and it
is stated here rather than left in the artifact. The decisive objections are recorded per candidate
in `primary_blocker`, and for the strongest candidates they are substantive:

| Candidate | What actually kills it |
|---|---|
| De-identification tool from released clinical notes | The tools emit distinctive surrogate formats — `[**Name**]`, `<NAME>`, `XXX` — so the producer is legible from a regex over placeholder syntax |
| DP mechanism and epsilon from a published release | Epsilon is **published by policy**, so the label is public and there is no task |
| Build pipeline from published container layers | OCI image history carries `created_by` strings containing the literal build command |
| Telescope pipeline from published survey images | The pipeline version ships in the FITS header by universal convention |
| Execution algorithm from a published trade tape | L3(ii): trade classification is a developed field and the incumbent is good |
| Redaction tool from FOIA releases | G5: the buyer reconstructs a past release — the **confirming** case for C1, not a falsifier |

### The refinement that came out of it, filed with C1 in the weakest class

Look at the top four rows. In every one, the label is **public** — not hidden, not hard, published.
And they are public for the same reason in each case:

> **Deliberate withholding is documented withholding.** When an institution withholds a transform's
> input on purpose — by privacy law, by regulation, by commercial policy — the same disclosure
> norms that govern the withholding make it publish *what it did*: the placeholder format, the
> `created_by` string, the epsilon, the header. The label ships with the artifact.
>
> The label is genuinely hidden only when the withholding was **accidental**. And accidental
> withholding is loss, which is the forensics case C1 already describes.

If that is right, C1's falsifier may not merely be rare. The two properties it requires —
withholding that is deliberate (so the market is not forensics) and a label that is hidden (so
there is a task) — may be close to mutually exclusive, because what makes withholding deliberate is
an institution, and institutions document.

This is a refinement of a conjecture by an argued reading of 14 screened candidates. It is **not**
measured, it is filed alongside C1 in the coverage map's weakest class, and the same falsifier
applies: an institution that deliberately withholds an input while publishing the artifact and
*not* documenting the transform.

### The third tension, and a cap on how much more of this is worth writing

Chasing the refinement's own falsifier — an institution that deliberately withholds an input while
publishing the artifact and *not* documenting the transform — leads somewhere that closes the
argument rather than opening it.

Institutions do decline to document when the transform is a competitively valuable secret. But a
free label manufacturer requires **possessing the transform** — G2 means running it yourself, at
near-zero marginal cost, as many times as you like. You cannot manufacture labels for a secret you
do not have. Google's ranking function is the cleanest case: SERPs are published in bulk, the
algorithm is deliberately undocumented, and the buyer is a large prospective industry — and it fails
G2 outright, because nobody outside Google can run it.

So:

> **C2 — G2 and G5 pull against each other.** A free label manufacturer requires possessing the
> transform. Possessing it means it is open or commoditised. And the provenance of a commoditised
> transform's output is usually worth little to know, because anyone could have produced it and the
> answer changes nothing the buyer can act on.

That is the carved-DEFLATE story in one line. We possess zlib, zopfli, ISA-L and libdeflate — which
is exactly why the labels are free, and exactly why knowing which one ran is worth so little.

**C2 has a falsifier and it exists.** A freely runnable transform whose output's provenance
materially changes a decision someone pays for: TLS stack identification. Every library is
installable, every handshake is published on the wire in enormous volume, and knowing the stack
tells you which CVEs apply. It is a real market. **And it is solved by JA3/JA4 — a hash, not a
learned model** — which is law L3(i) arriving from the other direction: where the label is both free
and valuable, someone has already built the non-learned tool, because a non-learned tool was
sufficient.

### The three tensions, together

| The shape needs | Which forces | And that costs |
|---|---|---|
| **Free labels** (G2) | possessing the transform | it is commoditised, so its provenance is cheap to know — **C2** |
| **A hidden label** (a task exists) | the input withheld | deliberate withholding is documented, accidental withholding is loss — **C1 + refinement** |
| **A valuable label** (G5) | someone acts on it | a non-learned tool already exists, because it was sufficient — **L3(i)** |

Each row is individually escapable. The archived trial found candidates that escaped one, and
carved-DEFLATE escapes two — free labels *and* a genuinely hidden label. It pays for that with the
third: the thing it recovers is worth little to know, which is G5, which is the gate it does not
clear.

**A cap, stated deliberately.** Everything in this section is argument, not measurement, and this
repository's entire discipline is that those are different. Three conjectures is already more
unmeasured reasoning than a document like this should carry, and the next round that matters is a
*measurement* that breaks one of these rows — not a fourth conjecture explaining why they hold. If a
later round produces more argument and no measurement, that is a signal to stop, not to continue.

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
| Every gate can be shown to fail | 205 mutations, 205 detected, 0 survived | primary-verifiable |
| A number that is real but STALE is caught, not just a fabricated one | `tools/freshness.py`, 9 mutations | primary-verifiable |
| Preregistration chain verifies, reader unchanged since freeze | 12 entries, head `4a230b96…` | primary-verifiable |
| Census leak reproduced first-hand | mean AUC 0.8026 from a one-line rule, 0 training rows | primary-verifiable |
| ACS PUMS record count reproduced | 392,318 records | primary-verifiable |
| Instrument reproduces on a cold clone | preflight names cause and fix | primary-verifiable |
| SAT free decoder re-derived | 0.9857 with zero training rows, against 0.1667 chance | primary-verifiable |
| Assembly-provenance split leak re-derived | temporal split 0.4765 **loses** to a 0.4805 constant | primary-verifiable |
| Assembly-provenance confound re-derived | a fake BioProject partition is predictable at 0.7772 | primary-verifiable |
| **Carved-DEFLATE scaling curve** | **`CURVE_ESTABLISHED`** — +0.0491/decade, cluster-corrected 95% CI [0.048216, 0.050014], over 2.9031 decades; margin +0.1003 frozen and +0.0583 stricter, both above 0.05 | primary-verifiable |

### Failed, or did not reach a conclusion

| Result | What happened | Class |
|---|---|---|
| **Phase 0 domain selection** | **Terminated with no domain. 99 candidates, 8 adversarial reviews, 0 SELECT.** | arithmetic-verifiable |
| Phase 1 (falsify the data thesis) | Delivered on the pivot, not on a selected domain. The null control, the grouped split and the trivial-baseline floor were all measured before any learned number was believed. | primary-verifiable |
| Phase 2 (the scaling curve) | **Delivered on the pivot.** `CURVE_ESTABLISHED` over 2.9031 decades, both margins clearing 0.05. It is a real curve on a real task — and on a domain that reached it through the archived trial rather than through Phase 0 selection, and that still has no buyer. | primary-verifiable |
| **2048-byte carve (0011)** | **`CARVE_FAILS`** — top-1 0.1741 against logistic 0.1266 (+0.0475, 0.0025 short of the bar) and against a depth-16 tree at 0.1447 (+0.0294); transfer from 4096 at 0.0455. The window boundary is bracketed to (2048, 4096]. Expected outcome, stated in the preregistration before the corpus existed. | primary-verifiable |
| Phase 3 (credibility artifact) | Partially delivered. The *instrument* ships and reproduces, and the manufacture-and-measure pipeline ships with it; the corpus itself is 5.8 GB and is not committed, so a stranger must re-manufacture rather than download. | n/a |
| Round 3 screener's own arithmetic | Reported 11 adversarial reviews. Recounted from the banked artifacts: **8**. The screener's candidate total of 99 is correct. | arithmetic-verifiable |
| Our own allocation-flag count | Recorded 76 against a subagent's 77 and filed it as *the subagent's* discrepancy. The subagent was right. Filed in `CORRECTIONS.md` at full size. | primary-verifiable |
| **G5 — a named buyer type** | **Not cleared, for any candidate including the pivot.** No buyer has been contacted, none is claimed, and nothing measured here establishes that one would pay. A rising curve does not supply a buyer. | n/a |
| **Three numbers in this document went stale** | The chain length, the coverage denominator and the primary-verifiable count kept being published after they stopped being true. The outbound gate passed all three, because a stale number is still a real one. Second instance of this bug; filed in `CORRECTIONS.md` with the general fix. | primary-verifiable |
| **A scaling-rate figure we published** | Stated the learned SAT arm at 0.2384 and +2.8 points per decade. Our own reproduction gives 0.18 and +1.21, in the direction that flatters our conclusion. **Not reproduced.** Filed in `CORRECTIONS.md`. | neither |

---

## Verification coverage

Machine-checked by `python3 tools/coverage.py`, which refuses to let a claim be filed as
primary-verifiable unless the command that re-derives it exists in this repository.

**The weakest row, stated loudest:**

> **14 of 96 claims are in `neither`.** They can be neither re-derived nor re-run by anyone,
> including us. Eight are subagent measurements made inside ephemeral scratch directories that no
> longer exist, with no script banked and no inputs retained. **The ninth is worse than unverified:
> it is a figure this repository actively tried to reproduce and could not.** The tenth is of a
> different kind and belongs here anyway: **the statement that G5 has no buyer.** The eleventh is
> conjectures `C1`, its refinement and `C2`, filed here deliberately: between them they are the
> most interesting reasoning in this document and the least supported, and putting them anywhere
> else would let them be read as findings. Three of them is already more unmeasured argument than
> a document like this should carry, which the section itself says out loud.** An absence cannot
> be re-derived from an artifact, it carries no measured value and none is asserted, and a
> self-reported `establishes_a_buyer: false` is evidence of intent rather than of fact.
>
> **This includes the measurements that close the search.** The Sentinel-1 fit that retires an
> entire candidate family under L1. The MOT numbers that are the strongest single piece of evidence
> for L3(iii). The javac byte-identity result. The ELF base-address entropy. A reader who declines
> to take a subagent's word for those is left with the laws unproven, and would be right to.
>
> Three of the four load-bearing measurements have since been pulled out of that class by
> re-deriving them here from public data with shipped code — the census leak, the SAT-solver
> decoder, and the assembly-provenance split leak. Reproducing the second one **contradicted a
> figure this repository had already published**, in the direction that flattered its own
> conclusion. That is filed in `CORRECTIONS.md` at full size rather than resolved by adopting the
> better-looking number. The rest have not been re-derived, and are marked accordingly rather than
> quietly upgraded. (An earlier version of this paragraph said "two" while the section below it
> said "three of the four" — caught by adversarial audit.)

| Class | Count | Meaning |
|---|---:|---|
| `neither` | **14** | Cannot be re-derived or re-run. Eight asserted from sources we cannot reproduce; one actively failed to reproduce; one is a statement about what was not done; three are explicitly labelled conjectures; one is a methodological inference from an inconclusive run. |
| `arithmetic-verifiable` | 18 | Follows by arithmetic from a banked artifact, but the artifact rests on our run. |
| `primary-verifiable` | 64 | A stranger can re-derive it from raw inputs with the shipped code. |

Three of the four load-bearing subagent measurements have now been pulled out of the weakest class
by re-deriving them here — the census leak, the SAT decoder, and the assembly-provenance split leak.
The last of those was only possible because that reviewer happened to write its inputs into the
repository instead of a scratch directory, which is luck rather than process, and is recorded as
such in `data/asmprov/README.md`.

---

---

---

## The pivot — `CURVE_ESTABLISHED` on carved-DEFLATE encoder provenance

The first curve in this repository that is a claim about the world rather than a test of the
instrument. **It does not make the thesis fundable** — see the buyer paragraph below, which is the
part to read.

**The task.** Take a window from the MIDDLE of a DEFLATE stream — no header, no stream start, no
plaintext, and not the stream length — and recover which of 26 (implementation, level)
configurations produced it. The label factory is free and unbounded: compress any bytes under every
configuration and the label *is* the configuration. Marginal cost per labelled example is one
compression call.

| | |
|---|---|
| **Verdict** | `CURVE_ESTABLISHED` |
| **Emitted by** | `tools/readers/pivot_deflate_curve.py`, frozen and hashed before the corpus existed |
| **Governed by** | `prereg/0003-pivot-deflate-curve`, chain seq 3 |
| **Artifact** | `artifacts/pivot/deflate_curve.json` |

| Rung (manufactured fragments) | Accuracy |
|---:|---:|
| 1000 | 0.0988 |
| 10000 | 0.1415 |
| 100000 | 0.1965 |
| 800000 | 0.2395 |

| Clause | Bar | Measured | |
|---|---|---|---|
| Rungs | ≥ 4 | 4 | pass |
| Decades | ≥ 2.0 | 2.9031 | pass |
| Slope 95% lower bound (cluster bootstrap) | > 0 | 0.048216 | pass |
| Margin over best trivial baseline | ≥ 0.05 | **0.1003** | pass |
| Split grouped by source | required | yes* | pass |
| Null control | ≤ chance + 0.02 | 0.0389 vs 0.038462 | pass |

Slope **+0.0491** accuracy points per decade, cluster-bootstrap 95% interval **[0.0482, 0.0500]**
(corrected — see the weakness list), r² **0.9978**, against a chance level of **0.038462** across
26 classes.

*\*The split clause needs an asterisk, found by adversarial audit.* The split groups by chunk
**index**, and for seven of eight content families the chunk index fully determines the bytes, so
the guarantee holds. For the **gutenberg** family, every chunk is a 32768-byte window drawn at a
random offset from one shared 7.84 MB pool — so gutenberg source **bytes** straddle the train/eval
boundary at roughly 26× coverage, and the sentence "fragments carved from the same source bytes
never straddle the boundary", frozen into the preregistration and repeated in three documents, is
**false for one eighth of the corpus**. The measured impact runs *against* the headline rather
than for it: gutenberg is among the hardest families (top-rung accuracy **0.1596** against
**0.2511** for the other seven), and excluding it from evaluation **raises** every rung and
steepens the slope to **+0.0524** `[0.0514, 0.0535]` (`artifacts/pivot/audit_rederivations.json`).
So the leak existed, the claim was wrong, and honouring it would have made the result look
better, not worse. The full restatement is now measured on both sides: refitting every baseline
(deterministic — each full-eval value reproduces the original run exactly) and scoring on the
non-gutenberg evaluation, **both preregistered margins widen**: frozen-set **+0.1073** against the
published +0.1003, expanded-set **+0.0620** against +0.0583. Every baseline is also weaker on
gutenberg than elsewhere, so the leaked family was *depressing* the headline, not inflating it
(`artifacts/pivot/baseline_family_rescore.json`). The same shared pool also voids the byte-level reading of 0007's
corpora-disjointness clause — which *strengthens* the transfer finding there: the 4096-trained
model had seen gutenberg-adjacent bytes and still collapsed to chance. Filed in `CORRECTIONS.md`.

### Where the curve lives — the per-family decomposition

Derived from the banked per-example scores with a cluster bootstrap per family
(`artifacts/pivot/per_family_curves.json`): the headline slope is a **mixture**. Structured content
carries the curve — csv **+0.0906**, log **+0.0909**, json **+0.0901**, code **+0.0690** per
decade, with top-rung accuracies of 0.3888, 0.3756, 0.3581 and 0.2944 against 0.038462 chance —
while the incompressible families sit near the byte-identity collision ceiling: binary **+0.0097**,
mixed **+0.0028**. Every family's interval excludes zero, including the ones that make the task
look hard, and all eight are reported either way.

### Would a rerun have said something different? Measured: no

0003's frozen scope said *"single seed... this is not a variance study"* — the most-repeated
disclosed weakness in the package. It is now measured (`artifacts/pivot/seed_robustness.json`): two
additional full-pipeline runs at independent seeds — fresh grouped split, fresh shuffles, fresh
initialisation — give slopes of **+0.0486** and **+0.0478** against the published **+0.0491**, a
spread of **0.0014**; margins **+0.1116** and **+0.1100** against the published **+0.1003**; null
controls **0.0384** and **0.0377**, both at chance. Every run clears every clause, and the published
run is the *lowest* of the three on top rung and margin. These replications cannot revise 0003's
verdict; they close its stated weakness.

### Both readings of the margin, at equal prominence

`artifacts/pivot/prereg_interpretation.json` — recorded mid-run and anchored to drand round
**6408095**, before the baseline and model numbers were known — commits this document to reporting
the stricter reading alongside the frozen one. Deep trees were added to the baseline set during
piloting and are **not** in the preregistered list, and they are substantially stronger than
anything that is:

| Reading | Best baseline | Margin |
|---|---|---:|
| **Frozen set** (majority, label-prior, depth-3 tree, logistic) — what the reader consumes | logistic **0.1392** | **+0.1003** |
| **Expanded set** (adds depth-8 and depth-16 trees) — the stricter reading | depth-16 tree **0.1812** | **+0.0583** |

**Both clear 0.05.** Every baseline was trained on the same 800000 fragments as the top rung, so
none of them is data-starved. That the stricter margin also clears is the single most load-bearing
line in this section — had it not, the commitment was to say so in the headline and not in a
footnote.

### What is weak about it, stated here rather than left to be found

- **The permutation p-value is at its arithmetic floor.** Reported **0.0417**, which is exactly
  1/24: an exact permutation test over four rungs has 4! = 24 orderings and cannot report anything
  smaller. It says the observed ordering is the most extreme of the 24 available. It does **not**
  mean "just under 0.05", and what would lower it is more rungs, not a better result.
- **The top rung was set by memory, not chosen.** 800000 of the 1040000 training fragments
  available. The cap was fixed during OOM debugging *before* any 800000-fragment number existed;
  the run that produced this was the first to survive. Six attempts, five killed at a ~13.9 GB
  ceiling. Recorded in `artifacts/pivot/engineering_log.json` with the root cause.
- **A cheaper option was declined because it flattered the result.** Restricting to the first 553
  feature columns roughly halves memory and yields a *larger* frozen-set margin — **0.0751** against
  **0.0723** on the pilot — by weakening the baselines rather than improving the model. Taking it
  after two OOM kills would have been choosing the flattering option under cover of a resource
  constraint. Banked, because the decision went against this study's interest and is otherwise
  invisible.
- **The published 95% interval was anti-conservative, and is corrected.** The bootstrap resampled
  260000 eval fragments as independent, but they are 10000 clusters of 26 fragments sharing a
  plaintext — the dependence unit this study's own grouped split declares. Measured within-chunk
  correctness correlation is 0.140 against 0.016 across chunk boundaries. The corrected interval,
  from a cluster bootstrap over the 10000 chunks, is **[0.0482, 0.0500]** — about half again as wide as
  the superseded [0.0485, 0.0497] — and the verdict clause (lower bound > 0) is unaffected.
  Found by adversarial audit; derivation in `artifacts/pivot/audit_rederivations.json`, filed in
  `CORRECTIONS.md`. The interval still covers evaluation sampling only — not seed variance, not
  corpus-manufacture variance, not model-class choice.
- **One carve size, one seed, one model class.** Generalisation across carve sizes is not
  established. Encoders absent from this box — 7-Zip's deflate, Java's `Deflater`, Go's `flate`,
  the Cloudflare and Windows zlib forks — are not covered.
- **Incompressible content caps what is achievable.** Base64 and packed-binary sources collapse to
  roughly **14** distinct streams of 26 (14.667 and 14.75 respectively); 22.27 is the mean across
  all eight content families, which an earlier version of this bullet wrongly attributed to the
  worst families — an error in the flattering direction, inside this very section. Caught by
  adversarial audit; filed in `CORRECTIONS.md`. Some fragments carry no recoverable signal at all.

### G5 is the gate this does not clear, and no amount of curve fixes it

The five gates are abundance, a label manufacturer, scale monotonicity, white space, and **a named
buyer type**. This result settles the first four. It does not settle the fifth, and this document
does not claim it does.

White space was verified first-hand across arXiv, the general web and HuggingFace
(`artifacts/pivot/g4_firsthand.json`). The three GitHub `total_count: 0` queries this document
previously folded into that claim were in fact a **round-1 subagent's** results — exactly the class
of evidence this repository refuses to call verified elsewhere, relabelled "first-hand" here. The
audit caught it, and the queries have now been re-run genuinely first-hand through the
authenticated GitHub API: **`total_count: 0`, `incomplete_results: false`, on all three
formulations** (`artifacts/pivot/g4_github_firsthand.json`). The **five** non-learned tools that do
exist — `preflate`, `precomp`, `grittibanzli`, `list-compresslevel.py`, and
`koutto/compression-identifier` (type only) — each need something a carved fragment does not have.
The honest limits stand: encode.su was unreachable and was not searched, and no patent search was
run.

But the buyers this points at — forensic carving of unallocated disk, archive recompression,
repackaged-APK detection — are narrow, and **no buyer has been contacted, none is claimed, and
nothing here establishes that one would pay.** A rising curve on a task nobody needs is a rising
curve on a task nobody needs. This is a validated label factory and a validated instrument; it is
not a business, and the gap between those two things is the honest state of this repository.

---

## `CARVE_FAILS` — the pivot's result is bound to one window size, and the binding is severe

Preregistration 0007, frozen at chain seq 7 before the second corpus existed. **This is the most
consequential result in this document, and it qualifies the two above it.**

Everything in 0003 and 0006 is measured at a 4096-byte carve. A forensic analyst — the one buyer
type for which a carved fragment is genuinely the operational setting — does not choose the window;
the carve does, and file carving works in disk clusters that are frequently smaller. So a second
corpus was built at **1024** bytes from source chunks **disjoint** from the first, and the same
protocol re-run.

| | |
|---|---|
| **Verdict** | `CARVE_FAILS` |
| **Emitted by** | `tools/readers/carve_generalisation_verdict.py`, frozen before the corpus existed |
| **Artifact** | `artifacts/pivot/carve_generalisation.json`, margins in `artifacts/pivot/carve_margins.json` |

| Clause | Bar | Measured | |
|---|---|---|---|
| Within-size margin, frozen baseline set | ≥ 0.05 | **+0.0099** | **fail** |
| Within-size margin, all baselines | ≥ 0.05 | **+0.0099** | **fail** |
| Transfer margin (4096-trained model, 1024 data) | ≥ 0.05 | **-0.0853** | **fail** |
| Rungs / decades | 4 / ≥ 2.0 | 4 / 2.699 | pass |
| Within-size slope 95% lower bound (cluster bootstrap) | > 0 | 0.0197 | pass |
| Null control | ≤ chance + 0.02 | 0.0389 vs 0.038462 | pass |
| Corpora share source chunks | must be false | false | pass |

### Three findings, in order of how much they cost

**1. At 1024 bytes the model ties a dumb rule.** Top-1 reaches **0.1355** at 500000 manufactured
fragments against a logistic-regression baseline of **0.1256** — a margin of **+0.0099** where the
preregistered bar is 0.05. Note which baseline won: at 4096 the strongest was a depth-16 tree at
0.1812; at 1024 the deep trees are *worse* than logistic (0.1197 and 0.1103), and plain logistic is
the thing the model fails to separate from.

**2. Holding data volume fixed, the shorter window costs 0.0800.** At the matched 100000 rung,
**0.1165** at 1024 against **0.1965** at 4096. That single number is larger than the entire margin
the study needed to clear.

**3. Transfer does not degrade — it collapses to chance.** A model trained at 4096 and evaluated on
1024-byte fragments scores **0.0403** against a chance level of **0.038462**. It is not a weakened
model; it is not a model. The feature set carries 512 bit-alignment histogram columns estimated
from the window, and their distributions at a quarter of the bytes are apparently a different
distribution rather than a noisier one.

### The excuse this result is not allowed to use

A1 was run on the **input** before the bar was frozen, and it removes the obvious defence. The
byte-identity collision ceiling barely moves across the range: **20.9125** distinct streams of 26 at
4096 against **20.79** at 512. The information is present at 1024. **This is a modelling failure,
not an information failure**, and the preregistration committed this document to saying so in those
words before the number existed.

### A rising curve that is worthless, which is the whole reason the margin clause exists

The within-size slope is **+0.0204** accuracy points per decade with a cluster-corrected 95% lower bound of **0.0197**
that excludes zero. The curve at 1024 genuinely rises with manufactured data. It rises from a base
that never separates from logistic regression, and it would need many more decades than exist to get
anywhere. Had this study been run without an A2 margin clause it would have reported a statistically
clean positive scaling result on a task the model cannot do. That is exactly the failure the
archived trial killed five candidates on, arriving this time in our own work.

### The boundary, bracketed — `CARVE_FAILS` at 2048 too (preregistration 0011)

Preregistration 0011, frozen at chain seq 11 (NIST Beacon pulse 1924204, drand round 6431543)
before the third corpus existed, after two adversarial review rounds — 60 raw findings, banked with
their dispositions in `artifacts/verification/prereg_0011_reviews.json` — which are the reason its
reader returns `VOID` for anything it cannot vouch for. The expected outcome was written
into the preregistration before the data: `CARVE_FAILS`. A third corpus at **2048** bytes — 25000
source chunks at ids 75000..99999, disjoint by chunk id from both earlier corpora — under the 0007
protocol plus gutenberg-excluded margin clauses in **both** arms.

| | |
|---|---|
| **Verdict** | `CARVE_FAILS` — boundary **(2048, 4096]** |
| **Emitted by** | `tools/readers/carve2048_verdict.py`, frozen before the corpus existed |
| **Artifact** | `artifacts/pivot/carve_generalisation_2048.json`, margins in `artifacts/pivot/carve_margins_2048.json` |
| **Validity** | every sealed parameter checked and passed: chunk-id range measured 75000..99999, 0 shared chunks with corpus A, the ten sources and corpus A's arrays hash-match the banked manifest, and the transfer model scored **0.1965** on corpus A's own held-out set — corpus A's banked matched-rung accuracy to the fourth decimal |

| Clause | Bar | Measured | |
|---|---|---|---|
| Within-size margin, frozen baseline set | ≥ 0.05 | **+0.0475** | **fail**, by 0.0025 |
| Within-size margin, all baselines | ≥ 0.05 | **+0.0294** | **fail** |
| Within-size margin, all baselines, gutenberg excluded | ≥ 0.05 | **+0.0308** | **fail** |
| Transfer margin (4096-trained model, 2048 data) | ≥ 0.05 | **-0.0811** | **fail** |
| Transfer margin, gutenberg excluded | ≥ 0.05 | **-0.0854** | **fail** |
| Within-size slope 95% lower bound (cluster bootstrap, 5000 chunks) | > 0 | 0.0307 | pass |
| Null control | ≤ chance + 0.02 | 0.0391 vs 0.038462 | pass |
| Rungs / decades | 4 / ≥ 2.0 | 4 / 2.699 | pass |

**1. It misses by 0.0025 on the frozen set, and by much more on the stricter one.** Top-1 reaches
**0.1741** at 500000 fragments against logistic regression at **0.1266**: a margin of **+0.0475**
where the bar is 0.05. The three frozen-set margins now read **+0.0099** at 1024, **+0.0475** at
2048 and **+0.1003** at 4096. The stricter reading is not close: the depth-16 tree reaches
**0.1447** at 2048 (it was **0.1197** at 1024 and **0.1812** at 4096), for a margin of **+0.0294**.
Excluding the gutenberg family — the rows the chunk-id disjointness guarantee does not cover —
moves the stricter margin to **+0.0308**, so the near-miss is not carried by leaked rows either.

**2. Holding data volume fixed, the upper halving costs more than the lower one.** At the matched
100000 rung: **0.1165** at 1024, **0.1461** at 2048, **0.1965** at 4096. The step from 2048 to 4096
is worth **0.0504**; the step from 1024 to 2048 is worth **0.0296**.

**3. Transfer collapses again, and this time the collapse is certified.** The 4096-trained model
scores **0.0455** on 2048-byte fragments against **0.038462** chance (**0.0461** with gutenberg
excluded), having first reproduced corpus A's banked **0.1965** on corpus A's own evaluation set.
Retraining is not the explanation; the representation is. L4 now rests on two shorter sizes, not
one.

**4. The 2048 curve rises, from a base that does not clear.** Slope **+0.0316** per decade with a
cluster-bootstrap interval of **[0.0307, 0.0326]** over the 5000 held-out chunks, r² **0.9919**,
between 1024's **+0.0204** and 4096's **+0.0491**. Rungs: **0.0882**, **0.1140**, **0.1461**,
**0.1741**. Per family at the top rung: csv **0.2915**, log **0.2482**, json **0.2359**, code
**0.1945**, gutenberg **0.1208**, mixed **0.1098**, base64 **0.103**, binary **0.0925** — the
same ordering as at 4096 for the top five, compressed; mixed and base64 swap places at the bottom.

**5. The scope sentence is now a measurement.** "Valid only at a 4096-byte window" was a two-point
statement with the boundary unmeasured across a factor of four. It is now bracketed to
**(2048, 4096]**, each size under its own measured protocol (4096 at an 800000-fragment top rung
in 0003; 1024 and 2048 at 500000). Nothing here says what happens above 4096 or below 1024.

**6. Where the near-miss lives — a decomposition, not a clause.** `tools/pivot/per_family_curves.py`
re-derives every family from the banked per-example scores and the per-family baselines the
script banked (`artifacts/pivot/per_family_curves_2048.json`; the re-derived top-rung accuracies
equal the artifact's to four decimals). On **csv** and **log** the 2048 model clears the 0.05 bar
on **both** readings: csv **+0.1105** over logistic and **+0.0554** over the depth-16 tree; log
**+0.0897** and **+0.0501**. **code** clears the frozen reading (**+0.0684**) and misses the
stricter one (**+0.0469**); **json** misses both at **+0.0438**; gutenberg, base64, binary and mixed
miss everything, mixed with a negative margin of **-0.0045**. The headline is a mixture; the same
script banks the mixture *without* the three incompressible families (base64, binary, mixed): top-1
**0.2172**, margin **+0.0673** over logistic and **+0.0478** over the depth-16 tree — still below the
bar on the binding reading. Only the structured four (csv, log, json, code) clear both readings as
a set, **+0.0774** and **+0.0549** at top-1 **0.2419**. So the honest sentence is narrower than
"a pass masked by noise": two families pass outright, the structured four pass together, and the
mixture fails even with the incompressible families removed, because gutenberg prose and json sit
between. This changes nothing about the verdict — the preregistered unit is the mixture, and the
mixture fails — and the per-family rows are what a buyer whose carves are csv or log would need
to see. The same script at
1024 (`per_family_curves_1024.json`, model side only; that run banked no per-family baselines)
puts csv at **0.2218** with a slope of **+0.0470** per decade, the steepest thing in the 1024 run.

**Cost, banked.** Corpus build **1564.0** seconds at 4 processes on the 4-core container, no GPU;
training **12.1**, **26.0**, **125.5** and **1036.0** seconds per rung, taken under `nice` with 3
BLAS threads (the artifact's `cost.train_environment`), so not comparable to 0007's 4-thread
ladder. Three earlier attempts were killed by container
restarts — two during the corpus build, one during the baselines — and the fourth reused the
corpus cache the third had written. The measurement script refuses a cache whose stored build
metadata disagrees with its command line and stamps the artifact with where `carve_bytes` came
from; the frozen reader requires that stamp. That is why a reused cache is safe to trust.

**What it does not establish.** A buyer. Anything about a different recipe at 2048: a frozen-set
margin 0.0025 short of the bar is exactly the gap a per-head recipe search might close, and that
is a new preregistration (M1's question at a second size), not a footnote to this one. The
stricter margin, +0.0294 against the deep tree, is not a gap a recipe search should be expected
to close.

**That preregistration exists, is frozen, and is running.** Preregistration 0012
(`prereg/0012-recipe-search-2048.json`, chain seq 12, NIST Beacon pulse 1925147, drand round
6433429, reader `tools/readers/recipe2048_verdict.py` hashed into the chain at a clean tree) is a
*symmetric* recipe search: every head with a hyperparameter — the HGB model, the logistic, the
depth-3 tree and the deep tree — gets an enumerated roster of eight recipes with the 0011 recipe
first, selected by one rule on a chunk-rule holdout that shares no chunk with the sealed
evaluation set, then fitted once on 0011's 500000-row pool and scored once on 0011's evaluation
set, the model last, with every baseline head floored at its 0011 value so the search can raise
the bar and never lower it. Its expected outcome, written before any fit, is `RECIPE_FAILS`. No
0012 number appears in this document until its frozen reader emits one; the run's checkpoints
are committed as they land under `artifacts/pivot/recipe_search_2048_ckpt/`.

### A learned representation over raw bytes does not rescue it either — `BYTE_MODEL_FAILS`

L4 was written with a scope limit in its own paragraph: it does not establish that a **learned**
representation over the raw bit sequence would be window-bound, because none had been tested.
Preregistration 0009 tested one, and this document's cap on further conjecture is why it is a
measurement rather than a fourth argument.

A small 1D convolutional network — **182842** parameters, a byte embedding, three convolution-and-pool
stages — trained on the raw 1024-byte fragments at the matched **100000** rung. The evaluation set is
identical to 0007's by construction *and by check*: the script computes the eval-group fingerprint
and refuses to run unless it matches corpus B's.

| | Accuracy |
|---|---:|
| Byte-sequence CNN | **0.0849** |
| Hand-engineered features, same rung (0007) | **0.1165** |
| Logistic regression on a plain byte histogram | **0.0943** |
| Shuffled-label null control | **0.0385** vs chance 0.038462 |

**Both clauses fail.** The A2 margin is **-0.0094** against a bar of 0.05, and the byte model loses
to the representation it was meant to replace. The striking part is the middle row: **seeing byte
order did worse than counting bytes.**

Per the meaning frozen before the run, this **strengthens L4**. The window binding is not an
artifact of hand engineering.

### Two readings of that negative, and the second one is against us

**It converged rather than running out of budget.** The training loss falls from 3.2587 to 3.0877
against a chance cross-entropy of ln(26) = **3.2581**, and flattens: the last five epochs move
**0.0145** in total, under 0.005 each. This is a model that reached a poor solution, not one
truncated mid-descent.

**The null control is clean — and reading it as evidence of limited capacity was wrong.** The
shuffled-label loss never moves from chance at all, **0.0006** across ten epochs. This document
first read that as "the model may be too small". It does not follow, and the retraction is in
`CORRECTIONS.md`. A probe holding everything fixed except the final pooling layer reaches
**0.364** train accuracy on 5000 shuffled labels with a flatten head, against **0.0486** with the
global average pool 0009 used, at identical convolutional capacity. The network could not memorise
because average pooling **averages away per-example identity**, not because it lacked capacity.

**The lesson generalises, and this repository should have reached it unaided.** A null control the
model *cannot fail* carries no information — which is precisely the argument `tests/mutation_test.py`
already makes about gates, applied to controls by nobody until a probe forced it.

**What survives as the honest caveat** is narrower: 0009 tested one architecture whose final pooling
is a strong inductive bias, and whether that bias hurts the *task* is untested. Local byte order may
be exactly the right signal and position irrelevant, in which case the pool is sensible and the
negative stands cleanly. **A negative here does not prove that no learned representation works at
1024.** It proves this one does not, and that the first thing anyone would reach for does not.

### The corrected-head round came back INCONCLUSIVE — and the reason is itself a finding

Preregistration 0010 replaced the global average pool with a flatten — the one change the probe
said mattered — holding everything else frozen: same corpus, same rung, same seed, same
convolution stack, same optimiser, same 10 epochs. Its new clause required the null control to
*prove it can fail* (`null_train_top1 ≥ 0.30`) before being credited.

| | Accuracy |
|---|---:|
| Flatten-head CNN, real labels | **0.0385** — exactly chance |
| Pooled-head CNN (0009), same recipe | 0.0849 |
| Hand-engineered features, same rung | 0.1165 |
| Null control, train accuracy on shuffled labels | **0.0393** — the control never became failable |

**Verdict `BYTE_FLAT_FAILS`, named by the frozen reader as inconclusive on the exact point the
round exists to settle.** Under the frozen recipe the flatten head does not train *at all* at this
scale — chance on real labels and on shuffled labels alike — even though the identical head
memorised 5000 shuffled labels at 30 epochs in the probe. About 3900 optimisation steps never left
the plateau the probe crossed in ~400.

**The methodological tension is worth more than the number.** "Change only the head" was chosen so
any difference would be attributable — and that constraint is what produced the inconclusive
result, because a training recipe tuned under one architecture is not architecture-neutral, and
freezing it privileges the incumbent. A fair 0011 would have to preregister a *recipe search* per
head, not a shared recipe; that is recorded here as the open question, and it is not run in this
container. The failable-control clause did exactly its job: without it, this run would have
published another architecture-guaranteed clean control as if it meant something.

### And it is not localised, so it is not cheaply fixable

A diagnostic run after the verdict — **not preregistered, and not a result about the world** —
asked whether the failure sits in one repairable part of the representation. It does not. At a
matched 100000 rung, every one of six feature subsets degrades from 4096 to 1024 by a ratio between
**0.5895** and **0.6275**: a spread of **0.038**. No family survives the shorter window and no family
dies in it. The whole representation degrades uniformly, which is what happens when every feature is
a statistical estimate over the window and a quarter of the bytes makes every estimate worse by
roughly the same factor.

**The prior recorded before that run was wrong**, and it is worth recording that it was. It said the
512 alignment-histogram columns would be the casualty. They are not — because they were never
carrying much at 4096 either. Dropping all **555** alignment features costs **0.0099** at 4096 and
**0.0016** at 1024. Roughly half the feature vector buys about one accuracy point where the study
works and near-nothing where it does not, which extends to v3's histograms the verdict this
repository already recorded against v2's alignment summaries.

So a model that works at 1024 would need a different *kind* of representation — learning from the
raw bit sequence rather than from summary statistics over it — not a mended feature family. That is
a materially larger project than this diagnostic was run to scope, and **it is not started here.**

### What this changes about everything above

`CURVE_ESTABLISHED` and `OUTPUT_USABLE` stand — they were measured correctly and 0007 cannot revise
them. But both are now **explicitly bound to a 4096-byte window**, and the binding is not a
technicality:

- Quoting the 4096 numbers as "carved DEFLATE encoder provenance works" is quoting them wrongly. It
  works *at 4096*.
- 0006's finding that the output has the shape a forensic use requires is **conditional on a window
  the forensic setting does not guarantee**. That was the buyer type the whole G5 argument leaned on.
- The label factory being free does not rescue this. `CARVE_SIZE_SPECIFIC` — train one model per
  carve size for one more compression pass — was the preregistered survivable outcome. This is not
  that outcome. At 1024 there is no model worth training, at any volume this study can reach.

---

## G5 attacked directly — `OUTPUT_USABLE`, and it still does not name a buyer

Preregistration 0006, frozen at chain seq 6 and anchored to NIST Beacon pulse **1917953** and drand
round **6408784** — **before any top-k, calibration or selective-prediction number existed on this
corpus**. It is a separate preregistration rather than an addition to 0003 precisely because 0003's
verdict was already known, and bolting a new reading onto a study whose result you have seen is the
move this instrument exists to prevent.

**The question.** Top-1 accuracy answers "is the single best guess right", which is the wrong
question for the only buyer type where a *carved* fragment is genuinely the operational setting.
Archive recompression and repackaged-artifact checks both hold the whole stream and the plaintext,
so incumbent tools apply there and this task's advantage disappears. Forensic carving of
unallocated disk does not. For that analyst the deliverable is a shortlist, plus an honest signal of
when to ignore the tool.

| | |
|---|---|
| **Verdict** | `OUTPUT_USABLE` — shape `BOTH HALVES USABLE` |
| **Emitted by** | `tools/readers/deflate_topk_verdict.py`, frozen and hashed before the measurement |
| **Artifact** | `artifacts/pivot/deflate_topk.json`, margins in `artifacts/pivot/deflate_topk_margins.json` |

| Reading | Model | Best baseline | Margin | Bar |
|---|---:|---:|---:|---:|
| Top-5, **frozen** baseline set | 0.5694 | logistic 0.3951 | **+0.1743** | 0.05 |
| Top-5, **all** baselines (deep trees included) | 0.5694 | depth-16 tree 0.4610 | **+0.1084** | 0.05 |
| Accuracy on the most-confident decile | 0.7922 | depth-16 tree 0.6937 | **+0.0985** | 0.05 |

Top-1 **0.2395**, top-3 **0.4497**, top-5 **0.5694**. Null control, labels shuffled: top-5
**0.1919** against a 5/26 chance of **0.1923** — a top-5 metric is five times easier to satisfy by
luck than top-1, so this control matters more here, not less. The confident decile is **26000**
evaluation fragments, so the selective figure is not a small-sample artefact.

**The shortlist improves roughly twice as fast as the single guess.** Top-5 slope **+0.0985**
accuracy points per decade, cluster-corrected 95% interval **[0.0971, 0.0999]**, against the top-1
slope of **+0.0491**. Both rise; the operationally useful one rises faster.

### The two clauses written down in advance as the likely failures both cleared

Recorded in the preregistration before the run: *"the two clauses most likely to fail"* were the
expanded-set top-5 margin — because ranking 5 of 26 is a far easier task than picking 1, so a deep
tree might close the gap — and the absolute selective floor of **0.5**, because a 0.2395 top-1 model
can easily have a most-confident decile no better than its average. Neither happened.

The selective clause is the tightest of the three, and it was scored under the **strictest** reading
available. `artifacts/pivot/topk_prereg_interpretation.json` resolved "the best trivial baseline"
to the **maximum over all baselines** rather than the best of the frozen set. That note carries a
drand anchor, and an audit correctly observed the anchor proves only **not-before** — it cannot
prove the numbers did not yet exist, which is a not-after claim; nothing in beacon arithmetic stops
an author computing first and anchoring afterwards. The precedence of the note over the
measurements therefore rests on the run logs and commit history, not on the beacon, and both
interpretation artifacts now carry that correction in their own text. Under the looser frozen-set reading the comparison would have been logistic's
**0.5412** and the margin **+0.2510** rather than **+0.0985**. The harder reading was chosen while
the numbers did not yet exist, and it still passed.

### What the tight intervals do NOT mean

The intervals published here were **doubly** over-tight, and only one of the two reasons was
disclosed at the time. First, as disclosed: the bootstrap does not sample seeds, corpora, or model
classes. Second, found later by adversarial audit: it resampled evaluation **fragments** as
independent when they are clusters of 26 sharing a plaintext, understating even the
evaluation-sampling uncertainty by roughly half (0003's corrected interval:
`artifacts/pivot/audit_rederivations.json`). The top-5 interval had the same defect; its
measurement was re-run deterministically (every measured value reproduced bit-exactly), the
per-example scores are now banked, and the cluster-corrected interval is **[0.0971, 0.0999]**
against the superseded [0.0977, 0.0993]. The 1024-carve within-size interval was corrected the
same way, to [0.0197, 0.0212]. All three verdict clauses are unaffected. "Pins the slope to about
a thousandth" — which an earlier version of this section said — was false even on its own terms.
Filed in `CORRECTIONS.md`.

The top-5 permutation p is again **0.0417**, its arithmetic floor of 1/24 for four rungs, for the
same reason as before.

### This does not establish a buyer, and could not have

The reader emits `establishes_a_buyer: false` into its own artifact rather than leaving the
disclaimer in prose. What 0006 shows is that the output has the **shape** a forensic use would
require: a shortlist that beats every dumb rule, and a confidence signal good enough to abstain on.
Whether anyone wants that shape is a commercial question, and **no buyer has been contacted, none is
claimed, and nothing in this repository establishes that one would pay.** G5 remains uncleared. The
work that would clear it is not work that can be done from inside this container.

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
- **It contains four fitted, interval-bounded curves, and exactly one of them is a claim about
  the world** — the carved-DEFLATE curve of preregistration 0003, valid at a 4096-byte window and
  only there (0007). The round-4 curve validates the instrument on a G4-dead domain; the 0006
  top-5 curve reads the same models operationally; the 1024-carve curve rises from a base that
  never separates from a dumb rule. An earlier version of this bullet said "no scaling curve that
  means anything" — prose written before the pivot that survived three sweeps of the exact
  stale-claim bug this repository built a gate for. Found by adversarial audit; filed in
  `CORRECTIONS.md`.
- **It has no customers, no users and no partners.** None are claimed anywhere.
- **Most of its findings rest on subagent measurements** that have not been independently
  reproduced, as the coverage map states in detail.
