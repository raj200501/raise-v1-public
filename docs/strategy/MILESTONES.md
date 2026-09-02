# Milestone map — what a raise buys

This document maps the raise to the open questions the record itself names, in `VERDICT.md`
and in the preregistrations. It is a use-of-funds document with a deliberate constraint:
**it contains zero dollar figures**, because no dollar figure is banked in any artifact and
the operating rules forbid writing numbers that are not. Every cost below is stated in the
units the artifacts actually measure — seconds of wall-clock compute on 4 CPU cores with no
GPU (the `cost` fields of `artifacts/pivot/*.json`), corpus build seconds, and array shapes
with their element sizes. Every forward projection is labelled **EXTRAPOLATION** with its
basis shown on the same line. Everything unverifiable is under COULD NOT VERIFY at the end.

The claim this map makes is narrow: each milestone below is a *question the record already
poses*, with a preregistration shape, a kill criterion, and a measured-unit cost basis. A
raise spent this way buys answers — including the answer "stop" — not activity.

## Where the record stands, in four lines

- `CURVE_ESTABLISHED` (prereg 0003): carved-DEFLATE encoder provenance rises +0.0491
  accuracy points per decade of manufactured data over 2.9031 decades, top rung 0.2395
  against 0.038462 chance, both preregistered margins clear — **valid only at a 4096-byte
  window** (0007).
- `CARVE_FAILS` (prereg 0007): at a 1024-byte window the model ties logistic regression
  (margin +0.0099 against a bar of 0.05), and a 4096-trained model transfers at 0.0403 —
  chance. The information is present (byte-identity ceiling 20.79 of 26 at 512 bytes
  against 20.9125 at 4096); the representation is what fails.
- `CARVE_FAILS` at 2048 too (prereg 0011, run 2026-09-02 ahead of M4 with the deviation stated in
  the preregistration): frozen-set margin +0.0475 against 0.05, stricter margin +0.0294, transfer
  0.0455. The boundary of the working window is bracketed to (2048, 4096].
- `BYTE_MODEL_FAILS` / `BYTE_FLAT_FAILS` (preregs 0009, 0010): one small learned
  representation did not rescue 1024, and the corrected-head round came back inconclusive
  because a training recipe tuned under one architecture privileged the incumbent.
- **G5 is uncleared.** No buyer contacted, none claimed, `establishes_a_buyer: false`
  emitted by the readers themselves. This is the gate no measurement in this repository can
  clear, and the map below is ordered around that fact.

## The cost unit, and the banked basis for it

All compute below is priced from these banked fields (4 CPU cores, `gpu: "none"` in every
`cost` block):

| Artifact | What it built | Banked cost |
|---|---|---|
| `artifacts/pivot/deflate_curve.json` | 4096-byte corpus, 1300000 fragments | `build_seconds` 3415.5 |
| `artifacts/pivot/deflate_curve.json` | training, rungs 1000 / 10000 / 100000 / 800000 | `train_seconds_per_rung` 14.5 / 40.3 / 203.6 / 1324.6 |
| `artifacts/pivot/carve_generalisation.json` | 1024-byte corpus, 650000 fragments | `build_seconds` 1066.6 |
| `artifacts/pivot/carve_generalisation.json` | training, rungs 1000 / 10000 / 100000 / 500000 | `train_seconds_per_rung` 11.1 / 24.5 / 99.4 / 751.5 |
| `artifacts/pivot/byte_model.json` | the whole 0009 CNN round (10 epochs, 182842 parameters) | `cost.build_seconds` 3665.7 |

Corpus sizes are banked as array shapes and dtypes in `artifacts/pivot/corpus_manifest.json`
(the corpora themselves are not committed; a cold clone re-manufactures them and checks the
hashes — after `tools/pivot/pin_sources.py` has verified the fetched sources are the banked
edition, because gutenberg.org re-edits files in place; CORRECTIONS.md 2026-09-02):

| Corpus | Shape | Element size |
|---|---|---|
| `data/pivot/full_c4096.npz` (features, 4096 carve) | 1300000 × 1108 | float32, 4 bytes per value |
| `data/pivot/carve_c1024.npz` (features, 1024 carve) | 650000 × 1108 | float32, 4 bytes per value |
| `data/pivot/raw_c1024.npz` (raw bytes, 1024 carve) | 650000 × 1024 | uint8, 1 byte per value |

The byte totals are deliberately not multiplied out: the factors are banked, the products
are not, and this repository's claim gate accepts only banked values. Anyone can do the
arithmetic; this file will not write a number no artifact contains.

The scale of a "free" label is also banked in kind rather than in dollars: the label factory
is the configuration itself, so marginal cost per labelled example is one compression call.

---

## M1 — The per-head recipe search at 1024 bytes

**What it answers.** Is law L4's window binding a property of the *task*, or of one frozen
training recipe? This is the exact question 0010 was named inconclusive on. Prereg 0009's
byte CNN (global average pool) converged and failed: 0.0849 against hand-engineered features
at 0.1165 and a logistic byte-histogram baseline at 0.0943. A probe then showed the pooling
itself destroys per-example identity — a flatten head memorises 5000 shuffled labels at
0.364 train accuracy where the pooled head reaches 0.0486, at identical convolutional
capacity. Prereg 0010 changed only the head — and under 0009's frozen recipe the flatten
head never trained at all: 0.0385 on real labels, exactly chance, with a null control that
never became failable (0.0393 train against the frozen 0.30 bar). `VERDICT.md` states the
open question in its own words: *"A fair 0011 would have to preregister a recipe search per
head, not a shared recipe."* This milestone is that preregistration. (Its id is whatever the
chain assigns when it is frozen; 0011 was taken on 2026-09-02 by the 2048-byte carve-boundary
run, so the "0011" in the quoted sentence is a placeholder, not a promise.)

**Preregistration it needs.** A preregistration freezing: the per-head recipe search space
(schedules, batch sizes, epoch budgets) *symmetrically for both heads*; the same
eval-group fingerprint refusal 0009 and 0010 used (the run refuses unless the evaluation
set matches 0007's corpus B); 0010's failable-null clause carried over (`null_train_top1`
must reach 0.30 before a clean control is credited); and the same three bars — A2 margin
0.05 over baselines trained on the same rows, strictly beating the hand-engineered 0.1165,
null control clean.

**Kill criteria.** If the best head found by the search still fails the A2 margin and still
loses to 0.1165, the 1024-byte window is closed for this architecture class at this scale:
L4 stands strengthened, `CARVE_FAILS` stands unqualified, and the forensic use case is
confined to carve sizes where the within-size margin clears — today, only 4096. That
outcome is a real answer and it feeds M4 directly (a buyer whose carves are small is then a
buyer this task cannot serve). What it would *not* kill: larger architectures or GPU-scale
training, which stay explicitly out of scope and unclaimed, as 0009's own scope note did.

**Cost basis (measured units).** The raw-byte corpus already exists and is hash-pinned
(650000 × 1024 uint8, `corpus_manifest.json`) — corpus cost for this milestone is zero
seconds. One full CNN round at the matched 100000 rung banked 3665.7 seconds on 4 CPU
cores, no GPU (0009's `cost` field). **EXTRAPOLATION:** a search over ten recipe
configurations per head, two heads, run to 0009's epoch budget, is on the order of ten
times two times 3665.7 seconds of the same 4-core compute — basis: cost linear in the
number of configurations, each configuration priced at the one banked run. Longer epoch
budgets scale the same figure by the epoch multiple; no GPU number is written because none
is banked.

---

## M2 — A fifth rung: one more decade of data at 4096 bytes

**What it answers.** Whether the one curve in this repository that is a claim about the
world keeps its slope. `CURVE_ESTABLISHED` rests on four rungs, 1000 to 800000, spanning
2.9031 decades, slope +0.0491 with cluster-corrected interval [0.0482, 0.0500]. Two facts
in the record make the next decade a genuine question rather than a victory lap. First, the
top rung was set by memory, not chosen: 800000 of the 1040000 fragments available, capped
during OOM debugging, with five of six attempts killed at about a 13.9 GB ceiling
(`engineering_log.json`). Second, the permutation p-value sits at its arithmetic floor of
0.0417 — exactly 1/24, all four-rung orderings exhausted — and the record itself says what
lowers it is *more rungs*, not a better result.

**Preregistration it needs.** A new prereg freezing, before the corpus exists: a
slope-continuation clause (the fifth rung must land inside the frozen fit's projected
band); the margin clause retained at 0.05 — this is non-negotiable, because 0007 showed
exactly what a statistically clean slope without a margin clause is worth (at 1024 the
within-size slope's interval excludes zero and the model still ties a dumb rule); source
chunks disjoint from both existing corpora, as 0007 required; and a fix for the known
defect — the gutenberg family's 32768-byte windows drawn from one shared pool, the leak
that made a frozen sentence false for one eighth of the corpus (it depressed the headline
rather than inflating it — excluding it steepens the slope — but the next prereg does not
get to repeat a known false sentence).

**Kill criteria.** If the fifth rung falls outside the frozen band on the low side, or the
margin over refreshed same-rung baselines falls below 0.05, the curve is bounded: the
honest statement becomes "the curve was real for 2.9031 decades and flattened", and M2's
answer is that more manufactured data is not where the value is. That kills the "just add
data" branch of the strategy at the price of one corpus build. It does not touch
`CURVE_ESTABLISHED` as measured — nothing can revise a banked verdict — it scopes it.

**Cost basis (measured units).** Banked: 3415.5 build seconds produced the 1300000-fragment
4096 corpus; banked train seconds across the four rungs were 14.5, 40.3, 203.6, 1324.6 —
note the growth is sublinear in rung size (an 8× step from 100000 to 800000 multiplied
train time by less than 8: 203.6 to 1324.6). **EXTRAPOLATION:** a fifth rung at ten times
the 800000-fragment top rung costs on the order of ten times 1324.6 train seconds, and the
corpus extension on the order of ten times 3415.5 build seconds — basis: linear scaling in
fragment count, which the banked ladder shows is a conservative upper bound for training.
**EXTRAPOLATION, weaker:** peak memory scales with the same factor of ten under the current
in-memory pipeline, against the ~13.9 GB ceiling that already killed five runs — so this
milestone carries an out-of-core engineering cost that has **no banked measurement**; see
COULD NOT VERIFY.

---

## M3 — Additional carve sizes and encoder families

**What it answers.** How far the established result extends beyond its box. Prereg 0003's
own scope paragraph names what is uncovered: *"encoders absent from this box, notably
7-Zip's deflate, Java's Deflater, Go's flate and the Cloudflare and Windows zlib forks"*,
and *"carve sizes other than the one frozen here."* Today there are three measured
sizes — 4096 (works, margin +0.1003 frozen and +0.0583 stricter), 2048 (fails by 0.0025 on the
frozen set, +0.0475, and by more on the stricter one, +0.0294; prereg 0011) and 1024 (fails,
margin +0.0099) — the boundary is bracketed to (2048, 4096], and nothing is measured beyond
4096 or below 1024. The information-side prerequisite is already
banked down to 512 bytes: the byte-identity ceiling is 20.79 distinct streams of 26 at 512
against 20.9125 at 4096, so any per-size failure is a modelling result, not an information
result, exactly as 0007 was forced to say.

**Preregistration it needs.** Per carve size: the 0007 protocol re-frozen — within-size
margin at 0.05 against same-rung baselines including the deep trees, four rungs, grouped
split, disjoint source chunks, null control. `CARVE_SIZE_SPECIFIC` — one model per carve
size, one more compression pass each — was 0007's preregistered survivable outcome and
remains the survivable outcome here. Per encoder family: a prereg freezing the expanded
configuration set before any corpus is built, with the margin re-cleared at the matched
rung on the expanded class set, and the per-family accuracy reported for the new families
the way `per_family_curves.json` reports content families — all of them, either way.

**Kill criteria.** A carve size whose within-size margin lands below 0.05 is dead at that
size, exactly as 1024 is — and if the sizes real buyers report (M4) are all dead sizes,
the forensic use dies with them. For encoders: if adding the named families drops the
matched-rung margin below 0.05, the result is bound to its current encoder box, and
quoting it as "carved DEFLATE encoder provenance" rather than "provenance among these 26
configurations" becomes the kind of overquote this repository files corrections for. Kill
here is cheap and informative in both directions.

**Cost basis (measured units).** The two banked corpus builds bracket the per-size cost:
1066.6 build seconds for 650000 fragments at 1024, 3415.5 for 1300000 at 4096, with train
ladders of 11.1–751.5 and 14.5–1324.6 seconds respectively. **EXTRAPOLATION:** one
additional carve size run to the full 0007 protocol costs on the order of one banked 1024
ladder — about 1066.6 build seconds plus under 1000 train seconds at 4 cores — basis: same
fragment counts, same pipeline, cost scaling between the two banked points with carve
bytes and fragment count. For encoder families the labels remain free — marginal cost one
compression call per fragment — and the build cost scales with the configuration count;
**EXTRAPOLATION:** growing the class set from 26 scales build seconds roughly in
proportion, basis: the build is one compression pass per configuration per chunk.

---

## M4 — Buyer discovery: G5, the gate no measurement clears

**Stated plainly: this is human work, and no measurement substitutes for it.** The record
says it three times in three artifacts — `establishes_a_buyer: false` is emitted by the
readers themselves — and once in prose: *"The work that would clear it is not work that can
be done from inside this container."* A rising curve does not supply a buyer. Funding M1–M3
without M4 is buying activity; M4 is what makes the other three answers *worth having*.
It therefore starts first, in parallel, and its findings gate the compute milestones.

**The three uses the record names, and what evidence each would need.**

1. **Forensic carving of unallocated disk.** The only use where a carved fragment is
   genuinely the operational setting — no header, no stream start, no plaintext — which is
   why 0006 measured the operational shape there: top-5 at 0.5694 against the strongest
   baseline's 0.4610, and 0.7922 accuracy on the most-confident decile, at 4096. Evidence
   needed: named practitioners (forensic labs, carving-tool maintainers) stating the
   fragment sizes their carves actually produce — because `VERDICT.md` notes carving works
   in disk clusters *"frequently smaller"* than 4096, with **no banked number**, and if
   the answer is predominantly below 4096 then `CARVE_FAILS` applies and this use is dead
   until M1 or M3 revives the small-carve case; whether a 5-of-26 shortlist plus an
   abstention signal fits an actual workflow; and an actual willingness to pay, which only
   a conversation establishes.
2. **Archive recompression.** The record's own analysis already runs against this one:
   the holder of an archive has the whole stream and the plaintext, so incumbent tools
   apply and this task's advantage disappears — that is the record's own analysis in the
   0006 section, not a concession invented here (`preflate` needs the stream start,
   `precomp` needs the plaintext — the C1 section's words). Evidence needed to keep it
   alive: a named
   operator whose recompression setting genuinely lacks the stream start or plaintext.
   Absent that, this use should be written off explicitly rather than kept on a slide.
3. **Repackaged-APK detection.** Same structural objection to confirm or refute: an APK in
   hand is a whole archive, not a carved fragment, so the burden is to find a named
   practitioner whose setting is fragment-only. Evidence needed: that practitioner, their
   current tool, and what the provenance answer would change in a decision they make —
   because conjecture C2's warning applies in full here: we possess zlib, zopfli, ISA-L
   and libdeflate, which is exactly why the labels are free and exactly why knowing which
   one ran may be worth little.

**Preregistration it needs.** Interview work can and should still be preregistered in this
repository's sense: the buyer types, the questions (carve-size distribution, incumbent
tool, decision changed, budget owner), the counts, and the pass/kill reading frozen
*before* the first conversation — because a buyer search that must return a buyer will
invent one, which is the exact failure mode Phase 0 was built to refuse (*"A search that
must return a domain will invent one"*).

**Kill criteria.** If no named buyer type both (a) operates on fragments at a size where
the within-size margin clears and (b) states a decision the provenance answer changes,
then G5 fails on evidence rather than by default, C2 is confirmed for this task, and the
honest verdict is that the pivot is a validated instrument and label factory with no
business attached — at which point M2 and M3 should not be funded, whatever their curves
look like. That is this map's most important kill, and it is cheap: it costs
conversations, not compute.

**Cost basis.** No compute. No banked artifact measures the cost of this work and no
figure is invented for it; see COULD NOT VERIFY.

---

## Sequencing and the shape of the spend

- **M4 starts immediately** and gates everything: it is the only milestone that can make
  the others matter, and its kill is the cheapest.
- **M1 runs early and cheap** (its corpus exists; its banked unit cost is 3665.7 seconds
  per training round) because its answer — is 1024 dead or merely mistrained — determines
  which buyers M4's forensic thread can serve.
- **M3's carve-size arm follows M4's carve-size evidence**: measure the sizes buyers
  actually report, not sizes chosen for convenience. (The 2048 run of 2026-09-02 was a
  deliberate exception, made to bound the record's own scope statement; its preregistration says
  so and M3 proper still waits for M4.)
- **M2 runs only if M4 finds a live buyer type at a working carve size.** One more decade
  of a curve nobody needs is the exact thing 0007 taught this repository to stop
  producing: a statistically clean positive scaling result on a task that fails its
  margin — *"a rising curve on a task nobody needs is a rising curve on a task nobody
  needs."*

Each milestone ends in a banked verdict from a frozen reader, pass or kill alike, under
the same chain (`prereg/chain.jsonl`) as everything above. The raise buys those verdicts.

## COULD NOT VERIFY

- **Peak memory for M2's fifth rung.** The ~13.9 GB ceiling at the 800000 rung is banked;
  the memory requirement of a rung ten times larger is not measured anywhere, and the
  linear-scaling figure above is an extrapolation with no artifact behind it.
- **The carve-size distribution of real forensic workloads.** The record says clusters are
  frequently smaller than 4096 and banks no number. This is M4 evidence item 1, not a fact.
- **Any dollar cost, for anything.** The banked `cost` blocks carry seconds, cores and
  `gpu: "none"`; no artifact in this repository prices a second of compute or an hour of a
  person, so this document prices nothing in currency.
- **Whether any buyer would pay.** G5 is uncleared; `establishes_a_buyer: false` stands.
  Nothing in this file, including M4's design, is evidence that one would.
- **Wall-clock or calendar duration of any milestone.** No banked artifact measures
  team throughput; no timeline figures are written.
