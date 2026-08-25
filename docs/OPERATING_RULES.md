# Operating rules

These are the rules the work in this repository is run under. They are stated before the
results so that they cannot be adjusted to fit them.

## 1. Preregister before you measure

The bar is frozen, the readings are frozen, and the reader script is committed **before the
data exists**. A reader written after seeing the number is shaped by it, whether or not its
author intends that.

Enforced by `tools/prereg.py`. Freezing records the reader's `sha256`; `prereg.py verify`
re-hashes the reader and fails if it changed. Freezing also appends to an append-only
hash chain (`prereg/chain.jsonl`) whose entry *N* carries the hash of entry *N-1*, so the
**order** of preregistrations is tamper-evident — you cannot silently insert a
preregistration between two that already exist.

Each frozen entry additionally embeds two public randomness beacon pulses (NIST
Interoperable Randomness Beacon 2.0 and drand). Those values cannot be known before their
round exists, so the entry carries a **not-before** proof that does not depend on this
repository's own git history or on anything under our control.

## 2. Numbers come only from artifacts

If a figure is not in a banked file under `artifacts/`, it does not go in a document.
Enforced by `tools/claimcheck.py`, which extracts every number from outbound copy and fails
unless some banked artifact contains a value that rounds to it *at the precision it was
written*. Numbers that are genuinely not measurements go in
`docs/claimcheck_allowlist.tsv` **with a written reason**; the allowlist is a diffable,
auditable file and an entry without a reason is a hard error.

## 3. A preregistration is a commitment, not a shield

When the letter of the frozen wording and its substance disagree, that is said out loud and
the reading taken is the one that does **not** flatter us. The frozen text is not a licence
to report a technically-compliant number that misleads.

## 4. Every gate must be able to fail

A verifier that cannot fail is decoration. `tests/mutation_test.py` deliberately breaks each
gate and asserts the gate notices. A mutation that survives is reported as a hole in the
instrument, not quietly dropped. The report is banked at
`artifacts/verification/mutation_report.json`.

## 4a. Measure the dumbest thing that could work, first

Before any learned result is believed, the trivial baselines are run and banked:
`tools/trivial_baselines.py` fits majority-class, label-prior sampling, a single thresholded
feature, a depth-3 tree, 1-NN and logistic regression, and reports the best of them as a floor.
A learned score is compared against **that floor plus a preregistered margin**, never against
chance. The gate exits non-zero when the floor is not cleared, and refuses to run at all if a
claimed score is offered without a margin frozen in advance.

This rule exists because of a specific near-miss. In round 1 of domain selection, a candidate
whose entire thesis was that a task required a learned model was killed by fifty lines of
non-learned rules reaching F1 0.768 on it; twenty thousand training records bought 1.4 more
points. That was found by an adversarial reviewer in under an hour. It is cheaper to find it
first.

## 5. File corrections against yourself, at full size

`CORRECTIONS.md` records every claim withdrawn or revised, dated. An over-claim against our
own interest is still an over-claim and is filed at the same size as the rest. The value of
the ledger comes entirely from what it costs us to keep it; a ledger that only ever contains
other people's mistakes is worth nothing.

## 6. State scope before the data, not after

"One corpus, one seed, one rung" belongs in the preregistration, not in a limitations
paragraph written once the number is known.

## 7. Cost beside quality, always

No price without the score that bought it, and no score without the price. Every arm reports
wall-clock, CPU-hours and, where relevant, dollars.

## 8. Never fabricate

Anything not verified is written as `COULD NOT VERIFY` together with the reason it could not
be verified. An absent result is reported as absent.

**A count derived from a pattern over names is not a measurement** until the pattern has been
checked against the authoritative definition, and any artifact reporting such a count must print
its derivation beside it. Where a check disagrees with the thing it is checking, the check is
assumed wrong until shown otherwise. Added 2026-08-25 after this repository miscounted a column
set with an unvalidated `F*P` filter and recorded the result as a defect in the work it was
checking — see `CORRECTIONS.md`.

## 9. Commit and push after every meaningful step

The execution container is ephemeral. Work that is not pushed does not exist.

## 10. No claimed customer, user, or partner that does not exist

There are none at the time of writing, and the documents here say so.

---

## Reproducing the instrument

```
python3 tools/prereg.py verify        # hash chain, sealed fields, reader hashes
python3 tests/mutation_test.py        # proof that the gates can fail
python3 tools/claimcheck.py outbound  # outbound-copy gate
```

All three are run in CI on every push (`.github/workflows/verify.yml`) and all three exit
non-zero on failure.
