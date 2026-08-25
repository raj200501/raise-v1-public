# Corrections ledger

Every claim withdrawn or revised, dated, at the same size as the claim it replaces.

The rule (`docs/OPERATING_RULES.md` §5): an over-claim against our own interest is still an
over-claim and gets filed here at full size. Entries are append-only. Nothing is deleted; a
correction that is itself wrong gets a further entry.

Format:

```
## YYYY-MM-DD - <one-line description>
**Claimed:**   what was said, quoted, with where it was said.
**Actual:**    what is true, with the artifact that establishes it.
**Size:**      how much the claim moved, in the units of the claim.
**Cause:**     why the wrong version was written.
**Fix:**       what changed in the instrument so this class of error is caught next time.
```

---

## 2026-08-25 — Miscounted the ACS PUMS allocation-flag columns, and blamed a subagent for it

**Claimed.** In `artifacts/phase0/reproduction_alloctrace.json`, first version, under
`discrepancies`: the round-2 reviewing agent reported "77 contiguous allocation flags" in the
2023 ACS PUMS person file; this repository recorded "76 columns match the filter
`startswith('F') and endswith('P')`" and assessed the gap as "a naming-filter difference, not a
substantive disagreement", listing it as a discrepancy in an artifact whose stated purpose was
checking the agent's work.

**Actual.** There are exactly **77** allocation flags, and the agent's count was right. The
person file has 80 columns beginning with `F`; three of them — `FER` (gave birth in the past 12
months), `FOD1P` and `FOD2P` (recoded field of degree) — are substantive data variables that
merely start with `F`. Three genuine flags end in `C` rather than `P` (`FHINS3C`, `FHINS4C`,
`FHINS5C`), which is why the filter used here does not return 77. The full column list is in the
banked artifact and can be recounted by anyone.

**Size.** One column in an absolute count (76 vs 77, 1.3% of the count). Substantively larger
than that: the entry appeared in a verification artifact, under a heading that reads as "what
the agent got wrong", and it recorded a defect in this repository's own check as though it were
a defect in the thing being checked. The direction of the error is the part that matters. An
independent-verification artifact that manufactures a discrepancy is worse than one that finds
none, because its whole value is that its findings can be trusted in both directions.

**Cause.** A regex-shaped assumption — that PUMS allocation flags are exactly the columns
matching `F*P` — was written into a one-off check and never tested against the data dictionary,
then reported as a measurement. It is the same failure this repository has spent two rounds
killing in other people's candidates: a heuristic mistaken for ground truth. It was caught only
because the raw column list was printed alongside the count, which is luck, not process.

**Fix.** Two changes, both made. (1) The artifact now records 77 with its derivation stated
explicitly, so the count can be checked without rerunning anything. (2) The standing rule, now
in `docs/OPERATING_RULES.md` §8: a count derived from a *pattern over names* is not a
measurement until the pattern has been checked against the authoritative definition, and any
artifact reporting such a count must print the derivation beside it. Where a check disagrees
with the thing it is checking, the check is assumed wrong until it is shown otherwise.
