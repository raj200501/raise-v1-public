# raise-v1

An evidence package built around one question: **does the quality of a model trained on
*manufactured* labels go up with the volume of manufactured data?**

The output is a scaling curve produced by an instrument that is designed to be unable to
cherry-pick, plus one shipped open artifact a stranger can reproduce from a cold clone.

## Status

| Phase | What it is | State |
|---|---|---|
| 0 | Domain selection against five hard gates | **terminated — NO VIABLE DOMAIN FOUND** (rounds 1–3, and round 4 agreed) |
| 1 | Falsify the data thesis cheaply | delivered on the pivot — null control, grouped split and baseline floor all measured first |
| 2 | The scaling curve | **`CURVE_ESTABLISHED`** at a 4096-byte carve — +0.0491/decade over 2.9031 decades. **`CARVE_FAILS`** at 1024. |
| 3 | Ship the credibility artifact | partial — the instrument and the manufacture-and-measure pipeline ship; the 5.8 GB corpus is not committed |
| 4 | The evidence package (`VERDICT.md`, `CORRECTIONS.md`, coverage map) | delivered |

**There is a curve, and it does not make the thesis fundable.** The pivot — recovering which of
26 DEFLATE (implementation, level) configurations produced a window carved from the *middle* of a
compressed stream, with no header, no stream start and no plaintext — clears every preregistered
clause: four rungs over 2.9031 decades, a slope of **+0.0491** accuracy points per decade with a
95% interval of **[0.0485, 0.0497]**, a null control at chance, and a margin over the best trivial
baseline of **+0.1003** under the frozen baseline set and **+0.0583** under the stricter one that
adds deep trees. Both clear the 0.05 frozen before the corpus existed.

**And it is bound to one window size.** A second preregistration built a corpus at a 1024-byte
carve and returned `CARVE_FAILS`: the model ties a dumb rule, and a 4096-trained model falls to
chance on the shorter window. The information is present at 1024 — the byte-identity ceiling barely
moves — so this is a modelling failure, and the forensic setting the buyer argument leaned on does
not guarantee the window the result needs.

What it also does not clear is **G5, a named buyer type**. No buyer has been contacted and none is
claimed. A rising curve on a task nobody needs is a rising curve on a task nobody needs, and the
gap between a validated label factory and a business is the honest state of this repository.

**Phase 0 terminated with no domain selected.** 99 candidates across three rounds, 8 put through
adversarial review with default posture REJECT, 0 SELECT. A fourth round, authorised afterwards
under its own preregistration with a *higher* bar, agreed — and retracted the most encouraging
claim the earlier rounds had produced. The verdict was emitted by a reader
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
python3 tools/freshness.py            # every LIVE number equals its artifact's current value
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
- **A stale number is caught, not just a fabricated one.** `claimcheck.py` asks whether a
  number exists in a banked artifact, which is the wrong question for a value that was true
  and no longer is — the old value stays banked forever, so it keeps passing. `freshness.py`
  re-derives each live number from its artifact and fails on divergence. It was written after
  that failure happened twice, and on its first run it caught three stale numbers in
  `VERDICT.md`.
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
trial/       archived work that did not select: the full 99-candidate search, kept in full
data/        corpora fetched by the shipped scripts; not committed
```

## Licence

Apache-2.0 (see `LICENSE`). Data licences are recorded per-corpus in `docs/` and are not
assumed to be the same as the code licence.
