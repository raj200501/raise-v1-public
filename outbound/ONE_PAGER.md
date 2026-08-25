# raise-v1 — a preregistered instrument, a curve that clears it, and no buyer

## What this is, and what it is not

**It is** a preregistered evaluation instrument, built and frozen before any of the numbers it
reports existed, and designed so that each of its gates can be shown to fail on demand.

**It is** a scaling curve that clears every clause frozen before its corpus existed —
`CURVE_ESTABLISHED`, **+0.0491** accuracy points per decade over **2.9031** decades, margin
**+0.1003** frozen and **+0.0583** under the stricter reading, both above the preregistered 0.05.

**It is not** a fundable thesis. The task has no established buyer, none has been contacted, and
none is claimed. There are no customers, no users and no partners.

---

## The result

Take a window from the MIDDLE of a DEFLATE stream — no header, no stream start, no plaintext, not
even the stream length — and recover which of **26** (implementation, level) configurations produced
it. The label factory is free and unbounded: compress any bytes under every configuration and the
label *is* the configuration you used.

| Rung | 1000 | 10000 | 100000 | 800000 |
|---|---:|---:|---:|---:|
| Accuracy | 0.0988 | 0.1415 | 0.1965 | **0.2395** |

Chance is **0.038462** across 26 classes. The split is grouped by source chunk, so no source bytes
straddle train and evaluation — a random split would measure content memorisation instead, and the
archived trial killed a candidate on exactly that, watching 0.4873 collapse to 0.1531. Labels
shuffled, the identical pipeline retrained, falls to **0.0389**.

Every trivial baseline was trained on the same 800000 fragments as the top rung, so none is
starved. Best of the **preregistered** set: logistic at **0.1392**, margin **+0.1003**. Best of the
stricter set that adds deep trees, which are *not* in the frozen list and are stronger than
anything in it: a depth-16 tree at **0.1812**, margin **+0.0583**. Both clear 0.05, and the
commitment to report both was recorded mid-run and anchored to drand round **6408095**, before
either number was known.

**Why no existing tool does this.** `preflate` and `grittibanzli` decode the token stream, which
needs the dynamic Huffman tables at the STREAM START. `precomp` and `list-compresslevel.py`
brute-force by RECOMPRESSING, which needs the PLAINTEXT. A carved fragment has neither. Three
GitHub API query formulations returned `total_count: 0`.

**What it does not establish.** A buyer. The uses this points at — forensic carving of unallocated
disk, archive recompression, repackaged-APK detection — are narrow, nobody has been contacted, and
nothing measured here says anyone would pay. The permutation p of **0.0417** is exactly its
arithmetic floor of 1/24 for four rungs and must not be read as "just under 0.05". The top rung was
capped at 800000 by memory during OOM debugging, before any 800000-fragment number existed.

---

## How the search got here

A search for a domain in which to reproduce the FDM-1 structure — abundant unlabelled corpus, a
mechanism that manufactures labels at near-zero marginal cost, a curve that rises with data — was
run to three rounds and terminated by a rule frozen before the final round ran.

**99 candidate domains. 8 put through adversarial review with default posture REJECT. 0 selected.**

The verdict `NO_VIABLE_DOMAIN_FOUND` was emitted by a reader written, committed and hashed before
the data it reads existed, under a preregistration whose ordering is hash-chained and whose
not-before time is anchored to a public randomness beacon (NIST Beacon 2.0 pulse 1916929, drand
round 6406735). The reader's sha256 is unchanged since freezing, and `tools/prereg.py verify`
fails if it ever is.

## Why it is worth more than a domain would have been

Every candidate died to one of five failure modes, each established by measurement rather than
argument. Three general laws fell out:

**L1 — Smooth reprocessing corrections are fitted, not learned.** A cubic polynomial plus one
sinusoid, about ten lines with no learning in them, explains up to 0.994 of the residual variance
in satellite orbit-correction arcs. This retires an entire family of candidate domains.

**L2 — An analytically invertible generator yields a closed-form inverse that takes the whole
label.** Only lossy, non-invertible generators are candidates at all.

**L3 — For labels to be free at scale, the labelling must already be someone's job, and there are
exactly three ways that happens — each destroying a different gate.** A *machine* does it, so
re-run-and-compare is a zero-training decoder. An *institution* reveals it on a schedule, so the
field already built the tool and the buyer's incumbent is "wait". A *human* records it in a
register — and a register publishes the decision, not the state.

**What that leaves.** A register row is a *description* of a decision; a video frame is a physical
*effect* of one. So the class the pool lacked is:

> a high-bandwidth physical recording that is the causal consequence of the hidden variable,
> published in bulk for a reason unrelated to the label.

None of the 99 candidates had it — **and a fourth round then found that class is not white space
either.** Every instance probed was already occupied, one of them by the FDM-1 structure itself
(AIS used to pseudo-label bulk hydrophone recordings for self-supervised learning). Pseudo-labelling
a large unlabelled sensor archive from weak supervision turns out to be the named, surveyed default
of every sensing discipline. An earlier version of this page called the class "a usable
specification"; that is withdrawn in the corrections ledger.

## A fourth round was authorised, and it also found nothing

Under a **new preregistration frozen before any candidate was chosen**, whose scope records in a
named field that it was opened *because of* a negative result, and whose bar moved **up** — four of
its seven clauses require a measured value and reject an estimate. Five candidates, all five already
occupied. Verdict: `NO_VIABLE_DOMAIN_FOUND_ROUND4`.

**The instrument was finally run on real data.** Until then every part of it had only ever been
exercised on synthetic fixtures, which is not evidence that it works. So it was run end to end on
400,000 units of a CC0 corpus — deliberately on a domain that *cannot be selected*, because that
removes any incentive to flatter the result. It fired correctly three times: it **refused** a
three-rung dataset for violating its own preregistered scope; it then fitted a real curve at
**+0.0338 accuracy points per decade** with a paired-bootstrap interval of **[0.0306, 0.0369]**
excluding zero; and it **rejected the candidate anyway**, because the measured margin over the best
trivial baseline was **0.0313** against a **0.05** frozen before the data existed.

That curve is a validation of the instrument, on a domain that cannot be used, that fails its own
margin. It is **not** the curve at the top of this page — that one is on the DEFLATE corpus, clears
every clause, and came out of the archived trial rather than out of Phase 0 selection. Both are
reported, and neither is quoted as the other.

## The part that should be read first

The verification-coverage map is machine-checked and prints its weakest class first, deliberately.

**9 of 45 claims are in the weakest class** — they can be neither re-derived nor re-run by anyone,
including us. Eight are measurements made by subagents inside scratch directories that no longer
exist, and **that includes measurements the conclusions rest on.** The ninth is worse than
unverified: it is a figure we published and then failed to reproduce ourselves.

Three of the four load-bearing measurements have since been pulled out of that class by re-deriving
them here from public data with shipped code. Doing so on one of them **contradicted a number this
repository had already published, in the direction that flattered its own conclusion.** It is filed
in the corrections ledger at full size rather than resolved by adopting the better-looking figure,
and neither version of it is quoted as established anywhere. A third was only re-derivable because
the reviewer who produced it happened to write its inputs into the repository instead of a scratch
directory — luck, not process, and recorded as such.

The ledger also carries a correction filed against this repository's own verification work, for
manufacturing a discrepancy against a subagent that turned out to be right.

## Verify it yourself, on a cold clone

```
git clone <repo> && cd raise-v1
python3 tools/preflight.py                        # interpreter + dependency floors, cause and fix
python3 tools/prereg.py verify                    # chain order, sealed fields, reader hashes
python3 tests/mutation_test.py                    # 67 deliberate mutations, 67 detected, 0 survived
python3 tools/coverage.py                         # coverage map, weakest class first
python3 tools/claimcheck.py outbound VERDICT.md   # every number traces to a banked artifact
python3 tools/freshness.py                        # every live number equals its CURRENT artifact value
```

Two dependencies, both CPU-only. Every command above exits non-zero on failure. This document
passes the outbound-copy gate with no allowlist entries, and every live number on it is checked
against the current artifact by the gate below it.
