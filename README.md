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
| 2 | The scaling curve | **`CURVE_ESTABLISHED`** at a 4096-byte carve — +0.0491/decade over 2.9031 decades. **`CARVE_FAILS`** at 1024 and at 2048; boundary (2048, 4096]. |
| 3 | Ship the credibility artifact | partial — the instrument and the manufacture-and-measure pipeline ship; the 5.8 GB corpus is not committed |
| 4 | The evidence package (`VERDICT.md`, `CORRECTIONS.md`, coverage map) | delivered |

**There is a curve, and it does not make the thesis fundable.** The pivot — recovering which of
26 DEFLATE (implementation, level) configurations produced a window carved from the *middle* of a
compressed stream, with no header, no stream start and no plaintext — clears every preregistered
clause: four rungs over 2.9031 decades, a slope of **+0.0491** accuracy points per decade with a
cluster-corrected 95% interval of **[0.048216, 0.050014]**, a null control at chance, and a margin over the best trivial
baseline of **+0.1003** under the frozen baseline set and **+0.0583** under the stricter one that
adds deep trees. Both clear the 0.05 frozen before the corpus existed.

**And it is bound to one window size.** A second preregistration built a corpus at a 1024-byte
carve and returned `CARVE_FAILS`: the model ties a dumb rule, and a 4096-trained model falls to
chance on the shorter window. The information is present at 1024 — the byte-identity ceiling barely
moves — so this is a modelling failure, and the forensic setting the buyer argument leaned on does
not guarantee the window the result needs. A third preregistration measured the midpoint: at
2048 bytes the model reaches 0.1741 against logistic regression at 0.1266 — a margin of +0.0475,
0.0025 short of the 0.05 bar — and +0.0294 against a depth-16 tree, with transfer from 4096 at
0.0455 against 0.038462 chance. The window boundary of this recipe is bracketed to (2048, 4096].
A fourth preregistration then searched the recipe symmetrically — eight enumerated recipes for
the model and for each baseline with a hyperparameter, selected by one rule on a holdout that
never touched the evaluation set, every baseline floored at its earlier value: the model rose to
0.212 and the standardised logistic baseline to 0.1886, so the margin fell to +0.0234 and the
verdict is `RECIPE_FAILS` (read under preregistration 0013 after 0012's own frozen reader
voided the run on a defect of its own, filed in the corrections ledger). Preregistration 0014
then applied the same search to the headline 4096-byte result — 0003's sealed evaluation set,
0003's 800000-row pool, every baseline floored at its 0003 value, the outcome stated in advance as
genuinely uncertain — and it clears: the searched model reaches 0.2884 against a searched
logistic at 0.2317, margins +0.0567 on both readings and +0.0576 with the leaked family excluded,
verdict `RECIPE_CLEARS`. The headline margin is therefore quoted at its searched size, +0.0567,
beside the +0.1003 that fixed recipes gave.
Decomposed by content family, csv and log clear the bar at 2048 on both readings (+0.0554 and
+0.0501 against the strongest baseline) and the structured four clear it as a set (+0.0549), but
the mixture fails even with the three incompressible families removed (+0.0478); the verdict is
the mixture's, and the decomposition is published beside it.

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

## Public mirror

**Public mirror:** https://github.com/raj200501/raise-v1-public — regenerated from this repository's `main`
with four GNSS product files and one e-mail address filtered out of history (its `docs/PUBLIC_MIRROR.md`
maps every preregistration's frozen commit to the mirror's); every artifact, reader, gate and document is
identical.

## Licence

Apache-2.0 (full text in `LICENSE`, copyright in `NOTICE`), for the code and for `outbound/`
alike. Data and dependency licences are recorded per-corpus in `docs/compliance/LICENSE_AUDIT.md`
— with the upstream licence texts and a hash manifest of every fetched source under
`docs/compliance/sources/` — and are not assumed to be the same as the code licence. One
component used only by an archived Phase-0 reproduction (Lingeling, via `python-sat`) carries a
licence that permits evaluation and research use and "does not allow this software to be used in
a commercial context"; it is not in the product path, and whether the banked reproduction run
falls inside that restriction is a legal question the audit records as COULD NOT VERIFY.
