# trial/pivot — the domain search that did not find one

This folder holds the record of a search that ran to four rounds under two preregistrations and
selected nothing. It is archived here so the current work is not read through it, and kept in full
because the pivot only makes sense against it.

## What happened

| | |
|---|---|
| Candidates generated | 99, across three rounds, before any was selected |
| Adversarial reviews, default posture REJECT | 8 |
| Candidates selected | 0 |
| Round 4, under a **higher** bar, authorised afterwards | also 0 |
| Corrections filed against ourselves | 3 |

Two frozen readers emitted the verdicts: `NO_VIABLE_DOMAIN_FOUND` (preregistration 0001) and
`NO_VIABLE_DOMAIN_FOUND_ROUND4` (preregistration 0002).

Read `DOMAIN_SELECTION.md` for every candidate, every gate score and every recorded search.

## Why the evidence files are NOT in this folder

`artifacts/phase0/` and `prereg/` stay where they are, deliberately.

The preregistration chain seals each entry's **file path** into its hash, and each frozen reader's
**sha256** is recorded at freeze time. Relocating a preregistration would break the chain hash;
relocating an artifact would break the reader that reads it, and editing that reader to follow the
file would fail `prereg.py verify` as a reader modified after freezing.

That is the tamper-evidence doing its job. A record you can quietly reorganise is a record you can
quietly rewrite, so the inconvenience is the feature. Tidying the narrative into this folder while
leaving the sealed evidence at its original paths is the only version of "archive it" that does not
weaken the instrument.

## What the trial actually bought

Three laws, each from measurement rather than argument, and all three still govern the current work:

- **L1** — smooth reprocessing corrections are *fitted, not learned*.
- **L2** — an analytically invertible generator yields a closed-form inverse that takes the whole label.
- **L3** — for labels to be free at scale the labelling must already be someone's job, and each of the
  three ways that happens destroys a different gate: a **machine** does it (re-run-and-compare is a
  zero-training decoder), an **institution** reveals it on a schedule (the field already built the
  tool), or a **human** records it in a register (a register publishes the decision, not the state).

Plus the methodological correction that drives the pivot: **G4 has two clauses joined by AND** —
*fewer than ~3 serious efforts* **and** *no open dataset at target scale*. Four rounds were spent
weighting the first clause and treating a studied problem as a dead one. FDM-1 was not a novel idea:
VPT was published, inverse dynamics models were known, screen recordings were not a secret. What
Standard Intelligence had was **a manufactured dataset at a scale nobody had built**. The second
clause is the one that decides whether there is something to build.

The pivot follows from that: stop looking for an unstudied problem, and go build the dataset that
does not exist.
