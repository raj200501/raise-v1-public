# raise-v1

An evidence package built around one question: **does the quality of a model trained on
*manufactured* labels go up with the volume of manufactured data?**

The output is a scaling curve produced by an instrument that is designed to be unable to
cherry-pick, plus one shipped open artifact a stranger can reproduce from a cold clone.

## Status

| Phase | What it is | State |
|---|---|---|
| 0 | Domain selection against five hard gates | **terminated — NO VIABLE DOMAIN FOUND** |
| 1 | Falsify the data thesis cheaply | not started — there is no thesis to falsify |
| 2 | The scaling curve | not started — **the headline absence** |
| 3 | Ship the credibility artifact | partial — the *instrument* ships; no dataset or weights exist |
| 4 | The evidence package (`VERDICT.md`, `CORRECTIONS.md`, coverage map) | delivered |

**Phase 0 terminated with no domain selected.** 99 candidates across three rounds, 8 put through
adversarial review with default posture REJECT, 0 SELECT. The verdict was emitted by a reader
frozen and hashed before the data existed, under a preregistration anchored to a public randomness
beacon. Read [`VERDICT.md`](VERDICT.md) first — it leads with what is missing, and the verification
coverage map publishes its weakest row loudest.

No customers, no users, no partners. Nothing in this repository claims otherwise.

## The instrument

The reason to believe any number here is that the machinery constraining how numbers may be
reported was built and committed *before* the numbers existed, and it is designed so that
each of its gates can be shown to fail on demand.

```
python3 tools/preflight.py            # interpreter + dependency floors, cause and fix
python3 tools/prereg.py verify        # hash-chained preregistration order + reader hashes
python3 tests/mutation_test.py        # deliberately break each gate; assert each notices
python3 tools/coverage.py             # verification-coverage map, weakest class printed first
python3 tools/claimcheck.py outbound VERDICT.md   # every number traces to a banked artifact
```

- **Preregistration is hash-chained.** Entry *N* carries the hash of entry *N-1*, so the
  *order* of preregistrations is tamper-evident, not just their contents. Each entry embeds
  a NIST Beacon 2.0 pulse and a drand round as a not-before proof that does not depend on
  this repository's own history.
- **Readers are frozen by hash before the data exists.** `prereg.py verify` fails if a
  reader was edited after its bar was frozen.
- **Numbers come only from banked artifacts.** `claimcheck.py` fails on any number in
  outbound copy that no artifact under `artifacts/` supports at the precision written.
- **The dumbest baseline is measured first.** `tools/trivial_baselines.py` establishes the
  floor a learned result must clear — best trivial baseline *plus a preregistered margin*, not
  chance — and refuses to run at all if the margin was not frozen in advance.
- **Every gate has a mutation test.** `tests/mutation_test.py` reports surviving mutations
  as holes in the instrument rather than dropping them.

Full rules: [`docs/OPERATING_RULES.md`](docs/OPERATING_RULES.md).

## Layout

```
tools/       the instrument (prereg chain, outbound-copy gate, shared hashing)
tests/       mutation tests proving the gates can fail
prereg/      frozen preregistrations + the append-only chain
artifacts/   banked machine-readable results; the only legal source of a number
docs/        domain selection, operating rules, verification coverage
outbound/    anything intended to leave the repo; gated by claimcheck
```

## Licence

Apache-2.0 (see `LICENSE`). Data licences are recorded per-corpus in `docs/` and are not
assumed to be the same as the code licence.
