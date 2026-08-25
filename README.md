# raise-v1

An evidence package built around one question: **does the quality of a model trained on
*manufactured* labels go up with the volume of manufactured data?**

The output is a scaling curve produced by an instrument that is designed to be unable to
cherry-pick, plus one shipped open artifact a stranger can reproduce from a cold clone.

## Status

| Phase | What it is | State |
|---|---|---|
| 0 | Domain selection against five hard gates | in progress |
| 1 | Falsify the data thesis cheaply (obtain data, measure label noise) | not started |
| 2 | The scaling curve: >=4 data scales, >=2 orders of magnitude, preregistered | not started |
| 3 | Ship the credibility artifact (open data/weights + harness, one command) | not started |
| 4 | The evidence package (`VERDICT.md`, `CORRECTIONS.md`, coverage map) | scaffolded |

No customers, no users, no partners. Nothing in this repository claims otherwise.

## The instrument

The reason to believe any number here is that the machinery constraining how numbers may be
reported was built and committed *before* the numbers existed, and it is designed so that
each of its gates can be shown to fail on demand.

```
python3 tools/preflight.py            # interpreter + dependency floors, cause and fix
python3 tools/prereg.py verify        # hash-chained preregistration order + reader hashes
python3 tests/mutation_test.py        # deliberately break each gate; assert each notices
python3 tools/claimcheck.py outbound  # every number in outbound copy traces to an artifact
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
