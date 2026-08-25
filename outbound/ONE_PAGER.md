# raise-v1 — an instrument, and the negative result it produced

## What this is, and what it is not

**It is** a preregistered evaluation instrument, and one negative finding produced by running it.

**It is not** a scaling curve. There is no curve in this repository. The machinery to fit one and
put an honest interval around it is built and mutation-tested; no real slope has been fitted,
because no domain survived selection.

There are no customers, no users and no partners, and nothing here claims otherwise.

---

## The finding

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
*effect* of one. So the class of problem that would work is:

> a high-bandwidth physical recording that is the causal consequence of the hidden variable,
> published in bulk for a reason unrelated to the label.

None of the 99 candidates had it. That is a usable specification, not a consolation.

## The part that should be read first

The verification-coverage map is machine-checked and prints its weakest class first, deliberately.

**9 of 24 claims are in the weakest class** — they can be neither re-derived nor re-run by anyone,
including us. Eight are measurements made by subagents inside scratch directories that no longer
exist, and **that includes measurements the conclusions rest on.** The ninth is worse than
unverified: it is a figure we published and then failed to reproduce ourselves.

Two of the load-bearing measurements have since been pulled out of that class by re-deriving them
here from public data with shipped code. Doing so on the second one **contradicted a number this
repository had already published, in the direction that flattered its own conclusion.** It is filed
in the corrections ledger at full size rather than resolved by adopting the better-looking figure,
and neither version of it is quoted as established anywhere.

The ledger also carries a correction filed against this repository's own verification work, for
manufacturing a discrepancy against a subagent that turned out to be right.

## Verify it yourself, on a cold clone

```
git clone <repo> && cd raise-v1
python3 tools/preflight.py                        # interpreter + dependency floors, cause and fix
python3 tools/prereg.py verify                    # chain order, sealed fields, reader hashes
python3 tests/mutation_test.py                    # 38 deliberate mutations, 38 detected, 0 survived
python3 tools/coverage.py                         # coverage map, weakest class first
python3 tools/claimcheck.py outbound VERDICT.md   # every number traces to a banked artifact
```

Two dependencies, both CPU-only. Every command above exits non-zero on failure. This document
passes the last one with no allowlist entries.
